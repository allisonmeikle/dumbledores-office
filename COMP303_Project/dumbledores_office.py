import random
from typing import Type, TypeVar, Optional, Set, TYPE_CHECKING, Any, cast
from enum import Enum
from .imports import *
from .position_observer import PositionObserver
from .house_observer import HouseObserver
from .house import House
from .null_player import NullPlayer
from .chatbot import *
from .user_commands import *
from .util import *
from .text_bubble import *

if TYPE_CHECKING:
    from coord import Coord
    from maps.base import Message
    from Player import Player, HumanPlayer
    from tiles.map_objects import *
    from .user_commands import *

class DumbledoresOffice(Map, SenderInterface):
    """
    Represents Dumbledore's Office in the virtual world.
    
    This class implements a singleton pattern to ensure that only one instance of
    DumbledoresOffice exists. It serves as the central hub for interactive components,
    observers, and commands within the office.
    """
    NULL_PLAYER = NullPlayer()    
    # Static field to hold the singleton instance
    __instance : Optional["DumbledoresOffice"] = None

    def __new__(cls : Type["DumbledoresOffice"]) -> "DumbledoresOffice":
        """
        Creates or retrieves the singleton instance of DumbledoresOffice.
        This method ensures that only one instance of DumbledoresOffice is created.
        If an instance already exists, it returns the existing one.

        Args:
            cls (Type[DumbledoresOffice]): The class reference that is calling the singleton instance.

        Returns:
            DumbledoresOffice: The singleton instance of the DumbledoresOffice class.
        """
        if cls.__instance is None:
            cls.__instance = super(DumbledoresOffice, cls).__new__(cls)
        return cls.__instance
    
    def __init__(self) -> None:
        """
        Initializes DumbledoresOffice with all its interactive components.

        This method sets up the initial state of the office:
        - Sets the current player to NullPlayer.
        - Initializes the observer lists for house and position changes.
        - Calls the superclass __init__ to configure the office properties including name, description,
          size, entry point, background music, background tile image, and chat commands.
        """
        # Track the current player
        self.__theme_updated = False
        # Initialize observer lists
        self.__house_observers: Set[HouseObserver] = set()
        self.__position_observers: Set[PositionObserver] = set()

        super().__init__(
            name="Dumbledore's Office",
            description="Welcome to Dumbledore's Office! Please be aware that this room is modelled after the Harry Potter series and we wish to acknowledge the ongoing public discussions and controversy regarding statements made by its author, J.K. Rowling, particularly concerning gender identity. We encourage all players to approach this game with an informed understanding of these discussions and to engage with the content thoughtfully and inclusively.\n",
            size=(15, 15),
            entry_point=Coord(13, 7),  # Where the player appears
            background_music='hedwigs_theme',
            background_tile_image='floor',
            chat_commands=[ChatBotChatCommand, BookCommand]
        )
  

    @staticmethod
    def get_instance() -> "DumbledoresOffice":
        """
        Returns the singleton instance of DumbledoresOffice, creating it if necessary.

        Returns:
            DumbledoresOffice: The singleton instance of DumbledoresOffice.
        """
        if DumbledoresOffice.__instance is None:
            DumbledoresOffice.__instance = DumbledoresOffice()
        return DumbledoresOffice.__instance
    
    def get_objects(self) -> list[tuple["MapObject", "Coord"]]:
        """
        Retrieves all objects to be placed in DumbledoresOffice.

        Returns:
            list[tuple["MapObject", "Coord"]]: A list of tuples where each tuple consists of a map object and its associated coordinate.
        """
        objects: list[tuple["MapObject", "Coord"]] = []
        
        # Door
        objects.append((InteriorDoor('arch', 'Example House'), Coord(13, 7)))
        
        # Rug
        rug = Rug()
        self.add_house_observer(rug)
        objects.append((rug, Coord(3, 3)))
        
        # Sorting hat
        sorting_hat_bubble = TextBubble(TextBubbleImage.SPACE)
        objects.append((sorting_hat_bubble, Coord(9, 8)))
        sorting_hat = SortingHat(
            [Coord(12, 7), Coord(12, 8)], 
            "sorting_hat", 
            sorting_hat_bubble
        )
        self.add_position_observer(sorting_hat)
        objects.append((sorting_hat, Coord(10, 7)))
        
        # Bookshelf
        active_positions = [Coord(2, 5), Coord(2, 7), Coord(2, 6), Coord(2, 8), Coord(2, 9)]
        bookshelf_text_bubble = TextBubble(TextBubbleImage.BOOK)
        objects.append((bookshelf_text_bubble, Coord(0, 8)))
        bookshelf = Bookshelf(
            bookshelf_text_bubble,
            "bookshelf",
            active_positions,
            passable = True
        )
        print(bookshelf.get_image_name())
        self.add_position_observer(bookshelf)
        objects.append((bookshelf, Coord(0, 5)))
        
        # Create the portraits

        # Dumbledore
        dumbledore_text_bubble = TextBubble(TextBubbleImage.CHAT)
        objects.append((dumbledore_text_bubble, Coord(0, 4)))
        dumbledore_portrait = ChatObject(
            dumbledore_text_bubble, 
            "portrait/dumbledore", 
            [Coord(2, 3), Coord(2, 4)]
        )
        self.add_position_observer(dumbledore_portrait)
        self.add_house_observer(dumbledore_portrait)
        objects.append((dumbledore_portrait, Coord(0, 3)))
        
        # Hermione
        hermione_text_bubble = TextBubble(TextBubbleImage.CHAT)
        objects.append((hermione_text_bubble, Coord(0, 11)))
        hermione_portrait = ChatObject(
            hermione_text_bubble, 
            "portrait/hermione", 
            [Coord(2, 10), Coord(2, 11)]
        )
        self.add_position_observer(hermione_portrait)
        self.add_house_observer(hermione_portrait)
        objects.append((hermione_portrait, Coord(0, 10)))
        
        # Snape
        snape_text_bubble = TextBubble(TextBubbleImage.CHAT_UP)
        objects.append((snape_text_bubble, Coord(6, 0)))
        snape_portrait = ChatObject(
            snape_text_bubble, 
            "portrait/snape", 
            [Coord(7, 2), Coord(8, 2)]
        )
        self.add_position_observer(snape_portrait)
        self.add_house_observer(snape_portrait)
        objects.append((snape_portrait, Coord(7, 0)))
        
        # Peeves
        peeves_text_bubble = TextBubble(TextBubbleImage.CHAT_UP)
        objects.append((peeves_text_bubble, Coord(6, 13)))
        peeves_portrait = ChatObject(
            peeves_text_bubble, 
            "portrait/peeves", 
            [Coord(7, 12), Coord(8, 12)]
        )
        self.add_position_observer(peeves_portrait)
        self.add_house_observer(peeves_portrait)
        objects.append((peeves_portrait, Coord(7, 13)))
        
        # Pensieve
        pensieve_text_bubble = TextBubble(TextBubbleImage.CHAT)
        objects.append((pensieve_text_bubble, Coord(4, 3)))
        pensieve = ChatObject(
            pensieve_text_bubble, 
            "pensieve", 
            [Coord(5, 3), Coord(6, 3), Coord(6, 2)]
        )
        self.add_position_observer(pensieve)
        self.add_house_observer(pensieve)
        objects.append((pensieve, Coord(4, 2)))
        
        # Phoenix
        phoenix_text_bubble = TextBubble(TextBubbleImage.SPACE_PHOENIX)
        objects.append((phoenix_text_bubble, Coord(2, 12)))
        phoenix = Phoenix(
            phoenix_text_bubble,
            "phoenix",
            [Coord(5, 10), Coord(5, 11), Coord(6, 11), Coord(6, 12)]
        )
        self.add_position_observer(phoenix)
        objects.append((phoenix, Coord(4, 12)))
        
        # Decor (walls, candles, etc)
        front_wall_left = Decor("front_wall_left", False, 1)
        objects.append((front_wall_left, Coord(13, 0)))
        front_wall_right = Decor("front_wall_right", False, 1)
        objects.append((front_wall_right, Coord(13, 9)))
        back_wall = Decor("back_wall_full", False, 1)
        objects.append((back_wall, Coord(0, 0)))
        right_wall = Decor("right_wall", False, 0)
        objects.append((right_wall, Coord(2, 13)))
        left_wall = Decor("left_wall", False, 0)
        objects.append((left_wall, Coord(2, 0)))
        
        # Desk
        objects.append((Decor("desk", False, 1), Coord(6, 5)))
        
        # Candles
        candle_positions = [(0, 2), (0, 12), (10, 2), (10, 12)]
        for y, x in candle_positions:
            objects.append((Candle(), Coord(y, x)))
        
        return objects
    
    def get_name(self) -> str:
        """
        Returns the name of the sender.

        Returns:
            str: The name of the sender, which is "DUMBLEDORE'S OFFICE".
        """
        return "DUMBLEDORE'S OFFICE"

    def is_occupied(self) -> bool:
        """
        Checks if the office is currently occupied by a player.

        Returns:
            bool: True if a player is in the office; otherwise, False.
        """
        return self.get_player() != self.NULL_PLAYER
    
    def get_player(self) -> HumanPlayer:
        """
        Retrieves the current player in the office.

        Returns:
            HumanPlayer: The current player, or a NullPlayer if the office is empty.
        """
        if (self.get_human_players()):
            return self.get_human_players()[0]
        else:
            return self.NULL_PLAYER

    def get_house(self) -> Optional[House]:
        """
        Retrieves the current player's house.

        Returns:
            Optional[House]: The House enum corresponding to the player's house if set; otherwise, None.
        """
        if self.get_player_state("House", ""):
            return House[self.get_player_state("House", "")]
        else:
            return None
        
    def get_player_name(self) -> str:
        """
        Retrieves the name of the current player in the office.

        Returns:
            str: The name of the current player.
        """
        return self.get_player().get_name()

    def get_player_position(self) -> Coord:
        """
        Retrieves the current position of the player in the office.

        Returns:
            Coord: The current coordinate position of the player.
        """
        return self.get_player().get_current_position()
    
    def get_player_state(self, state: str, default: Any = 0) -> Any:
        """
        Retrieves the specified state value of the current player.

        Args:
            state (str): The name of the state variable to retrieve.
            default (Any, optional): The default value to return if the state is not set. Defaults to 0.

        Returns:
            Any: The value of the specified state for the current player.
        """
        return self.get_player().get_state(state, default)
    
    def set_player_state(self, state: str, value: Any) -> None:
        """
        Sets the specified state for the current player.

        Args:
            state (str): The name of the state variable to set.
            value (Any): The value to assign to the specified state.
        """
        self.get_player().set_state(state, value)

    def update_theme(self) -> list[Message]:
        """
        Updates the room's theme based on the current player's house.

        Returns:
            list[Message]: A list of messages notifying the observers and the players of the theme change.
        """
        messages = []
        print ("Update theme called, got house: " + str(self.get_house()))
        if self.get_house():
            theme_messages = {
                House.GRYFFINDOR: "The room transforms with Gryffindor's scarlet and gold!",
                House.HUFFLEPUFF: "The room warms with Hufflepuff's yellow and black!",
                House.RAVENCLAW: "The room brightens with Ravenclaw's blue and bronze!",
                House.SLYTHERIN: "The room shifts with Slytherin's green and silver!",
            }
            message = theme_messages.get(self.get_house())
            messages.extend(self.send_message_to_players(message))
            self.__theme_updated = True
        return self.notify_house_observers(self.get_house()) + messages
    
    def set_theme_updated(self, theme_updated : bool) -> None:
        self.__theme_updated = theme_updated

    def update(self) -> list[Message]:
        messages = super().update()
        print("Called update on DumbledoresOffic, theme updated is " + str(self.__theme_updated))
        if (not self.__theme_updated):
            messages.extend(self.update_theme())
        return messages

    def move(self, player: "Player", direction: str) -> list[Message]:
        """
        Handles player movement with minimal interference.

        Args:
            player (Player): The player who is moving.
            direction (str): The direction in which the player is moving (e.g., 'up', 'down', 'left', 'right').

        Returns:
            list[Message]: A list of messages generated as a result of the player's movement.
        """
        messages: list[Message] = []

        if (Coord(12, 7).distance(player.get_current_position()) == 0):
            print('Player is at (12, 7)')
            messages.extend(self.update())
        
        # Can't exit through door without moving off of it
        if (Coord(13, 7).distance(player.get_current_position()) == 0 and 
            direction in ['down', 'right'] and isinstance(player, HumanPlayer)):
            messages.append(ServerMessage(player, "Please step off the door before trying to exit"))
            return messages

        # Can't interact with the room (move past the sorting hat) until sorted
        sorting_hat = MapObject.get_obj("sorting_hat")
        if hasattr(sorting_hat, "is_sorting_in_progress"):
            sorting_hat = cast(SortingHat, sorting_hat)
            # Check that player is in range of the sorting hat and is not sorted before restricting movement
            messages.append(ServerMessage(player, f"Current sorting state: {sorting_hat.is_player_sorted(player)}, house is {player.get_state("House", "")}, and player in sorting range is {player.get_state("in_sorting_range", False)}"))
            if (isinstance(player, HumanPlayer) and not sorting_hat.is_player_sorted(player) and player.get_state("in_sorting_range", False)):
                # If not sorted and try to move past the sorting hat, restrict room access until sorted
                if ((player.get_current_position().distance(Coord(12, 7)) == 0 and direction == 'left') or (player.get_current_position().distance(Coord(12, 8)) == 0 and direction == 'right')):
                    messages.append(ChatMessage(sorting_hat, player, "Sorry, I can't let you explore the rest of the office until I know what house to put you in! Try interacting with me!"))
                    return messages
        
        # Call the original move method first
        messages.extend(super().move(player, direction))
        messages.extend(self.notify_position_observers(player.get_current_position()))
        messages.append(ServerMessage(player, f"Moved {direction} to {player.get_current_position()}"))
        # Return the messages generated during the movement process
        return messages

    # Observer pattern methods
    def add_house_observer(self, observer: HouseObserver) -> None:
        """
        Adds a house observer to the office and updates it with the current house.

        Args:
            observer (HouseObserver): The observer to add.
        """
        self.__house_observers.add(observer)
        observer.update_house(self.get_house())
    
    def add_position_observer(self, observer: PositionObserver) -> None:
        """
        Adds a position observer to the office and updates it with the current player's position if available.

        Args:
            observer (PositionObserver): The observer to add.
        """
        self.__position_observers.add(observer)
        if self.get_player() != self.NULL_PLAYER:
            observer.update_position(self.get_player_position())
    
    def remove_house_observer(self, observer: HouseObserver) -> None:
        """
        Removes a house observer from the office.

        Args:
            observer (HouseObserver): The observer to remove.
        """
        if observer in self.__house_observers:
            self.__house_observers.remove(observer)
        
    def remove_position_observer(self, observer: PositionObserver) -> None:
        """
        Removes a position observer from the office.

        Args:
            observer (PositionObserver): The observer to remove.
        """
        if observer in self.__position_observers:
            self.__position_observers.remove(observer)
    
    def notify_position_observers(self, position: Coord) -> list[Message]:
        """
        Notifies all position observers of a new player position.

        Args:
            position (Coord): The new player position.

        Returns:
            list[Message]: A list of messages generated by each observer in response to the new position.
        """
        messages = []
        for observer in self.__position_observers:
            messages.extend(observer.update_position(position))
        return messages
            
    def notify_house_observers(self, house: Optional[House]) -> list[Message]:
        """
        Notifies all house observers of a change in the player's house.

        Args:
            house (Optional[House]): The new house to notify observers about; None if the player's house is not set.

        Returns:
            list[Message]: A list of messages generated by each observer in response to the house change.
        """
        messages = []
        # Notify all house observers
        for observer in self.__house_observers:
            messages.extend(observer.update_house(house))
        return messages

