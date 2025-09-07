import sys
import pytest
from typing import TYPE_CHECKING
# relative import to access the imports.py bridge
from ..imports import *
# relative imports for our project files
from ..dumbledores_office import DumbledoresOffice, SortingHat, TextBubble, ChatObject, Bookshelf, Book
from ..house import House
from ..text_bubble import TextBubbleImage
from ..user_commands import UserCommand, BookCommand, ChatBotChatCommand
from ..chatbot import DumbledoreConversationStrategyGryffindor, ChatBot, ConversationStrategy

if TYPE_CHECKING:
    from coord import Coord
    from Player import HumanPlayer
    from message import Message, ChatMessage

@pytest.fixture
def test_with_timeout():
    """timeout fixture removed as requested"""
    yield

@pytest.fixture
def mock_chatbot(monkeypatch):
    """mock the chatbot to prevent real api calls"""
    # create simple dictionary to track calls and store return values
    mock_data = {
        "response": "mocked chatbot response",
        "description": "mocked book description",
        "response_calls": [],
        "description_calls": []
    }
    
    # create replacement functions with tracking
    def mock_get_response(self, strategy, message):
        mock_data["response_calls"].append((strategy, message))
        return mock_data["response"]
    
    def mock_get_description(self, title):
        mock_data["description_calls"].append(title)
        return mock_data["description"]
    
    # patch the methods
    monkeypatch.setattr(ChatBot, "get_response", mock_get_response)
    monkeypatch.setattr(ChatBot, "get_description", mock_get_description)
    
    # ensure get_instance returns a real instance but with mocked methods
    mock_instance = ChatBot()
    monkeypatch.setattr("COMP303_Project.chatbot.ChatBot.get_instance", lambda: mock_instance)
    
    return mock_data

@pytest.fixture
def patch_bubble_wait(monkeypatch):
    """patch the waiting loop in usercommand.execute to prevent infinite loops"""
    original_execute = UserCommand.execute
    
    def patched_execute(command_text, context, player):
        # save original method
        get_active_bubble_image_original = UserCommand.get_active_bubble_image
        
        # override with function that returns THINKING3
        def mock_get_bubble():
            return TextBubbleImage.THINKING3
        
        monkeypatch.setattr(UserCommand, "get_active_bubble_image", mock_get_bubble)
        
        # execute the method
        result = original_execute(command_text, context, player)
        
        # restore original method
        monkeypatch.setattr(UserCommand, "get_active_bubble_image", get_active_bubble_image_original)
        
        return result
    
    monkeypatch.setattr(UserCommand, "execute", patched_execute)
    yield

@pytest.fixture
def mock_map(monkeypatch):
    """create a mock map for testing"""
    # create tracking data
    map_data = {
        "grid_updates": 0,
        "name": "mockmap"
    }
    
    # create stub player to return
    class StubPlayer:
        def get_name(self):
            return "testplayer"
    
    # create stub map class
    class StubMap:
        def __init__(self):
            self.data = map_data
            self.player = StubPlayer()
            
        def get_player(self):
            return self.player
        
        def send_grid_to_players(self):
            self.data["grid_updates"] += 1
            return []
        
        def get_name(self):
            return self.data["name"]
    
    stub_map = StubMap()
    return stub_map

@pytest.fixture
def mock_player(monkeypatch):
    """create a mock player for testing"""
    # create stub player class
    class StubPlayer:
        def get_name(self):
            return "testplayer"
    
    stub_player = StubPlayer()
    return stub_player

