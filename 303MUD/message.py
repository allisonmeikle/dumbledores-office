import os
import time
import json
from abc import ABC, abstractmethod
from typing import Literal, TYPE_CHECKING

from .coord import Coord
from .resources import get_resource_path
if TYPE_CHECKING:
    from Player import HumanPlayer

class SenderInterface(ABC):
    @abstractmethod
    def get_name(self) -> str:
        """ Returns the name of the sender. """
        pass

class RecipientInterface:
    def __init__(self) -> None:
        self._message_sequence_number: int = 0
    
    def get_and_increment_seq_num(self) -> int:
        """ Returns the sequence number of the recipient and increments it. """
        self._message_sequence_number += 1
        return self._message_sequence_number

class Message(ABC):
    """ A message to be sent between a sender and a recipient. The recipient can be
    a Map (i.e., a collection of HumanPlayers) or a HumanPlayer.
    """
    
    def __init__(self, sender: SenderInterface, recipient: RecipientInterface) -> None:
        """ Initializes the message with the sender and recipient. """
        if type(self) == Message:
            raise Exception("Message must be subclassed.")

        self.__sender: SenderInterface = sender
        self.__recipient: RecipientInterface = recipient
    
    def get_sender(self) -> SenderInterface:
        """ Returns the sender of the message. """
        return self.__sender

    def get_recipient(self) -> RecipientInterface:
        """ Returns the recipient of the message. """
        return self.__recipient

    def prepare(self) -> str:
        """ Returns a JSON string representation of the message. """
        return json.dumps({
            'classname': self.__class__.__name__,
            'handle': self.__sender.get_name(),
            'time': time.time(),
            'seq_num': self.__recipient.get_and_increment_seq_num() if hasattr(self.__recipient, 'get_and_increment_seq_num') else 0,
            **self._get_data(),
        })

    @abstractmethod
    def _get_data(self) -> dict:
        """ Returns the data to be sent in the message. """
        return {}

class ChatMessage(Message):
    """ A message to be displayed in the user's chat window. """

    def __init__(self, sender: SenderInterface, recipient: RecipientInterface, text: str) -> None:
        """ Initializes the chat message with the sender, recipient, and text. """
        self.__text: str = text
        super().__init__(sender, recipient)

    def _get_data(self) -> dict:
        return {
            'text': self.__text,
        }

class DialogueMessage(Message):
    """ A message to be displayed in the user's dialogue window. """
    def __init__(self, sender: SenderInterface, recipient: RecipientInterface, text: str, image: str, font: str = 'pkmn', bg_color: tuple = (255, 255, 255), text_color: tuple = (0, 0, 0), press_enter: bool = True, auto_delay: int = 500) -> None:
        """ Initializes the dialogue message with the sender, recipient, text, image, and display options.
        
        The pressEnter field determines if the dialogue box should wait for the user to press enter
        before proceeding. By default, it is set to True.
        """
        self.__text: str = text
        self.__image: str = image
        self.__font: str = font
        self.__bg_color: tuple = bg_color
        self.__text_color: tuple = text_color
        self.__press_enter: bool = press_enter
        self.__auto_delay: int = auto_delay
        super().__init__(sender, recipient)

    def _get_data(self) -> dict:
        return {
            'dialogue_text': self.__text,
            'dialogue_image': self.__image,
            'dialogue_font': self.__font,
            'dialogue_bg_color': self.__bg_color,
            'dialogue_text_color': self.__text_color,
            'dialogue_press_enter': self.__press_enter,
            'dialogue_auto_delay': self.__auto_delay,
        }

class NPCMessage(DialogueMessage):
    """ A message to be displayed in the user's dialogue window from an NPC. """
    def __init__(self, sender: SenderInterface, recipient: RecipientInterface, text: str, image: str) -> None:
        """ Initializes the NPC message with the sender, recipient, text, and image. """
        self.__npc_name: str = sender.get_name()
        super().__init__(sender, recipient, text, image)
    
    def _get_data(self) -> dict:
        data: dict = super()._get_data()
        data['npc_name'] = self.__npc_name
        return data

class EmoteMessage(Message):
    """ A message to display an emote at a specific position. """
    def __init__(self, sender: SenderInterface, recipient: RecipientInterface, emote: str, emote_pos: Coord) -> None:
        """ Initializes the emote message with the sender, recipient, emote, and position. """
        self.__emote: str = emote
        self.__emote_pos: tuple[int, int] = emote_pos.to_tuple()
        super().__init__(sender, recipient)
    
    def _get_data(self) -> dict:
        return {
            'emote': self.__emote,
            'emote_pos': self.__emote_pos
        }

