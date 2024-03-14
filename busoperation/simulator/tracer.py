from typing import Dict, List, Tuple
import numpy as np
from collections import defaultdict

from .stop import Stop
from .link import Link
from .holder import Holder
from .snapshot import Snapshot, StopSnapshot, BusSnapshot
from .utils import calculate_headway_std, calculate_mean_abs_epsilon


class Tracer:
    def __init__(self) -> None:
        self._snapshots: List[Snapshot] = []

    def take_snapshot(self, t: int, links: Dict[str, Link], stops: Dict[str, Stop], holder: Holder) -> Snapshot:
        bus_snapshots: Dict[Tuple[str, str], BusSnapshot] = {}
        stop_snapshots: Dict[str, StopSnapshot] = {}

        # links
        for link in links.values():
            for bus in link.buses:
                bus_snapshot = bus.take_snapshot()
                bus_snapshots[(bus.route_id, bus.bus_id)] = bus_snapshot

        # stops
        for stop_id, stop in stops.items():
            stop_snapshots[stop_id] = stop.take_snapshot()

            for bus in stop.get_total_buses():
                bus_snapshot = bus.take_snapshot()
                bus_snapshots[(bus.route_id, bus.bus_id)] = bus_snapshot

        # holder
        for (stop_id, route_id, bus_id), bus in holder.stop_identifier_bus.items():
            bus_snapshot = bus.take_snapshot()
            bus_snapshots[(bus.route_id, bus.bus_id)] = bus_snapshot

        holder_snapshot = holder.take_snapshot()
        snapshot = Snapshot(t, bus_snapshots, stop_snapshots, holder_snapshot)

        self._snapshots.append(snapshot)
        return snapshot

    def get_metric(self, route_stop_ids: Dict[str, List[str]]):
        ''' Get the metrics of given stops for each route
        '''
        warm_up_time = 0
        last_snapshot = self._snapshots[-1]
        metrics = {}

        for route_id, stop_ids in route_stop_ids.items():
            arrival_stds = []
            rtd_stds = []
            departure_stds = []
            epsilon_arrival_mean_abs = []
            epsilon_rtd_mean_abs = []
            epsilon_departure_mean_abs = []

            for stop_id in stop_ids:
                arrival_time_seq = last_snapshot.stop_snapshots[stop_id].route_arrival_time_seq[route_id]
                arrival_std = calculate_headway_std(
                    arrival_time_seq, warm_up_time)
                arrival_stds.append(arrival_std)

                rtd_time_seq = last_snapshot.stop_snapshots[stop_id].route_rtd_time_seq[route_id]
                rtd_std = calculate_headway_std(rtd_time_seq, warm_up_time)
                rtd_stds.append(rtd_std)

                departure_time_seq = last_snapshot.holder_snapshot.route_stop_departure_time_seq[
                    route_id][stop_id]
                departure_std = calculate_headway_std(
                    departure_time_seq, warm_up_time)
                departure_stds.append(departure_std)

                bus_epsilon_arrival = last_snapshot.stop_snapshots[
                    stop_id].route_bus_epsilon_arrival[route_id]
                mean_abs_epsilon_arrival = calculate_mean_abs_epsilon(
                    list(bus_epsilon_arrival.values()))
                epsilon_arrival_mean_abs.append(mean_abs_epsilon_arrival)

                bus_epsilon_rtd = last_snapshot.stop_snapshots[
                    stop_id].route_bus_epsilon_rtd[route_id]
                mean_abs_epsilon_rtd = calculate_mean_abs_epsilon(
                    list(bus_epsilon_rtd.values()))
                epsilon_rtd_mean_abs.append(mean_abs_epsilon_rtd)

                bus_epsilon_departure = last_snapshot.holder_snapshot.route_stop_bus_epsilon_departure[
                    route_id][stop_id]
                mean_abs_epsilon_departure = calculate_mean_abs_epsilon(list(
                    bus_epsilon_departure.values()))
                epsilon_departure_mean_abs.append(mean_abs_epsilon_departure)

            metrics[f'route-{route_id}\'s arrival headway std'] = np.mean(
                arrival_stds)
            metrics[f'route-{route_id}\'s rtd headway std'] = np.mean(rtd_stds)
            metrics[f'route-{route_id}\'s departure headway std'] = np.mean(
                departure_stds)
            metrics[f'route-{route_id}\'s arrival epsilon'] = np.mean(
                epsilon_arrival_mean_abs)
            metrics[f'route-{route_id}\'s rtd epsilon'] = np.mean(
                epsilon_rtd_mean_abs)
            metrics[f'route-{route_id}\'s departure epsilon'] = np.mean(
                epsilon_departure_mean_abs)

        # get route holding times
        route_all_stop_hold_times: Dict[str, List[float]] = defaultdict(list)
        counted_snapshots = [
            snapshot for snapshot in self._snapshots if snapshot.t > warm_up_time]
        for snapshot in counted_snapshots:
            for (stop_id, route_id, bus_id), holding_time in snapshot.action_record.items():
                if stop_id in route_stop_ids[route_id]:
                    route_all_stop_hold_times[route_id].append(holding_time)

        for route_id, hold_times in route_all_stop_hold_times.items():
            hold_times = np.array(hold_times)
            metrics[f'route-{route_id}\'s holding time'] = np.mean(hold_times)

        return metrics

    def get_stop_average_hold_time(self) -> Dict[str, Dict[str, float]]:
        ''' Get the average holding time of each stop for each route.

        Returns:
            route_stop_hold_time: a dictionary {route_id -> {stop_id -> average_hold_time}}

        '''
        route_stop_hold_times: Dict[Tuple[str, str], List] = defaultdict(list)
        for snapshot in self._snapshots:
            for (stop_id, route_id, bus_id), holding_time in snapshot.action_record.items():
                route_stop_hold_times[(route_id, stop_id)].append(holding_time)

        route_stop_hold_time = defaultdict(dict)
        for (route_id, stop_id), holding_times in route_stop_hold_times.items():
            route_stop_hold_time[route_id][stop_id] = np.mean(holding_times)
        return dict(route_stop_hold_time)

    # def get_metrics(self, route_last_stop: Dict[str, str]) -> Dict[str, float]:
    #     warm_up_time = 0
    #     metrics = {}

    #     # get route headway std
    #     route_all_stop_headway: Dict[str, List[int]] = defaultdict(list)
    #     last_snapshot = self._snapshots[-1]
    #     for stop_id, stop_snapshot in last_snapshot.stop_snapshots.items():
    #         for route_id, rtd_times in stop_snapshot.route_rtd_time_seq.items():
    #             # the last stop of a route is not included
    #             if stop_id == route_last_stop[route_id]:
    #                 continue

    #             filtered_rtd_times = [
    #                 t for t in rtd_times if t >= warm_up_time]
    #             filtered_rtd_times = np.array(
    #                 filtered_rtd_times, dtype=np.int32)
    #             headways = np.diff(filtered_rtd_times).tolist()
    #             route_all_stop_headway[route_id].extend(headways)

    #     for route_id, headways in route_all_stop_headway.items():
    #         headways = np.array(headways)
    #         metrics[f'route-{route_id}\'s headway std'] = np.std(headways)

    #     # get route holding times
    #     route_all_stop_hold_times: Dict[str, List[float]] = defaultdict(list)
    #     for snapshot in self._snapshots:
    #         if snapshot.t <= warm_up_time:
    #             continue
    #         for (stop_id, route_id, bus_id), holding_time in snapshot.action_record.items():
    #             route_all_stop_hold_times[route_id].append(holding_time)

    #     for route_id, hold_times in route_all_stop_hold_times.items():
    #         hold_times = np.array(hold_times)
    #         metrics[f'route-{route_id}\'s holding time'] = np.mean(hold_times)

    #     return metrics