class Phoenix(MapObject, PositionObserver):
    """
    Represents Fawkes the Phoenix, who can burn and regenerate.
    Implements the PositionObserver interface to update visibility based on player position.
    """
    __is_burning : bool = False
    __regeneration_countdown = 0
    def __init__(self, text_bubble: "TextBubble", image_name: str = "phoenix", active_positions: list[Coord] = []) -> None:
        """
        Initializes a new Phoenix instance.

        Args:
            text_bubble (TextBubble): The text bubble to display when near the phoenix.
            image_name (str, optional): The image name for the phoenix. Defaults to "phoenix".
            active_positions (list[Coord], optional): The coordinates where the phoenix is considered active. Defaults to an empty list.
        """
        super().__init__(f"tile/object/{image_name}", passable=False)
        
        self._text_bubble = text_bubble
        self._active_positions = active_positions
        self._message = "Interact with Fawkes the phoenix to watch him burst into flames and regenerate before your eyes!"
        self._message_displayed = False

    def player_interacted(self, player: "HumanPlayer") -> list["Message"]:
        """
        Handles player interaction with Fawkes the Phoenix.
        If the player presses space bar near Fawkes, he will burst into flames and begin the regeneration process.

        Args:
            player (HumanPlayer): The player interacting with Fawkes.

        Returns:
            list[Message]: A list of messages to send to the player.
        """
        if Phoenix.__is_burning:
            return [get_custom_dialogue_message(DumbledoresOffice.get_instance(), player, "Fawkes is already in the process of burning and regenerating.")]
        
        # Start the burning and regeneration cycle
        Phoenix.__is_burning = True
        Phoenix.__regeneration_countdown = 3  # Will regenerate after 3 updates
        
        return []
    
    def update(self) -> list["Message"]:
        """
        Update method called every tick.
        Handles the phoenix's burning and regeneration cycle.

        Returns:
            list[Message]: A list of messages to send to players.
        """
        messages = []
        
        if Phoenix.__is_burning:
            self.set_image_name(f"tile/object/phoenix{Phoenix.__regeneration_countdown}")
            Phoenix.__regeneration_countdown -= 1
            if Phoenix.__regeneration_countdown < 0:
                # Regenerate the phoenix
                Phoenix.__is_burning = False
                self.set_image_name("tile/object/phoenix")
                
                messages.append(get_custom_dialogue_message(
                    DumbledoresOffice.get_instance(),
                    DumbledoresOffice.get_instance().get_player(),
                    "From the ashes, Fawkes is reborn as a tiny chick that quickly grows back to his majestic form."
                ))
            messages.extend(DumbledoresOffice.get_instance().send_grid_to_players())
        return messages


