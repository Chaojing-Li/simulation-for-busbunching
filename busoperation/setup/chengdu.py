from collections import defaultdict
from typing import List, Dict, Tuple
from typing_extensions import override


from .calibration.dataloader import DataLoader
from .network import Network
from .route import RouteInfo
from .config_dataclass import *

data_loader = DataLoader()
node_ids = data_loader.node_ids
link_time_info = data_loader.link_time_info
stop_pax_arrival_rate = data_loader.stop_pax_arrival_rate
H_mean, H_std = data_loader.dispatching_headway
# print(node_ids)
# print(link_time_info)

berth_num = 3
start_terminal = node_ids[0]
end_terminal = node_ids[-1]
visit_seq_stops = node_ids[1:-1]

spacing = 1500  # meters


class CDRoute3Network(Network):
    def __init__(self) -> None:
        super().__init__()

    def _define_network(self):
        x_cum = 0
        y_cum = 0

        # build nodes
        for node_id in node_ids:
            x = x_cum
            y = y_cum
            node_id = str(node_id)
            if node_id == start_terminal or node_id == end_terminal:
                terminal_node_geometry = TerminalNodeGeometry(x, y)
                self._G.add_node(node_id, node_type='terminal',
                                 terminal_node_geometry=terminal_node_geometry)
            else:
                stop_node_geometry = StopNodeGeometry(x, y, berth_num, x_cum)
                self._G.add_node(node_id, node_type='stop',
                                 stop_node_geometry=stop_node_geometry)
            self._name_coordinates[node_id] = (x, y)
            x_cum += spacing

        # build links
        distance_cum = 0
        link_id = 0
        adds = 0
        for head_node, tail_node in zip(node_ids[:-1], node_ids[1:]):
            head_node = int(head_node)
            tail_node = int(tail_node)

            tt_mean = link_time_info[tail_node]['loc'] * 1.1
            adds += tt_mean
            tt_cv = link_time_info[tail_node]['scale'] / tt_mean * 0.9
            tt_type = 'normal'
            link_distribution = LinkDistribution(tt_mean, tt_cv, tt_type)
            link_geometry = LinkGeometry(str(head_node), str(
                tail_node), distance_cum, 0, spacing, distance_cum)
            self._G.add_edge(str(head_node), str(tail_node), link_id=link_id,
                             link_geometry=link_geometry, link_distribution=link_distribution)
            link_id += 1
            distance_cum += spacing


class CDRoute3NetworkRouteInfo(RouteInfo):
    def __init__(self) -> None:
        super().__init__()

    def _define_od_table(self) -> Dict[str, Dict[str, Dict[str, float]]]:
        od_rate_table = defaultdict(dict)
        for idx, origin_stop in enumerate(visit_seq_stops):
            for dest_stop in visit_seq_stops[idx+1:]:
                # all the passengers will be dropped off at the last stop
                if dest_stop != visit_seq_stops[-1]:
                    od_rate_table[origin_stop][dest_stop] = 0.0
                else:
                    od_rate_table[origin_stop][dest_stop] = stop_pax_arrival_rate[origin_stop] * 1.2
        od_rate_table = dict(od_rate_table)
        return {'0': od_rate_table}

    @override
    def _define_route_ids(self) -> List[str]:
        return ['0']

    @override
    def _define_schedule_headway(self) -> Dict[str, Tuple[float, float]]:
        return {'0': (H_mean, H_std)}
        # return {'0': (170.70676691728573, 53.17763250051282)}

    @override
    def _define_terminal(self) -> Dict[str, str]:
        return {'0': start_terminal}

    @override
    def _define_visit_seq_stops(self) -> Dict[str, List[str]]:
        return {'0': visit_seq_stops}
    # 35 middle stops and 2 terminals
    # @override
    # def _define_visit_seq_links(self) -> Dict[str, List[str]]:
    #     return {'0': [str(x) for x in range(len(visit_seq_stops))]}

    @override
    def _define_end_terminal(self) -> Dict[str, str]:
        return {'0': end_terminal}

    @override
    def _define_boarding_rate(self) -> Dict[str, Dict[str, float]]:
        return {'0': {stop_id: 1/2.5 for stop_id in visit_seq_stops}}
