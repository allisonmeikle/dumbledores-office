from datetime import datetime
from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

from ..message import *
from ..coord import Coord
from ..command import MenuCommand
from ..tiles.base import MapObject, Exit, Observer

if TYPE_CHECKING:
    from NPC import NPC
    from maps.base import Map

class SelectionInterface(ABC):
    """ Interface for an object that can be used as a menu. """

    @abstractmethod
    def select_option(self, player: "HumanPlayer", option: str) -> list[Message]:
        """ Called when the player selects the specified option from this menu. """
        pass

class CharacterMapObject(MapObject):
    def __init__(self, image_name: str, passable: bool, facing_direction : Literal['up', 'down', 'left', 'right'] = 'down') -> None:
        self.__facing_direction: Literal['up', 'down', 'left', 'right'] = facing_direction
        super().__init__(f'character/{image_name}', passable=passable, z_index=1)

    def get_facing_direction(self) -> Literal['up', 'down', 'left', 'right']:
        """ Get the player's facing direction. """
        return self.__facing_direction

    def set_facing_direction(self, direction: Literal['up', 'down', 'left', 'right']) -> None:
        """ Set the player's facing direction. """
        self.__facing_direction = direction

    def get_image_name(self) -> str:
        """ Returns the name of the image file for the object. """
        return f"{super().get_image_name()}/{self.__facing_direction}1"

    def _get_image_size(self) -> tuple[int, int]:
        return (1, 1)

class Empty(MapObject):
    def __init__(self, passable: bool = True) -> None:
        super().__init__('', passable=passable)

class Door(MapObject):
    def __init__(self, image_name: str, linked_room: str = "", is_main_entrance=False) -> None:
        """
        Creates a new Door object.

        Arguments:
        image_name: The name of the image file for the door.
        linked_room: The classname of the Map that this door leads to.
        is_main_entrance: Whether this door is the main entrance to your group's space.
        """
        super().__init__(f'tile/door/{image_name}', passable=True, z_index=0)
        self.__connected_room = None
        self.__linked_room = linked_room
        self.__is_main_entrance = is_main_entrance

    def connect_to(self, connected_room: "Map", new_entry_point: Coord) -> None:
        self.__connected_room = connected_room
        self.__new_entry_point = new_entry_point
    
    def is_main_entrance(self) -> bool:
        return self.__is_main_entrance

    def player_entered(self, player) -> list[Message]:
        if self.__connected_room is None or self.__new_entry_point is None:
            print("Door has no link")
            return []

        # move player to the new map
        return player.change_room(self.__connected_room, entry_point=self.__new_entry_point)

    def get_exits(self) -> list[Exit]:
        return [Exit(self, self._position, self.__linked_room, is_main_entrance=self.__is_main_entrance)]

class Background(MapObject):
    def __init__(self, image_name: str, passable: bool = True) -> None:
        super().__init__(f'tile/background/{image_name}', passable=passable, z_index=-2)

class Water(Background):
    def __init__(self, image_name: str = 'water') -> None:
        super().__init__(image_name, passable=False)

class ExtDecor(MapObject):
    def __init__(self, image_name: str, passable = False) -> None:
        super().__init__(f'tile/ext_decor/{image_name}', passable=passable)

class Sign(ExtDecor):
    def __init__(self, image_name: str = 'sign', text: str = '') -> None:
        super().__init__(image_name)
        self._text: str = text
    
    def player_interacted(self, player: "HumanPlayer") -> list[Message]:
        return [DialogueMessage(self, player, self._text, 'sign')]

class IntDecor(MapObject):
    def __init__(self, image_name: str, z_index: int = 0) -> None:
        super().__init__(f'tile/int_decor/{image_name}', passable=False, z_index=z_index)

class Counter(IntDecor):
    def __init__(self, image_name: str, npc: "NPC") -> None:
        super().__init__(f'counter_{image_name}')
        self.__npc: "NPC" = npc
    
    def player_interacted(self, player: "HumanPlayer") -> list[Message]:
        return self.__npc.player_interacted(player)

class YellowCounter(Counter):
    def __init__(self, npc: "NPC") -> None:
        super().__init__('yellow', npc)

class Utility(MapObject):
    def __init__(self, image_name: str, passable: bool = True) -> None:
        super().__init__(f'tile/utility/{image_name}', passable=passable, z_index=-1)

UtilityObject = Utility

class PressurePlate(Utility, Observer):
    def __init__(self, image_name='pressure_plate', stepping_text='You stepped on the pressure plate!'):
        super().__init__(image_name, passable=True)
        self.__stepping_text = stepping_text
    
    def update_on_notification(self, stepping_text):
        self.__stepping_text = stepping_text

    def player_entered(self, player) -> list[Message]:
        return [DialogueMessage(self, player, self.__stepping_text, 'pressure_plate')]

class Board(Sign, Observer):
    def __init__(self, image_name='board', text='template'):
        super().__init__(image_name, text)
    
    def update_on_notification(self, chosen_song_name):
        # This method is called whenever the plate picks a new song.
        self._text = chosen_song_name

class MusicPlayingPressurePlate(PressurePlate):
    def __init__(self, sound_path: str = ''):
        self.__sound_path = sound_path
        super().__init__()

    def set_sound_path(self, sound_path: str):
        self.__sound_path = sound_path

    def player_entered(self, player) -> list[Message]:
        return [SoundMessage(player, self.__sound_path)]

class Computer(Utility, SelectionInterface):
    def __init__(self, image_name: str = 'computer', menu_name: str = 'Select an option', menu_options: dict[str, MenuCommand] = {}) -> None:
        super().__init__(image_name, passable=False)
        self.__menu_name: str = menu_name
        self.__menu_options: dict[str, MenuCommand] = dict(menu_options)

    def select_option(self, player: "HumanPlayer", option: str) -> list[Message]:
        return self.__menu_options[option].execute(player.get_current_room(), player)

    def player_interacted(self, player: "HumanPlayer") -> list[Message]:
        player.set_current_menu(self)
        return [MenuMessage(self, player, self.__menu_name, list(self.__menu_options))]

class SpecialTree(ExtDecor):
    def __init__(self, image_name='special_tree') -> None:
        super().__init__(f'special_tree')
    
    def player_interacted(self, player: "HumanPlayer") -> list[Message]:
        items = player.get_state('special_tree_items', [])

        current_date = datetime.now().strftime('%m/%d/%Y')
        current_coord = player.get_position()
        item = (current_date, current_coord)
        if item in items:
            return [DialogueMessage(self, player, "There is nothing left to take! Better come back later...", 'sign')]
        else:
            items.append(item)
            player.set_state('special_tree_items', items)
            return [DialogueMessage(self, player, "You take a fruit from the tree.", 'sign')]