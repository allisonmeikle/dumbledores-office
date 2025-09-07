import pytest
from typing import TYPE_CHECKING, List, Dict, Any

from ..imports import *
from ..dumbledores_office import ChatBotObject, TextBubble, TextBubbleImage 
from ..user_commands import UserCommand

if TYPE_CHECKING:
    from coord import Coord
    from Player import HumanPlayer
    from maps.base import Message


class TestChatBotObject:
    """
    Tests for the ChatBotObject class.

    The ChatBotObject class is an abstract base class that provides common functionality for
    objects that can interact with a ChatBot, such as portraits and the pensieve.
    """

    @pytest.fixture(autouse=True)
    def setup_environment(self, monkeypatch):
        """Setup environment for all tests."""
        # mock cycle_thinking_image to avoid dependencies
        self.cycle_thinking_called = False

        def mock_cycle_thinking():
            self.cycle_thinking_called = True
            return []

        monkeypatch.setattr(ChatBotObject, "cycle_thinking_image", mock_cycle_thinking)

    @pytest.fixture
    def tracked_text_bubble(self, monkeypatch) -> Dict[str, Any]:
        """Create a text bubble with tracked method calls."""
        bubble = TextBubble(TextBubbleImage.CHAT)
        # track method calls
        tracker = {
            "bubble": bubble,
            "set_image_calls": [],
            "set_to_default_called": False
        }

        # mock methods
        def mock_set_image_name(image_name):
            tracker["set_image_calls"].append(image_name)

        def mock_set_to_default():
            tracker["set_to_default_called"] = True

        def mock_get_image():
            return TextBubbleImage.CHAT

        # apply mocks
        monkeypatch.setattr(bubble, "set_image_name", mock_set_image_name)
        monkeypatch.setattr(bubble, "set_to_default", mock_set_to_default)
        monkeypatch.setattr(bubble, "get_image", mock_get_image)
        return tracker

    @pytest.fixture
    def test_chatbot(self, tracked_text_bubble) -> ChatBotObject:
        """Create a concrete ChatBotObject for testing."""
        class TestChatBot(ChatBotObject):
            def get_response(self, input_str: str) -> str:
                return f"Response to: {input_str}"

            def __init__(self, text_bubble, image_name, active_positions):
                self._text_bubble = text_bubble
                self._name = image_name.split("/")[-1].upper()
                self._active_positions = active_positions
                self._message_displayed = False
                self._image_name = f"tile/object/{image_name}"
                self._passable = False
                self._z_index = 1
                self.num_rows = 1
                self.num_cols = 1

            def update_position(self, position):
                return []

        active_positions = [Coord(1, 1), Coord(1, 2)]
        return TestChatBot(tracked_text_bubble["bubble"], "test_image", active_positions)

    @pytest.fixture
    def tracked_user_command(self, monkeypatch) -> Dict[str, Any]:
        """Mock UserCommand static methods and track calls."""
        tracker = {
            "set_active_object_calls": [],
            "get_player_message_called": False,
            "active_object": None,
            "is_active": False
        }

        # mock methods
        def mock_is_active():
            return tracker["is_active"]

        def mock_get_active_object():
            return tracker["active_object"]

        def mock_set_active_object(obj):
            tracker["set_active_object_calls"].append(obj)
            tracker["active_object"] = obj

        def mock_get_player_message(context):
            tracker["get_player_message_called"] = True
            return []

        # apply mocks
        monkeypatch.setattr(UserCommand, "is_active", mock_is_active)
        monkeypatch.setattr(UserCommand, "get_active_object", mock_get_active_object)
        monkeypatch.setattr(UserCommand, "set_active_object", mock_set_active_object)
        monkeypatch.setattr(UserCommand, "get_player_message", mock_get_player_message)
        return tracker

    def test_get_name(self, test_chatbot):
        """Tests that get_name returns the expected name."""
        assert test_chatbot.get_name() == "TEST_IMAGE"

    def test_set_text_bubble_image(self, test_chatbot, tracked_text_bubble):
        """Tests that set_text_bubble_image sets the correct image."""
        test_chatbot.set_text_bubble_image(TextBubbleImage.THINKING1)
        assert len(tracked_text_bubble["set_image_calls"]) == 1
        assert tracked_text_bubble["set_image_calls"][0] == f"tile/object/message/{TextBubbleImage.THINKING1.value}"

    def test_set_text_bubble_to_default(self, test_chatbot, tracked_text_bubble):
        """Tests that set_text_bubble_to_default calls set_to_default."""
        test_chatbot.set_text_bubble_to_default()
        assert tracked_text_bubble["set_to_default_called"]

    def test_get_text_bubble_image(self, test_chatbot):
        """Tests that get_text_bubble_image returns the expected image."""
        # act & assert
        assert test_chatbot.get_text_bubble_image() == TextBubbleImage.CHAT

    def test_update_when_object_is_active(self, test_chatbot, tracked_user_command):
        """Tests update when object is active."""
        tracked_user_command["is_active"] = True
        tracked_user_command["active_object"] = test_chatbot
        messages = test_chatbot.update()
        assert tracked_user_command["get_player_message_called"]
        assert self.cycle_thinking_called
        assert messages == []

    def test_update_when_object_is_not_active(self, test_chatbot, tracked_user_command):
        """Tests update when object is not active."""
        tracked_user_command["is_active"] = True
        tracked_user_command["active_object"] = None
        messages = test_chatbot.update()
        assert not tracked_user_command["get_player_message_called"]
        assert not self.cycle_thinking_called
        assert messages == []

    def test_update_position_when_player_in_active_position(self, test_chatbot, tracked_user_command):
        """Tests update_position when player is in an active position."""
        class TestPositionChatBot(ChatBotObject):
            def __init__(self, text_bubble, image_name, active_positions):
                self._text_bubble = text_bubble
                self._name = image_name.split("/")[-1].upper()
                self._active_positions = active_positions
                self._message_displayed = False
                self._image_name = f"tile/object/{image_name}"
                self._passable = False
                self._z_index = 1
                self.num_rows = 1
                self.num_cols = 1
                self._message = "Test message for player"
                self._message = "Test message for player"

            def get_response(self, input_str: str) -> str:
                return f"Response to: {input_str}"

            def super_update_position(self, position):
                return []

        chatbot = TestPositionChatBot(
            test_chatbot._text_bubble, 
            "position_test", 
            [Coord(1, 1), Coord(1, 2)]
        )
        original_update_position = chatbot.update_position

        def test_update_position(position):
            messages = original_update_position(position)
            chatbot.super_update_position(position)
            return messages

        chatbot.update_position = test_update_position
        messages = chatbot.update_position(Coord(1, 1)) # position in active_positions
        assert len(tracked_user_command["set_active_object_calls"]) == 1
        assert tracked_user_command["set_active_object_calls"][0] is chatbot

    def test_update_position_when_player_not_in_active_position(self, test_chatbot, tracked_user_command, monkeypatch):
        """Tests update_position when player is not in an active position but is the active object."""
        from ..util import get_custom_dialogue_message as original_get_dialogue
        from ..dumbledores_office import DumbledoresOffice

        def mock_get_custom_dialogue():
            return []

        def mock_send_grid():
            return []

        def mock_get_instance():
            mock_instance = type('MockDumbledoresOffice', (), {
                'get_player': lambda: type('MockPlayer', (), {'get_name': lambda: 'TestPlayer'}),
                'send_grid_to_players': mock_send_grid
            })()

            return mock_instance

        monkeypatch.setattr("COMP303_Project.dumbledores_office.DumbledoresOffice.get_instance", mock_get_instance)
        monkeypatch.setattr("COMP303_Project.util.get_custom_dialogue_message", lambda *args: [])
        class TestPositionChatBot(ChatBotObject):
            def __init__(self, text_bubble, image_name, active_positions):
                self._text_bubble = text_bubble
                self._name = image_name.split("/")[-1].upper()
                self._active_positions = active_positions
                self._message_displayed = False
                self._image_name = f"tile/object/{image_name}"
                self._passable = False
                self._z_index = 1
                self.num_rows = 1
                self.num_cols = 1
                self._message = "Test message for player"

            def get_response(self, input_str: str) -> str:
                return f"Response to: {input_str}"

        chatbot = TestPositionChatBot(
            test_chatbot._text_bubble, 
            "position_test", 
            [Coord(1, 1), Coord(1, 2)]
        )
        def mock_position_observer_update(self, position):
            return []

        original_update = ChatBotObject.update_position
        monkeypatch.setattr("COMP303_Project.position_observer.PositionObserver.update_position", mock_position_observer_update)
        tracked_user_command["active_object"] = chatbot
        chatbot.update_position(Coord(5, 5))
        assert len(tracked_user_command["set_active_object_calls"]) == 1
        assert tracked_user_command["set_active_object_calls"][0] is None

    def test_update_position_when_not_active_object(self, test_chatbot, tracked_user_command):
        """Tests update_position when object is not the active object."""
        class TestPositionChatBot(ChatBotObject):
            def __init__(self, text_bubble, image_name, active_positions):
                self._text_bubble = text_bubble
                self._name = image_name.split("/")[-1].upper()
                self._active_positions = active_positions
                self._message_displayed = False
                self._image_name = f"tile/object/{image_name}"
                self._passable = False
                self._z_index = 1
                self.num_rows = 1
                self.num_cols = 1

            def get_response(self, input_str: str) -> str:
                return f"Response to: {input_str}"

            def super_update_position(self, position):
                return []

        chatbot = TestPositionChatBot(
            test_chatbot._text_bubble, 
            "position_test", 
            [Coord(1, 1), Coord(1, 2)]
        )
        original_update_position = chatbot.update_position

        def test_update_position(position):
            messages = original_update_position(position)
            chatbot.super_update_position(position)
            return messages

        chatbot.update_position = test_update_position
        tracked_user_command["active_object"] = "some_other_object"
        messages = chatbot.update_position(Coord(5, 5))
        assert len(tracked_user_command["set_active_object_calls"]) == 0
