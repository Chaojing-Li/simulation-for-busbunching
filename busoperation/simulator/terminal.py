from typing import List, Dict

from agent.agent import Agent
from setup.route import Route
from setup.config_dataclass import TerminalNodeGeometry, TerminalNodeOperation
from setup.blueprint import Blueprint
from simulator.virtual_bus import VirtualBus

from .bus import Bus


class Terminal:
    """ Terminal class that dispatches buses to work on routes and recycle buses that have finished their work.

    Attributes:
    """

    _terminal_id: str
    _blueprint: Blueprint
    _routes: List[Route]
    _route_round_count: Dict[str, int]

    def __init__(self, terminal_id: str, terminal_node_geometry: TerminalNodeGeometry,
                 terminal_node_operation: TerminalNodeOperation, routes: List[Route],
                 blueprint: Blueprint, virtual_bus: VirtualBus) -> None:

        # TODO Terminal_node_geometry and terminal_node_operation are not used yet
        # Maybe used in the future when considering terminal operations (e.g., schedule planning and EV charging)

        self._terminal_id = terminal_id
        # A blueprint contains the network and route information
        self._blueprint = blueprint
        # the routes that start from this terminal
        self._routes = routes
        # count how many buses have been dispatched on each route
        self._route_round_count = {route.route_id: 1 for route in self._routes}
        # the virtual bus is used to get the schedules for each route
        self._virtual_bus = virtual_bus

    def dispatch(self, t: int) -> List[Bus]:
        """Dispatch buses from this terminal.

        Args:
            t: current time

        Returns:
            List[Bus]: a list of buses that are dispatched from this terminal
        """

        dispatching_buses = []
        for route in self._routes:
            # The first bus on a route is dispatched one schedule headway after the simulation starts.
            # TODO add std to the schedule headway
            if t % int(route.schedule_headway) == 0 and t > 0:
                # A bus's id is the number of times that the buses on this route has been dispatched.
                bus_id = str(self._route_round_count[route.route_id])
                node_distance: Dict[str,
                                    float] = self._blueprint.route_node_distance[route.route_id]

                bus = Bus(bus_id, route, node_distance,
                          self._virtual_bus)
                bus.log.record_when_dispatch(t)
                dispatching_buses.append(bus)
                self._route_round_count[route.route_id] += 1

                # bus.log.record_when_departure(self._terminal_id, t, 0)

                # print('dispatching bus on route {} with id {}'.format(
                #     route.route_id, bus_id))

        return dispatching_buses

    def recycle(self, bus: Bus) -> None:
        bus.set_status('finished')
