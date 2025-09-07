from .imports import *
from typing import TYPE_CHECKING, Optional
from abc import ABC
from .chatbot import *
from .text_bubble import *

if TYPE_CHECKING:
    from command import *
    from .dumbledores_office import ChatBotObject, TextBubbleImage
    from .util import *
    from message import *

class UserCommand(ChatCommand, ABC):
    _player_input: str = ""
    _chatbot_response: str = ""
    _waiting_for_response: bool = False
    _active_object: Optional["ChatBotObject"] = None

    @staticmethod
    def is_active() -> bool:
        """
        Returns whether the UserCommand is currently active (i.e. waiting for a chatbot response).

        Returns:
            bool: True if a chatbot response is currently awaited; otherwise, False.
        """
        return UserCommand._waiting_for_response

    @staticmethod
    def get_player_message(context: Map) -> list[Message]:
        """
        Gets a list of the ChatMessage to send to the player with their input to the ChatBot.

        Pre:
            UserCommand._active_object must not be None as it needs to be sending the message.

        Returns:
            list[Message]: A list of ChatMessage objects based on the player's input.
        """
        assert UserCommand._active_object is not None, (
            "Cannot create the message as there is no active object to send it from"
        )
        assert hasattr(context, "get_player"), "Must be able to retrieve the current player from the Map"

        messages = []
        if (UserCommand._player_message_sent):
            return messages
        UserCommand._player_message_sent = True
        messages.append(ChatMessage(context.get_player(), context, UserCommand._player_input))
        return messages

    @staticmethod
    def get_active_bubble_image() -> "TextBubbleImage":
        """
        Gets the UserCommand._active_object's TextBubbleImage.

        Pre:
            UserCommand._active_object must not be None.

        Returns:
            TextBubbleImage: The text bubble image of the active object.
        """
        assert UserCommand._active_object is not None, (
            "Cannot get the active text bubble image as there is no active object"
        )
        return UserCommand._active_object.get_text_bubble_image()

    @staticmethod
    def set_active_bubble_image(image: TextBubbleImage) -> None:
        """
        Sets the UserCommand._active_object's TextBubbleImage to the given one.

        Pre:
            UserCommand._active_object must not be None.

        Args:
            image (TextBubbleImage): The image to set for the active object's text bubble.
        """
        assert UserCommand._active_object is not None, (
            "Cannot set the active text bubble image as there is no active object"
        )
        UserCommand._active_object.set_text_bubble_image(image)

    @staticmethod
    def set_active_bubble_default() -> None:
        """
        Sets the UserCommand._active_object's TextBubbleImage to its default.

        Pre:
            UserCommand._active_object must not be None.
        """
        assert UserCommand._active_object is not None, (
            "Cannot set the text bubble image as there is no active object"
        )
        UserCommand._active_object.set_text_bubble_to_default()

    @staticmethod
    def get_active_object() -> Optional["ChatBotObject"]:
        """
        Gets the UserCommand._active_object attribute.

        Returns:
            Optional[ChatBotObject]: The currently active object, or None if there is none.
        """
        return UserCommand._active_object

    @staticmethod
    def set_active_object(object: Optional["ChatBotObject"]) -> None:
        """
        Sets the UserCommand._active_object attribute.
        If the ChatBot is still generating a response, doesn't update the attribute.

        Args:
            object (Optional[ChatBotObject]): The object that interfaces with the ChatBot which is now active. None if no object is active.
        """
        if not UserCommand._waiting_for_response:
            UserCommand._active_object = object

    @staticmethod
    def execute(command_text: str, context: 'Map', player: 'HumanPlayer') -> list[Message]:
        """
        Executes the command entered by the user.
        Sends the ChatBot the user input and returns its response in a ChatMessage.

        Args:
            command_text (str): Full text typed into the chat window by the user.
            context (Map): The map the user is currently in when sending the command.
            player (HumanPlayer): The player sending the command.

        Pre:
            UserCommand._active_object must not be None.

        Returns:
            list[Message]: A list of messages to send to the player, including the ChatBot's response.
        """
        assert UserCommand._active_object, "Cannot execute this command as there is no active object"

        messages = []
        UserCommand._player_message_sent = False
        UserCommand._player_input = command_text[4:].strip()
        UserCommand._chatbot_response = ""
        UserCommand._waiting_for_response = True
        UserCommand._chatbot_response = UserCommand._active_object.get_response(UserCommand._player_input)
        # Display response after third dot appears
        while (UserCommand.get_active_bubble_image() != TextBubbleImage.THINKING3):
            pass
        UserCommand._waiting_for_response = False
        UserCommand.set_active_bubble_default()
        messages.extend(context.send_grid_to_players())
        return messages

