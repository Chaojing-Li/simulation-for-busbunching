import wandb
import matplotlib.pyplot as plt
from typing import Dict, Any

api = wandb.Api()
entity = 'samuel'


filt: Dict[str, Any] = {'config.agent': 'Xuan_Nonlinear',
                        'config.env': 'homogeneous_one_route'}
filt: Dict[str, Any] = {'config.agent': 'Xuan_Nonlinear',
                        'config.env': 'cd_route_3'}

base_type_marker = {1: 'o', 2: 's', 3: '^'}
base_type_linestyle = {'arrival': '-', 'rtd': ':', 3: '--'}
metric_color = {'rtd': 'k', 'arrival': 'b'}
fg, ax = plt.subplots()
for f0 in [-1.0, -0.9]:
    for base_type in ['arrival', 'rtd']:
        slack_hold_times = []
        slack_arrival_headway_stds = []
        slack_rtd_headway_stds = []
        # for slack in [0, 10, 20, 30, 40, 50, 60, 70]:
        for slack in [0, 10, 30, 50, 70, 90]:
            extra_filt = {'config.f0': f0, 'config.slack': slack,
                          'config.base_type': base_type}
            filt.update(extra_filt)

            runs = api.runs(entity + '/' + 'bunching', filters=filt)
            run_summary = runs[0].summary

            hold_time = run_summary['route-0\'s holding time']
            arrival_headway = run_summary['route-0\'s arrival headway std']
            rtd_headway = run_summary['route-0\'s rtd headway std']
            # arrival_headway = run_summary['route-0\'s arrival epsilon']
            # rtd_headway = run_summary['route-0\'s rtd epsilon']

            slack_hold_times.append(hold_time)
            slack_arrival_headway_stds.append(arrival_headway)
            slack_rtd_headway_stds.append(rtd_headway)

        if f0 == -1:
            ax.plot(slack_hold_times, slack_arrival_headway_stds, linewidth=3, color=metric_color['arrival'],
                    label='arr.-headway stdev. for {}-based control'.format(base_type), linestyle=base_type_linestyle[base_type])
        else:
            ax.plot(slack_hold_times, slack_arrival_headway_stds, linewidth=3, color=metric_color['arrival'],
                    label='arr.-headway stdev. for {}-based control'.format(base_type), linestyle=base_type_linestyle[base_type], marker='o')

        if f0 == -1:
            ax.plot(slack_hold_times, slack_rtd_headway_stds, linewidth=3, color=metric_color['rtd'],
                    label='dept.-headway stdev. for {}-based control'.format(base_type), linestyle=base_type_linestyle[base_type])
        else:
            ax.plot(slack_hold_times, slack_rtd_headway_stds, linewidth=3, color=metric_color['rtd'],
                    label='dept.-headway stdev. for {}-based control'.format(base_type), linestyle=base_type_linestyle[base_type], marker='o')


ax.set_ylabel('headway std', fontsize=14)
ax.set_xlabel('holding time per bus per stop', fontsize=14)
plt.legend()
plt.show()
