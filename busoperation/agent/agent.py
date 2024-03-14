from abc import ABC, abstractmethod
from typing import Dict, Tuple, Any

from simulator.snapshot import Snapshot
from simulator.virtual_bus import VirtualBus


class Agent(ABC):
    """
    The Mixin interface declares operations common to all supported versions of holding agents.

    Attributes:
        virtual_bus: Virtual bus that defines the starting of pax arrival at each stop

    """

    _virtual_bus: VirtualBus

    def __init__(self, agent_config: Dict[str, Any]) -> None:
        self._agent_name = agent_config['agent_name']

    @property
    def agent_name(self):
        return self._agent_name

    @property
    def virtual_bus(self):
        ''' The virtual bus is created by subclasses of Agent.

            The property does not exist if the subclass does not implement it.

        '''
        return self._virtual_bus

    # @abstractmethod
    # def _generate_virtual_bus(self) -> VirtualBus:
    #     ''' Generate the virtual bus (first bus).
    #         The virtual bus is used for generating the boundary condition of the dynamics
    #     '''
    #     ...

    @abstractmethod
    def reset(self, episode: int) -> None:
        ''' Reset the agent for the next episode
        '''
        ...

    @abstractmethod
    def calculate_hold_time(self, snapshot: Snapshot) -> Dict[Tuple[str, str, str], float]:
        ''' Given the snapshot of the current state, calculate the hold time of each bus at each stop
            Note that the snapshot also contains historical information, e.g., the last bus's arrival time at each stop
            #TODO add a wrapper to pick up parts of the snapshot of interest

        '''
        ...
