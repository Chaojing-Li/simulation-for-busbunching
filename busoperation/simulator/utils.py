from typing import Dict, List
import numpy as np


def calculate_headway_std(times: List[float], warm_up_time: int) -> float:
    filtered_rtd_times = [t for t in times if t >= warm_up_time]
    filtered_rtd_times = np.array(filtered_rtd_times, dtype=np.int32)
    headways = np.diff(filtered_rtd_times).tolist()
    headway_std = float(np.std(headways))
    return headway_std


def calculate_mean_abs_epsilon(epsilons: List[float]) -> float:
    return float(np.mean(np.abs(np.array(epsilons))))