class Rug(MapObject, HouseObserver):
    """
    Represents a magical rug that changes appearance based on the player's Hogwarts house.
    Implements the HouseObserver interface to update appearance when the house changes.
    """

    def __init__(self, image_name: str = "rug_neutral", passable: bool = True, z_index: int = -1) -> None:
        """
        Initializes a new Rug.

        Args:
            image_name (str): The default image name for the rug.
            passable (bool): Indicates if the player is able to move on top of the rug.
            z_index (int): The z-index at which to place the rug.
        """
        super().__init__(f"tile/decor/rugs/{image_name}", passable, z_index)
    
    def update_house(self, house: Optional[House]) -> list[Message]:
        """
        Updates the rug's appearance based on the player's house.
        Implements the HouseObserver update method.

        Args:
            house (Optional[House]): The player's new house; None if the player is a NullPlayer.

        Returns:
            list[Message]: A list of messages notifying the players of the updated grid state.
        """
        messages = []
        if house is None:
            self.set_image_name("tile/decor/rugs/rug_neutral")
        else:
            self.set_image_name(f"tile/decor/rugs/rug_{house.name.lower()}")
        messages.extend(DumbledoresOffice.get_instance().send_grid_to_players())
        return messages


class ChatBotObject(MapObject, PositionObserver, RecipientInterface, ABC):
    """
    Represents an interactive object that communicates with the ChatBot.
    
    This abstract class provides the basis for objects that utilize a text bubble
    to display messages and that become active at specified positions. It implements
    the PositionObserver and RecipientInterface protocols.
    """
    
    def __init__(self, text_bubble: TextBubble, image_name: str, active_positions: list[Coord] = [], passable: bool = False, z_index: int = 1) -> None:
        """
        Initializes a new ChatBotObject.
        
        Args:
            text_bubble (TextBubble): The TextBubble object that appears when the player is within range.
            image_name (str): The image name for the object.
            active_positions (list[Coord], optional): A list of coordinates where the object is active. Defaults to an empty list.
            passable (bool, optional): Indicates if the player is able to move on top of the object. Defaults to False.
            z_index (int, optional): The z-index at which to place the object. Defaults to 1.
        """
        super().__init__(f"tile/object/{image_name}", passable, z_index)
        self._text_bubble = text_bubble
        self._name = image_name.split("/")[-1].upper()
        self._active_positions = active_positions
        self._message_displayed = False
    
    def get_name(self) -> str:
        """
        Returns the ChatBotObject's name attribute.

        Returns:
            str: The name of the ChatBotObject.
        """
        return self._name

    def set_text_bubble_image(self, image: TextBubbleImage) -> None:
        """
        Sets the text bubble's image for the ChatBotObject.

        Args:
            image (TextBubbleImage): The new image to set for the text bubble.
        """
        self._text_bubble.set_image_name(f"tile/object/message/{image.value}")

    def set_text_bubble_to_default(self) -> None:
        """
        Resets the text bubble's image to its default value.
        """
        self._text_bubble.set_to_default()

    def get_text_bubble_image(self) -> TextBubbleImage:
        """
        Retrieves the current image of the text bubble associated with the ChatBotObject.

        Returns:
            TextBubbleImage: The current image of the text bubble.
        """
        return self._text_bubble.get_image()

    @staticmethod
    def cycle_thinking_image() -> list[Message]:
        """
        Cycles through the 'thinking' images for the active object's text bubble and returns the updated grid messages.

        Returns:
            list[Message]: The grid messages after cycling the text bubble image.
        """
        if UserCommand.get_active_bubble_image() not in THINKING_IMAGES:
            UserCommand.set_active_bubble_image(TextBubbleImage.THINKING1)
        else:
            UserCommand.set_active_bubble_image(THINKING_IMAGES[(THINKING_IMAGES.index(UserCommand.get_active_bubble_image()) + 1) % len(THINKING_IMAGES)])
        return DumbledoresOffice.get_instance().send_grid_to_players()

    def update(self) -> list[Message]:
        """
        Updates the ChatBotObject. If the UserCommand is active and this object is the active object,
        it retrieves the player's message and cycles the 'thinking' image.

        Returns:
            list[Message]: The messages generated during the update.
        """
        messages = []
        if (UserCommand.is_active() and UserCommand.get_active_object() is self):
            messages.extend(UserCommand.get_player_message(DumbledoresOffice.get_instance()))
            messages.extend(ChatBotObject.cycle_thinking_image())
        return messages

    def update_position(self, position: Coord) -> list[Message]:
        """
        Updates the active object based on the player's new position.

        Args:
            position (Coord): The player's new position.

        Returns:
            list[Message]: The messages generated from the update, including any grid updates.
        """
        messages = super().update_position(position)
        if position in self._active_positions:
            UserCommand.set_active_object(self)
        else:
            if (UserCommand.get_active_object() is self):
                UserCommand.set_active_object(None)
        return messages

    @abstractmethod
    def get_response(self, input: str) -> str:
        """
        Retrieves the response for the given input.

        Args:
            input (str): The user input for which a response is to be generated.

        Returns:
            str: The generated response.
        """
        pass

