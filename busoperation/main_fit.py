import numpy as np
import random
from scipy.stats import norm
import matplotlib.pyplot as plt
import wandb

from busoperation.agent.do_nothing import DoNothing
from agent.xuan_nonlinear import XuanNonlinear
from runner import run
from setup.calibration.dataloader import DataLoader
from setup.blueprint import Blueprint

seed = 0
np.random.seed(seed)
random.seed(seed)

env_name = 'cd_route_3'
agent_config = {'env': env_name, 'agent': 'Do_Nothing'}
# wandb.init(project='bus-operation-2', config=agent_config)

blueprint = Blueprint(env_name)
# agent = XuanNonlinear(agent_config, blueprint)
agent = DoNothing(agent_config, blueprint)

name_metrics, route_trip_times = run(
    blueprint, 3, int(3600*2.5), agent)
print(name_metrics)
print(route_trip_times)

simulate_trip_times = route_trip_times['0']
real_trip_times = DataLoader().trip_times

# Fit the simulated and real distributions
params_simulated = norm.fit(simulate_trip_times)
params_real = norm.fit(real_trip_times)

# Generate data points from the fitted distributions
fitted_simulated = norm.rvs(*params_simulated, size=len(simulate_trip_times))
fitted_real = norm.rvs(*params_real, size=len(real_trip_times))

# Plot histograms
plt.hist(simulate_trip_times, alpha=0.5, label='Simulated', density=True)
plt.hist(real_trip_times, alpha=0.5, label='Real', density=True)

# Plot fitted curves
xmin, xmax = plt.xlim()
x_simulated = np.linspace(xmin, xmax, 100)
x_real = np.linspace(xmin, xmax, 100)
pdf_simulated = norm.pdf(x_simulated, *params_simulated)
pdf_real = norm.pdf(x_real, *params_real)

plt.plot(x_simulated, pdf_simulated, 'k--', label='Fitted Simulated')
plt.plot(x_real, pdf_real, 'r--', label='Fitted Real')

plt.legend()
plt.xlabel('Trip Times')
plt.ylabel('Density')
plt.title('Histograms with Fitted Curves')
plt.show()

# for name, metric in name_metrics.items():
#     wandb.log({name: metric})

# wandb.finish()
