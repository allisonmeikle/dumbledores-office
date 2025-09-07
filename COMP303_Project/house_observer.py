from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional
from .imports import *

if TYPE_CHECKING:
    from .house import House
    from message import Message

class HouseObserver(ABC):
    """
    Interface for objects that need to be notified when the player's house changes.
    Part of the Observer design pattern implementation.
    """
    @abstractmethod
    def update_house(self, house: Optional["House"]) -> list[Message]:
        """
        Updates the observer based on the given house.

        Args:
            house (Optional[House]): The player's house (GRYFFINDOR, HUFFLEPUFF, RAVENCLAW, SLYTHERIN) from the House enum; None if the player is a NullPlayer.

        Returns:
            list[Message]: A list of messages notifying the observer of the house change.
        """
        pass
