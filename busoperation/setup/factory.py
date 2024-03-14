
from typing import Protocol, Dict

from agent.agent import Agent
from simulator.terminal import Terminal
from simulator.link import Link
from simulator.stop import Stop
from simulator.pax_generation import PaxGenerator
from simulator.virtual_bus import VirtualBus

from .blueprint import Blueprint


class ComponentFactory(Protocol):
    ''' Protocol for creating components for the simulation environment

    '''

    def create_virtual_bus(self, blueprint: Blueprint, agent: Agent) -> VirtualBus:
        ...

    def create_pax_generator(self, blueprint: Blueprint, virtual_bus: VirtualBus) -> PaxGenerator:
        ...

    def create_terminals(self, blueprint: Blueprint, virtual_bus: VirtualBus) -> Dict[str, Terminal]:
        ...

    def create_links(self, blueprint: Blueprint) -> Dict[str, Link]:
        ...

    def create_stops(self, blueprint: Blueprint, virtual_bus: VirtualBus) -> Dict[str, Stop]:
        ...
