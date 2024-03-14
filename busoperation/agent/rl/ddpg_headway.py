from copy import deepcopy
from collections import deque, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Tuple, Optional, List
import random
import numpy as np
import torch

from simulator.snapshot import Snapshot
from setup.blueprint import Blueprint
from simulator.virtual_bus import VirtualBus
from simulator.simulator import Simulator

from .rl_agent import RLAgent
from .net import Actor_Net, Critic_Net


@dataclass(frozen=True)
class SAR:
    state: Tuple[Optional[float], Optional[float]]
    action: float
    reward: Optional[float]


@dataclass(frozen=True)
class SARS:
    state: Tuple[Optional[float], Optional[float]]
    action: float
    reward: Optional[float]
    next_state: Tuple[Optional[float], Optional[float]]


@dataclass(frozen=True)
class StopDuration:
    stop_id: str
    route_id: str
    duration: float

class DDPG(RLAgent):
    def __init__(self, agent_config: Dict[str, Any], blueprint: Blueprint) -> None:
        super().__init__(agent_config, blueprint)

        self._actor_net = Actor_Net(state_size=agent_config['state_size'], hidde_size=tuple(agent_config['hidden_size']))
        self._critic_net = Critic_Net(state_size=agent_config['state_size'], hidde_size=tuple(agent_config['hidden_size']))
        self._target_actor_net = deepcopy(self._actor_net)
        self._target_critic_net = deepcopy(self._critic_net)
        # Freeze target networks with respect to optimizers (only update via polyak averaging)
        for param in self._target_actor_net.parameters():
            param.requires_grad = False
        for param in self._target_critic_net.parameters():
            param.requires_grad = False
        self._actor_optim = torch.optim.Adam(
            self._actor_net.parameters(), lr=agent_config['actor_lr'])
        self._critic_optim = torch.optim.Adam(
            self._critic_net.parameters(), lr=agent_config['critic_lr'])

        self._gamma = agent_config['gamma']
        self._polya = agent_config['polya']
        self._memory = deque(maxlen=agent_config['memory_size'])
        self._max_hold_time = agent_config['max_hold_time']
        # (route_id, bus_id) -> [(stop_id, SAR)]
        self._bus_stop_sar: Dict[Tuple[str, str],
                                 List[Tuple[str, SAR]]] = defaultdict(list)
        self._add_event_count = 0
        self._update_cycle = agent_config['update_cycle']
        self._batch_size = agent_config['batch_size']
        self._H = 300 if agent_config['env'] == 'homogeneous_one_route' else 170
        self._init_noise_level = agent_config['init_noise_level']
        self._decay_rate = agent_config['decay_rate']
        self._noise_level = self._init_noise_level
        self._slack = agent_config['slack']
        self._stop_duration: StopDuration
        self._generate_virtual_bus()



    def reset(self, episode: int):
        self._noise_level = self._decay_rate ** episode * self._init_noise_level
        print(self._noise_level, '!!!!!')

    def _transform_snapshot_to_SR(self, snapshot: Snapshot,
                                  acting_bus: Tuple[str, str], stop_id: str
                                  ) -> [Optional[float], Optional[float]]:
        ''' Transform the snapshot to state, reward.

        Args:
            snapshot: the snapshot of the current time step
            acting_bus: the bus that is acting: (route_id, bus_id)

        '''

        stop_snapshots = snapshot.stop_snapshots

        current_stop_arrival_info = stop_snapshots[stop_id].route_arrival_time_seq[acting_bus[0]]  # all the buses' arrival time at this stop
        # current_stop_departure_info = holder_snapshots.route_stop_departure_time_seq[acting_bus[0]][stop_id]
        pervious_bus_arrival_time = current_stop_arrival_info[-2] # the pervious bus's arrival time at this stop
        current_bus_arrival_time = current_stop_arrival_info[-1] # the current bus's arrival time at this stop
        headway = current_bus_arrival_time - pervious_bus_arrival_time
        spacings = headway / self._H

        if spacings is None:
            reward = None
        else:
            assert spacings is not None
            reward = -abs(self._H - headway)
        return spacings, reward

    def _push_transitions_to_memory(self):
        for (route_id, bus_id), sar_list in self._bus_stop_sar.items():
            if len(sar_list) > 1:
                for (stop_id, sar), (next_stop_id, next_sar) in zip(sar_list[0:-1], sar_list[1:]):
                    if int(next_stop_id) - int(stop_id) == 1:
                        state = sar.state
                        action = sar.action
                        reward = next_sar.reward
                        next_state = next_sar.state
                        sars = SARS(state, action, reward, next_state)
                        self._memory.append(sars)
        self._bus_stop_sar = defaultdict(list)

    def calculate_hold_time(self, snapshot: Snapshot):
        stop_bus_hold_time = {}
        for (stop_id, route_id, bus_id) in snapshot.holder_snapshot.action_buses:
            state, reward = self._transform_snapshot_to_SR(
                snapshot, (route_id, bus_id), stop_id)
            action, hold_time = self.infer(state)
            stop_bus_hold_time[(stop_id, route_id, bus_id)] = hold_time

            if state is not None:
                sar = SAR(state, action, reward)
                self._bus_stop_sar[(route_id, bus_id)].append((stop_id, sar))
                self._add_event_count += 1
                if self._add_event_count % self._batch_size == 0:
                    self._push_transitions_to_memory()

            self.learn()

            snapshot.record_holding_time(stop_bus_hold_time)

        return stop_bus_hold_time

    def infer(self, state: Tuple[Optional[float]]) -> Tuple[float, float]:
        state = np.array(state)
        state = torch.tensor(state, dtype=torch.float32).reshape(-1, 1)
        if state is not None:
            self._actor_net.eval()
            # with torch.no_grad():
            #     action = self._actor_net(state)
            #     action = float(action)
            with torch.no_grad():
                action = self._actor_net(state)
                # when training, add noise
                noise = np.random.normal(0, self._noise_level)
                action = (action + noise).clip(0, 1)
                action = float(action)
        else:
            action = 0
        hold_time = action * self._max_hold_time
        return action, hold_time

    def learn(self):
        if self._add_event_count % self._update_cycle != 0 or len(self._memory) < self._batch_size:
            return

        samples = random.sample(self._memory, self._batch_size)
        stats = []
        actis = []
        rewas = []
        next_stats = []
        for sample in samples:
            stats.append(sample.state)
            actis.append(sample.action)
            rewas.append(sample.reward)
            next_stats.append(sample.next_state)

        s = torch.tensor(stats, dtype=torch.float32).reshape(-1, 1)
        # LongTensor for idx selection
        a = torch.tensor(actis, dtype=torch.float32)
        r = torch.tensor(rewas, dtype=torch.float32)
        n_s = torch.tensor(next_stats, dtype=torch.float32).reshape(-1, 1)

        # update critic network
        # self.__criti_net.zero_grad()
        self._critic_optim.zero_grad()
        # current estimate
        s_a = torch.concat((s, a.unsqueeze(dim=1)), dim=1)
        for param in self._critic_net.parameters():
            param.requires_grad = True
        Q = self._critic_net(s_a)

        # Bellman backup for Q function
        targe_imagi_a = self._target_actor_net(n_s)  # (batch_size, 1)
        s_targe_imagi_a = torch.concat((n_s, targe_imagi_a), dim=1)
        with torch.no_grad():
            q_polic_targe = self._target_critic_net(s_targe_imagi_a)
            # r is (batch_size, ), need to align with output from NN
            back_up = r.unsqueeze(1) + self._gamma * q_polic_targe
        # MSE loss against Bellman backup
        # Unfreeze Q-network so as to optimize it
        td = Q - back_up
        criti_loss = (td**2).mean()
        # update critic parameters
        criti_loss.backward()
        self._critic_optim.step()

        # update actor network
        self._actor_optim.zero_grad()
        imagi_a = self._actor_net(s)
        s_imagi_a = torch.concat((s, imagi_a), dim=1)
        # Freeze Q-network to save computational efforts
        for param in self._critic_net.parameters():
            param.requires_grad = False
        Q = self._critic_net(s_imagi_a)
        actor_loss = -Q.mean()
        actor_loss.backward()
        self._actor_optim.step()

        # Finally, update target networks by polyak averaging.
        with torch.no_grad():
            for p, p_targ in zip(self._actor_net.parameters(), self._target_actor_net.parameters()):
                p_targ.data.mul_(self._polya)
                p_targ.data.add_((1 - self._polya) * p.data)
            for p, p_targ in zip(self._critic_net.parameters(), self._target_critic_net.parameters()):
                p_targ.data.mul_(self._polya)
                p_targ.data.add_((1 - self._polya) * p.data)

    def evaluate(self, snapshot: Snapshot):
        stop_bus_hold_time = {}
        for (stop_id, route_id, bus_id) in snapshot.holder_snapshot.action_buses:
            state, reward = self._transform_snapshot_to_SR(
                snapshot, (route_id, bus_id), stop_id)
            action, hold_time = self.infer(state)
            stop_bus_hold_time[(stop_id, route_id, bus_id)] = hold_time
            snapshot.record_holding_time(stop_bus_hold_time)

        return stop_bus_hold_time

    def save_actor_net(self, path):
        torch.save(self._actor_net.state_dict(), path)

    def load_actor_net(self, path):
        self._actor_net.load_state_dict(torch.load(path))

    def _generate_virtual_bus(self):
        ''' Generate the virtual bus.
        For nonlinear version, the average holding time at each stop is dynamically updated
        by running the simulation until convergence.
        '''
        # the virtual bus's average holding time is initialized to be the slack
        self._virtual_bus = VirtualBus(self._blueprint)
        self._virtual_bus.initialize_with_perfect_schedule(
            self._route_stop_arrival_rate, self._slack)

        route_stop_average_hold_time: Dict[str, Dict[str, float]] = {}
        for _ in range(1):
            simulator = Simulator(self._blueprint, self)
            stop_bus_hold_action: Dict[Tuple[str, str, str], float] = {}
            for t in range(int(3600 * 3)):
                snapshot = simulator.step(t, stop_bus_hold_action)
                stop_bus_hold_action = self.calculate_hold_time(snapshot)

            route_stop_average_hold_time = simulator.get_stop_average_hold_time()
            self._virtual_bus.update_trajectory(route_stop_average_hold_time)

