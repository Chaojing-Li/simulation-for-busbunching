from typing import List, Optional, Dict, Tuple
from collections import defaultdict

from simulator.virtual_bus import VirtualBus
from setup.blueprint import Blueprint


class StopLog:
    def __init__(self, stop_id: str, virtual_bus: VirtualBus) -> None:
        # route -> [arrival time at this stop]
        self.route_arrival_time_seq: Dict[str, List[float]] = {}
        # route -> [arrival bus_id]
        self.route_arrival_bus_id_seq: Dict[str, List[str]] = {}
        # route -> [rtd time at this stop]
        self.route_rtd_time_seq: Dict[str, List[float]] = {}
        # route -> [rtd bus_id]
        self.route_rtd_bus_id_seq: Dict[str, List[str]] = {}
        # record: route_id -> [bus_id -> epsilon when arrival]
        self.route_bus_epsilon_arrival: Dict[str,
                                             Dict[str, float]] = defaultdict(dict)
        # record: route_id -> [bus_id -> epsilon when rtd]
        self.route_bus_epsilon_rtd: Dict[str,
                                         Dict[str, float]] = defaultdict(dict)

        # initialize the arrival time of the first virtual bus with `bus_id=0` on each route
        for route_id, stop_arrival_time in virtual_bus.route_stop_arrival_time.items():
            arrival_time_this_stop = stop_arrival_time[stop_id]
            self.route_arrival_time_seq[route_id] = [arrival_time_this_stop]
            self.route_arrival_bus_id_seq[route_id] = ['0']
            # the epsilon_arrival of the first virtual bus is 0
            self.route_bus_epsilon_arrival[route_id]['0'] = 0

        # initialize the rtd time of the first virtual bus with `bus_id=0` on each route
        for route_id, stop_rtd_time in virtual_bus.route_stop_rtd_time.items():
            rtd_time_this_stop = stop_rtd_time[stop_id]
            self.route_rtd_time_seq[route_id] = [rtd_time_this_stop]
            self.route_rtd_bus_id_seq[route_id] = ['0']
            # the epsilon_rtd of the first virtual bus is 0
            self.route_bus_epsilon_rtd[route_id]['0'] = 0

    def record_when_bus_arrival(self, route_id: str, bus_id: str, t: int, epsilon_arrival: float) -> None:
        self.route_bus_epsilon_arrival[route_id][bus_id] = epsilon_arrival
        self.route_arrival_time_seq[route_id].append(t)
        self.route_arrival_bus_id_seq[route_id].append(bus_id)

    def record_when_bus_rtd(self, route_id: str, bus_id: str, t: int, epsilon_rtd: float) -> None:
        self.route_bus_epsilon_rtd[route_id][bus_id] = epsilon_rtd
        self.route_rtd_time_seq[route_id].append(t)
        self.route_rtd_bus_id_seq[route_id].append(bus_id)


class HolderLog:
    def __init__(self, virtual_bus: VirtualBus) -> None:
        self.route_stop_departure_time_seq: Dict[str, Dict[str, List[float]]] = defaultdict(
            lambda: defaultdict(list))
        self.route_stop_departure_bus_id_seq: Dict[str, Dict[str, List[str]]] = defaultdict(
            lambda: defaultdict(list))

        self.route_stop_bus_epsilon_departure: Dict[str, Dict[str, Dict[str, float]]] = defaultdict(
            lambda: defaultdict(dict))

        # initialize the departure time of the first virtual bus with `bus_id=0` on each route
        for route_id, stop_departure_time in virtual_bus.route_stop_departure_time.items():
            for stop_id, departure_time in stop_departure_time.items():
                self.route_stop_departure_time_seq[route_id][stop_id] = [
                    departure_time]
                self.route_stop_departure_bus_id_seq[route_id][stop_id] = ['0']
                # the epsilon_departure of the first virtual bus is 0
                self.route_stop_bus_epsilon_departure[route_id][stop_id]['0'] = 0

    def record_when_bus_departure(self, stop_id: str, route_id: str, bus_id: str,
                                  t: int, epsilon_departure: float) -> None:
        self.route_stop_departure_time_seq[route_id][stop_id].append(t)
        self.route_stop_departure_bus_id_seq[route_id][stop_id].append(bus_id)
        self.route_stop_bus_epsilon_departure[route_id][stop_id][bus_id] = epsilon_departure


class BusRunningLog:
    def __init__(self, schedule_headway: float, virtual_bus_stop_arrival_time: Dict[str, float],
                 virtual_bus_stop_rtd_time: Dict[str, float], virtual_bus_stop_departure_time: Dict[str, float]) -> None:

        self.virtual_bus_stop_arrival_time = virtual_bus_stop_arrival_time
        self.virtual_bus_stop_rtd_time = virtual_bus_stop_rtd_time
        self.virtual_bus_stop_departure_time = virtual_bus_stop_departure_time

        # mean of H
        self.schedule_headway = schedule_headway
        # record the dispatch time from the terminal
        self.dispatch_time: Optional[int] = None
        # record the end time of the bus operation
        self.end_time: Optional[int] = None

        # record the link travel time deviation from mean at each stop
        self.link_tt_deviation: Dict[str, float] = {}
        # record the dwell time at each stop
        self.stop_dwell_time: Dict[str, int] = defaultdict(int)
        # record visited stops
        self.visited_stops: List[str] = []

        # record the schedule deviation when arrival at each stop
        self.stop_epsilon_arrival: Dict[str, float] = {}
        # record the schedule deviation when ready-to-departure at each stop
        self.stop_epsilon_rtd: Dict[str, float] = {}
        # record the schedule deviation when departure after holding (at the holder)
        self.stop_epsilon_departure: Dict[str, float] = {}

    def record_when_dispatch(self, t: int) -> None:
        self.dispatch_time = t
        self.terminal_epsilon_departure = 0

    def record_when_enter_link(self, link_id: str, tt_deviation: float) -> None:
        self.link_tt_deviation[link_id] = tt_deviation

    def record_when_arrival(self, stop_id: str, t: int,  last_arrival_idx_count: int) -> float:
        shift = self.schedule_headway * last_arrival_idx_count
        schedule_arrival = self.virtual_bus_stop_arrival_time[stop_id] + shift
        epsilon_arrival = t - schedule_arrival
        self.stop_epsilon_arrival[stop_id] = epsilon_arrival
        return epsilon_arrival

    def record_when_dwell(self, stop_id: str) -> None:
        self.stop_dwell_time[stop_id] += 1

    def record_when_rtd(self, stop_id: str, t: int,  last_rtd_idx_count: int) -> float:
        shift = self.schedule_headway * last_rtd_idx_count
        schedule_rtd = self.virtual_bus_stop_rtd_time[stop_id] + shift
        epsilon_rtd = t - schedule_rtd
        self.stop_epsilon_rtd[stop_id] = epsilon_rtd
        return epsilon_rtd

    def record_when_departure(self, stop_id: str, t: int, last_departure_idx_count: int) -> float:
        shift = self.schedule_headway * last_departure_idx_count
        schedule_departure = self.virtual_bus_stop_departure_time[stop_id] + shift
        epsilon_departure = t - schedule_departure
        self.stop_epsilon_departure[stop_id] = epsilon_departure
        return epsilon_departure

    def record_when_finish(self, t: int) -> None:
        self.end_time = t