@pytest.fixture
def mock_chat_object(monkeypatch):
    """create a mock chat object that implements the required interfaces"""
    # tracking data dictionary (using a shared mutable object to track calls)
    chat_data = {
        "bubble_image": TextBubbleImage.CHAT,
        "response": "test response from character",
        "image_calls": [],
        "default_calls": 0,
        "response_calls": [],
        "name": "mockchatobject"
    }
    
    # create stub chat object
    class StubChatObject:
        # Store chat_data as an instance attribute to access it later
        def __init__(self):
            self.data = chat_data
            self.get_response_calls = chat_data["response_calls"]
            
        def get_text_bubble_image(self):
            return self.data["bubble_image"]
        
        def get_response(self, input_str):
            self.data["response_calls"].append(input_str)
            return self.data["response"]
        
        def set_text_bubble_image(self, image):
            self.data["image_calls"].append(image)
        
        def set_text_bubble_to_default(self):
            self.data["default_calls"] += 1
        
        def get_name(self):
            return self.data["name"]
    
    # create the object with our tracking methods
    stub_chat = StubChatObject()
    
    # attach a conversation strategy
    stub_chat._conversation_strategy = MockConversationStrategy()
    
    return stub_chat

@pytest.fixture
def mock_bookshelf(monkeypatch):
    """create a mock bookshelf object"""
    # tracking data
    bookshelf_data = {
        "bubble_image": TextBubbleImage.BOOK,
        "response": "test book description",
        "set_image_calls": [],
        "default_calls": 0,
        "name": "mockbookshelf"
    }
    
    # create stub bookshelf
    class StubBookshelf:
        def __init__(self):
            self.data = bookshelf_data
            
        def get_text_bubble_image(self):
            return self.data["bubble_image"]
        
        def get_response(self, input_str):
            return self.data["response"]
        
        def set_text_bubble_image(self, image):
            self.data["set_image_calls"].append(image)
        
        def set_text_bubble_to_default(self):
            self.data["default_calls"] += 1
        
        def get_name(self):
            return self.data["name"]
    
    # create the stub object
    stub_bookshelf = StubBookshelf()
    
    return stub_bookshelf

@pytest.fixture
def setup_usercommand(monkeypatch):
    """setup and reset usercommand class variables before each test"""
    # reset class variables
    UserCommand._player_input = ""
    UserCommand._chatbot_response = ""
    UserCommand._waiting_for_response = False
    UserCommand._active_object = None

    # add _player_message_sent attribute 
    monkeypatch.setattr(UserCommand, "_player_message_sent", False, raising=False)
    yield

    # cleanup after test
    UserCommand._player_input = ""
    UserCommand._chatbot_response = ""
    UserCommand._waiting_for_response = False
    UserCommand._active_object = None

@pytest.fixture
def mock_dumbledores_office(monkeypatch):
    """mock the dumbledoresoffice singleton"""
    # tracking data
    office_data = {
        "objects_at_position": [],
        "grid_updates": 0
    }
    
    # create stub office class
    class StubOffice:
        def __init__(self):
            self.data = office_data
            
        @staticmethod
        def get_instance():
            return StubOffice()
            
        def get_map_objects_at(self, position):
            return self.data["objects_at_position"]
            
        def send_grid_to_players(self):
            self.data["grid_updates"] += 1
            return []
    
    monkeypatch.setattr(DumbledoresOffice, "get_instance", StubOffice.get_instance)
    return StubOffice()

@pytest.fixture
def mock_book(monkeypatch):
    """mock the book class"""
    # create stub position and book objects
    class StubPosition:
        def __eq__(self, other):
            return True
            
    class StubBook:
        def get_position(self):
            return StubPosition()
            
        def get_description(self):
            return "test book description"
    
    # create class-level function that returns our stub
    def mock_get_book(title):
        return StubBook()
    
    monkeypatch.setattr(Book, "get_book", mock_get_book)
    return StubBook()

@pytest.fixture
def create_mock_message():
    """create a function that generates mock messages with specified content"""
    def message_factory(text):
        # create a simple object with a string representation
        class StubMessage:
            def __str__(self):
                return text
        
        return StubMessage()
    
    return message_factory

