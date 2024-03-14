from typing import List, Optional, Dict, Tuple
from abc import ABC, abstractmethod

from agent.agent import Agent
from setup.config_dataclass import StopNodeGeometry, StopNodeOperation

from .pax_queue import PaxQueue
from .bus import Bus
from .pax_generation import Pax
from .snapshot import StopSnapshot
from .log import StopLog


class Stop(ABC):
    _stop_id: str
    _berth_num: int
    _distance_from_terminal: float
    _arrive_queue: List[Bus]
    # _pax_queue: PaxQueue
    _entry_queue: List[Bus]
    _buses_in_berth: List[Optional[Bus]]
    _leave_queue: List[Bus]

    def __init__(self, stop_id: str, node_geometry: StopNodeGeometry, agent: Agent):
        self._stop_id = stop_id
        self._berth_num = node_geometry.berth_num
        self._distance_from_terminal = node_geometry.distance_from_terminal

        # arriving area for buses to decelerate
        self._arrive_queue = []
        # queueing area for buses waiting to enter the berth
        self._entry_queue = []

        # buses in berth:
        # if the berth is empty, then the value is None
        # if the berth is occupied, then the value is the bus
        # the index larger, the berth closer to the downstream
        self._buses_in_berth = [None] * self._berth_num
        # buses finished service, door closed and accelerating
        self._leave_queue = []

        # track the remaining time of bus deceleration when entering the berth
        self._bus_deceleration_remain_time: Dict[Tuple[str, str], float] = {}
        # track the remaining time of acceleration time leaving the stop
        self._bus_acceleration_remain_time: Dict[Tuple[str, str], float] = {}

        self.log = StopLog(self._stop_id, agent.virtual_bus)

        # # instantiated by subclass
        # self._pax_queue

    @property
    @abstractmethod
    def _pax_queue(self) -> PaxQueue:
        ...

    def take_snapshot(self) -> StopSnapshot:
        total_pax_num = self._pax_queue.get_total_pax_num()
        stop_snapshot = StopSnapshot(self._stop_id, total_pax_num,
                                     self.log.route_arrival_time_seq, self.log.route_arrival_bus_id_seq,
                                     self.log.route_rtd_time_seq, self.log.route_rtd_bus_id_seq,
                                     self.log.route_bus_epsilon_arrival, self.log.route_bus_epsilon_rtd)
        return stop_snapshot

    # accept passengers arriving at this stop
    def pax_arrive(self, paxs: List[Pax]):
        for pax in paxs:
            self._pax_queue.add_pax(pax)

    # accept a bus entering this stop
    def enter_stop(self, bus: Bus, t: int):
        self._arrive_queue.append(bus)
        bus.update_location(t, 'stop', self._stop_id, self._stop_id, 0)

        # initialize the remaining time of bus deceleration and door opening time when entering the berth
        self._bus_deceleration_remain_time[(bus.route_id, bus.bus_id)] = 0
        bus.set_status('decelerating')

    @abstractmethod
    def get_total_buses(self) -> List[Bus]:
        ...

    # accept a bus entering the berth
    @abstractmethod
    def _enter_berth(self) -> None:
        ...

    @abstractmethod
    def _arriving(self, t: int) -> None:
        ...

    @abstractmethod
    def _board(self, t) -> None:
        ...

    @abstractmethod
    def _check_leave(self, t: int):
        ...

    @abstractmethod
    def _leave(self, t: int) -> List[Bus]:
        ...

    # move buses one step (delta t) forward
    def operation(self, t: int):
        for bus in self.get_total_buses():
            bus.update_location(t, 'stop', self._stop_id, self._stop_id, 0)
        self._arriving(t)
        self._enter_berth()
        self._board(t)
        self._check_leave(t)
        leaving_buses = self._leave(t)
        return leaving_buses


