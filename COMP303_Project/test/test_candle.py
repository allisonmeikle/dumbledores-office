import pytest
from typing import TYPE_CHECKING

from ..imports import *
from ..dumbledores_office import DumbledoresOffice, Candle, MapObject

if TYPE_CHECKING:
    from coord import Coord
    from message import Message
    from Player import HumanPlayer


class TestCandle:
    """
    Test suite for the candle class.
    Tests the initialization and behavior of the Candle implementation of MapObject.
    """

    @pytest.fixture(autouse=True)
    def setup_environment(self, monkeypatch):
        """Setup necessary environment variables for tests."""
        # sets up environment variables needed for API calls in the background
        monkeypatch.setenv("GITHUB_LOGIN", "test_user")
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")

    @pytest.fixture
    def mock_get_tilemap(self, monkeypatch):
        """Fixture to mock the _get_tilemap method of MapObject."""
        def mock_get_tilemap(*args, **kwargs):
            # return dummy values suitable for testing
            return [[None]], 1, 1

        # apply the mock
        monkeypatch.setattr(MapObject, "_get_tilemap", mock_get_tilemap)

        return None  # No need to return anything, just applying the monkeypatch

    @pytest.fixture
    def default_candle(self, mock_get_tilemap):
        """Fixture to create a candle instance with default parameters for testing."""
        # creates a fresh candle instance for each test
        return Candle()

    @pytest.fixture
    def custom_candle(self, mock_get_tilemap):
        """Fixture to create a candle instance with custom parameters for testing."""
        # creates a candle with custom initialization parameters
        return Candle("candelabrum_small_2", True, 2)

    @pytest.fixture
    def mock_dumbledores_office(self, monkeypatch):
        """
        Fixture to mock DumbledoresOffice.get_instance().send_grid_to_players().
        Creates a tracker to monitor calls to send_grid_to_players().
        """
        # Create a mock for DumbledoresOffice
        office = DumbledoresOffice.get_instance()

        # Create a tracker to monitor send_grid_to_players calls
        office_tracker = {
            "send_grid_to_players_called": False,
            "send_grid_call_count": 0,
            "messages": ["test message 1", "test message 2"]  # Default test messages
        }

        # Mock the send_grid_to_players method
        def mock_send_grid():
            office_tracker["send_grid_to_players_called"] = True
            office_tracker["send_grid_call_count"] += 1
            return office_tracker["messages"]

        # Apply the mock
        monkeypatch.setattr(office, "send_grid_to_players", mock_send_grid)

        return office_tracker

    # INITIALIZATION TESTS

    def test_default_candle_initialization(self, default_candle):
        """Test that the candle is properly initialized with default values."""
        # Verify the default image name
        assert default_candle.get_image_name() == "tile/decor/candle/candelabrum_small_1", "Candle should initialize with the default image name"
        
        # Verify the passable flag
        assert default_candle.is_passable() is False, "Candle should initialize as not passable by default"
        
        # Verify the z-index
        assert default_candle.get_z_index() == 1, "Candle should initialize with default z-index of 1"
        
        # Verify the image name index
        assert default_candle._Candle__image_name_index == 1, "Candle should initialize with image name index of 1"

    def test_custom_candle_initialization(self, custom_candle):
        """Test that the candle can be initialized with custom parameters."""
        # Verify the custom image name
        assert custom_candle.get_image_name() == "tile/decor/candle/candelabrum_small_2", "Candle should use custom image name"
        
        # Verify the custom passable flag
        assert custom_candle.is_passable() is True, "Candle should be passable when set to True"
        
        # Verify the custom z-index
        assert custom_candle.get_z_index() == 2, "Candle should use custom z-index"

    # UPDATE METHOD TESTS

    def test_update_increments_image_index(self, default_candle):
        """Test that update() increments the image name index and cycles through values 0-5."""
        # Get the initial index
        initial_index = default_candle._Candle__image_name_index

        # Call update
        default_candle.update()

        # Verify the index was incremented
        expected_index = (initial_index + 1) % 6
        assert default_candle._Candle__image_name_index == expected_index, f"Update should increment the image index from {initial_index} to {expected_index}"

    def test_update_changes_image_name(self, default_candle):
        """Test that update() changes the image name based on the new index."""
        # Set a specific starting index for consistent testing
        default_candle._Candle__image_name_index = 1
        initial_image = default_candle.get_image_name()

        # Call update
        default_candle.update()

        # Verify the image name was changed
        assert default_candle.get_image_name() == "tile/decor/candle/candelabrum_small_2", "Update should change the image name to match the new index"
        assert default_candle.get_image_name() != initial_image, "Image name should be different after update"

    def test_update_cycles_through_all_images(self, default_candle):
        """Test that update() cycles through all 6 images in sequence."""
        # Set a starting index for consistent testing
        default_candle._Candle__image_name_index = 0

        # Collect all image names through a full cycle
        image_names    = []
        expected_indices = []

        for i in range(6):
            # Update and collect the image name
            default_candle.update()
            image_names.append(default_candle.get_image_name())
            expected_indices.append((i + 1) % 6)

        # Verify we got the expected sequence of image names
        # verify we got the expected sequence of image names
        expected_names = [
            f"tile/decor/candle/candelabrum_small_{i}" for i in expected_indices
        ]
        
        assert image_names == expected_names, "Update should cycle through images in the correct sequence"

    def test_update_wraps_around_at_index_5(self, default_candle):
        """Test that the image index wraps around from 5 back to 0."""
        # Set index to 5 (just before wrap-around)
        default_candle._Candle__image_name_index = 5

        # Call update
        default_candle.update()

        # Verify wrap-around to 0
        assert default_candle._Candle__image_name_index == 0, "Index should wrap from 5 to 0"
        assert default_candle.get_image_name() == "tile/decor/candle/candelabrum_small_0", "Image name should reflect the wrapped index"

    def test_update_returns_grid_messages(self, default_candle, mock_dumbledores_office):
        """Test that update() calls send_grid_to_players() and returns its messages."""
        # Call update
        messages = default_candle.update()

        # Verify send_grid_to_players was called
        assert mock_dumbledores_office["send_grid_to_players_called"], "Update should call send_grid_to_players"
        
        # Verify the messages were returned
        assert messages == mock_dumbledores_office["messages"], "Update should return messages from send_grid_to_players"
    def test_update_calls_send_grid_to_players_once(self, default_candle, mock_dumbledores_office):
        """Test that update() calls send_grid_to_players() exactly once."""
        # Call update
        default_candle.update()

        # Verify send_grid_to_players was called exactly once
        assert mock_dumbledores_office["send_grid_call_count"] == 1, "Update should call send_grid_to_players exactly once"

    # INHERITANCE TESTS

    def test_candle_is_instance_of_map_object(self, default_candle):
        """Test that Candle is properly inheriting from MapObject."""
        assert isinstance(default_candle, MapObject), "Candle should be an instance of MapObject"

    def test_candle_inherits_map_object_methods(self, default_candle):
        """Test that Candle inherits and can use MapObject methods."""
        # Test position getting/setting (inherited from MapObject)
        position = Coord(5, 7)
        default_candle.set_position(position)

        assert default_candle.get_position() == position, "Candle should inherit position methods from MapObject"