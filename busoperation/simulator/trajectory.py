from typing import List
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np

from dataclasses import dataclass


@dataclass
class TrajectoryPoint:
    spot_type: str
    spot_id: str
    distance_from_terminal: float


def plot_time_space_diagram(buses):
    _, ax = plt.subplots()
    ax.set_xlabel('Time (sec)', fontsize=12)
    ax.set_ylabel('Offset (km)', fontsize=12)

    for bus in buses:
        # plot trajectory
        x = []
        y = []
        for t, point in bus.trajectory.items():
            x.append(t)
            y.append(point.distance_from_terminal)
        ax.plot(x, y, 'k')

        # plot holding durations
        hold_xs = defaultdict(list)
        hold_ys = {}
        for t, point in bus.trajectory.items():
            if point.spot_type == 'holder':
                hold_xs[point.spot_id].append(t)
                hold_ys[point.spot_id] = point.distance_from_terminal
        for spot_id, xs in hold_xs.items():
            start, end = min(xs), max(xs)
            y = hold_ys[spot_id]
            ax.hlines(y=y, xmin=start, xmax=end,
                      color='red', linewidth=1.5)

    plt.show()