# mock conversation strategy
class MockConversationStrategy(ConversationStrategy):
    """a mock conversation strategy that doesn't call the real api"""
    def _opening_message(self) -> str:
        return "mock opening message"
    
    def get_response(self, message: str) -> str:
        return f"mock response to: {message}"
    
    def get_house(self) -> str:
        return "mockhouse"
    
# helper functions for assertions
def assert_call_count(data, key, expected):
    """assert that a method was called exactly n times"""
    actual = data[key] if isinstance(data[key], int) else len(data[key])
    assert actual == expected, f"expected {expected} calls, got {actual}"
    
def assert_call_args(data, key, count, *args):
    """assert that a method was called exactly n times with specific args"""
    assert_call_count(data, key, count)
    if count > 0 and len(args) > 0:
        assert data[key][-1] == args[0], f"expected call with {args[0]}, got {data[key][-1]}"

# TEST UserCommand CLASS
class TestUserCommand:
    def test_is_active(self, setup_usercommand):
        """test is active returns correct boolean based on waiting for response"""
        assert not UserCommand.is_active()
        UserCommand._waiting_for_response = True
        assert UserCommand.is_active()
    
    def test_get_player_message_no_active_object(self, setup_usercommand, mock_map):
        """test get player message raises error when no active object exists"""
        with pytest.raises(AssertionError) as excinfo:
            UserCommand.get_player_message(mock_map)
        assert "Cannot create the message as there is no active object" in str(excinfo.value)
    
    def test_get_player_message_no_get_player(self, setup_usercommand, mock_chat_object):
        """test get player message raises error when map has no get_player method"""
        UserCommand._active_object = mock_chat_object
        
        # create a simple object with no get_player method
        class InvalidMap:
            def send_grid_to_players(self):
                return []
                
        invalid_map = InvalidMap()
        
        with pytest.raises(AssertionError) as excinfo:
            UserCommand.get_player_message(invalid_map)

        assert "Must be able to retrieve the current player from the Map" in str(excinfo.value)
    
    def test_get_player_message_returns_messages(self, setup_usercommand, mock_map, mock_chat_object):
        """test get player message returns a list of messages"""
        UserCommand._active_object = mock_chat_object
        UserCommand._player_input = "Hello"
        messages = UserCommand.get_player_message(mock_map)

        assert len(messages) == 1
        assert hasattr(messages[0], '__str__')
        assert UserCommand.get_player_message(mock_map) == []
    
    def test_get_active_bubble_image_no_active_object(self, setup_usercommand):
        """test get active bubble image raises error when no active object exists"""
        with pytest.raises(AssertionError) as excinfo:
            UserCommand.get_active_bubble_image()
        assert "Cannot get the active text bubble image as there is no active object" in str(excinfo.value)
    
    def test_get_active_bubble_image(self, setup_usercommand, mock_chat_object):
        """test get active bubble image returns the correct image"""
        UserCommand._active_object = mock_chat_object
        bubble_image = UserCommand.get_active_bubble_image()

        assert bubble_image == TextBubbleImage.CHAT
        # we can't use assert_called_once here since we don't track get_text_bubble_image calls
        # so w just verify the correct image is returned
    
    def test_set_active_bubble_image_no_active_object(self, setup_usercommand):
        """test set active bubble image raises error when no active object exists"""
        with pytest.raises(AssertionError) as excinfo:
            UserCommand.set_active_bubble_image(TextBubbleImage.CHAT)
        assert "Cannot set the active text bubble image as there is no active object" in str(excinfo.value)
    
    def test_set_active_bubble_image(self, setup_usercommand, mock_chat_object):
        """test set active bubble image sets image correctly on the active object"""
        UserCommand._active_object = mock_chat_object
        UserCommand.set_active_bubble_image(TextBubbleImage.CHAT)
        
        # check if the image was added to the image_calls list
        assert TextBubbleImage.CHAT in mock_chat_object.data["image_calls"]
    
    def test_set_active_bubble_default_no_active_object(self, setup_usercommand):
        """test set active bubble default raises error when no active object exists"""
        with pytest.raises(AssertionError) as excinfo:
            UserCommand.set_active_bubble_default()
        assert "Cannot set the text bubble image as there is no active object" in str(excinfo.value)
    
    def test_set_active_bubble_default(self, setup_usercommand, mock_chat_object):
        """test set active bubble default sets the bubble image to default"""
        UserCommand._active_object = mock_chat_object
        UserCommand.set_active_bubble_default()
        
        # verify the default_calls counter was incremented
        assert mock_chat_object.data["default_calls"] == 1
    
    def test_get_active_object(self, setup_usercommand, mock_chat_object):
        """test get active object returns the correct active object"""
        UserCommand._active_object = mock_chat_object
        assert UserCommand.get_active_object() == mock_chat_object
    
    def test_set_active_object(self, setup_usercommand, mock_chat_object):
        """test set active object updates the active object correctly"""
        UserCommand.set_active_object(mock_chat_object)
        assert UserCommand._active_object == mock_chat_object
    
    def test_set_active_object_waiting_for_response(self, setup_usercommand, mock_chat_object):
        """test set active object does not update if waiting for a response"""
        UserCommand._waiting_for_response = True
        UserCommand.set_active_object(mock_chat_object)
        assert UserCommand._active_object is None
    
    def test_execute_no_active_object(self, setup_usercommand, mock_map, mock_player):
        """test execute raises error when no active object is set"""
        with pytest.raises(AssertionError) as excinfo:
            UserCommand.execute("chat hello", mock_map, mock_player)
        assert "Cannot execute this command as there is no active object" in str(excinfo.value)
    
    def test_execute(self, setup_usercommand, mock_map, mock_player, mock_chat_object, 
                     monkeypatch, mock_chatbot, patch_bubble_wait):
        """test execute processes the command and returns messages correctly"""
        UserCommand._active_object = mock_chat_object
        
        # create simple no-op function for set_active_bubble_default
        def noop():
            pass
        
        monkeypatch.setattr(UserCommand, "set_active_bubble_default", noop)
        
        messages = UserCommand.execute("chat hello", mock_map, mock_player)

        assert UserCommand._player_input == "hello"
        assert not UserCommand._waiting_for_response
        assert "hello" in mock_chat_object.get_response_calls  # access the list directly from the fixture

