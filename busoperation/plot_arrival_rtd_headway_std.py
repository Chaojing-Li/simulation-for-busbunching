import wandb
import matplotlib.pyplot as plt

api = wandb.Api()
entity = 'samuel'


filt = {'config.agent': 'Xuan_Nonlinear'}


base_type_marker = {'arrival': 'o', 'rtd': 's'}
base_type_linestyple = {'arrival': '-', 'rtd': ':'}
metric_color = {'arrival': 'k', 'rtd': 'blue'}
alpha = 0
fg, ax = plt.subplots()
for base_stop in ['current']:
    # for is_dwell_known in [True]:
    for is_dwell_known in [False]:
        for base_type in ['arrival', 'rtd']:
            slack_hold_times = []
            slack_arrival_headway_stds = []
            slack_rtd_headway_stds = []
            # for slack in [0, 10, 20, 30, 40, 50]:
            for slack in [0, 15, 30, 45, 60, 100]:
                extra_filt = {'config.alpha': alpha, 'config.slack': slack,
                              'config.is_dwell_time_known': is_dwell_known, 'config.base_type': base_type,
                              'config.base_stop': base_stop}
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
                    marker=base_type_marker[base_type], linestyle=base_type_linestyple[base_type],
                    linewidth=2, label='arrival headway std using {}-time information'.format(base_type),
                    color=metric_color['arrival'])

            ax.plot(slack_hold_times, slack_rtd_headway_stds,
                    marker=base_type_marker[base_type], linestyle=base_type_linestyple[base_type],
                    linewidth=2, label='rtd headway std using {}-time information'.format(base_type),
                    color=metric_color['rtd'])

ax.set_ylabel('headway std', fontsize=14)
ax.set_xlabel('holding time per bus per stop', fontsize=14)
plt.legend()
plt.show()
