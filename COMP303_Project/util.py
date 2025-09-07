from typing import Type, Optional, Set, TYPE_CHECKING, Dict
from .imports import *
from .position_observer import PositionObserver
from .house_observer import HouseObserver
from .user_commands import *
from .house import House
from .null_player import NullPlayer
from .chatbot import *

if TYPE_CHECKING:
    from coord import Coord
    from maps.base import Message
    from Player import Player, HumanPlayer
    from tiles.map_objects import *

def get_custom_dialogue_message(
    sender: SenderInterface,
    recipient: RecipientInterface,
    text: str,
    image: str = "",
    font: str = 'harryp',
    bg_color: tuple = (0, 0, 0),
    text_color: tuple = (255, 255, 255),
    press_enter: bool = True,
    auto_delay: int = 500
) -> Message:
    """
    Creates a custom DialogueMessage to be sent between sender and recipient.

    Args:
        sender (SenderInterface): The source of the message.
        recipient (RecipientInterface): The target of the message.
        text (str): The content of the dialogue message.
        image (str, optional): Optional image to display with the message. Defaults to "".
        font (str, optional): Font to be used in the dialogue. Defaults to 'harryp'.
        bg_color (tuple, optional): Background color as an RGB tuple. Defaults to (0, 0, 0).
        text_color (tuple, optional): Text color as an RGB tuple. Defaults to (255, 255, 255).
        press_enter (bool, optional): Whether the message requires the player to press enter. Defaults to True.
        auto_delay (int, optional): Delay before the message disappears automatically (ms). Defaults to 500.

    Returns:
        Message: A fully constructed DialogueMessage object with the specified parameters.
    """
    return DialogueMessage(sender, recipient, text, image, font, bg_color, text_color, press_enter, auto_delay)
