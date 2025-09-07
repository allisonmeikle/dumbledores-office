import pytest
from typing import TYPE_CHECKING, Any, Literal

from ..imports import *
from ..null_player import NullPlayer
from ..dumbledores_office import DumbledoresOffice

if TYPE_CHECKING:
    from coord import Coord
    from Player import HumanPlayer
    from maps.base import Map, Message


class TestNullPlayer:
    """
    Test suite for the NullPlayer class.
    Tests the initialization and behavior of the Null Object implementation of HumanPlayer.
    """

    @pytest.fixture(autouse=True)
    def setup_environment(self, monkeypatch):
        """Setup necessary environment variables for tests."""
        # Sets up environment variables needed for API calls in the background
        monkeypatch.setenv("GITHUB_LOGIN", "test_user")
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")

    @pytest.fixture
    def null_player(self):
        """Fixture to create a NullPlayer instance for testing."""
        return NullPlayer()

    @pytest.fixture
    def mock_dumbledores_office(self, monkeypatch):
        """Fixture to mock DumbledoresOffice instance."""
        dumbledores_office = DumbledoresOffice.get_instance()

        # Store the original get_instance method
        original_get_instance = DumbledoresOffice.get_instance

        # Create a mock get_instance that returns the singleton
        def mock_get_instance():
            return dumbledores_office

        # Apply the mock
        monkeypatch.setattr(DumbledoresOffice, "get_instance", mock_get_instance)
        return dumbledores_office

    # Initialization tests

    def test_initialization(self, null_player):
        """Test that NullPlayer initializes correctly with expected defaults."""
        # Check initial state
        assert null_player.get_name() == "NullPlayer", "Name should be 'NullPlayer'"
        assert null_player.get_current_position() == Coord(0, 0), "Initial position should be (0, 0)"
        assert null_player.get_image_name() == "character/empty/up1", "Image should match the expected path"
        assert null_player.is_passable() is True, "NullPlayer should be passable"

    def test_string_representation(self, null_player):
        """Test that string representation of NullPlayer returns its name."""
        assert str(null_player) == "NullPlayer", "String representation should return player name"

    # Method behavior tests

    def test_update_position_does_nothing(self, null_player, mock_dumbledores_office):
        """Test that update_position does nothing (returns None) and position remains unchanged."""
        # Get initial position
        initial_position = null_player.get_current_position()

        # Try to update position
        result = null_player.update_position(Coord(10, 10), mock_dumbledores_office)

        # Check that position didn't change and method returned None
        assert result is None, "update_position should return None"
        assert null_player.get_current_position() == initial_position, "Position should not change"

    def test_get_current_room_returns_dumbledores_office(self, null_player, mock_dumbledores_office):
        """Test that get_current_room returns DumbledoresOffice singleton."""
        # Get current room
        current_room = null_player.get_current_room()

        # Check that it's the DumbledoresOffice singleton
        assert current_room is mock_dumbledores_office, "get_current_room should return DumbledoresOffice singleton"

    def test_get_current_map_object_returns_empty_list(self, null_player):
        """Test that get_current_map_object returns an empty list."""
        # Get current map objects
        map_objects = null_player.get_current_map_object()

        # Check that it's an empty list
        assert map_objects == [], "get_current_map_object should return an empty list"
        assert isinstance(map_objects, list), "get_current_map_object should return a list"

    def test_move_returns_empty_message_list(self, null_player):
        """Test that move returns an empty list of messages for all directions."""
        # Try moving in all directions
        directions: list[Literal['up', 'down', 'left', 'right']] = ['up', 'down', 'left', 'right']

        for direction in directions:
            # Move in direction
            messages = null_player.move(direction)
            # Check that an empty list is returned
            assert messages == [], f"move({direction}) should return an empty list"
            assert isinstance(messages, list), f"move({direction}) should return a list"

    def test_change_room_returns_empty_message_list(self, null_player, mock_dumbledores_office):
        """Test that change_room returns an empty list of messages regardless of parameters."""
        # Try changing room with various parameters
        messages = null_player.change_room(
            mock_dumbledores_office,
            msg_to_cur_room="Leaving",
            msg_to_new_room="Arriving"
        )

        # Check that an empty list is returned
        assert messages == [], "change_room should return an empty list"
        assert isinstance(messages, list), "change_room should return a list"

        # Test with different parameters to ensure consistent behavior
        messages_with_entry_point = null_player.change_room(
            mock_dumbledores_office,
            msg_to_cur_room="",
            msg_to_new_room="",
            entry_point=Coord(5, 5)
        )

        assert messages_with_entry_point == [], "change_room should return empty list with entry_point"

    # Inherited method tests

    def test_get_set_state(self, null_player):
        """Test that the player state management works correctly."""
        # Set state
        null_player.set_state("test_key", "test_value")

        # Get state
        value = null_player.get_state("test_key")

        # Check that state is correctly stored and retrieved
        assert value == "test_value", "get_state should return the value set with set_state"

        # Test default value
        nonexistent_value = null_player.get_state("nonexistent_key", "default_value")
        assert nonexistent_value == "default_value", "get_state should return default value for nonexistent keys"

    # Type verification tests

    def test_is_instance_of_human_player(self, null_player):
        """Test that NullPlayer is an instance of HumanPlayer (verifies inheritance)."""
        assert isinstance(null_player, HumanPlayer), "NullPlayer should be an instance of HumanPlayer"
