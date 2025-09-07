import pytest
from typing import TYPE_CHECKING

from ..imports import *
from ..dumbledores_office import DumbledoresOffice, SortingHat, InteriorDoor, MapObject, Door
from ..house import House

if TYPE_CHECKING:
    from coord import Coord
    from message import Message, ServerMessage
    from Player import HumanPlayer


class TestInteriorDoor:
    """
    Test suite for the InteriorDoor class.
    Tests the behavior of the InteriorDoor implementation that extends the Door class.
    """

    @pytest.fixture(autouse=True)
    def setup_environment(self, monkeypatch):
        """Setup necessary environment variables for tests."""
        # Sets up environment variables needed for API calls in the background
        monkeypatch.setenv("GITHUB_LOGIN", "test_user")
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")

    @pytest.fixture
    def interior_door(self):
        """Fixture to create an InteriorDoor instance for testing."""
        # Creates a fresh InteriorDoor instance for each test
        return InteriorDoor('arch', 'Example House')

    @pytest.fixture
    def player(self):
        """Fixture to create a player for testing."""
        # Creates a clean player with default state for testing
        return HumanPlayer("test_player")

    @pytest.fixture
    def mock_sorting_hat(self, monkeypatch):
        """
        Fixture to create a mock sorting hat and track calls to its methods.

        Returns:
            Dictionary tracking calls to sorting_hat.player_left method
        """
        # Create a mock sorting hat instance
        sorting_hat = SortingHat([Coord(12, 7), Coord(12, 8)], "sorting_hat")

        # Create a tracker to monitor sorting hat method calls
        sorting_hat_tracker = {
            "player_left_called": False,
            "player_left_args": None
        }

        # Mock the player_left method
        def mock_player_left(player):
            sorting_hat_tracker["player_left_called"] = True
            sorting_hat_tracker["player_left_args"] = player
            return []

        monkeypatch.setattr(sorting_hat, "player_left", mock_player_left)

        # Mock get_obj to return our sorting hat
        def mock_get_obj(name):
            if name == "sorting_hat":
                return sorting_hat
            return None

        monkeypatch.setattr(MapObject, "get_obj", mock_get_obj)

        return sorting_hat_tracker

    @pytest.fixture
    def mock_parent_player_entered(self, monkeypatch):
        """
        Fixture to mock the player_entered method of the parent Door class.

        Returns:
            Dictionary tracking calls to Door.player_entered method
        """
        # Create a tracker to monitor door method calls
        door_tracker = {
            "super_player_entered_called": False,
            "super_player_entered_args": None,
            "super_player_entered_return": []
        }

        # Mock the super().player_entered method
        def mock_super_player_entered(self, player):
            door_tracker["super_player_entered_called"] = True
            door_tracker["super_player_entered_args"] = player
            return door_tracker["super_player_entered_return"]

        # Patch the Door.player_entered method that InteriorDoor would call via super()
        monkeypatch.setattr(Door, "player_entered", mock_super_player_entered)

        return door_tracker

    def test_player_entered_calls_sorting_hat_player_left(self, interior_door, player, mock_sorting_hat, mock_parent_player_entered):
        """Test that player_entered calls sorting_hat.player_left when sorting hat is found."""
        # Call the method under test
        interior_door.player_entered(player)

        # Verify sorting_hat.player_left was called with the player
        assert mock_sorting_hat["player_left_called"], "sorting_hat.player_left should be called"
        assert mock_sorting_hat["player_left_args"] == player, "sorting_hat.player_left should be called with the player"

    def test_player_entered_calls_super_player_entered(self, interior_door, player, mock_sorting_hat, mock_parent_player_entered):
        """Test that player_entered calls the parent Door.player_entered method."""
        # Call the method under test
        interior_door.player_entered(player)

        # Verify super().player_entered was called with the player
        assert mock_parent_player_entered["super_player_entered_called"], "super().player_entered should be called"
        assert mock_parent_player_entered["super_player_entered_args"] == player, "super().player_entered should be called with the player"

    def test_player_entered_returns_super_result(self, interior_door, player, mock_sorting_hat, mock_parent_player_entered):
        """Test that player_entered returns the result from parent Door.player_entered."""
        # Set up expected return value from super().player_entered
        expected_messages = [ServerMessage(player, "Test message")]
        mock_parent_player_entered["super_player_entered_return"] = expected_messages

        # Call the method under test
        result = interior_door.player_entered(player)

        # Verify the result is the expected messages
        assert result == expected_messages, "player_entered should return the result from super().player_entered"

    def test_player_entered_when_get_obj_returns_none(self, interior_door, player, monkeypatch, mock_parent_player_entered):
        """Test player_entered behavior when sorting_hat is not found (get_obj returns None)."""
        # Mock get_obj to return None
        def mock_get_obj(name):
            return None

        monkeypatch.setattr(MapObject, "get_obj", mock_get_obj)

        # Set up expected return value
        expected_messages = [ServerMessage(player, "Test message")]
        mock_parent_player_entered["super_player_entered_return"] = expected_messages

        # Call the method under test
        result = interior_door.player_entered(player)

        # Verify super().player_entered was still called
        assert mock_parent_player_entered["super_player_entered_called"], "super().player_entered should be called even when sorting_hat is not found"
        assert result == expected_messages, "player_entered should return the result from super().player_entered"

    def test_player_entered_when_get_obj_returns_wrong_type(self, interior_door, player, monkeypatch, mock_parent_player_entered):
        """Test player_entered behavior when get_obj returns an object of the wrong type."""
        # Create a different type of object (not a SortingHat)
        class NotASortingHat:
            pass

        # Mock get_obj to return the wrong type
        def mock_get_obj(name):
            if name == "sorting_hat":
                return NotASortingHat()
            return None

        monkeypatch.setattr(MapObject, "get_obj", mock_get_obj)

        # Set up expected return value
        expected_messages = [ServerMessage(player, "Test message")]
        mock_parent_player_entered["super_player_entered_return"] = expected_messages

        # Call the method under test
        result = interior_door.player_entered(player)

        # Verify super().player_entered was still called
        assert mock_parent_player_entered["super_player_entered_called"], "super().player_entered should be called even with wrong type"
        assert result == expected_messages, "player_entered should return the result from super().player_entered"
