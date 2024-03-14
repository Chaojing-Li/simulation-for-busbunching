from typing import Dict, Any, Tuple

from setup.blueprint import Blueprint
from simulator.virtual_bus import VirtualBus
from simulator.snapshot import Snapshot

from ..agent import Agent
from ..single_line_agent import AgentByLine


class XuanNonlinear(AgentByLine):
    ''' Nonlinear version of Xuan et al. (2011)

    '''

    _slack: float
    _f0: float
    _base_type: str

    def __init__(self, agent_config: Dict[str, Any], blueprint: Blueprint) -> None:
        super().__init__(agent_config, blueprint)
        self._slack = agent_config['slack']
        self._f0 = agent_config['f0']
        self._base_type = agent_config['base_type']
        self._blueprint = blueprint
        # self._generate_virtual_bus()

    def _generate_virtual_bus(self):
        ''' Generate the virtual bus.

        For nonlinear version, the average holding time at each stop is dynamically updated
            by running the simulation until convergence.

        '''
        # the virtual bus's average holding time is initialized to be the slack
        self._virtual_bus = VirtualBus(self._blueprint)
        self._virtual_bus.initialize_with_perfect_schedule(
            self._route_stop_arrival_rate, self._slack)

        # route_stop_average_hold_time: Dict[str, Dict[str, float]] = {}
        # for _ in range(1):
        #     simulator = Simulator(self._blueprint, self)
        #     stop_bus_hold_action: Dict[Tuple[str, str, str], float] = {}
        #     for t in range(int(3600*3)):
        #         snapshot = simulator.step(t, stop_bus_hold_action)
        #         stop_bus_hold_action = self.calculate_hold_time(snapshot)

        #     route_stop_average_hold_time = simulator.get_stop_average_hold_time()
        #     self._virtual_bus.update_trajectory(route_stop_average_hold_time)

    def calculate_hold_time(self, snapshot: Snapshot) -> Dict[Tuple[str, str, str], float]:
        stop_bus_hold_time = {}
        for (stop_id, route_id, bus_id) in snapshot.holder_snapshot.action_buses:

            stop_boarding_rate = self._blueprint.route_info.route_infos[route_id].boarding_rate
            arrival_rate = self._route_stop_arrival_rate[route_id][stop_id]
            beta = arrival_rate / stop_boarding_rate[stop_id]
            H = self._route_schedule[route_id]

            node_type, last_node_id = self._blueprint.get_previous_node(
                route_id, stop_id)
            last_rtd_time = snapshot.get_last_rtd_time(
                route_id, stop_id)
            current_time = snapshot.t
            h = current_time - last_rtd_time

            # for current bus
            # 1. get the current bus's `epsilon_arrival` and `epsilon_rtd` at the current stop
            epsilon_arrival_curr_stop, epsilon_rtd_curr_stop = snapshot.get_bus_epsilon(
                route_id, bus_id, stop_id)

            # # 2. get the current bus's `epsilon_arrival` and `epsilon_rtd` at the last stop
            # epsilon_arrival_last_stop, epsilon_rtd_last_stop = snapshot.get_bus_epsilon(
            #     route_id, bus_id, last_stop_id)

            # 3. get the current bus's `epsilon_departure` at the last stop
            if node_type == 'terminal':
                epsilon_departure_last_stop = 0
            else:
                epsilon_departure_last_stop = snapshot.get_holder_epsilon(
                    last_node_id, route_id, bus_id)

            # for last bus
            # get the last bus's epsilon_arrival and epsilon_rtd at the current stop
            last_bus_epsilon_arrival_curr_stop, last_bus_epsilon_rtd_curr_stop = snapshot.get_stop_epsilon(
                route_id, stop_id, bus_id)

            numerical_diff = (h-H) - (epsilon_rtd_curr_stop -
                                      last_bus_epsilon_rtd_curr_stop)
            # assert abs(
            #     numerical_diff) < 1, f'numerical_diff = {numerical_diff}'

            hold_time = 0
            if self._base_type == 'arrival':
                hold_time = self._slack + self._f0*epsilon_arrival_curr_stop
            elif self._base_type == 'rtd':
                hold_time = self._slack + self._f0*epsilon_rtd_curr_stop

            # hold_time = 0
            hold_time = max(0, hold_time)
            stop_bus_hold_time[(stop_id, route_id, bus_id)] = hold_time

        snapshot.record_holding_time(stop_bus_hold_time)

        return stop_bus_hold_time

    def reset(self, episode: int) -> None:
        ''' Reset the agent for the next episode
        '''
        pass
