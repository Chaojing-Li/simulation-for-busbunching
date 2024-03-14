import numpy as np
import random
import torch
# import wandb
import yaml
from runner import run
from setup.blueprint import Blueprint
# from agent.xuan_nonlinear import XuanNonlinear
# from agent.simple_control_nonlinear import SimpleControlNonlinear
# from agent.do_nothing import DoNothing
from agent.model_based.xuan_nonlinear import XuanNonlinear
from agent.model_based.simple_control_nonlinear import SimpleControlNonlinear
from agent.rl.ddpg_headway import DDPG

file = open('config.yaml', 'r')
config = yaml.load(file, Loader=yaml.FullLoader)
file.close()

seed = config['train_config']['seed']
np.random.seed(seed)
random.seed(seed)


env_name = config['env_name']
blueprint = Blueprint(env_name)
use_model_based_model = config['agent_type']

episode_num = config['train_config']['episode_num']
step_num = config['train_config']['step_num']

if use_model_based_model:
    agent_config = config['model_based_agent_config']
    agent_config['env'] = env_name
    agent = SimpleControlNonlinear(agent_config, blueprint)

else:
    torch.random.manual_seed(seed)
    agent_config = config['RL_agent_config']
    agent_config['env'] = env_name

    agent = DDPG(agent_config, blueprint)


#
name_metric = run(blueprint, episode_num, step_num, agent)

print(name_metric)
