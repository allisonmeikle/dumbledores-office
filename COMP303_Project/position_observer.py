from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, List
from .imports import *

if TYPE_CHECKING:
    from coord import Coord
    from message import Message
    from .text_bubble import *

class PositionObserver(ABC):
    """
    Interface for objects that need to be notified when the player's position changes.
    Part of the Observer design pattern implementation.
    """
    _message : str
    _text_bubble : 'TextBubble'
    _active_positions : List['Coord']
    _message_displayed : bool

    def update_position(self, position: Coord) -> list[Message]:
        """
        Update the observer based on the player's new position.
        
        Args:
            position: The player's new position
        """
        from .util import get_custom_dialogue_message
        from .dumbledores_office import DumbledoresOffice
        messages = []
        if self._text_bubble:
            # Show text bubble if player is adjacent
            if position in self._active_positions:
                self._text_bubble.show()
                if (not self._message_displayed):
                    self._message_displayed = True
                    messages.append(get_custom_dialogue_message(DumbledoresOffice.get_instance(), DumbledoresOffice.get_instance().get_player(), self._message))
            else:
                self._message_displayed = False
                if (self._text_bubble.is_visible()):
                    self._text_bubble.hide()
        return messages + DumbledoresOffice.get_instance().send_grid_to_players()