class ChatObject(ChatBotObject, HouseObserver):
    """
    Represents a chat object that interacts with the ChatBot.
    Extends ChatBotObject and implements HouseObserver to update its conversation strategy
    based on changes in the player's house.
    """
    def __init__(self, text_bubble: TextBubble, image_name: str = "", active_positions: list[Coord] = [], passable: bool = False, z_index: int = 1) -> None:
        """
        Initializes a new ChatObject.

        Args:
            text_bubble (TextBubble): The TextBubble object that appears when the player is within range.
            image_name (str): The image name for the object.
            active_positions (list[Coord]): A list of coordinates where the object is active (when the player is there).
            passable (bool, optional): Indicates if the player is able to move on top of the object. Defaults to False.
            z_index (int, optional): The z-index at which to place the object. Defaults to 1.
        """
        super().__init__(text_bubble, image_name, active_positions, passable, z_index)
        self._conversation_strategy = NullConversationStrategy()
        self._message = f"Enter /chat in the chat followed by your prompt to speak to {self.get_name()}"

    def get_response(self, input: str) -> str:
        """
        Retrieves a response from the current conversation strategy based on the provided input.

        Args:
            input (str): The user input for which a response is required.

        Returns:
            str: The response generated by the conversation strategy.
        """
        return self._conversation_strategy.get_response(input)
    
    def update_house(self, house: Optional["House"]) -> list[Message]:
        """
        Updates the conversation strategy based on the given house.

        If a house is provided, dynamically selects and sets the appropriate conversation strategy
        for this ChatObject based on the house. If no house is provided, resets the conversation
        strategy to the null strategy.

        Args:
            house (Optional[House]): The player's house from the House enum; None if the player is a NullPlayer.

        Returns:
            list[Message]: An empty list of messages.
        """
        if house:
            class_name = f"{self.get_name().lower().capitalize()}ConversationStrategy{house.name.lower().capitalize()}"
            from . import chatbot
            strategy_class = getattr(chatbot, class_name, None)

            if strategy_class is None:
                raise ValueError(f"No conversation strategy found for {class_name}")

            self._conversation_strategy = strategy_class()
        else:
            self._conversation_strategy = NullConversationStrategy()
        return []
    