class ServerMessage(Message, SenderInterface):
    """ A message from the server to a recipient. """
    def __init__(self, recipient: RecipientInterface, text: str) -> None:
        """ Initializes the server message with the recipient and text. """
        self.__text: str = text
        Message.__init__(self, self, recipient)

    def get_name(self) -> Literal['***SERVER***']:
        return "***SERVER***"

    def _get_data(self) -> dict[str, str]:
        return {
            'text': self.__text,
        }
    
class GridMessage(Message, SenderInterface):
    """ A message to update the grid of a recipient. """
    def __init__(self, recipient: "HumanPlayer", send_desc : bool = True) -> None:
        """ Initializes the grid message with the recipient. """
        self.__send_desc: bool = send_desc
        self.__position: tuple[int, int] = recipient.get_current_position().to_tuple()
        self.__room_info: dict = recipient.get_current_room().get_info(recipient)
        Message.__init__(self, self, recipient)

    def get_name(self) -> Literal['***SERVER***']:
        return "***SERVER***"
    
    def _get_data(self) -> dict:
         data = dict(self.__room_info)
         data['position'] = self.__position
         if not self.__send_desc:
             del data['description']
         return data

class SoundMessage(Message, SenderInterface):
    """ A message to play a sound for a recipient. """
    def __init__(self, recipient, sound_path: str, volume: float = 0.5, repeat: bool = True) -> None:
        """ Initializes the sound message with the recipient and sound path. """
        self.__sound_path: str = sound_path
        self.__volume: float = volume
        self.__repeat: bool = repeat
        Message.__init__(self, self, recipient)

    def get_name(self) -> Literal['***SERVER***']:
        return "***SERVER***"
    
    def _get_data(self) -> dict:
        return {
            'sound_path': self.__sound_path,
            'volume': self.__volume,
            'repeat': self.__repeat,
        }

class MenuMessage(Message):
    """ A message to display a menu for a recipient. """
    def __init__(self, sender, recipient, menu_name: str, menu_options: list[str]) -> None:
        """ Initializes the menu message with the recipient, menu name, and options. """
        self.__menu_name: str = menu_name
        self.__menu_options: list[str] = menu_options
        Message.__init__(self, sender, recipient)

    def get_name(self) -> Literal['***SERVER***']:
        return "***SERVER***"
    
    def _get_data(self) -> dict:
        return {
            'menu_name': self.__menu_name,
            'menu_options': self.__menu_options,
        }

'''
class FileMessage(Message):
    """ A message to download a file for a recipient. """
    def __init__(self, sender, recipient, file_path: str) -> None:
        """ Initializes the file message with the recipient and file path. """

        self.__file_path: str = file_path
        if not os.path.exists(get_resource_path(file_path)):
            print(f"File {file_path} does not exist.")
        Message.__init__(self, sender, recipient)

    def get_name(self) -> Literal['***SERVER***']:
        return "***SERVER***"
    
    def _get_data(self) -> dict:
        return {
            'file_path': self.__file_path,
        }
'''

# Group 29 additions
# --------------------------------
class PokemonBattleMessage(Message):
    def __init__(self, sender, recipient, player_data: dict, enemy_data: dict, destroy: bool = False) -> None:
        """
        Initializes the pokemon battle message with both player and enemy Pokemon data dictionaries.
        
        Parameters:
        - player_data: dictionary of the player's Pokemon data.
        - enemy_data: dictionary of the enemy's Pokemon data.
        - destroy: flag to destroy the battle window.
        
        Example structure for player and enemy datadata:
        {
            "name": "Pikachu",
            "level": 2,
            "hp": 50,
            "max_hp": 100
        }
        """
        super().__init__(sender, recipient)
        self.__player_data = player_data
        self.__enemy_data = enemy_data
        self.__destroy = destroy

    def get_name(self) -> Literal['***SERVER***']:
        return "***SERVER***"

    def _get_data(self) -> dict:
        return {
            "player_data": self.__player_data,
            "enemy_data": self.__enemy_data,
            "destroy": self.__destroy
        }
        

class OptionsMessage(Message):
    def __init__(self, sender, recipient, options: list[str], destroy: bool = False) -> None:
        """ Initializes the options message with the options. 
        
        Parameters:
        - options: list of strings representing the options available to the user.
        - destroy: flag to destroy the options window.
        """
        super().__init__(sender, recipient)
        self.__options = options
        self.__destroy = destroy

    def get_name(self) -> Literal['***SERVER***']:
        return "***SERVER***"

    def _get_data(self) -> dict:
        return {
            "options": self.__options, 
            "destroy": self.__destroy
        }
        

