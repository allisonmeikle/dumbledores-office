from typing import Type, Optional, Set, TYPE_CHECKING, Any
from .imports import *
from .position_observer import PositionObserver
from .house_observer import HouseObserver
from .user_commands import *
from .house import House
from .null_player import NullPlayer
from .chatbot import *
from .util import *
from .dumbledores_office import *

if TYPE_CHECKING:
    from coord import Coord
    from maps.base import Message
    from Player import Player, HumanPlayer
    from tiles.map_objects import *
    from .user_commands import *

class ExampleHouse(Map, SenderInterface):
    MAIN_ENTRANCE = True
    __instance: Optional["ExampleHouse"] = None

    def __new__(cls: Type["ExampleHouse"]) -> "ExampleHouse":
        """
        Creates or retrieves the singleton instance of ExampleHouse.

        Args:
            cls (Type[ExampleHouse]): The class reference used to create or retrieve the singleton instance.

        Returns:
            ExampleHouse: The singleton instance of ExampleHouse. If an instance already exists, it returns the existing one.
        """
        if cls.__instance is None:
            cls.__instance = super(ExampleHouse, cls).__new__(cls)
        return cls.__instance

    
    def __init__(self) -> None:
        """
        Initializes the ExampleHouse object.

        This method initializes the observer list for position observers before calling the superclass
        constructor to configure the map properties. The ExampleHouse is set up with a specific name,
        description, size, entry point, background music, and background tile image.

        Precondition:
            The observer list is initialized prior to calling the superclass __init__.

        Returns:
            None
        """
        # Observer list - initialize this before calling super().__init__
        self.__position_observers: Set[PositionObserver] = set()
        
        super().__init__(
            name="Example Map",
            description="The is the waiting lobby! If you cannot enter Dumbledore's Office right away, you will need to wait for your turn.",
            size=(15, 15),
            entry_point=Coord(15, 2),  # Where the player appears
            background_music='lobby_music',
            background_tile_image='floor'
        )

    @staticmethod
    def get_instance() -> "ExampleHouse":
        """
        Returns the singleton instance of DumbledoresOffice, creating it if necessary.

        Returns:
            ExampleHouse: The singleton instance of DumbledoresOffice.
        """
        if ExampleHouse.__instance is None:
            ExampleHouse.__instance = ExampleHouse()
        return ExampleHouse.__instance

    def get_name(self) -> str:
        """
        Returns the name of the sender.

        Returns:
            str: The name of the sender ("EXAMPLE HOUSE").
        """
        return "EXAMPLE HOUSE"

    def get_player(self) -> HumanPlayer:
        """
        Retrieves the current player in the room.

        Returns:
            HumanPlayer: The current player, or a NullPlayer if the room is empty.
        """
        players = self.get_human_players()
        if not players:
            # Return a NullPlayer instance if no players are in the room.
            return NullPlayer()
        return players[0]

    def get_objects(self) -> list[tuple["MapObject", "Coord"]]:
        """
        Retrieves all objects to be placed in the office.

        Returns:
            list[tuple["MapObject", "Coord"]]: A list of tuples, each containing a map object and its coordinate.
        """
        objects: list[tuple["MapObject", "Coord"]] = []

        objects.append((SinglePlayerDoor('arch_bottom', 'Dumbledores Office'), Coord(1, 7)))
        
        objects.append((Door("arch", linked_room="Trottier Town", is_main_entrance=True), Coord(13, 7)))

        # Decor (walls, candles, etc)
        objects.append((Decor("front_wall_left", False, 1), Coord(13, 0)))
        objects.append((Decor("front_wall_right", False, 1), Coord(13, 9)))
        objects.append((Decor("front_wall_left", False, 1), Coord(0, 0)))
        objects.append((Decor("front_wall_right", False, 1), Coord(0, 9)))
        objects.append((Decor("right_wall", False, 0), Coord(2, 13)))
        objects.append((Decor("left_wall", False, 0), Coord(2, 0)))
        objects.append((Decor("arch_top", False, 0), Coord(0, 7)))
        
        # Define active positions 
        dobby_active_positions = [
            Coord(7, 4),   # left
            Coord(9, 4),   # right
            Coord(8, 3),   # above
            Coord(8, 5)    # below
        ]
        
        # Create and add Dobby as a position observer.
        dobby = DobbyDecor("dobby", dobby_active_positions)
        self.add_position_observer(dobby)
        objects.append((dobby, Coord(6, 4)))  

        for y in range(1, 11, 3):
            for x in (2, 12):  # Left and right wall positions.
                objects.append((CandleLobby(), Coord(y, x)))

        return objects
    
    def add_position_observer(self, observer: PositionObserver) -> None:
        """
        Adds a position observer to the map and notifies it of the current positions of all human players.

        Args:
            observer (PositionObserver): The observer to add.
        """
        self.__position_observers.add(observer)
        # Notify with positions of existing players
        for player in self.get_human_players():
            observer.update_position(player.get_current_position())
        
    def remove_position_observer(self, observer: PositionObserver) -> None:
        """
        Removes a position observer from the map.

        Args:
            observer (PositionObserver): The observer to remove.
        """
        if observer in self.__position_observers:
            self.__position_observers.remove(observer)
            
    def notify_position_observers(self, position: Coord) -> list[Message]:
        """
        Notifies all position observers about a position change.

        Args:
            position (Coord): The position to notify observers about.

        Returns:
            list[Message]: A list of messages to send to players generated by the observers.
        """
        messages = []
        for observer in self.__position_observers:
            messages.extend(observer.update_position(position))
        return messages
        
    def move(self, player: "Player", direction: str) -> list[Message]:
        """
        Handles player movement and notifies position observers of the new position.

        Args:
            player (Player): The player who is moving.
            direction (str): The direction in which the player is moving (e.g., 'up', 'down', 'left', 'right').

        Returns:
            list[Message]: A list of messages generated as a result of the player's movement.
        """
        # Call the original move method first.
        messages = super().move(player, direction)
        
        # After move is complete, notify position observers.
        messages.extend(self.notify_position_observers(player.get_current_position()))
        
        return messages