class Bookshelf(ChatBotObject):
    def __init__(self, text_bubble: "TextBubble", image_name: str = "bookshelf", active_positions: list[Coord] = [], passable: bool = False, z_index: int = 1) -> None:
        """
        Initializes a new Bookshelf.

        Args:
            text_bubble (TextBubble): The text bubble associated with the bookshelf.
            image_name (str): The default image name. Defaults to "bookshelf".
            active_positions (list[Coord]): The positions where the bookshelf becomes active.
            passable (bool): Whether the player can walk over the bookshelf. Defaults to False.
            z_index (int): The drawing order. Defaults to 1.
        """
        super().__init__(text_bubble, image_name, active_positions, passable, z_index)
        self._message = "Enter /book in the chat followed by any book title you can dream up and the magical bookshelf will retrieve it for you!"
    
    def get_response(self, input: str) -> str:
        """
        Retrieves the response for a given book title by adding the book object to the grid
        and returning its generated description.

        Args:
            input (str): The book title provided by the user.

        Returns:
            str: The description of the book generated by the ChatBot.
        """
        DumbledoresOffice.get_instance().add_to_grid(Book.get_book(input), Book.get_book(input).get_position())
        return Book.get_book(input).get_description()
    
class Book(MapObject):
    flyweightStore = []

    def __init__(self, title: str, description: str = "", position: Coord = Coord(3, 6)):
        """
        Initializes a new Book instance with the given title, description, and position.

        Args:
            title (str): The title of the book.
            description (str, optional): The description of the book. Defaults to an empty string.
            position (Coord, optional): The position of the book on the grid. Defaults to Coord(3, 6).
        """
        self.__image_name = f"tile/object/book/book{random.randint(1, 5)}"
        super().__init__(self.__image_name, True, 2)
        self.__title = title
        self.__description = description
        self.__position = position

    @staticmethod
    def get_book(title: str) -> 'Book':
        """
        Retrieves a shared Book instance. If a book with the given title does not exist,
        calls the ChatBot to generate a creative description and creates a new Book instance.

        Args:
            title (str): The title of the book to retrieve.

        Returns:
            Book: The Book instance corresponding to the given title.
        """
        for book in Book.flyweightStore:
            if book.__title == title:
                return book

        description = ChatBot.get_instance().get_description(title)
        new_book = Book(title, description, random.choice([Coord(3, 5), Coord(3, 7), Coord(3, 6), Coord(3, 8), Coord(3, 9)]))
        Book.flyweightStore.append(new_book)
        return new_book

    def get_name(self) -> str:
        """
        Returns the name of the book in uppercase.

        Returns:
            str: The uppercase title of the book.
        """
        return self.__title.upper()

    def get_position(self) -> Coord:
        """
        Returns the position of the book.

        Returns:
            Coord: The grid coordinate of the book.
        """
        return self.__position

    def get_image_name(self) -> str:
        """
        Returns the image name of the book (for testing purposes).

        Returns:
            str: The image name assigned to the book.
        """
        return self.__image_name

    def get_description(self) -> str:
        """
        Returns the description of the book.

        Returns:
            str: The description of the book.
        """
        return self.__description

    def player_entered(self, player: "HumanPlayer") -> list[Message]:
        """
        Called when a player enters the tile(s) occupied by the book.
        Removes the book from the grid and sends a chat message with its description.

        Args:
            player (HumanPlayer): The player who entered the book's area.

        Returns:
            list[Message]: A list of messages generated as a result of the interaction.
        """
        messages = []
        DumbledoresOffice.get_instance().remove_from_grid(self, self.__position)
        messages.append(ChatMessage(self, player, self.__description))
        messages.extend(DumbledoresOffice.get_instance().send_grid_to_players())
        return messages

