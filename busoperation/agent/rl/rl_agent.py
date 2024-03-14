# from agent.agent import Agent
from typing import Dict, Any
from abc import abstractmethod
from collections import defaultdict
from setup.blueprint import Blueprint
from setup.calibration.dataloader import DataLoader
from simulator.snapshot import Snapshot

from agent.agent import Agent


class RLAgent(Agent):
    def __init__(self, agent_config: Dict[str, Any], blueprint: Blueprint) -> None:
        super().__init__(agent_config)
        self._blueprint = blueprint
        self._route_stop_arrival_rate = self._calculate_total_arrival_rate()

    def _calculate_total_arrival_rate(self) -> Dict[str, Dict[str, float]]:
        ''' Calculate the total arrival rate at each stop for each route by summing up the OD table by row.
        '''
        route_total_arrival_rate = defaultdict(dict)
        for route_id, route in self._blueprint.route_info.route_infos.items():
            for origin_stop_id, destination_rate in route.od_rate_table.items():
                total_origin_demand = sum(destination_rate.values())
                route_total_arrival_rate[route_id][origin_stop_id] = total_origin_demand

            last_stop_id = route.visit_seq_stops[-1]

            # # case 1. the last stop's arrival demand rate is 0, i.e., no one will get on the bus at the last stop
            # route_total_arrival_rate[route_id][last_stop_id] = 0.0

            # case 2. the last stop's arrival demand rate equals the last but one stop's arrival demand rate
            last_but_one_stop_id = route.visit_seq_stops[-2]
            route_total_arrival_rate[route_id][last_stop_id] = route_total_arrival_rate[route_id][last_but_one_stop_id]

        return dict(route_total_arrival_rate)
    # @abstractmethod
    # def retrieve_state(self, snapshot: Snapshot):
    #     pass
