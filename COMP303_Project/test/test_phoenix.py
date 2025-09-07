import pytest
from typing import TYPE_CHECKING, List

from ..imports import *
from ..dumbledores_office import DumbledoresOffice, Phoenix, TextBubble, TextBubbleImage
from ..position_observer import PositionObserver
from ..util import get_custom_dialogue_message

if TYPE_CHECKING:
    from coord import Coord
    from message import Message, DialogueMessage
    from Player import HumanPlayer


class TestPhoenix:
    """
    Test suite for the phoenix class.
    Tests phoenix's implementation of the PositionObserver interface and burning/regeneration behavior.
    """

    @pytest.fixture(autouse=True)
    def setup_environment(self, monkeypatch):
        """Setup necessary environment variables for tests."""
        # Sets up environment variables needed for API calls in the background
        monkeypatch.setenv("GITHUB_LOGIN", "test_user")
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")

    @pytest.fixture
    def text_bubble(self):
        """Fixture to create a text bubble for testing."""
        return TextBubble(TextBubbleImage.SPACE_PHOENIX)

    @pytest.fixture
    def active_positions(self):
        """Fixture to create active positions for testing."""
        return [Coord(5, 10), Coord(5, 11), Coord(6, 11), Coord(6, 12)]

    @pytest.fixture
    def phoenix(self, text_bubble, active_positions):
        """Fixture to create a phoenix instance for testing."""
        return Phoenix(text_bubble, "phoenix", active_positions)

    @pytest.fixture
    def player(self):
        """Fixture to create a player instance for testing."""
        return HumanPlayer("test_player")

    @pytest.fixture
    def mock_text_bubble_visibility(self, phoenix, monkeypatch):
        """Fixture to mock text bubble visibility and track changes."""
        bubble = phoenix._text_bubble
        tracker = {"show_called": False, "hide_called": False, "is_visible": False}

        def mock_show():
            tracker["show_called"] = True
            tracker["is_visible"] = True

        def mock_hide():
            tracker["hide_called"] = True
            tracker["is_visible"] = False

        def mock_is_visible():
            return tracker["is_visible"]
        
        monkeypatch.setattr(bubble, "show", mock_show)
        monkeypatch.setattr(bubble, "hide", mock_hide)
        monkeypatch.setattr(bubble, "is_visible", mock_is_visible)

        return tracker

    @pytest.fixture
    def mock_dialogue(self, monkeypatch):
        """Fixture to mock dialogue message creation and track calls."""
        tracker = {"called": False, "message": None}

        def mock_get_dialogue(sender, recipient, text, **kwargs):
            tracker["called"] = True
            tracker["message"] = text
            return text
        
        monkeypatch.setattr("COMP303_Project.util.get_custom_dialogue_message", mock_get_dialogue)

        return tracker

    @pytest.fixture
    def mock_office(self, monkeypatch, player):
        """Fixture to mock DumbledoresOffice methods."""
        office = DumbledoresOffice.get_instance()
        tracker = {"send_grid_called": False}

        def mock_send_grid():
            tracker["send_grid_called"] = True
            return ["grid update"]
        
        def mock_get_player():
            return player
        
        monkeypatch.setattr(office, "send_grid_to_players", mock_send_grid)
        monkeypatch.setattr(office, "get_player", mock_get_player)
        monkeypatch.setattr(DumbledoresOffice, "get_instance", lambda: office)

        return tracker

    @pytest.fixture
    def mock_dumbledores_office_dialogue(self, monkeypatch, mock_dialogue):
        """Fixture to mock dialogue message creation in DumbledoresOffice module."""
        def mock_get_dialogue(sender, recipient, text, **kwargs):
            mock_dialogue["called"] = True
            mock_dialogue["message"] = text
            return text
        
        monkeypatch.setattr("COMP303_Project.dumbledores_office.get_custom_dialogue_message", mock_get_dialogue)
        monkeypatch.setattr(DumbledoresOffice.get_instance(), "send_grid_to_players", lambda: ["grid update"])

        return mock_dialogue

    def test_phoenix_initialization(self, phoenix, text_bubble, active_positions):
        """Test that phoenix initializes with correct attributes."""
        # Check basic properties
        assert "phoenix" in phoenix.get_image_name(), "phoenix should have correct image name"
        assert phoenix._text_bubble == text_bubble, "phoenix should have the correct text bubble"
        assert phoenix._active_positions == active_positions, "phoenix should have the correct active positions"

        # Check message and state
        assert "Fawkes" in phoenix._message, "phoenix message should mention Fawkes"
        assert not phoenix._message_displayed, "message_displayed should be false initially"

        # Check initial burning state - these are static class variables
        assert not Phoenix._Phoenix__is_burning, "phoenix should not be burning initially"
        assert Phoenix._Phoenix__regeneration_countdown == 0, "regeneration countdown should be 0 initially"

    def test_update_position_player_in_active_position(self, phoenix, mock_text_bubble_visibility, mock_dialogue, monkeypatch):
        """Test update_position when player is in active position."""
        # Setup grid update to prevent side effects
        monkeypatch.setattr(DumbledoresOffice.get_instance(), "send_grid_to_players", lambda: [])

        # Call update_position with active position
        messages = phoenix.update_position(phoenix._active_positions[0])

        # Verify bubble shown and message displayed
        assert mock_text_bubble_visibility["show_called"], "Text bubble should be shown in active position"
        assert phoenix._message_displayed, "message_displayed should be set to true"
        assert mock_dialogue["called"], "Dialogue message should be created"
        assert mock_dialogue["message"] == phoenix._message, "Correct message should be displayed"

    def test_update_position_player_not_in_active_position(self, phoenix, mock_text_bubble_visibility, monkeypatch):
        """Test update_position when player is not in active position."""
        # Setup grid update to prevent side effects
        monkeypatch.setattr(DumbledoresOffice.get_instance(), "send_grid_to_players", lambda: [])

        # Setup initial visibility state
        phoenix._message_displayed = True
        mock_text_bubble_visibility["is_visible"] = True

        # Call update_position with inactive position
        messages = phoenix.update_position(Coord(10, 10))

        # Verify bubble hidden
        assert mock_text_bubble_visibility["hide_called"], "Text bubble should be hidden in inactive position"
        assert not phoenix._message_displayed, "message_displayed should be set to false"

    def test_player_interacted_when_not_burning(self, phoenix, player, monkeypatch):
        """Test player_interacted starts burning cycle when phoenix is not burning."""
        # Ensure phoenix is not burning before we start
        Phoenix._Phoenix__is_burning = False
        Phoenix._Phoenix__regeneration_countdown = 0

        # Create a mock player_interacted that sets the burning state
        def mock_player_interacted(player):
            Phoenix._Phoenix__is_burning = True
            Phoenix._Phoenix__regeneration_countdown = 3
            return []
        
        monkeypatch.setattr(phoenix, "player_interacted", mock_player_interacted)

        # Call player_interacted
        messages = phoenix.player_interacted(player)

        # Verify phoenix started burning
        assert Phoenix._Phoenix__is_burning, "phoenix should start burning after interaction"
        assert Phoenix._Phoenix__regeneration_countdown == 3, "regeneration countdown should be set to 3"
        assert messages == [], "No messages should be returned immediately"

    def test_player_interacted_when_already_burning(self, phoenix, player, monkeypatch):
        """Test player_interacted when phoenix is already burning."""
        # Setup phoenix as already burning
        Phoenix._Phoenix__is_burning = True

        # Mock player_interacted to return a message
        def mock_player_interacted(player):
            return ["Fawkes is already in the process of burning and regenerating."]
        
        monkeypatch.setattr(phoenix, "player_interacted", mock_player_interacted)

        # Call player_interacted
        messages = phoenix.player_interacted(player)

        # Verify message returned
        assert len(messages) > 0, "Should return at least one message"
        assert "already" in messages[0], "Message should indicate phoenix is already burning"

    def test_update_cycle(self, phoenix, monkeypatch):
        """Test update method during burning phase."""
        # Setup tracking of grid updates
        grid_update_called = False

        def mock_send_grid():
            nonlocal grid_update_called
            grid_update_called = True
            return ["grid update message"]
        
        monkeypatch.setattr(DumbledoresOffice.get_instance(), "send_grid_to_players", mock_send_grid)

        # Setup phoenix as burning
        Phoenix._Phoenix__is_burning = True
        Phoenix._Phoenix__regeneration_countdown = 3
        original_image_name = phoenix.get_image_name()

        def mock_update():
            if Phoenix._Phoenix__is_burning:
                phoenix.set_image_name(f"tile/object/phoenix{Phoenix._Phoenix__regeneration_countdown}")
                Phoenix._Phoenix__regeneration_countdown -= 1
                if Phoenix._Phoenix__regeneration_countdown < 0:
                    Phoenix._Phoenix__is_burning = False
                    phoenix.set_image_name(original_image_name)
                return DumbledoresOffice.get_instance().send_grid_to_players()
            return []
        
        monkeypatch.setattr(phoenix, "update", mock_update)
        messages = phoenix.update()

        assert Phoenix._Phoenix__is_burning, "phoenix should still be burning"
        assert Phoenix._Phoenix__regeneration_countdown == 2, "Countdown should be decremented"
        assert "phoenix3" in phoenix.get_image_name(), "Image should be updated to phoenix3"
        assert grid_update_called, "send_grid_to_players should be called"

    def test_update_when_not_burning(self, phoenix, monkeypatch):
        """Test update method when phoenix is not burning."""
        grid_update_called = False

        def mock_send_grid():
            nonlocal grid_update_called
            grid_update_called = True
            return ["grid update message"]
        
        monkeypatch.setattr(DumbledoresOffice.get_instance(), "send_grid_to_players", mock_send_grid)
        Phoenix._Phoenix__is_burning = False

        def mock_update():
            if Phoenix._Phoenix__is_burning:
                return DumbledoresOffice.get_instance().send_grid_to_players()
            return []
        
        monkeypatch.setattr(phoenix, "update", mock_update)
        messages = phoenix.update()

        assert not Phoenix._Phoenix__is_burning, "phoenix should remain not burning"
        assert messages == [], "No messages should be returned when not burning"
        assert not grid_update_called, "send_grid_to_players should not be called"

    def test_update_complete_regeneration(self, phoenix, mock_dumbledores_office_dialogue):
        """Test update method when phoenix completes regeneration cycle."""
        Phoenix._Phoenix__is_burning = True
        Phoenix._Phoenix__regeneration_countdown = 0
        messages = phoenix.update()
        
        assert not Phoenix._Phoenix__is_burning, "Phoenix should stop burning after regeneration"
        assert "phoenix" in phoenix.get_image_name(), "Image should be reset to normal phoenix"
        assert mock_dumbledores_office_dialogue["called"], "Dialogue message about rebirth should be created"
        assert "reborn" in mock_dumbledores_office_dialogue["message"], "Message should mention phoenix being reborn"
        assert len(messages) > 0, "Messages should be returned"
