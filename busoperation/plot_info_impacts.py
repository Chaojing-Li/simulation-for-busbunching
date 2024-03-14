import wandb
import matplotlib.pyplot as plt
from typing import Dict, Any

api = wandb.Api()
entity = 'samuel'


filt: Dict[str, Any] = {'config.agent': 'Xuan_Nonlinear'}
env_marker = {'homogeneous_one_route_s1': 'o', 'homogeneous_one_route_s2': 's'}
env_style = {'homogeneous_one_route_s1': '--', 'homogeneous_one_route_s2': '-'}

fg, ax = plt.subplots()
for env in ['homogeneous_one_route_s1', 'homogeneous_one_route_s2']:
    # for env in ['homogeneous_one_route_s1', 'homogeneous_one_route_s2',]:
    slack_hold_times = []
    slack_arrival_headway_stds = []
    slack_rtd_headway_stds = []
    # for slack in [0, 10, 20, 30, 40, 50]:
    for slack in [0, 5, 10, 20, 30, 40, 100]:
        extra_filt = {'config.slack': slack, 'config.env': env}
        filt.update(extra_filt)

        runs = api.runs(entity + '/' + 'bus-operation-2', filters=filt)
        run_summary = runs[0].summary

        hold_time = run_summary['route-0\'s holding time']
        arrival_headway = run_summary['route-0\'s arrival headway std']
        rtd_headway = run_summary['route-0\'s rtd headway std']
        slack_hold_times.append(hold_time)
        slack_arrival_headway_stds.append(arrival_headway)
        slack_rtd_headway_stds.append(rtd_headway)

    if env == 'homogeneous_one_route_s1':
        label1 = 'arr.-hdwy stdev. for arr.-time based control'
        color1 = 'orange'
        label2 = 'dpt.-hdwy stdev. for arr.-time based control'
        color2 = 'gold'
    else:
        label1 = 'arr.-hdwy stdev. for rtd.-time based control'
        label2 = 'dpt.-hdwy stdev. for rtd.-time based control'
        color1 = 'blue'
        color2 = 'grey'

    ax.plot(slack_hold_times, slack_arrival_headway_stds,
            linewidth=2, linestyle='solid', label=label1, color=color1, marker=env_marker[env])
    ax.plot(slack_hold_times, slack_rtd_headway_stds,
            linewidth=2, linestyle='dashed', label=label2, color=color2, marker=env_marker[env])


ax.set_ylabel('headway std', fontsize=14)
ax.set_xlabel('holding time per bus per stop', fontsize=14)
plt.legend(handlelength=3)
plt.show()
