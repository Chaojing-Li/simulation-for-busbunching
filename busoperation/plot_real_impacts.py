import wandb
import matplotlib.pyplot as plt
from typing import Dict, Any

api = wandb.Api()
entity = 'samuel'


filt: Dict[str, Any] = {'config.agent': 'Xuan_Nonlinear'}
env_marker = {'homogeneous_one_route_s1': 'o', 'homogeneous_one_route_s2': 's',
              'homogeneous_one_route_s3': '^', 'homogeneous_one_route_s4': '*'}
env_style = {'homogeneous_one_route_s1': '-', 'homogeneous_one_route_s2': '--',
             'homogeneous_one_route_s3': ':', 'homogeneous_one_route_s4': '-.'}
env_color = {'homogeneous_one_route_s1': 'blue',
             'homogeneous_one_route_s2': 'orange', 'homogeneous_one_route_s3': 'grey', }
metric_color = {'rtd': 'k', 'arrival': 'b'}
fg, ax = plt.subplots()
for env in ['homogeneous_one_route_s1', 'homogeneous_one_route_s2', 'homogeneous_one_route_s3']:
    # for env in ['homogeneous_one_route_s1', 'homogeneous_one_route_s2',]:
    slack_hold_times = []
    slack_arrival_headway_stds = []
    slack_rtd_headway_stds = []
    # for slack in [0, 10, 20, 30, 40, 50]:
    for slack in [0, 5, 10, 20, 30, 40, 100]:
        extra_filt = {'config.slack': slack, 'config.env': env}
        filt.update(extra_filt)

        runs = api.runs(entity + '/' + 'bus-operation', filters=filt)
        run_summary = runs[0].summary

        hold_time = run_summary['route-0\'s holding time']
        arrival_headway = run_summary['route-0\'s arrival headway std']
        rtd_headway = run_summary['route-0\'s rtd headway std']
        slack_hold_times.append(hold_time)
        slack_arrival_headway_stds.append(arrival_headway)
        slack_rtd_headway_stds.append(rtd_headway)

    ax.plot(slack_hold_times, slack_arrival_headway_stds,
            linewidth=2, linestyle=env_style[env], label=env, color=env_color[env])
    # ax.plot(slack_hold_times, slack_rtd_headway_stds,
    #         linewidth=2, linestyle=env_style[env], label=env, color='r')


ax.set_ylabel('headway std', fontsize=14)
ax.set_xlabel('holding time per bus per stop', fontsize=14)
plt.legend()
plt.show()
