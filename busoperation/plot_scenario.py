import wandb
import matplotlib.pyplot as plt
from typing import Dict, Any

api = wandb.Api()
entity = 'samuel'


filt: Dict[str, Any] = {'config.agent': 'Xuan_Nonlinear'}

scenario_marker = {1: 'o', 2: 's', 3: '^'}
scenario_linestyple = {1: '-', 2: ':', 3: '--'}
metric_color = {'rtd': 'k', 'arrival': 'b'}
fg, ax = plt.subplots()
for scenario in [1, 2, 3]:
    slack_hold_times = []
    slack_arrival_headway_stds = []
    slack_rtd_headway_stds = []
    # for slack in [0, 10, 20, 30, 40, 50]:
    for slack in [0, 15, 30, 45, 60, 100]:
        if scenario == 1:
            f0 = 0
        elif scenario == 2:
            f0 = -1
        else:
            f0 = -1
        extra_filt = {'config.f0': f0,
                      'config.slack': slack, 'config.scenario': scenario}
        filt.update(extra_filt)

        runs = api.runs(entity + '/' + 'bus-operation', filters=filt)
        run_summary = runs[0].summary

        hold_time = run_summary['route-0\'s holding time']
        arrival_headway = run_summary['route-0\'s arrival headway std']
        rtd_headway = run_summary['route-0\'s rtd headway std']
        slack_hold_times.append(hold_time)
        slack_arrival_headway_stds.append(arrival_headway)
        slack_rtd_headway_stds.append(rtd_headway)

    ax.plot(slack_hold_times, slack_arrival_headway_stds, linewidth=2, color=metric_color['arrival'],
            label='arrival headway std, scenario = {}'.format(scenario), linestyle=scenario_linestyple[scenario])

    ax.plot(slack_hold_times, slack_rtd_headway_stds, linewidth=3, color=metric_color['rtd'],
            label='dpt headway std, scenario = {}'.format(scenario), linestyle=scenario_linestyple[scenario])


ax.set_ylabel('headway std', fontsize=14)
ax.set_xlabel('holding time per bus per stop', fontsize=14)
plt.legend()
plt.show()