class BoardingStop(Stop):
    def __init__(self, stop_id: str, stop_node_geometry: StopNodeGeometry, stop_node_operation: StopNodeOperation, agent: Agent):
        super().__init__(stop_id, stop_node_geometry, agent)
        self._queue_rule = stop_node_operation.queue_rule
        self._is_alight = stop_node_operation.is_alight
        self._board_truncation = stop_node_operation.board_truncation
        self._board_pax_queue = PaxQueue(stop_id, self._board_truncation)

    @property
    def _pax_queue(self) -> PaxQueue:
        ''' Implement the abstract property method from the parent class

        '''
        return self._board_pax_queue

    def get_total_buses(self) -> List[Bus]:
        ''' Return all the buses in the stop, including buses in berth and buses in queue

        Returns:
            List[Bus]: all the buses in the stop
        '''
        buses_in_arrive_queue = [bus for bus in self._arrive_queue]
        buses_in_queue = [bus for bus in self._entry_queue]
        buses_in_berth = [
            bus for bus in self._buses_in_berth if bus is not None]
        buses_in_leave_queue = [bus for bus in self._leave_queue]
        return buses_in_arrive_queue + buses_in_queue + buses_in_berth + buses_in_leave_queue

    def _arriving(self, t: int) -> None:
        entering_buses: List[Bus] = []
        for bus in self._arrive_queue:
            remain_time = self._bus_deceleration_remain_time[(
                bus.route_id, bus.bus_id)]
            if remain_time == 0:
                entering_buses.append(bus)
                self._arrive_queue.remove(bus)

                # the bus arrived in the entry queue
                arrival_idx_count = len(
                    self.log.route_arrival_time_seq[bus.route_id])
                # last_arrival_time = self.log.route_arrival_time_seq[bus.route_id][-1]
                epsilon_arrival = bus.log.record_when_arrival(
                    self._stop_id, t, arrival_idx_count)

                self.log.record_when_bus_arrival(
                    bus.route_id, bus.bus_id, t, epsilon_arrival)
            else:
                self._bus_deceleration_remain_time[(
                    bus.route_id, bus.bus_id)] -= 1
                bus.set_status('decelerating')

        for enter_bus in entering_buses:
            self._entry_queue.append(enter_bus)
            enter_bus.set_status('queueing_at_stop')

    def _enter_berth(self) -> None:
        if len(self._entry_queue) == 0:
            return

        head_bus = self._entry_queue[0]
        # decelaeration and door opening operations
        target_berth = self._get_target_berth()
        if target_berth >= 0:  # has available berth
            self._buses_in_berth[target_berth] = head_bus
            head_bus.set_status('dwelling_at_stop')
            self._entry_queue.pop(0)

    def _board(self, t: int) -> None:
        for bus_in_berth in self._buses_in_berth:
            if bus_in_berth is None:
                continue
            self._pax_queue.board(bus_in_berth, t)
            bus_in_berth.log.record_when_dwell(self._stop_id)

    def _check_leave(self, t: int):
        for berth_idx, bus_in_berth in enumerate(self._buses_in_berth):
            if bus_in_berth is None:
                continue
            remaining_pax_num = self._pax_queue.check_remaining_pax_num(
                bus_in_berth)
            if remaining_pax_num == 0:
                # initialize the remaining time of door closing time and bus acceleration time leaving the stop
                self._bus_acceleration_remain_time[(
                    bus_in_berth.route_id, bus_in_berth.bus_id)] = 0
                self._buses_in_berth[berth_idx] = None
                self._leave_queue.append(bus_in_berth)

    def _leave(self, t: int) -> List[Bus]:
        leaving_buses: List[Bus] = []
        for bus in self._leave_queue:
            remain_time = self._bus_acceleration_remain_time[(
                bus.route_id, bus.bus_id)]
            # the bus left the stop after acceleration
            if remain_time == 0:
                rtd_idx_count = len(
                    self.log.route_rtd_bus_id_seq[bus.route_id])
                # last_rtd_time = self.log.route_rtd_time_seq[bus.route_id][-1]
                epsilon_rtd = bus.log.record_when_rtd(
                    self._stop_id, t, rtd_idx_count)
                self.log.record_when_bus_rtd(
                    bus.route_id, bus.bus_id, t, epsilon_rtd)
                leaving_buses.append(bus)
                self._leave_queue.remove(bus)
            else:
                bus.set_status('accelerating')
                self._bus_acceleration_remain_time[(
                    bus.route_id, bus.bus_id)] -= 1
        return leaving_buses

    def _get_target_berth(self) -> int:
        target_berth = -1  # negative means no berth is available
        for b in range(len(self._buses_in_berth) - 1, -1, -1):
            if self._buses_in_berth[b] == None:
                target_berth = b
            else:
                break
        return target_berth
