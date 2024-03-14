from typing import List, Optional
from abc import ABC, abstractmethod

from agent.agent import Agent
from setup.config_dataclass import StopNodeGeometry
from simulator.virtual_bus import VirtualBus

from .pax_queue import PaxQueue
from .bus import Bus
from .pax_generation import Pax
from .snapshot import StopSnapshot
from .log import StopLog


class Stop(ABC):
    _stop_id: str
    _berth_num: int
    _distance_from_terminal: float
    # _pax_queue: PaxQueue
    _entry_queue: List[Bus]
    _buses_in_berth: List[Optional[Bus]]
    _leave_queue: List[Bus]

    def __init__(self, stop_id: str, node_geometry: StopNodeGeometry, virtual_bus: VirtualBus):
        self._stop_id = stop_id
        self._berth_num = node_geometry.berth_num
        self._distance_from_terminal = node_geometry.distance_from_terminal

        # queueing area for buses waiting to enter the berth
        self._entry_queue = []
        # buses in berth:
        # if the berth is empty, then the value is None
        # if the berth is occupied, then the value is the bus
        # the index larger, the berth closer to the downstream
        self._buses_in_berth = [None] * self._berth_num

        self.log = StopLog(self._stop_id, virtual_bus)
        # store buses finished service and used for processing the leaving event
        self._leave_queue = []

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
        # the bus arrived in the entry queue
        arrival_idx_count = len(
            self.log.route_arrival_time_seq[bus.route_id])
        # last_arrival_time = self.log.route_arrival_time_seq[bus.route_id][-1]
        epsilon_arrival = bus.log.record_when_arrival(
            self._stop_id, t, arrival_idx_count)
        self.log.record_when_bus_arrival(
            bus.route_id, bus.bus_id, t, epsilon_arrival)
        self._entry_queue.append(bus)
        bus.set_status('queueing_at_stop')
        bus.update_location(t, 'stop', self._stop_id, self._stop_id, 0)

    @abstractmethod
    def get_total_buses(self) -> List[Bus]:
        ...

    # accept a bus entering the berth
    @abstractmethod
    def _enter_berth(self) -> None:
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
        self._enter_berth()
        self._board(t)
        self._check_leave(t)
        leaving_buses = self._leave(t)
        return leaving_buses
