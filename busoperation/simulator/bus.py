from typing import List, Literal, Dict, Optional
from collections import defaultdict

from simulator.virtual_bus import VirtualBus
from setup.route import Route

from .pax_generation import Pax
from .trajectory import TrajectoryPoint
from .snapshot import BusSnapshot
from .log import BusRunningLog


class Bus:
    ''' Represent a bus in the simulation.

    Attributes:
        log: BusRunningLog
        speed: traversing speed on link, in meters/sec
        loc_relative_to_terminal: location relative to the terminal, in meters
        trajectory: time-point trajectory for plotting
        route_id: route id
        bus_id: bus id
        board_status: boarding status, either 'boarding' or 'idle'

    Methods:
        set_status(self, status: Literal['dispatching', 'running_on_link', 'decelerating', 
                                        'queueing_at_stop', 'dwelling_at_stop', 'accelerating', 
                                        'holding', 'finished'])
        accumate_board_fraction(self) -> None
        board(self, pax: Pax) -> None
        update_location(self, t: int, spot_type: str, spot_id: str, node_id: str, offset: float) -> None
        take_snapshot(self) -> BusSnapshot

    '''

    _bus_id: str
    _route_id: str
    _capacity: int
    _node_distance: Dict[str, float]
    _status: Literal['dispatching', 'running_on_link', 'decelerating',
                     'queueing_at_stop', 'dwelling_at_stop', 'accelerating', 'holding', 'finished']
    _board_status: Literal['boarding', 'idle']
    # onboard pax list
    _paxs: List[Pax]
    # boarding fraction indicate how much of a single boarding action has been completed
    _board_fraction: float
    # the boarding rate determined by the boarding pax
    _pax_board_rate: Optional[float]
    _trajectory: Dict[int, TrajectoryPoint]
    log: BusRunningLog
    speed: float
    loc_relative_to_terminal: float

    def __init__(self, bus_id: str,
                 route: Route,
                 node_distance: Dict[str, float],
                 virtual_bus: VirtualBus
                 ) -> None:

        self._bus_id = bus_id
        self._route_id = route.route_id
        self._capacity = route.bus_capacity
        # the distance of each node from the terminal
        self._node_distance = node_distance

        self._status = 'dispatching'
        self._board_status = 'idle'
        self._paxs = []
        self._board_fraction = 0.0
        self._pax_board_rate = None
        self._trajectory = {}

        virtual_bus_stop_arrival_time = virtual_bus.route_stop_arrival_time[self._route_id]
        virtual_bus_stop_rtd_time = virtual_bus.route_stop_rtd_time[self._route_id]
        virtual_bus_stop_departure_time = virtual_bus.route_stop_departure_time[self._route_id]

        self.log = BusRunningLog(
            route.schedule_headway, virtual_bus_stop_arrival_time, virtual_bus_stop_rtd_time, virtual_bus_stop_departure_time)
        self.speed = 0.0
        self.loc_relative_to_terminal = 0.0

    def __repr__(self) -> str:
        return f'Bus {self._bus_id} on route {self._route_id} with pax_num {len(self._paxs)}'

    @property
    def trajectory(self) -> Dict[int, TrajectoryPoint]:
        return self._trajectory

    @property
    def route_id(self) -> str:
        return self._route_id

    @property
    def bus_id(self) -> str:
        return self._bus_id

    @property
    def board_status(self) -> Literal['boarding', 'idle']:
        return self._board_status

    def set_status(self, status: Literal['dispatching', 'running_on_link', 'decelerating',
                                         'queueing_at_stop', 'dwelling_at_stop', 'accelerating',
                                         'holding', 'finished']) -> None:
        self._status = status

    def accumate_board_fraction(self) -> None:
        ''' Accumulate the board fraction for bus that is boarding pax.

        The bus will be first set to 'boarding' status from 'idle' status, and then the board fraction will be accumulated.
        After the board fraction reaches 1, the bus will be set to 'idle' status again.
        The process will be repeated for the next boarding pax.

        '''
        assert self._board_status == 'boarding', 'bus is not boarding, cannot accumate board fraction'
        assert self._pax_board_rate is not None, 'pax board rate is None'
        self._board_fraction += self._pax_board_rate
        if self._board_fraction >= 1:
            self._board_fraction -= 1
            self._board_status = 'idle'
            self._pax_board_rate = None

    def board(self, pax: Pax) -> None:
        ''' Board pax onto the bus.

        The pax is first added to the onboard pax list, 
        and then the bus is set to 'boarding' status and boarding fraction will be accumulated.

        Args:
            pax: the pax to board onto the bus

        '''
        self._board_status = 'boarding'
        self._pax_board_rate = pax.board_rate
        self._paxs.append(pax)

    def update_location(self, t: int, spot_type: str, spot_id: str, node_id: str, offset: float) -> None:
        ''' Update bus's relative location to the terminal.

        One purpose is to record trajectory for plotting.
        Another purpose is to provide a state of the current bus, for the control agent to make decisions.

        Args:
            t: current time
            spot_type: 'link', 'node' or 'holder'
            spot_id: the id of the spot
            offset: for the spot_type of 'link', the offset from the head node
                    for the spot_type of 'stop', offset=0
        '''
        self.loc_relative_to_terminal = self._node_distance[node_id] + offset
        self._trajectory[t] = TrajectoryPoint(
            spot_type, spot_id, self.loc_relative_to_terminal)

    def take_snapshot(self) -> BusSnapshot:
        '''Take a snapshot of the bus at the current time step.

        Pax_num, loc_relative_to_terminal and status are instantaneous values.
        Dwell times, link tt deviation, epsilon arrival and epsilon rtd contains all the historical values by `RunningLog`

        Returns:
            BusSnapshot: a snapshot of the bus at the current time step
        '''

        pax_num = len(self._paxs)
        bus_snapshot = BusSnapshot(self._bus_id, self._route_id, pax_num, self.loc_relative_to_terminal,
                                   self._status, dict(
                                       self.log.stop_dwell_time), self.log.link_tt_deviation,
                                   self.log.stop_epsilon_arrival, self.log.stop_epsilon_rtd,
                                   self.log.stop_epsilon_departure, self.log.visited_stops)
        return bus_snapshot