class ChooseObjectMessage(Message):
    def __init__(self, sender, recipient, options: list[dict], window_title: str = "Choose Object", sprite_size: int = 160, orientation: Literal["landscape", "portrait"] = "landscape", width: int = 540, height: int = 230, gap: int = 170, label_height: int = 150, offset_x: int = 30, offset_y: int = 150) -> None:
        """
        A message used to open a selection window with options, each having a label and associated image above.

        Parameters:
        - options: list of dicts containing the label and image path for each option.
                   Example: [{"Charmander": "image/Pokemon/Charmander_front.png"}, ..., ...]
        - window_title: the title.
        - sprite_size: the sprite size (does not necessarily need to match the pixel size)
        - orientation: "landscape" for 1 row and multiple cols or "portrait" for 1 col and multiple rows
        - width: width of window
        - height: height of window
        - gap: gap between options
        - label_height: y positioning of label only for portrait
        - offset_x: x positioning of window
        - offset_y: y positioning of window
        """
        
        super().__init__(sender, recipient)
        self.__options = options
        self.__window_title = window_title
        self.__sprite_size = sprite_size
        self.__orientation = orientation
        self.__width = width
        self.__height = height
        self.__gap = gap
        self.__label_height = label_height
        self.__offset_x = offset_x
        self.__offset_y = offset_y

    def get_name(self):
        return "***SERVER***"

    def _get_data(self):
        return {
            'options': self.__options,
            'window_title': self.__window_title,
            'sprite_size': self.__sprite_size,
            'orientation': self.__orientation,
            'height': self.__height,
            'width': self.__width,
            'gap': self.__gap,
            'label_height': self.__label_height,
            'offset_x': self.__offset_x,
            'offset_y': self.__offset_y
        }
    

class DisplayStatsMessage(Message):
    def __init__(self, sender, recipient, stats: list[str], 
                 top_image_path: str = "", bottom_image_path: str = "", 
                 scale: float = 1.5, window_title: str = "Stats") -> None:
        super().__init__(sender, recipient)
        self.__stats = stats  # Any list of strings you want to display (doesn't have to be stats)

        """
        IMPORTANT: top_image_path and bottom_image_path should be the path of the image under resources, not the full path
        
        Example 1: if you have an image called "pikachu.png" under resources directory, you should pass "pikachu.png" as the path  
        Example 2: if you have an image called "pikachu.png" under resources/image/Pokemon directory, you should pass "image/Pokemon/pikachu.png" as the path
        """
        self.__top_image_path = top_image_path
        self.__bottom_image_path = bottom_image_path
        self.__scale = scale  # Image scaling factor
        self.__window_title = window_title  # Title of the display window

    def get_name(self):
        return "***SERVER***"

    def _get_data(self):
        return {
            'stats': self.__stats,
            'top_image_path': self.__top_image_path,
            'bottom_image_path': self.__bottom_image_path,
            'scale': self.__scale,
            'window_title': self.__window_title
        }

class MagicalKeyMessage(Message):
    def __init__(self, sender: SenderInterface, recipient: RecipientInterface) -> None:
        super().__init__(sender, recipient)
        
    def get_classname(self) -> str:
        return "***SERVER***"
        
    def _get_data(self) -> dict:
        return {}

# --------------------------------
# Group 69 additions
# --------------------------------

# Combat UI and Winner related messages
class CombatUIMessage(Message):
    def __init__(self, sender, recipient, 
                 left_character: dict = None, 
                 right_character: dict = None, 
                 destroy: bool = False) -> None:
        """
        Message to create and update a combat UI display.
        
        Parameters:
        - left_character: Dictionary containing stats for the left character (player)
          Example: {"name": "Player", "hp": 100, "max_hp": 100, "attack": 20, "special_cooldown": 0}
        - right_character: Dictionary containing stats for the right character (opponent)
          Example: {"name": "Opponent", "hp": 100, "max_hp": 100, "attack": 20, "special_cooldown": 0}
        - destroy: Flag to destroy the combat UI
        """
        super().__init__(sender, recipient)
        self.__left_character = left_character
        self.__right_character = right_character
        self.__destroy = destroy

    def get_name(self) -> Literal['***SERVER***']:
        return "***SERVER***"

    def _get_data(self) -> dict:
        return {
            "left_character": self.__left_character,
            "right_character": self.__right_character,
            "destroy": self.__destroy
        }

