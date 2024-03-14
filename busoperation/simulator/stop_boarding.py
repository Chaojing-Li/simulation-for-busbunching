from typing import List

from agent.agent import Agent
from setup.config_dataclass import StopNodeGeometry, StopNodeOperation
from simulator.virtual_bus import VirtualBus

from .stop import Stop
from .pax_queue import PaxQueue
from .bus import Bus


class BoardingStop(Stop):
    def __init__(self, stop_id: str, stop_node_geometry: StopNodeGeometry,
                 stop_node_operation: StopNodeOperation, virtual_bus: VirtualBus):
        super().__init__(stop_id, stop_node_geometry, virtual_bus)
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
        buses_in_queue = [bus for bus in self._entry_queue]
        buses_in_berth = [
            bus for bus in self._buses_in_berth if bus is not None]
        return buses_in_queue + buses_in_berth

    def _enter_berth(self) -> None:
        if len(self._entry_queue) == 0:
            return
        head_bus = self._entry_queue[0]
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
                self._buses_in_berth[berth_idx] = None
                self._leave_queue.append(bus_in_berth)

    def _leave(self, t: int) -> List[Bus]:
        leaving_buses: List[Bus] = []
        for bus in self._leave_queue:
            rtd_idx_count = len(
                self.log.route_rtd_bus_id_seq[bus.route_id])
            # last_rtd_time = self.log.route_rtd_time_seq[bus.route_id][-1]
            epsilon_rtd = bus.log.record_when_rtd(
                self._stop_id, t, rtd_idx_count)
            self.log.record_when_bus_rtd(
                bus.route_id, bus.bus_id, t, epsilon_rtd)
            leaving_buses.append(bus)
            self._leave_queue.remove(bus)
        return leaving_buses

    def _get_target_berth(self) -> int:
        target_berth = -1  # negative means no berth is available
        for b in range(len(self._buses_in_berth) - 1, -1, -1):
            if self._buses_in_berth[b] == None:
                target_berth = b
            else:
                break
        return target_berth
