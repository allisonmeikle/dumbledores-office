from abc import ABC
from typing import TYPE_CHECKING
from collections.abc import Callable

if TYPE_CHECKING:
    from message import Message
    from Player import HumanPlayer

class KeybindInterface(ABC):
    def __init__(self):
        pass #self._keybinds = {}

    def _get_keybinds(self) -> dict[str, Callable[["HumanPlayer"], list["Message"]]]:
        """ Get the keybinds for the map. Can be overridden by subclasses, but super() should be called. """
        return {}

    def is_valid_keybind(self, key: str) -> bool:
        """ Check if the key is a valid keybind. """
        return key in self._get_keybinds() # self._keybinds

    def key_event(self, player: "HumanPlayer", key: str) -> list["Message"]:
        """ Handle a key event for a player. """
        return self._get_keybinds()[key](player)