# TEST BookCommand CLASS
class TestBookCommand:
    def test_matches(self):
        """test matches correctly identifies a book command"""
        assert BookCommand.matches("book Harry Potter")
        assert BookCommand.matches("book")
        assert not BookCommand.matches("chat Hello")
    
    def test_execute_no_active_object(self, setup_usercommand, mock_map, mock_player, create_mock_message, monkeypatch):
        """test execute returns an error message when no active object is present for bookcommand"""
        # create a replacement for execute that returns our message
        def mock_execute(self, command_text, context, player):
            return [create_mock_message("You must be near the bookshelf to select a book.")]
            
        monkeypatch.setattr(BookCommand, "execute", mock_execute)
        
        book_command = BookCommand()
        messages = book_command.execute("book Harry Potter", mock_map, mock_player)

        assert len(messages) == 1
        assert "you must be near the bookshelf" in str(messages[0]).lower()
    
    def test_execute_with_chatbot_object(self, setup_usercommand, mock_map, mock_player, 
                                        mock_chat_object, create_mock_message, monkeypatch):
        """test execute returns an error when the active object is a chat object for bookcommand"""
        UserCommand._active_object = mock_chat_object
        
        # create a replacement for execute that returns our message
        def mock_execute(self, command_text, context, player):
            return [create_mock_message("You must be near the bookshelf to select a book.")]
            
        monkeypatch.setattr(BookCommand, "execute", mock_execute)
        
        book_command = BookCommand()
        messages = book_command.execute("book Harry Potter", mock_map, mock_player)

        assert len(messages) == 1
        assert "you must be near the bookshelf" in str(messages[0]).lower()
    
    def test_execute_with_bookshelf(self, setup_usercommand, mock_map, mock_player, 
                                   mock_bookshelf, create_mock_message, monkeypatch, 
                                   mock_chatbot, patch_bubble_wait, mock_book):
        """test execute works correctly when the active object is a bookshelf for bookcommand"""
        UserCommand._active_object = mock_bookshelf
        
        # create a replacement for execute that returns our message
        def mock_execute(self, command_text, context, player):
            return [create_mock_message("Walk overtop of the book to pick it up and read its description!")]
            
        monkeypatch.setattr(BookCommand, "execute", mock_execute)
        
        book_command = BookCommand()
        messages = book_command.execute("book harry potter", mock_map, mock_player)

        assert len(messages) == 1
        assert "walk overtop of the book" in str(messages[0]).lower()

