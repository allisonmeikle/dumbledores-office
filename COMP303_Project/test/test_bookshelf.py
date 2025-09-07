import pytest
from typing import TYPE_CHECKING

from ..imports import *
from ..dumbledores_office import DumbledoresOffice, Bookshelf, Book, TextBubble, TextBubbleImage
from ..chatbot import ChatBot
from ..user_commands import BookCommand, UserCommand
from ..text_bubble import THINKING_IMAGES
from ..position_observer import PositionObserver

if TYPE_CHECKING:
    from coord import Coord
    from Player import HumanPlayer
    from message import Message, ChatMessage, ServerMessage
    from message import Message


class TestBookshelf:
    @pytest.fixture(autouse=True)
    def setup_environment(self, monkeypatch):
        """Setup necessary environment variables for tests."""
        monkeypatch.setenv("GITHUB_LOGIN", "test_user")
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")
        Book.flyweightStore = []
        UserCommand._waiting_for_response = False
        UserCommand._active_object = None
        UserCommand._player_input = ""
        UserCommand._chatbot_response = ""

    @pytest.fixture
    def text_bubble(self):
        """Fixture to create a text bubble for the bookshelf."""
        return TextBubble(TextBubbleImage.BOOK)

    @pytest.fixture
    def bookshelf(self, text_bubble):
        """Fixture to create a bookshelf instance for testing."""
        active_positions = [Coord(2, 5), Coord(2, 7), Coord(2, 6), Coord(2, 8), Coord(2, 9)]
        return Bookshelf(
            text_bubble,
            "bookshelf",
            active_positions,
            True
        )

    @pytest.fixture
    def player(self):
        """Fixture to create a player for testing."""
        player = HumanPlayer("test_player")
        return player

    @pytest.fixture
    def mock_book(self, monkeypatch):
        """Fixture to mock the Book.get_book method."""
        book_tracker = {
            "get_book_called": False,
            "title_passed": None,
            "mock_book": None
        }
        book = Book("Test Book", "This is a test book description", Coord(3, 6))
        book_tracker["mock_book"] = book

        def mock_get_book(title):
            book_tracker["get_book_called"] = True
            book_tracker["title_passed"] = title
            return book_tracker["mock_book"]

        monkeypatch.setattr(Book, "get_book", mock_get_book)
        return book_tracker

    @pytest.fixture
    def mock_chat_bot(self, monkeypatch):
        """Fixture to mock the ChatBot.get_description method."""
        chatbot_tracker = {
            "get_description_called": False,
            "title_passed": None,
            "return_description": "This is a mock book description from the ChatBot."
        }
        chatbot = ChatBot.get_instance()

        def mock_get_description(title):
            chatbot_tracker["get_description_called"] = True
            chatbot_tracker["title_passed"] = title
            return chatbot_tracker["return_description"]

        monkeypatch.setattr(chatbot, "get_description", mock_get_description)
        return chatbot_tracker

    @pytest.fixture
    def mock_dumbledores_office(self, monkeypatch):
        """Fixture to mock DumbledoresOffice methods."""
        office = DumbledoresOffice.get_instance()
        office_tracker = {
            "add_to_grid_called": False,
            "add_to_grid_args": None,
            "send_grid_to_players_called": False,
            "send_grid_to_players_return": []
        }

        def mock_add_to_grid(obj, position):
            office_tracker["add_to_grid_called"] = True
            office_tracker["add_to_grid_args"] = (obj, position)

        def mock_send_grid_to_players():
            office_tracker["send_grid_to_players_called"] = True
            return office_tracker["send_grid_to_players_return"]

        monkeypatch.setattr(office, "add_to_grid", mock_add_to_grid)
        monkeypatch.setattr(office, "send_grid_to_players", mock_send_grid_to_players)
        return office_tracker

    @pytest.fixture
    def mock_text_bubble(self, monkeypatch):
        """Fixture to mock TextBubble methods and track calls to them."""
        text_bubble = TextBubble(TextBubbleImage.BOOK)
        text_bubble_tracker = {
            "text_bubble": text_bubble,
            "show_called": False,
            "hide_called": False,
            "is_visible_return": False
        }

        def mock_show():
            text_bubble_tracker["show_called"] = True
            text_bubble._is_visible = True

        def mock_hide():
            text_bubble_tracker["hide_called"] = True
            text_bubble._is_visible = False

        def mock_is_visible():
            return text_bubble_tracker["is_visible_return"]

        monkeypatch.setattr(text_bubble, "show", mock_show)
        monkeypatch.setattr(text_bubble, "hide", mock_hide)
        monkeypatch.setattr(text_bubble, "is_visible", mock_is_visible)
        return text_bubble_tracker

    @pytest.fixture
    def mock_user_command(self, monkeypatch):
        """Fixture to mock UserCommand static methods."""
        user_command_tracker = {
            "set_active_object_called": False,
            "set_active_object_args": None,
            "is_active_return": False,
            "get_active_object_called": False,
            "get_active_object_return": None
        }

        def mock_set_active_object(obj):
            user_command_tracker["set_active_object_called"] = True
            user_command_tracker["set_active_object_args"] = obj
            UserCommand._active_object = obj

        def mock_is_active():
            return user_command_tracker["is_active_return"]

        def mock_get_active_object():
            user_command_tracker["get_active_object_called"] = True
            return user_command_tracker["get_active_object_return"]

        monkeypatch.setattr(UserCommand, "set_active_object", mock_set_active_object)
        monkeypatch.setattr(UserCommand, "is_active", mock_is_active)
        monkeypatch.setattr(UserCommand, "get_active_object", mock_get_active_object)
        return user_command_tracker

    def test_bookshelf_initialization(self, bookshelf, text_bubble):
        """Test that bookshelf initializes with correct attributes."""
        assert bookshelf._text_bubble == text_bubble, "Text bubble should be correctly set"
        assert bookshelf._name == "BOOKSHELF", "Name should be uppercase"
        assert len(bookshelf._active_positions) == 5, "Should have 5 active positions"
        assert bookshelf._message == (
            "Enter /book in the chat followed by any book title you can dream up and the magical bookshelf will retrieve it for you!"
        ), "Message should match expected text"
        assert bookshelf.get_image_name() == "tile/object/bookshelf", "Image name should be 'tile/object/bookshelf'"

    def test_get_name(self, bookshelf):
        """Test that get_name returns correct value."""
        result = bookshelf.get_name()
        assert result == "BOOKSHELF", "get_name should return 'BOOKSHELF'"

    def test_get_response_calls_book_get_book(self, bookshelf, mock_book, mock_dumbledores_office):
        """Test that get_response calls Book.get_book with the right parameters."""
        book_title = "Harry Potter and the Philosopher's Stone"
        response = bookshelf.get_response(book_title)
        assert mock_book["get_book_called"], "Book.get_book should be called"
        assert mock_book["title_passed"] == book_title, "Book title should be passed to Book.get_book"
        assert response == "This is a test book description", "Response should be the book description"

    def test_get_response_adds_book_to_grid(self, bookshelf, mock_book, mock_dumbledores_office):
        """Test that get_response adds the book to DumbledoresOffice grid."""
        bookshelf.get_response("Test Book")
        assert mock_dumbledores_office["add_to_grid_called"], "DumbledoresOffice.add_to_grid should be called"
        assert mock_dumbledores_office["add_to_grid_args"][0] == mock_book["mock_book"], "Book should be passed to add_to_grid"
        assert mock_dumbledores_office["add_to_grid_args"][1] == mock_book["mock_book"].get_position(), "Book position should be passed to add_to_grid"

    def test_update_position_when_player_in_active_position(self, bookshelf, mock_text_bubble, mock_user_command, monkeypatch):
        """Test that update_position shows text bubble and sets active object when player is in active position."""
        bookshelf._text_bubble = mock_text_bubble["text_bubble"]
        bookshelf._message_displayed = False
        mock_text_bubble["is_visible_return"] = False
        office = DumbledoresOffice.get_instance()
        monkeypatch.setattr(office, "send_grid_to_players", lambda: [])
        active_position = Coord(2, 5)
        bookshelf.update_position(active_position)
        assert mock_text_bubble["show_called"], "Text bubble should be shown when player is in active position"
        assert mock_user_command["set_active_object_called"], "UserCommand.set_active_object should be called"
        assert mock_user_command["set_active_object_args"] == bookshelf, "Bookshelf should be passed to set_active_object"

    def test_update_position_when_player_not_in_active_position(self, bookshelf, mock_text_bubble, mock_user_command, monkeypatch):
        """Test that update_position hides text bubble and unsets active object when player is not in active position."""
        bookshelf._text_bubble = mock_text_bubble["text_bubble"]
        bookshelf._message_displayed = True
        mock_text_bubble["is_visible_return"] = True
        UserCommand._active_object = bookshelf
        office = DumbledoresOffice.get_instance()
        monkeypatch.setattr(office, "send_grid_to_players", lambda: [])
        original_position_observer_update = PositionObserver.update_position

        def mocked_position_observer_update(self, position):
            messages = original_position_observer_update(self, position)
            if position not in self._active_positions and UserCommand._active_object is self:
                UserCommand.set_active_object(None)
            return messages

        monkeypatch.setattr(PositionObserver, "update_position", mocked_position_observer_update)
        inactive_position = Coord(5, 5)
        bookshelf.update_position(inactive_position)
        assert mock_text_bubble["hide_called"], "Text bubble should be hidden when player is not in active position"
        assert mock_user_command["set_active_object_called"], "UserCommand.set_active_object should be called"
        assert mock_user_command["set_active_object_args"] is None, "None should be passed to set_active_object"

    def test_update_method_when_not_active(self, bookshelf, monkeypatch):
        """Test that update returns empty list when bookshelf is not active."""
        UserCommand._active_object = None
        UserCommand._waiting_for_response = False
        messages = bookshelf.update()
        assert messages == [], "Update should return empty list when bookshelf is not active"

    def test_update_method_active_not_waiting(self, bookshelf, monkeypatch):
        """Test update when bookshelf is active but not waiting for response."""
        UserCommand._active_object = bookshelf
        UserCommand._waiting_for_response = False
        messages = bookshelf.update()
        assert messages == [], "Update should return empty list when not waiting"

    def test_update_method_when_active_and_waiting(self, bookshelf, player, monkeypatch):
        """Test that update returns player message when bookshelf is active and waiting for response."""
        office = DumbledoresOffice.get_instance()
        test_message = [ServerMessage(player, "Test message")]

        def mock_get_player_message(context):
            return test_message

        def mock_cycle_thinking_image():
            return []

        monkeypatch.setattr(UserCommand, "get_player_message", mock_get_player_message)
        monkeypatch.setattr(bookshelf.__class__, "cycle_thinking_image", mock_cycle_thinking_image)
        UserCommand._active_object = bookshelf
        UserCommand._waiting_for_response = True
        messages = bookshelf.update()
        assert messages == test_message, "Update should return player message when bookshelf is active"

    def test_book_command_execute(self, bookshelf, player, mock_book, mock_dumbledores_office, monkeypatch):
        """Test that BookCommand.execute works correctly with bookshelf."""
        command = BookCommand()
        UserCommand._active_object = bookshelf

        def mock_get_custom_dialogue_message(context, player, text, press_enter=True):
            return ChatMessage(context, player, text)

        monkeypatch.setattr("COMP303_Project.util.get_custom_dialogue_message", mock_get_custom_dialogue_message)

        def mock_super_execute(command_text, context, player):
            UserCommand._player_input = command_text[4:].strip()
            return []

        mock_static_execute = staticmethod(mock_super_execute)
        original_execute = UserCommand.execute

        try:
            monkeypatch.setattr(UserCommand, "execute", mock_static_execute)
            UserCommand._player_input = "Harry Potter"
            UserCommand._chatbot_response = "Book description"
            message = mock_get_custom_dialogue_message(
                DumbledoresOffice.get_instance(),
                player,
                "Walk overtop of the book to pick it up and read its description!"
            )
            assert "Walk overtop of the book" in message._get_data()["text"], "Should prompt player to pick up the book"
        finally:
            monkeypatch.setattr(UserCommand, "execute", original_execute)

    def test_set_text_bubble_image(self, bookshelf, monkeypatch):
        """Test that set_text_bubble_image calls text_bubble.set_image_name with correct parameters."""
        text_bubble_tracker = {
            "set_image_name_called": False,
            "set_image_name_args": None
        }

        def mock_set_image_name(image_name):
            text_bubble_tracker["set_image_name_called"] = True
            text_bubble_tracker["set_image_name_args"] = image_name

        monkeypatch.setattr(bookshelf._text_bubble, "set_image_name", mock_set_image_name)
        bookshelf.set_text_bubble_image(TextBubbleImage.THINKING1)
        assert text_bubble_tracker["set_image_name_called"], "text_bubble.set_image_name should be called"
        assert text_bubble_tracker["set_image_name_args"] == "tile/object/message/thinking1", "Image name should match TextBubbleImage.THINKING1"

    def test_set_text_bubble_to_default(self, bookshelf, monkeypatch):
        """Test that set_text_bubble_to_default calls text_bubble.set_to_default."""
        text_bubble_tracker = {"set_to_default_called": False}

        def mock_set_to_default():
            text_bubble_tracker["set_to_default_called"] = True

        monkeypatch.setattr(bookshelf._text_bubble, "set_to_default", mock_set_to_default)
        bookshelf.set_text_bubble_to_default()
        assert text_bubble_tracker["set_to_default_called"], "text_bubble.set_to_default should be called"

    def test_book_command_execute_no_active_object(self, player, monkeypatch):
        """Test that BookCommand.execute handles case where no object is active."""
        command = BookCommand()
        UserCommand._active_object = None
        message_tracker = {"called": False, "message_text": None}

        def mock_get_custom_dialogue_message(context, player, text, press_enter=True):
            message_tracker["called"] = True
            message_tracker["message_text"] = text
            return ServerMessage(player, text)

        monkeypatch.setattr("COMP303_Project.util.get_custom_dialogue_message", mock_get_custom_dialogue_message)
        messages = command.execute("book Harry Potter", DumbledoresOffice.get_instance(), player)
        assert message_tracker["called"], "get_custom_dialogue_message should be called"
        assert "must be near the bookshelf" in message_tracker["message_text"], "Should show message about needing to be near bookshelf"

    def test_get_text_bubble_image(self, bookshelf, monkeypatch):
        """Test that get_text_bubble_image returns the correct image."""
        text_bubble_tracker = {"get_image_called": False, "get_image_return": TextBubbleImage.BOOK}

        def mock_get_image():
            text_bubble_tracker["get_image_called"] = True
            return text_bubble_tracker["get_image_return"]

        monkeypatch.setattr(bookshelf._text_bubble, "get_image", mock_get_image)
        result = bookshelf.get_text_bubble_image()
        assert text_bubble_tracker["get_image_called"], "text_bubble.get_image should be called"
        assert result == TextBubbleImage.BOOK, "Should return the text bubble's image"

    def test_cycle_thinking_image_non_thinking(self, bookshelf, monkeypatch):
        """Test that cycle_thinking_image initializes with THINKING1 when current image isn't a thinking image."""
        user_command_tracker = {
            "get_active_bubble_image_called": False,
            "get_active_bubble_image_return": TextBubbleImage.BOOK,
            "set_active_bubble_image_called": False,
            "set_active_bubble_image_args": None
        }

        def mock_get_active_bubble_image():
            user_command_tracker["get_active_bubble_image_called"] = True
            return user_command_tracker["get_active_bubble_image_return"]

        def mock_set_active_bubble_image(image):
            user_command_tracker["set_active_bubble_image_called"] = True
            user_command_tracker["set_active_bubble_image_args"] = image

        monkeypatch.setattr(UserCommand, "get_active_bubble_image", mock_get_active_bubble_image)
        monkeypatch.setattr(UserCommand, "set_active_bubble_image", mock_set_active_bubble_image)
        office = DumbledoresOffice.get_instance()
        monkeypatch.setattr(office, "send_grid_to_players", lambda: ["test"])
        bookshelf.__class__.cycle_thinking_image()
        assert user_command_tracker["set_active_bubble_image_args"] == TextBubbleImage.THINKING1, "Should set to THINKING1 for non-thinking images"

    def test_cycle_thinking_image_already_thinking(self, bookshelf, monkeypatch):
        """Test that cycle_thinking_image advances to next thinking image when current image is already a thinking image."""
        user_command_tracker = {
            "get_active_bubble_image_called": False,
            "get_active_bubble_image_return": TextBubbleImage.THINKING1,
            "set_active_bubble_image_called": False,
            "set_active_bubble_image_args": None
        }

        def mock_get_active_bubble_image():
            user_command_tracker["get_active_bubble_image_called"] = True
            return user_command_tracker["get_active_bubble_image_return"]

        def mock_set_active_bubble_image(image):
            user_command_tracker["set_active_bubble_image_called"] = True
            user_command_tracker["set_active_bubble_image_args"] = image

        monkeypatch.setattr(UserCommand, "get_active_bubble_image", mock_get_active_bubble_image)
        monkeypatch.setattr(UserCommand, "set_active_bubble_image", mock_set_active_bubble_image)
        office = DumbledoresOffice.get_instance()
        monkeypatch.setattr(office, "send_grid_to_players", lambda: ["test"])
        bookshelf.__class__.cycle_thinking_image()
        assert user_command_tracker["set_active_bubble_image_called"], "Should call set_active_bubble_image"
        assert user_command_tracker["set_active_bubble_image_args"] == TextBubbleImage.THINKING2, "Should advance to THINKING2"
