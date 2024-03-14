from typing import Dict

from agent.agent import Agent
from setup.homo_one_route_factory import HomoOneRouteComponentsFactory
from setup.chengdu_factory import CDRoute3ComponentsFactory
from setup.factory import ComponentFactory
from setup.blueprint import Blueprint
from simulator.virtual_bus import VirtualBus

from .terminal import Terminal
from .link import Link
from .stop import Stop
from .pax_generation import PaxGenerator


class Builder:
    ''' Create simulation components by factory.

    Methods:
        create_terminals(self, agent: Agent) -> Dict[str, Terminal]:
        create_links(self) -> Dict[str, Link]:
        create_stops(self, agent: Agent) -> Dict[str, Stop]:
        create_pax_generator(self, agent: Agent) -> PaxGenerator:

    '''
    _blueprint: Blueprint
    _component_factory: ComponentFactory

    def __init__(self, blueprint: Blueprint) -> None:
        self._blueprint = blueprint
        if blueprint.env_name == 'homogeneous_one_route':
            self._component_factory = HomoOneRouteComponentsFactory(
                blueprint)
        elif blueprint.env_name == 'cd_route_3':
            self._component_factory = CDRoute3ComponentsFactory(
                blueprint)

    def create_virtual_bus(self, agent: Agent) -> VirtualBus:
        virtual_bus = self._component_factory.create_virtual_bus(
            self._blueprint, agent)
        return virtual_bus

    def create_pax_generator(self, virtual_bus: VirtualBus) -> PaxGenerator:
        pax_generator = self._component_factory.create_pax_generator(
            self._blueprint, virtual_bus)
        return pax_generator

    def create_terminals(self, virtual_bus: VirtualBus) -> Dict[str, Terminal]:
        terminals = self._component_factory.create_terminals(
            self._blueprint, virtual_bus)
        return terminals

    def create_links(self) -> Dict[str, Link]:
        links = self._component_factory.create_links(self._blueprint)
        return links

    def create_stops(self, virtual_bus: VirtualBus) -> Dict[str, Stop]:
        stops = self._component_factory.create_stops(
            self._blueprint, virtual_bus)
        return stops