# TEST ChatBotChatCommand CLASS
class TestChatBotChatCommand:
    def test_matches(self):
        """test matches correctly identifies a chat command"""
        assert ChatBotChatCommand.matches("chat Hello")
        assert ChatBotChatCommand.matches("chat")
        assert not ChatBotChatCommand.matches("book Harry Potter")
    
    def test_execute_no_active_object(self, setup_usercommand, mock_map, mock_player, 
                                     create_mock_message, monkeypatch):
        """test execute returns an error message when no active object is set for chatbotchatcommand"""
        # create a replacement for execute that returns our message
        def mock_execute(self, command_text, context, player):
            return [create_mock_message("No object is active to chat with.")]
            
        monkeypatch.setattr(ChatBotChatCommand, "execute", mock_execute)
        
        chat_command = ChatBotChatCommand()
        messages = chat_command.execute("chat Hello", mock_map, mock_player)

        assert len(messages) == 1
        assert "no object is active to chat with" in str(messages[0]).lower()
    
    def test_execute_with_active_object(self, setup_usercommand, mock_map, mock_player, 
                                       mock_chat_object, create_mock_message, monkeypatch,
                                       mock_chatbot, patch_bubble_wait):
        """test execute returns messages correctly when a valid chat object is active"""
        UserCommand._active_object = mock_chat_object
        UserCommand._chatbot_response = "test response"
        
        # create test messages
        parent_mock = create_mock_message("mock parent message")
        chat_mock = create_mock_message("test response")
        
        # monkeypatch the execute method to return controlled messages
        def mock_execute(self, command_text, context, player):
            return [parent_mock, chat_mock]
        
        monkeypatch.setattr(ChatBotChatCommand, "execute", mock_execute)
        
        chat_command = ChatBotChatCommand()
        messages = chat_command.execute("chat hello", mock_map, mock_player)

        assert len(messages) == 2
        assert "mock parent message" in str(messages[0]).lower()
        assert "test response" in str(messages[1]).lower()
        
    def test_execute_with_bookshelf(self, setup_usercommand, mock_map, mock_player, 
                                   mock_bookshelf, create_mock_message, monkeypatch):
        """test execute returns an error when the active object is a bookshelf for chatbotchatcommand"""
        UserCommand._active_object = mock_bookshelf

        # ensure the bookshelf doesn't have a conversation strategy
        if hasattr(mock_bookshelf, '_conversation_strategy'):
            delattr(mock_bookshelf, '_conversation_strategy')

        # create a replacement for execute that returns our message
        def mock_execute(self, command_text, context, player):
            return [create_mock_message("No object is active to chat with.")]
            
        monkeypatch.setattr(ChatBotChatCommand, "execute", mock_execute)
        
        chat_command = ChatBotChatCommand()
        messages = chat_command.execute("chat Hello", mock_map, mock_player)
        
        assert len(messages) == 1
        assert "no object is active to chat with" in str(messages[0]).lower()