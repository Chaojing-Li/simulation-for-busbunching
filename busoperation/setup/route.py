from abc import ABC, abstractmethod
from typing import List, Dict, Tuple
from dataclasses import dataclass

INF = int(1e8)


@dataclass
class Route:
    route_id: str
    terminal_id: str
    visit_seq_stops: List[str]
    end_terminal_id: str
    od_rate_table: Dict[str, Dict[str, float]]
    schedule_headway: float
    schedule_headway_std: float
    boarding_rate: Dict[str, float]
    bus_capacity: int


class RouteInfo(ABC):
    """ Abstract class for defining route information.

    Attributes
        route_infos: a dictionary of Route objects that contains all the route information, i.e., {route_id -> Route}
        route_OD_rate_table: a dictionary of route-specific od rate table, i.e., {route_id -> {stop_id -> {stop_id -> od_rate}}}
        end_terminal: a dictionary of route-specific ending terminal, i.e., {route_id -> terminal_id}
        terminal_to_routes_info: a dictionary of terminal to routes, i.e., {terminal_id -> [Route]}

    Methods:

    Abstract Methods:
        _define_route_ids(self) -> List[str]
        _define_od_table(self) -> Dict[str, Dict[str, Dict[str, float]]]
        _define_schedule_headway(self) -> Dict[str, Tuple[float, float]]
        _define_terminal(self) -> Dict[str, str]
        _define_visit_seq_stops(self) -> Dict[str, List[str]]
        _define_end_terminal(self) -> Dict[str, str]
        _define_boarding_rate(self) -> Dict[str, Dict[str, float]]

    """

    # a list of ids of routes running in the network
    _route_ids: List[str]
    # od demand rate (i.e., pax/sec) table for each route
    _route_od_rate_table: Dict[str, Dict[str, Dict[str, float]]]
    # each route's starting terminal id
    _route_terminals: Dict[str, str]
    # each route's visited stop ids
    _route_visit_seq_stops: Dict[str, List[str]]
    # each route's ending terminal id
    _route_end_terminals: Dict[str, str]
    # each route's schedule headway
    _route_schedule_headway_infos: Dict[str, Tuple[float, float]]
    # each route's stop-specific boarding rate
    _route_boarding_rate: Dict[str, Dict[str, float]]
    _route_infos: Dict[str, Route]

    def __init__(self) -> None:
        self._route_ids = self._define_route_ids()
        # route -> od_rate_table
        # od_rate_table: Dict[stop_id, Dict[stop_id, od_rate]]
        self._route_od_rate_table = self._define_od_table()
        # route -> terminal id
        self._route_terminals = self._define_terminal()
        # route -> visited stop ids
        self._route_visit_seq_stops = self._define_visit_seq_stops()
        # route -> ending terminal id
        self._route_end_terminals = self._define_end_terminal()
        # route -> schedule (dispatching) headway
        self._route_schedule_headway_infos = self._define_schedule_headway()
        self._route_boarding_rate = self._define_boarding_rate()

        # transform the route information into a dictionary of Route objects
        self._route_infos = {}
        for route_id in self._route_ids:
            route = Route(
                route_id=route_id,
                terminal_id=self._route_terminals[route_id],
                visit_seq_stops=self._route_visit_seq_stops[route_id],
                end_terminal_id=self._route_end_terminals[route_id],
                od_rate_table=self._route_od_rate_table[route_id],
                schedule_headway=self._route_schedule_headway_infos[route_id][0],
                schedule_headway_std=self._route_schedule_headway_infos[route_id][1],
                boarding_rate=self._route_boarding_rate[route_id],
                bus_capacity=INF
            )
            self._route_infos[route_id] = route

    @property
    def route_infos(self) -> Dict[str, Route]:
        return self._route_infos

    @property
    def route_OD_rate_table(self) -> Dict[str, Dict[str, Dict[str, float]]]:
        return self._route_od_rate_table

    @property
    def end_terminal(self) -> Dict[str, str]:
        return self._route_end_terminals

    @property
    def terminal_to_routes_info(self) -> Dict[str, List[Route]]:
        terminal_to_route_info = {}

        # for starting terminal with dispatching routes
        terminal_to_routes = self._find_terminal_to_common_routes()
        for terminal_id, routes in terminal_to_routes.items():
            terminal_to_route_info[terminal_id] = [
                self._route_infos[route] for route in routes]

        # for ending terminal without any dispatching routes
        for route, terminal in self._route_end_terminals.items():
            if terminal not in terminal_to_route_info:
                terminal_to_route_info[terminal] = []

        return terminal_to_route_info

    def _find_terminal_to_common_routes(self) -> Dict[str, List[str]]:
        terminal_to_routes = {}
        for route, terminal in self._route_terminals.items():
            if terminal not in terminal_to_routes:
                terminal_to_routes[terminal] = []
            terminal_to_routes[terminal].append(route)
        return terminal_to_routes

    @abstractmethod
    def _define_route_ids(self) -> List[str]:
        ...

    @abstractmethod
    def _define_od_table(self) -> Dict[str, Dict[str, Dict[str, float]]]:
        ...

    @abstractmethod
    def _define_schedule_headway(self) -> Dict[str, Tuple[float, float]]:
        ...

    @abstractmethod
    def _define_terminal(self) -> Dict[str, str]:
        ...

    @abstractmethod
    def _define_visit_seq_stops(self) -> Dict[str, List[str]]:
        ...

    @abstractmethod
    def _define_end_terminal(self) -> Dict[str, str]:
        ...

    @abstractmethod
    def _define_boarding_rate(self) -> Dict[str, Dict[str, float]]:
        ...