class Candle(MapObject):
    """
    Represents a decorative candle in the game.

    This candle cycles through images to simulate flickering. It updates its image every tick and
    sends updated grid messages through DumbledoresOffice.
    """
    def __init__(self, image_name: str = "candelabrum_small_1", passable: bool = False, z_index: int = 1) -> None:
        """
        Initializes a new Candle object.

        Args:
            image_name (str): The default image name for the candle.
            passable (bool, optional): Whether the player is able to move on top of the candle. Defaults to False.
            z_index (int, optional): The z-index at which to place the candle. Defaults to 1.
        """
        super().__init__(f"tile/decor/candle/{image_name}", passable, z_index)
        self.__image_name_index = 1
    
    def update(self) -> list[Message]:
        """
        Called every second.
        Updates the candle's image by cycling through a set of images and returns updated grid messages.

        Returns:
            list[Message]: A list of messages sent from DumbledoresOffice to update the grid.
        """
        self.__image_name_index = (self.__image_name_index + 1) % 6
        self.set_image_name(f"tile/decor/candle/candelabrum_small_{self.__image_name_index}")
        return DumbledoresOffice.get_instance().send_grid_to_players()

class InteriorDoor(Door):
    def player_entered(self, player: HumanPlayer) -> list[Message]:
        """
        Handles the event when a player enters through the interior door.

        This method checks if a SortingHat is present (retrieved using its identifier "sorting_hat").
        If a SortingHat instance is found, it calls its player_left method to handle any necessary exit actions
        before delegating the standard door entry behavior to the superclass.

        Args:
            player (HumanPlayer): The player entering the door.

        Returns:
            list[Message]: A list of messages generated from processing the door entry.
        """
        sorting_hat = MapObject.get_obj("sorting_hat")
        if isinstance(sorting_hat, SortingHat):
            sorting_hat.player_left(player)
        return super().player_entered(player)

class Decor(MapObject):
    def __init__(self, image_name: str, passable: bool = False, z_index: int = 0) -> None:
        """
        Initializes a new piece of decor.

        Args:
            image_name (str): The image name for the decor.
            passable (bool, optional): Indicates if the decor is passable. Defaults to False.
            z_index (int, optional): The z-index at which to place the decor. Defaults to 0.
        """
        self.__image_name = image_name
        super().__init__(f"tile/decor/{self.__image_name}", passable, z_index)

