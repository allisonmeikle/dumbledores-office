from typing import TYPE_CHECKING, Literal
from .imports import *

if TYPE_CHECKING:
    from coord import Coord
    from maps.base import Message
    from Player import HumanPlayer
    from tiles.map_objects import *

class NullPlayer(HumanPlayer):
    """
    A Null Object version of Player. Used when no actual player is present.
    Provides default behavior for all player methods without causing errors.
    """

    def __init__(self) -> None:
        """
        Initializes a NullPlayer with a default name and position.
        """
        super().__init__("NullPlayer", image = 'empty', passable=True, facing_direction='up')
        self.__name: str = "NullPlayer"
        self.__current_position = Coord(0, 0)

    def update_position(self, new_position: Coord, map: "Map") -> None:
        """
        Stub method to match HumanPlayer interface. Does nothing for NullPlayer.

        Args:
            new_position (Coord): The new position to update to.
            map (Map): The map in which the player resides.
        """
        return

    def get_name(self) -> str:
        """
        Returns the name of the NullPlayer.

        Returns:
            str: The name "NullPlayer".
        """
        return self._name

    def get_current_position(self) -> Coord:
        """
        Returns the current position of the NullPlayer.

        Returns:
            Coord: The position as a Coord object.
        """
        return Coord.from_Coord(self._current_position)

    def get_current_room(self) -> 'Map':
        """
        Returns the current room the player is in.

        Returns:
            Map: The singleton instance of Dumbledore's Office.
        """
        from .dumbledores_office import DumbledoresOffice
        return DumbledoresOffice.get_instance()

    def get_current_map_object(self) -> 'list[MapObject]':
        """
        Returns an empty list of map objects since the NullPlayer has no interactions.

        Returns:
            list[MapObject]: An empty list.
        """
        return []

    def move(self, direction_s: Literal['up', 'down', 'left', 'right']) -> list[Message]:
        """
        Stub method to match HumanPlayer interface. NullPlayer cannot move.

        Args:
            direction_s (str): The direction to move in.

        Returns:
            list[Message]: Always returns an empty list.
        """
        return []

    def __str__(self) -> str:
        """
        String representation of the NullPlayer.

        Returns:
            str: The name of the player.
        """
        return self.get_name()

    def change_room(self, new_room: 'Map', msg_to_cur_room: str = "", msg_to_new_room: str = "", entry_point = None) -> list[Message]:
       """
        Stub method for room changes. Does nothing for NullPlayer.

        Args:
            new_room (Map): The new room to enter.
            msg_to_cur_room (str): Message to send to current room (unused).
            msg_to_new_room (str): Message to send to new room (unused).
            entry_point (Coord, optional): Entry point for new room (unused).

        Returns:
            list[Message]: Always returns an empty list.
        """
       return []