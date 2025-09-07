import pytest
from typing import TYPE_CHECKING, List

from ..imports import *
from ..position_observer import PositionObserver
from ..text_bubble import TextBubble, TextBubbleImage
from ..dumbledores_office import DumbledoresOffice

if TYPE_CHECKING:
    from coord import Coord
    from message import Message, DialogueMessage
    from Player import HumanPlayer


class MockPositionObserver(PositionObserver):
    """
    Concrete implementation of PositionObserver for testing.
    """
    def __init__(self, text_bubble: TextBubble, active_positions: List['Coord'], message: str = "Test message"):
        self._text_bubble = text_bubble
        self._active_positions = active_positions
        self._message = message
        self._message_displayed = False

class MockObserverWithoutTextBubble(PositionObserver):
    """
    Special implementation of PositionObserver for testing the null text bubble condition.
    This class intentionally sets _text_bubble to None to test error handling.
    """
    def __init__(self, active_positions: List['Coord'], message: str = "Test message"):
        self._active_positions = active_positions
        self._message = message
        self._message_displayed = False
        # Set _text_bubble to None instead of not defining it.
        self._text_bubble = None  # type: ignore

class TestPositionObserver:
    """
    Test suite for the PositionObserver abstract class.
    Tests the update_position method behavior in various scenarios.
    """

    @pytest.fixture(autouse=True)
    def setup_environment(self, monkeypatch):
        """Setup necessary environment variables for tests."""
        monkeypatch.setenv("GITHUB_LOGIN", "test_user")
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")

    @pytest.fixture
    def text_bubble(self):
        """Fixture to create a TextBubble for testing."""
        return TextBubble(TextBubbleImage.CHAT)

    @pytest.fixture
    def active_positions(self):
        """Fixture to create active positions for testing."""
        return [Coord(1, 1), Coord(2, 2), Coord(3, 3)]

    @pytest.fixture
    def position_observer(self, text_bubble, active_positions):
        """Fixture to create a MockPositionObserver for testing."""
        return MockPositionObserver(text_bubble, active_positions)

    @pytest.fixture
    def mock_player(self):
        """Fixture to create a mock player for testing."""
        player = HumanPlayer("test_player")
        return player

    @pytest.fixture
    def mock_message(self):
        """Fixture to mock a message response."""
        class MockMessage:
            def __init__(self, content):
                self.content = content

        return MockMessage("Test message")

    @pytest.fixture
    def mock_dumbledores_office(self, monkeypatch, mock_player, mock_message):
        """Fixture to mock DumbledoresOffice methods."""
        dumbledores_office = DumbledoresOffice.get_instance()

        # Mock methods
        monkeypatch.setattr(dumbledores_office, "get_player", lambda: mock_player)
        monkeypatch.setattr(dumbledores_office, "send_grid_to_players", lambda: [mock_message])

        # Mock the get_instance method
        def mock_get_instance():
            return dumbledores_office
        
        monkeypatch.setattr(DumbledoresOffice, "get_instance", mock_get_instance)

        return dumbledores_office

    @pytest.fixture
    def mock_dialogue_message(self, monkeypatch):
        """Fixture to mock DialogueMessage creation."""

        # Track if the function was called
        dialogue_tracker = {"called": False, "message": None}

        # Create a mock function that matches get_custom_dialogue_message
        def mock_get_dialogue(sender, recipient, text, image="", font='harryp',
                              bg_color=(0, 0, 0), text_color=(255, 255, 255),
                              press_enter=True, auto_delay=500):
            dialogue_tracker["called"] = True
            dialogue_tracker["message"] = text
            return DialogueMessage(sender, recipient, text, image, font, bg_color, text_color, press_enter, auto_delay)
        
        monkeypatch.setattr("COMP303_Project.util.get_custom_dialogue_message", mock_get_dialogue)

        return dialogue_tracker

    def test_update_position_player_in_active_position(self, position_observer, mock_dumbledores_office, mock_dialogue_message):
        """Test update_position when player is in an active position."""
        active_position = position_observer._active_positions[0]

        messages = position_observer.update_position(active_position)

        assert position_observer._text_bubble.is_visible(), "Text bubble should be visible when player is in active position"
        assert position_observer._message_displayed, "Message_displayed should be set to True"
        assert mock_dialogue_message["called"], "get_custom_dialogue_message should be called"
        assert mock_dialogue_message["message"] == position_observer._message, "Correct message should be passed"
        assert len(messages) > 0, "Should return at least one message"

    def test_update_position_player_in_different_active_position(self, position_observer, mock_dumbledores_office, mock_dialogue_message):
        """Test update_position when player is in a different active position."""
        active_position = position_observer._active_positions[1]

        messages = position_observer.update_position(active_position)

        assert position_observer._text_bubble.is_visible(), "Text bubble should be visible for any active position"
        assert position_observer._message_displayed, "Message_displayed should be set to True"
        assert mock_dialogue_message["called"], "get_custom_dialogue_message should be called"
        assert len(messages) > 0, "Should return at least one message"

    def test_update_position_player_not_in_active_position(self, position_observer, mock_dumbledores_office, mock_dialogue_message):
        """Test update_position when player is not in an active position."""
        inactive_position = Coord(10, 10)

        messages = position_observer.update_position(inactive_position)

        assert not position_observer._text_bubble.is_visible(), "Text bubble should be hidden when player is not in active position"
        assert not position_observer._message_displayed, "Message_displayed should be set to False"
        assert not mock_dialogue_message["called"], "get_custom_dialogue_message should not be called"
        assert len(messages) > 0, "Should return at least one message (grid update)"

    def test_update_position_player_moving_from_active_to_inactive(self, position_observer, mock_dumbledores_office, mock_dialogue_message):
        """Test update_position when player moves from active to inactive position."""
        active_position = position_observer._active_positions[0]
        position_observer.update_position(active_position)
        mock_dialogue_message["called"] = False
        inactive_position = Coord(10, 10)
        messages = position_observer.update_position(inactive_position)

        assert not position_observer._text_bubble.is_visible(), "Text bubble should be hidden after moving to inactive position"
        assert not position_observer._message_displayed, "Message_displayed should be set to False"
        assert not mock_dialogue_message["called"], "get_custom_dialogue_message should not be called again"
        assert len(messages) > 0, "Should return at least one message (grid update)"

    def test_update_position_player_moving_from_inactive_to_active(self, position_observer, mock_dumbledores_office, mock_dialogue_message):
        """Test update_position when player moves from inactive to active position."""
        inactive_position = Coord(10, 10)
        position_observer.update_position(inactive_position)
        mock_dialogue_message["called"] = False
        active_position = position_observer._active_positions[0]
        messages = position_observer.update_position(active_position)

        assert position_observer._text_bubble.is_visible(), "Text bubble should be visible after moving to active position"
        assert position_observer._message_displayed, "Message_displayed should be set to True"
        assert mock_dialogue_message["called"], "get_custom_dialogue_message should be called"
        assert len(messages) > 0, "Should return at least one message"

    def test_update_position_player_already_in_active_position(self, position_observer, mock_dumbledores_office, mock_dialogue_message):
        """Test update_position when player is already in an active position (no message duplication)."""
        active_position = position_observer._active_positions[0]
        position_observer.update_position(active_position)
        mock_dialogue_message["called"] = False
        messages = position_observer.update_position(active_position)

        assert position_observer._text_bubble.is_visible(), "Text bubble should remain visible"
        assert position_observer._message_displayed, "Message_displayed should remain True"
        assert not mock_dialogue_message["called"], "get_custom_dialogue_message should not be called again"
        assert len(messages) > 0, "Should return at least one message (grid update)"

    def test_update_position_with_missing_text_bubble(self, active_positions, mock_dumbledores_office):
        """Test update_position behavior when text_bubble attribute is missing."""
        observer = MockObserverWithoutTextBubble(active_positions)
        active_position = active_positions[0]
        messages = observer.update_position(active_position)

        assert len(messages) > 0, "Should return at least one message (grid update)"