class SortingHat(MapObject, PositionObserver, SelectionInterface):
    """
    Represents the Sorting Hat that assigns players to Hogwarts houses.
    Implements MapObject for basic functionality, PositionObserver to update visibility based on player position,
    and HouseObserver to track house changes.
    """
    def __init__(self, active_positions: list[Coord], image_name: str = "sorting_hat", text_bubble: TextBubble = TextBubble(TextBubbleImage.BLANK)) -> None:
        """
        Initializes a new SortingHat.

        Args:
            active_positions (list[Coord]): A list of coordinates that, when the player is in one of them, will cause the TextBubble to appear.
            image_name (str, optional): The image name for the sorting hat. Defaults to "sorting_hat".
            text_bubble (TextBubble, optional): The text bubble for the sorting hat. Defaults to a TextBubble with the BLANK image.
        """
        print(f"SORTING HAT GIVEN {active_positions}")
        super().__init__(f"tile/object/{image_name}", passable=False)
        self._active_positions = active_positions
        self._text_bubble = text_bubble
        # Indicates when to pop up the dialogue message telling the player how to interact with the sorting quiz.
        self._message_displayed = False
        self._message = ""
        
        # Define the questions and options
        self.__questions = [
            "Which trait do you value most?",
            "What sounds most appealing?",
            "How do you face challenges?",
            "What would be your favourite Hogwarts class?",
            "Your preferred pet?"
        ]
        
        # Options are limited to 16 characters to fit in the menu pop up.
        # Answers are aligned with houses: [Gryffindor, Hufflepuff, Ravenclaw, Slytherin]
        self.__options = [
            ["Bravery", "Loyalty", "Intelligence", "Ambition"],
            ["Forest adventure", "Helping friends", "Solving puzzles", "Leading others"],
            ["Head-on attack", "Team approach", "Analyze first", "Strategic plan"],
            ["Defense Arts", "Herbology", "Charms", "Potions"],
            ["Noble owl", "Friendly cat", "Wise raven", "Sleek snake"]
        ]

    def is_player_sorted(self, player: Player) -> bool:
        """
        Checks if a player has completed their sorting.

        Args:
            player (Player): The player to check for sorting completion.

        Returns:
            bool: True if the player's "House" state is not empty (indicating the player has been sorted); otherwise, False.
        """
        return player.get_state("House", "") != ""

    def is_sorting_in_progress(self, player: Player) -> bool:
        """
        Checks if a player is currently in the middle of being sorted.

        Args:
            player (Player): The player whose sorting process is to be verified.

        Returns:
            bool: True if the player's "sorting_in_progress" state is True; otherwise, False.
        """
        return player.get_state("sorting_in_progress", False)

    def player_left(self, player: Player) -> list[Message]:
        """
        Called when a player leaves the room while sorting is in progress.

        Args:
            player (Player): The player who is leaving the room.

        Returns:
            list[Message]: An empty list of messages.
        """
        if isinstance(player, HumanPlayer):
            # If player leaves during quiz, cancel it
            player.set_state("sorting_in_progress", False)
            player.set_state("sorting_answers", [])
        return []

    def player_interacted(self, player: HumanPlayer) -> list[Message]:
        """
        Handles player interaction with the Sorting Hat.

        Args:
            player (HumanPlayer): The player object that interacted with the Sorting Hat.

        Returns:
            list[Message]: A list of messages resulting from the player's interaction with the Sorting Hat.
        """
        if player.get_current_position() not in self._active_positions:
            return []
        if self.is_sorting_in_progress(player):
            return [ServerMessage(player, "You are already being sorted. Please answer the questions in the menu.")]
        
        messages = []
        if not self.is_player_sorted(player):
            messages.append(get_custom_dialogue_message(self, player, "Welcome to Dumbledore's Office! You must complete the Sorting Ceremony before exploring further. Press enter to begin."))
        else:
            messages.append(get_custom_dialogue_message(self, player, "The Sorting Hat welcomes you back! Press enter if you wish to be sorted again."))
        
        # Start the sorting quiz
        answers: list[int] = []
        player.set_state("sorting_answers", answers)
        player.set_state("sorting_in_progress", True)
        player.set_state("on_last_question", False)

        # Show the first question
        return messages + self._show_question(player, 0)
    
    # PositionObserver interface implementation
    def update_position(self, position: Coord) -> list[Message]:
        """
        Updates the sorting hat's text bubble visibility based on the player's new position.
        Implements the PositionObserver update method.

        Args:
            position (Coord): The player's updated position.

        Returns:
            list[Message]: A list of messages generated by the update, excluding DialogueMessage instances,
                           combined with grid update messages from DumbledoresOffice.
        """
        messages = super().update_position(position)
        for message in messages:
            # SortingHat shouldn't display DialogueMessage
            if isinstance(message, DialogueMessage):
                messages.remove(message)
        DumbledoresOffice.get_instance().set_player_state("in_sorting_range", self._text_bubble.is_visible())
        return messages

    def _show_question(self, player: "HumanPlayer", question_index: int) -> list["Message"]:
        """
        Shows a sorting quiz question to the player.

        Args:
            player (HumanPlayer): The player taking the sorting hat quiz.
            question_index (int): The index of the question to be presented.

        Returns:
            list[Message]: A list of messages that include the sorting quiz question and the corresponding menu options.
        """
        if question_index >= len(self.__questions):
            # Breaks up the update cycle to simulate the sorting hat "thinking" before deciding the house.
            player.set_state("on_last_question", True)
            player.set_state("sorting_delay_timer", 2)
            return [get_custom_dialogue_message(self, player, "Ah, yes! I know exactly where to put you...", press_enter=False)]
        
        # Create menu options for this question.
        menu_options = {
            f"{chr(97 + i)}) {option}": SortingOptionCommand(self, player, question_index, i)
            for i, option in enumerate(self.__options[question_index])
        }
        
        # Get the question text.
        question = self.__questions[question_index]
        
        # Format dialogue messages.
        messages = []
        
        # First question gets an introduction.
        if question_index == 0:
            messages.append(get_custom_dialogue_message(self, player, "Hmm, interesting... Let's see which house suits you best."))
        
        # Always add the actual question as a dialogue message.
        messages.append(get_custom_dialogue_message(self, player, question))
        
        # And include the menu for options.
        messages.append(MenuMessage(self, player, question, list(menu_options.keys())))
        
        # Set the current menu for the player.
        player.set_current_menu(self)
        
        return messages

    def _answer_question(self, player: "HumanPlayer", question_index: int, answer_index: int) -> list["Message"]:
        """
        Records the player's answer to the current sorting quiz question and presents the next question.

        Args:
            player (HumanPlayer): The player providing the answer.
            question_index (int): The index of the current question.
            answer_index (int): The index of the chosen answer.

        Returns:
            list[Message]: A list of messages representing the next question or subsequent quiz content.
        """
        player_answers = player.get_state("sorting_answers", [])
        player_answers.append(answer_index)
        player.set_state("sorting_answers", player_answers)
        return self._show_question(player, question_index + 1)

    def _calculate_result(self, player: HumanPlayer) -> list[Message]:
        """
        Calculates the result of the sorting quiz based on the player's answers and assigns the player to a house.

        Args:
            player (HumanPlayer): The player whose quiz answers are to be evaluated.

        Returns:
            list[Message]: A list of messages announcing the assigned house and updating the room theme.
        """
        # Count votes for each house.
        house_counts = [0, 0, 0, 0]  # [Gryffindor, Hufflepuff, Ravenclaw, Slytherin]
        for answer in player.get_state("sorting_answers", []):
            house_counts[answer] += 1
        
        # Find the house with the most votes.
        max_count = max(house_counts)
        # Map indices directly to House enum values.
        house_mapping = {
            0: House.GRYFFINDOR,
            1: House.HUFFLEPUFF,
            2: House.RAVENCLAW,
            3: House.SLYTHERIN
        }

        # Determine the winning house(s) using the mapping.
        winning_houses = [house_mapping[i] for i, count in enumerate(house_counts) if count == max_count]
        
        # If there's a tie, select the first one.
        assigned_house = winning_houses[0]
        
        # Clean up the quiz state.
        player.set_state("sorting_in_progress", False)
        player.set_state("on_last_question", False)
        player.set_state("House", assigned_house.name)
        messages = []
        # Create a descriptive message for the assigned house.
        house_messages = {
            House.GRYFFINDOR: "GRYFFINDOR! Where dwell the brave at heart. Their daring, nerve, and chivalry set Gryffindors apart.",
            House.HUFFLEPUFF: "HUFFLEPUFF! Where they are just and loyal. Those patient Hufflepuffs are true and unafraid of toil.",
            House.RAVENCLAW: "RAVENCLAW! Where those of wit and learning will always find their kind.",
            House.SLYTHERIN: "SLYTHERIN! Those cunning folk use any means to achieve their ends."
        }
        messages.append(get_custom_dialogue_message(self, player, text=house_messages[assigned_house]))
        # Return the announcement combined with theme update messages.
        return messages + DumbledoresOffice.get_instance().update_theme()

    def select_option(self, player: HumanPlayer, option: str) -> list[Message]:
        """
        Handles the player's selection from the sorting hat quiz menu.

        Args:
            player (HumanPlayer): The player who selected an option.
            option (str): The selected option string (e.g., "a) Courage").

        Returns:
            list[Message]: A list of messages generated as a result of processing the player's selection.
        """
        # If player is not in a quiz, return an empty list.
        if not self.is_sorting_in_progress(player):
            return []
        
        # Parse the option (it comes in the format 'a) Option text'); extract the index by getting the letter prefix.
        option_index = ord(option[0]) - ord('a')
        
        # Determine the current question index based on how many answers have been recorded.
        question_index = len(player.get_state("sorting_answers", []))
        
        # Record the answer and present the next question.
        return self._answer_question(player, question_index, option_index)

    def get_name(self) -> str:
        """
        Retrieves the name of the Sorting Hat.

        Returns:
            str: The string "SORTING HAT".
        """
        return "SORTING HAT"

    def update(self) -> list[Message]:
        """
        Updates the Sorting Hat's state during the game cycle.
        If sorting is in progress for the current player, it processes the delay timer and calculates the result
        when ready.

        Returns:
            list[Message]: A list of messages generated as a result of updating the sorting quiz.
        """
        messages = []
        if self.is_sorting_in_progress(DumbledoresOffice.get_instance().get_player()):
            if DumbledoresOffice.get_instance().get_player_state("on_last_question", False):
                if DumbledoresOffice.get_instance().get_player_state("sorting_delay_timer") > 0:
                    DumbledoresOffice.get_instance().set_player_state(
                        "sorting_delay_timer",
                        DumbledoresOffice.get_instance().get_player_state("sorting_delay_timer") - 1
                    )
                else:
                    messages.extend(self._calculate_result(DumbledoresOffice.get_instance().get_player()))
        return messages

class SortingOptionCommand(MenuCommand):
    """
    Command for handling sorting hat quiz option selections.
    """
    def __init__(self, sorting_hat: SortingHat, player: "HumanPlayer", question_index: int, answer_index: int) -> None:
        """
        Initializes a new SortingOptionCommand.

        Args:
            sorting_hat (SortingHat): The sorting hat instance associated with the quiz.
            player (HumanPlayer): The player who selected the option.
            question_index (int): The current question index.
            answer_index (int): The index of the answer selected by the player.
        """
        self.__sorting_hat = sorting_hat
        self.__player = player
        self.__question_index = question_index
        self.__answer_index = answer_index
    
    def execute(self, context: "Map", player: "HumanPlayer") -> list["Message"]:
        """
        Executes the sorting option command by recording the player's answer and proceeding to the next question.

        Args:
            context (Map): The map context in which the command is executed.
            player (HumanPlayer): The player executing the command.

        Returns:
            list[Message]: A list of messages generated as a result of processing the player's answer.
        """
        return self.__sorting_hat._answer_question(self.__player, self.__question_index, self.__answer_index)
