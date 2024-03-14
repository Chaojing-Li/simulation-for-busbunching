from typing import List, Dict, Tuple
from collections import defaultdict

from agent.agent import Agent
from setup.blueprint import Blueprint
from simulator.virtual_bus import VirtualBus

from .holder import Holder
from .bus import Bus
from .pax_generation import PaxGenerator
from .terminal import Terminal
from .tracer import Tracer
from .snapshot import Snapshot
from .mediator import Mediator
from .builder import Builder
from .link import Link
from .stop import Stop


class Simulator:
    ''' The simulator that simulates the operation of a bus system.

    Attributes:
        total_buses: all the buses that have been dispatched from terminals

    Methods:
        step(self, t: int, stop_bus_hold_times: Dict[Tuple[str, str, str], float]) -> Snapshot
        take_snapshot(self, t: int) -> Snapshot
        get_metrics(self) -> Tuple[Dict[str, float], Dict[str, Dict[int, int]]]
        get_stop_average_hold_time(self) -> Dict[str, Dict[str, float]]

    '''
    _agent: Agent
    _blueprint: Blueprint
    _builder: Builder
    _virtual_bus: VirtualBus
    _pax_generator: PaxGenerator
    _terminals: Dict[str, Terminal]
    _links: Dict[str, Link]
    _stops: Dict[str, Stop]
    _holder: Holder
    _mediator: Mediator
    _tracer: Tracer
    _total_buses: List[Bus]

    def __init__(self, blueprint: Blueprint, agent: Agent) -> None:
        self._agent = agent
        self._blueprint = blueprint
        # A builder is used to create all the components in the simulation with the help of a blueprint
        self._builder = Builder(blueprint)

        # A virtual bus is used to specify the `initial` condition of the dynamics
        # if the agent has created a virtual bus (by repeatedly running the simulation and taking the convergent holding time), use it
        # otherwise, create a virtual bus with perfect schedule (without repeated simulation)
        if hasattr(agent, 'virtual_bus'):
            self._virtual_bus = agent.virtual_bus
        else:
            self._virtual_bus = self._builder.create_virtual_bus(self._agent)
        # # A pax generator is used to generate passengers at stops
        self._pax_generator = self._builder.create_pax_generator(
            self._virtual_bus)
        # Terminals that dispatch and recycle buses
        self._terminals = self._builder.create_terminals(self._virtual_bus)
        # Links that buses run on
        self._links = self._builder.create_links()
        # Stops that buses stop at to pick up and drop off passengers
        self._stops = self._builder.create_stops(self._virtual_bus)
        # Holder that holds buses after they finish their operation at a stop
        self._holder: Holder = Holder(self._agent, self._virtual_bus)
        # A mediator is used to transfer buses between components
        self._mediator: Mediator = Mediator(
            blueprint, self._terminals, self._links, self._stops, self._holder)

        # A tracer is used to record the status of the simulation
        self._tracer: Tracer = Tracer()
        # Maintain a list of all the buses that have been dispatched from terminals
        # used for time-space diagram visualization in the end
        self._total_buses: List[Bus] = []

        # self._network.visualize()

    @property
    def total_buses(self) -> List[Bus]:
        ''' Get all the buses that have been dispatched from terminals.

        '''
        return self._total_buses

    def step(self, t: int, stop_bus_hold_times: Dict[Tuple[str, str, str], float]) -> Snapshot:
        '''Accept holding actions and move buses one step forward

        Args:
            t: current time
            stop_bus_hold_times: {(stop_id, route_id, bus_id): specified holding time}

        Returns:
            Snapshot: a snapshot of current time t
        '''

        # 0. dispatch buses from terminal to their first links
        for terminal_id, terminal in self._terminals.items():
            dispatching_buses = terminal.dispatch(t)
            self._mediator.transfer(
                dispatching_buses, 'terminal', terminal_id, t)
            # record all the dispatched buses for future visualization
            for bus in dispatching_buses:
                self._total_buses.append(bus)

        # 1. passengers arrive at stops
        stop_paxs = self._pax_generator.generate(t)
        for stop_id, paxs in stop_paxs.items():
            self._stops[stop_id].pax_arrive(paxs)

        # 2. link operation
        for link_id, link in self._links.items():
            leaving_link_buses = link.forward(t)
            self._mediator.transfer(leaving_link_buses, 'link', link_id, t)

        # 3. stop operation
        for stop_id, stop in self._stops.items():
            leaving_stop_buses = stop.operation(t)
            self._mediator.transfer(leaving_stop_buses, 'stop', stop_id, t)

        # 4. holding operation
        self._holder.set_hold_action(stop_bus_hold_times)
        stop_held_buses = self._holder.operation(t)

        # transfer buses that finish holding to the next link
        for stop_id, held_buses in stop_held_buses.items():
            self._mediator.transfer(held_buses, 'holder', stop_id, t)

        snapshot = self.take_snapshot(t)
        return snapshot

    def take_snapshot(self, t: int) -> Snapshot:
        ''' Take a snapshot of the whole current state of the simulation.

        '''
        snapshot = self._tracer.take_snapshot(
            t, self._links, self._stops, self._holder)
        return snapshot

    def get_metrics(self) -> Tuple[Dict[str, float], Dict[str, Dict[int, int]]]:
        ''' Get the metrics of the simulation.

        Generally called after one episode of simulation finished.

        Returns:
            metrics: a dictionary of metrics
            route_dispatch_time_trip_time: a dictionary {route_id -> {dispatch_time -> trip_time}}
                dispatch_time is the time when the bus is dispatched from the terminal
                trip_time is the duration of the trip from the terminal to the ending terminal

        '''
        # stats all the stops except the last stop
        route_stats_stop_ids: Dict[str, List[str]] = defaultdict(list)
        for route_id, route in self._blueprint.route_info.route_infos.items():
            route_stats_stop_ids[route_id].extend(route.visit_seq_stops[:-1])
        metrics = self._tracer.get_metric(route_stats_stop_ids)

        # stats the trip time
        route_dispatch_time_trip_time: Dict[str, Dict[int, int]] = {}
        for route_id, route in self._blueprint.route_info.route_infos.items():
            dispatch_time_trip_time = {}
            for bus in self._total_buses:
                if bus.route_id == route_id:
                    if bus.log.end_time is not None:
                        assert bus.log.dispatch_time is not None
                        trip_time = bus.log.end_time - bus.log.dispatch_time
                        dispatch_time_trip_time[bus.log.dispatch_time] = trip_time
            route_dispatch_time_trip_time[route_id] = dispatch_time_trip_time
        return metrics, route_dispatch_time_trip_time

    def get_stop_average_hold_time(self) -> Dict[str, Dict[str, float]]:
        ''' Get the average holding time at each stop for each route.

        Generally called after one episode of simulation finished.

        '''
        route_stop_average_hold_time = self._tracer.get_stop_average_hold_time()
        return route_stop_average_hold_time