# Single-player door
class SinglePlayerDoor(Door):
    """
    A door that only allows one player at a time into Dumbledore's Office.
   
    """
    def player_entered(self, player: HumanPlayer) -> list[Message]:
        """
        Handles a player entering the door, only allowing entry if the office is empty.

        Args:
            player (HumanPlayer): The player entering the door.

        Returns:
            list[Message]: A list of messages to send to the player.
        """
        messages = []
        player.set_state("sorting_in_progress", False)
        if DumbledoresOffice.get_instance().is_occupied():
            return [ServerMessage(player, "Sorry, Dumbledore is currently busy counseling a troubled student... or possibly just gossiping with the portraits. Please come back later.")]
        DumbledoresOffice.get_instance().set_theme_updated(False)
        messages.extend(super().player_entered(player))
        return messages

class CandleLobby(MapObject):
    """
    Represents a candle in the lobby environment.

    This candle cycles through a series of images to create an animated flickering effect.
    It updates its appearance every second and triggers grid updates for the room.
    """

    def __init__(self, image_name: str = "candelabrum_small_1", passable: bool = False, z_index: int = 1) -> None:
        """
        Initializes a new CandleLobby object.

        Args:
            image_name (str): The default image name for the candle.
            passable (bool): Indicates if the player is able to move on top of the candle.
            z_index (int): The z-index at which to place the candle.
        """
        super().__init__(f"tile/decor/candle/{image_name}", passable, z_index)
        self.__image_name_index = 1

    def update(self) -> list[Message]:
        """
        Updates the candle's image to simulate flickering and returns updated grid messages.

        Returns:
            list[Message]: A list of messages generated by ExampleHouse to update the grid.
        """
        # Called every second.
        self.__image_name_index = (self.__image_name_index + 1) % 6
        self.set_image_name(f"tile/decor/candle/candelabrum_small_{self.__image_name_index}")
        return ExampleHouse.get_instance().send_grid_to_players()

class DobbyDecor(MapObject, PositionObserver):
    """
    Represents Dobby the house elf.
    Implements the PositionObserver interface to update visibility based on player position.
    """

    def __init__(self, image_name: str = "dobby", active_positions: list[Coord] = []) -> None:
        """
        Initializes a new DobbyDecor instance.

        Args:
            image_name (str): The image name for Dobby.
            active_positions (list[Coord]): A list of coordinates where Dobby is active.
                If no active positions are provided, default positions (adjacent tiles) are set.
        """
        super().__init__(f"tile/object/{image_name}", passable=False)
        
        # if no active positions are provided, create default ones (adjacent tiles)
        if not active_positions:
            # define active positions as tiles adjacent to Dobby's position
            self.__active_positions = [
                Coord(6, 4),  # left
                Coord(8, 4),  # right
                Coord(7, 3),  # above
                Coord(7, 5)   # below
            ]
        else:
            self.__active_positions = active_positions
        
        # track whether the interaction has happened in the current visit
        self.__has_interacted = False

    def update_position(self, position: Coord) -> list[Message]:
        """
        Updates DobbyDecor based on the player's new position.
        Implements the PositionObserver update method.

        Args:
            position (Coord): The new position of the player.

        Returns:
            list[Message]: A list of messages generated when the player enters an active position.
        """
        messages = []
        
        # check if the player is in an active position
        if position in self.__active_positions:
            # only trigger if not already interacted in this visit
            if not self.__has_interacted:
                # using ExampleHouse as the sender
                player = ExampleHouse.get_instance().get_player()
                if player:
                    # mark as interacted
                    self.__has_interacted = True
                    
                    # add the sound message
                    messages.append(SoundMessage(player, "dobby_free.mp3", repeat=False))
                    
                    # add the dialogue message 
                    dialogue_message = get_custom_dialogue_message(
                        ExampleHouse.get_instance(), 
                        player, 
                        "Master has presented Dobby with clothes........................ Dobby is freeeeeeeeeeeeeee!",
                        auto_delay=0, 
                        press_enter=True  
                    )
                    messages.append(dialogue_message)
        
        return messages