class BookCommand(UserCommand):
    name = 'book'
    desc = 'Select a book from the bookshelf.'

    @classmethod
    def matches(cls, command_text: str) -> bool:
        """
        Checks if the provided command text matches the expected '/book' command format.

        Args:
            command_text (str): The full command text entered by the user in the chat window.

        Returns:
            bool: True if command_text starts with "book", indicating that this command should handle the input; otherwise, False.
        """
        return command_text.startswith("book")

    def execute(self, command_text: str, context: "Map", player: "HumanPlayer") -> list[Message]:
        """
        Executes the user's command /book {title}.
        Returns a list of messages with the results.

        Args:
            command_text (str): Full text typed into the chat window by the user.
            context (Map): The map the user is currently in when sending the command.
            player (HumanPlayer): The player sending the command.

        Pre:
            The 'context' argument must be an instance of a class that implements 'SenderInterface'
            (i.e. has the get_name() method).

        Returns:
            list[Message]: A list of messages with the book retrieval result.
        """
        assert isinstance(context, SenderInterface), "The player's current map must implement SenderInterface"
        from .util import get_custom_dialogue_message
        from .dumbledores_office import DumbledoresOffice, Book

        # Check if there's an active bookshelf; if it has a conversation strategy, it's not a bookshelf.
        if UserCommand._active_object is None or hasattr(UserCommand._active_object, "get_conversation_strategy"):
            return [get_custom_dialogue_message(context, player, "You must be near the bookshelf to select a book.")]
        
        messages = super().execute(command_text, context, player)
        print(f"BOOK SUCCESFULLY ADDED TO GRID?")
        for obj in DumbledoresOffice.get_instance().get_map_objects_at(Book.get_book(UserCommand._player_input).get_position()):
            print(obj)
        messages.extend(context.send_grid_to_players())
        messages.append(get_custom_dialogue_message(context, player, "Walk overtop of the book to pick it up and read its description!"))
        return messages

class ChatBotChatCommand(UserCommand):
    name = 'chat'
    desc = 'Talk to any object that has a "/chat" bubble appear when you move close to it.'
    
    @classmethod
    def matches(cls, command_text: str) -> bool:
        """
        Returns True if the command_text matches the pattern for this command.

        Args:
            command_text (str): Player's input in the chat window.

        Returns:
            bool: True if command_text starts with "chat", indicating that this command should handle the input; otherwise, False.
        """
        return command_text.startswith("chat")

    def execute(self, command_text: str, context: Map, player: HumanPlayer) -> list[Message]:
        """
        Executes the chat command. Instead of printing to the terminal, it sends the chatbot response as a dialogue message to the game.

        Args:
            command_text (str): Player's input in the chat window.
            context (Map): The map in which to execute the command.
            player (HumanPlayer): The player sending the command.

        Pre:
            The 'context' argument must be an instance of a class that implements 'SenderInterface'.

        Returns:
            list[Message]: A list of messages, including the ChatBot's response, to send to the player.
        """
        assert isinstance(context, SenderInterface), "The player's current map must implement SenderInterface"
        from .util import get_custom_dialogue_message

        messages = []
        # Check if there's an active ChatObject; if it doesn't have a conversation strategy, it's not a ChatObject.
        if UserCommand._active_object is None or not hasattr(UserCommand._active_object, "_conversation_strategy"):
            return [get_custom_dialogue_message(context, player, "No object is active to chat with.")]
        
        messages.extend(super().execute(command_text, context, player))
        messages.append(ChatMessage(UserCommand._active_object, player, UserCommand._chatbot_response))
        return messages
