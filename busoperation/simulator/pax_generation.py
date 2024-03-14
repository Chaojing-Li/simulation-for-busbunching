from dataclasses import dataclass
from typing import List, Dict, Tuple
import numpy as np
from scipy.stats import norm
from collections import defaultdict

from setup.route import RouteInfo
from setup.config_dataclass import PaxOperation
from simulator.virtual_bus import VirtualBus


@dataclass(frozen=True)
class Pax:
    pax_id: str
    origin: str
    destination: str
    routes: List[str]
    arrival_time: int
    board_rate: float

    def __repr__(self) -> str:
        return f'Pax {self.pax_id} from {self.origin} to {self.destination} on {self.routes}, arrived at {self.arrival_time}'


class PaxGenerator:
    pax_count = 0

    def __init__(self, route_info: RouteInfo, pax_operation: PaxOperation, virtual_bus: VirtualBus) -> None:
        self._route_od_table = route_info.route_OD_rate_table
        self._route_stop_pax_arrival_start_time = virtual_bus.route_stop_pax_arrival_start_time
        self._pax_arrival_type = pax_operation.pax_arrival_type
        self._pax_board_time_mean = pax_operation.pax_board_time_mean
        self._pax_board_time_std = pax_operation.pax_board_time_std
        self._pax_board_time_type = pax_operation.pax_board_time_type

        if self._pax_arrival_type == 'deterministic':
            self._route_od_arrival_marker: Dict[str, Dict[Tuple[str, str], float]] = defaultdict(
                lambda: defaultdict(float))

        if self._pax_board_time_type == "normal":
            mu, sigma = self._pax_board_time_mean, self._pax_board_time_std
            self._board_time_distribution = norm(mu, sigma)

    def _get_deterministic_pax_num(self, route_id: str, origin_stop_id: str, dest_stop_id: str, rate: float) -> int:
        current_rate = self._route_od_arrival_marker[route_id][(
            origin_stop_id, dest_stop_id)]
        new_rate = current_rate + rate
        if new_rate >= 1:
            new_rate -= 1
            self._route_od_arrival_marker[route_id][(
                origin_stop_id, dest_stop_id)] = new_rate
            return 1
        else:
            self._route_od_arrival_marker[route_id][(
                origin_stop_id, dest_stop_id)] = new_rate
            return 0

    def _get_poission_pax_num(self, rate: float) -> int:
        return np.random.poisson(rate)

    def _get_board_rate(self):
        if self._pax_board_time_type == 'deterministic':
            return 1 / self._pax_board_time_mean
        else:
            sampled_time = self._board_time_distribution.rvs(size=1).item()
            sampled_time = max(0.01, sampled_time)
            sampled_time = min(10, sampled_time)
            return 1/sampled_time

    def generate(self, t: int) -> Dict[str, List[Pax]]:
        stop_paxs = defaultdict(list)
        for route_id, od_table in self._route_od_table.items():
            for origin_stop_id, dest_stop_od in od_table.items():
                if t <= self._route_stop_pax_arrival_start_time[route_id][origin_stop_id]:
                    continue
                for dest_stop_id, rate in dest_stop_od.items():
                    # TODO search common routes between origin and destination
                    common_routes = [route_id]
                    # rate = rate*self._warm_discount_rate if t < self._warm_time else rate
                    pax_num = 0
                    if self._pax_arrival_type == 'deterministic':
                        pax_num = self._get_deterministic_pax_num(
                            route_id, origin_stop_id, dest_stop_id, rate)
                    else:
                        assert self._pax_arrival_type == 'poisson'
                        pax_num = self._get_poission_pax_num(rate)

                    for pax in range(pax_num):
                        board_rate = self._get_board_rate()
                        pax = Pax(str(PaxGenerator.pax_count), origin_stop_id,
                                  dest_stop_id, common_routes, t, board_rate)
                        stop_paxs[origin_stop_id].append(pax)
                        PaxGenerator.pax_count += 1
        return dict(stop_paxs)
