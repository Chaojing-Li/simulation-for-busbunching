import numpy as np
from typing import Dict, Tuple, List
from collections import defaultdict
import matplotlib.pyplot as plt

import wandb

from simulator.simulator import Simulator
from simulator.trajectory import plot_time_space_diagram
from setup.blueprint import Blueprint
from agent.agent import Agent


def run(blueprint: Blueprint, episode_num: int, episode_duration: int, agent: Agent) -> Tuple[Dict[str, float], Dict[str, List[float]]]:
    name_episode_metrics: Dict[str, List[float]] = defaultdict(list)
    route_trip_times: Dict[str, List[float]] = defaultdict(list)

    for episode in range(episode_num):
        simulator = Simulator(blueprint, agent)
        stop_bus_hold_action: Dict[Tuple[str, str, str], float] = {}

        for t in range(episode_duration):
            snapshot = simulator.step(t, stop_bus_hold_action)
            stop_bus_hold_action = agent.evaluate(snapshot)

            if t > 3600:
                metrics, route_dispatch_time_trip_time = simulator.get_metrics()
                for name, metric in metrics.items():
                    name_episode_metrics[name].append(metric)

        # for route, dispatch_time_trip_time in route_dispatch_time_trip_time.items():
        #     for dispatch_time, trip_time in dispatch_time_trip_time.items():
        #         if dispatch_time < 3600:
        #             route_trip_times[route].append(trip_time)
        route_trip_times = dict(route_trip_times)


        print(f'episode {episode} finished')
        print(f'metrics is {metrics}')
        agent.reset(episode)
        if episode % 10 == 0 or episode == episode_num - 1:
            plot_time_space_diagram(simulator.total_buses)

    name_value = {}
    for name, episode_metrics in name_episode_metrics.items():
        metric_mean = np.mean(np.array(episode_metrics))
        name_value[name] = metric_mean

    return name_value, route_trip_times
