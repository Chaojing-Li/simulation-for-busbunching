from agent.rl.ddpg_headway import DDPG
from test_runner import run
from setup.blueprint import Blueprint
import numpy as np
import random

seed = 0
np.random.seed(seed)
random.seed(seed)
slack = 20
fs = {'f0': -1, 'f1': 0}
env_name = 'homogeneous_one_route'
agent_config = {'env': env_name, 'agent_name': 'Simple_Control',
                'fs': fs, 'slack': slack, 'base_type': 'rtd'}
blueprint = Blueprint(env_name)
# agent_config = {'env': env_name, 'agent_name': 'Do_Nothing'}
agent = DDPG(agent_config, blueprint)
agent.load_actor_net(path='actor_net_home_one.pth')
name_metric, route_trip_times = run(blueprint, 30, int(3600*5), agent)

print(name_metric)

