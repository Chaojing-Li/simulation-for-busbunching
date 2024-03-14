# from agent.agent import Agent
from typing import Dict, Any

from setup.blueprint import Blueprint
from setup.calibration.dataloader import DataLoader

from agent.virtual_bus import VirtualBus
from agent.agent import Agent
from agent.single_line_agent import AgentByLine


class DoNothing(AgentByLine):
    def __init__(self, blueprint: Blueprint) -> None:
        super().__init__(blueprint)
        self._blueprint = blueprint
        self._generate_virtual_bus()

    def _generate_virtual_bus(self):
        self._virtual_bus = VirtualBus(self._blueprint)
        if self._blueprint.env_name == 'cd_route_3':
            virtual_bus_rtd_info = DataLoader().virtual_bus_rtd_info
            virtual_bus_rtd_time = {
                stop: info[0] for stop, info in virtual_bus_rtd_info.items()}
            route_virtual_bus_rtd_time = {'0': virtual_bus_rtd_time}
            self._virtual_bus.initialize_by_data(route_virtual_bus_rtd_time)
        elif self._blueprint.env_name == 'homogeneous_one_route':
            self._virtual_bus.initialize_with_perfect_schedule(
                self._route_stop_arrival_rate, slack=0)

    def calculate_hold_time(self, snapshot):
        stop_bus_hold_time = {}
        for (stop_id, route_id, bus_id) in snapshot.holder_snapshot.action_buses:
            stop_bus_hold_time[(stop_id, route_id, bus_id)] = 0
        return stop_bus_hold_time