class TimerMessage(Message):
    def __init__(self, sender, recipient, time_str: str = "03:00", is_match_over: bool = False, destroy: bool = False) -> None:
        """
        Message to create and update a match timer.
        
        Parameters:
        - time_str: String representation of the remaining time (e.g., "03:00")
        - is_match_over: Flag indicating if the match is over
        - destroy: Flag to destroy the timer UI
        """
        super().__init__(sender, recipient)
        self.__time_str = time_str
        self.__is_match_over = is_match_over
        self.__destroy = destroy

    def get_name(self) -> Literal['***SERVER***']:
        return "***SERVER***"

    def _get_data(self) -> dict:
        return {
            "time_str": self.__time_str,
            "is_match_over": self.__is_match_over,
            "destroy": self.__destroy
        }

class CombatResultMessage(Message):
    def __init__(self, sender, recipient, fighter_data: dict, result_type: str = "win", destroy: bool = False) -> None:
        """
        Message to display the result of a combat.
        
        Parameters:
        - fighter_data: Dictionary containing information about the fighter
          Example: {"name": "Player", "hp": 75, "max_hp": 100}
        - result_type: String indicating the result type ("win" or "lose")
        - destroy: Flag to destroy the result screen
        """
        super().__init__(sender, recipient)
        self.__fighter_data = fighter_data
        self.__result_type = result_type
        self.__destroy = destroy

    def get_name(self) -> Literal['***SERVER***']:
        return "***SERVER***"

    def _get_data(self) -> dict:
        return {
            "fighter_name": self.__fighter_data.get("name", "Unknown Fighter"),
            "fighter_stats": {
                "hp": self.__fighter_data.get("hp", 0),
                "max_hp": self.__fighter_data.get("max_hp", 100)
            },
            "result_type": self.__result_type,
            "destroy": self.__destroy
        } 
    
# group 7 additions -----------------------------------------------------------------
# -----------------------------------------------------------------------------------

class BoxingMatchMessage(Message):
    def __init__(self, sender, recipient,
                 player_name: str,
                 npc_name: str,
                 player_initial_hp: int,
                 npc_initial_hp: int,
                 turn: int        # ← new
                ) -> None:
        super().__init__(sender, recipient)
        self.__player_name  = player_name
        self.__npc_name = npc_name
        self.__player_initial_hp = player_initial_hp
        self.__npc_initial_hp  = npc_initial_hp
        self.__turn = turn               

    def _get_data(self) -> dict:
        return {
            "classname": "BoxingMatchMessage",
            "player_name": self.__player_name,
            "npc_name":self.__npc_name,
            "player_initial_hp":self.__player_initial_hp,
            "npc_initial_hp":self.__npc_initial_hp,
            "turn":self.__turn,         
        }
        
    def get_name(self) -> str:
        return "***SERVER***"

class BattleResultMessage(Message):
    """
    Tells the client to open the battle result window.
    Contains result (e.g. "WIN" or "LOSE") and a fighter_data dict with details.
    """
    def __init__(self, sender, recipient, result: str) -> None:
        super().__init__(sender, recipient)
        self.__result = result
       

    def get_name(self) -> str:
        return "***SERVER***"

    def _get_data(self) -> dict:
        return {
            "window_type": "battle_result",
            "result": self.__result,
           
        }

class EnduranceGameMessage(Message):
    """
    Instructs the client to start the endurance minigame.
    You can include additional configuration (such as starting time) if needed.
    """
    def __init__(self, sender, recipient, time_left: int = 10) -> None:
        super().__init__(sender, recipient)
        self.__time_left = time_left

    def get_name(self) -> str:
        return "***SERVER***"

    def _get_data(self) -> dict:
        return {
            "window_type": "endurance_game",
            "time_left": self.__time_left
        }

class WeightliftingMinigameMessage(Message):
    def __init__(self, sender, recipient, difficulty: float = 1.0, player_email: str = "", player_strength: int = 1):
        super().__init__(sender, recipient)
        self.__difficulty = difficulty
        self.__player_email = player_email
        self.__player_strength = player_strength

    def get_name(self) -> Literal['***SERVER***']:
        return "***SERVER***"

    def _get_data(self) -> dict:
        return {
            'difficulty': self.__difficulty,
            'player_email': self.__player_email,
            'player_strength': self.__player_strength,
            'classname': 'WeightliftingMinigameMessage'
        }
# ----- end of GROUP 7 additions ------------------------------------
#--------------------------------------------------------------------
