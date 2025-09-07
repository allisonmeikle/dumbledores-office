import pytest
from typing import TYPE_CHECKING, List

from ..imports import *
from ..dumbledores_office import DumbledoresOffice, Rug
from ..house import House

if TYPE_CHECKING:
    from coord import Coord
    from message import Message, ServerMessage
    from Player import HumanPlayer

class TestRug:
    """
    Test suite for the Rug class.
    Tests Rug's implementation of the HouseObserver interface and behavior when house changes.
    """

    @pytest.fixture(autouse=True)
    def setup_environment(self, monkeypatch):
        """Setup necessary environment variables for tests."""
        # Sets up environment variables needed for API calls in the background
        monkeypatch.setenv("GITHUB_LOGIN", "test_user")
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")

    @pytest.fixture
    def rug(self):
        """Fixture to create a Rug instance for testing."""
        # Creates a fresh Rug instance for each test
        return Rug()

    @pytest.fixture
    def mock_dumbledores_office(self, monkeypatch):
        """Fixture to mock DumbledoresOffice methods."""
        dumbledores_office = DumbledoresOffice.get_instance()

        # Track calls to send_grid_to_players
        tracker = {"send_grid_called": False}

        def mock_send_grid():
            tracker["send_grid_called"] = True
            return ["mocked grid message"]

        # Apply mock
        monkeypatch.setattr(dumbledores_office, "send_grid_to_players", mock_send_grid)

        # Mock the get_instance method
        def mock_get_instance():
            return dumbledores_office

        monkeypatch.setattr(DumbledoresOffice, "get_instance", mock_get_instance)
        return tracker

    # Test cases

    def test_rug_initialization(self, rug):
        """Test that Rug initializes with correct default values."""
        # Assert default image name includes "rug_neutral"
        assert "rug_neutral" in rug.get_image_name(), "rug should initialize with neutral image"
        assert rug.get_z_index() == -1, "rug should have z-index of -1"
        assert rug.is_passable(), "rug should be passable by default"

    def test_update_house_to_gryffindor(self, rug, mock_dumbledores_office):
        """Test that update_house changes rug to Gryffindor theme."""
        # Act - update to Gryffindor house
        messages = rug.update_house(House.GRYFFINDOR)

        # Assert: verify image update, grid update call, and messages returned
        assert "rug_gryffindor" in rug.get_image_name(), "rug image should change to Gryffindor theme"
        assert mock_dumbledores_office["send_grid_called"], "send_grid_to_players should be called"
        assert len(messages) > 0, "update_house should return messages from send_grid_to_players"

    def test_update_house_to_hufflepuff(self, rug, mock_dumbledores_office):
        """Test that update_house changes rug to Hufflepuff theme."""
        # Act - update to Hufflepuff house
        messages = rug.update_house(House.HUFFLEPUFF)

        # Assert: verify image update, grid update call, and messages returned
        assert "rug_hufflepuff" in rug.get_image_name(), "rug image should change to Hufflepuff theme"
        assert mock_dumbledores_office["send_grid_called"], "send_grid_to_players should be called"
        assert len(messages) > 0, "update_house should return messages from send_grid_to_players"

    def test_update_house_to_ravenclaw(self, rug, mock_dumbledores_office):
        """Test that update_house changes rug to Ravenclaw theme."""
        # Act - update to Ravenclaw house
        messages = rug.update_house(House.RAVENCLAW)

        # Assert: verify image update, grid update call, and messages returned
        assert "rug_ravenclaw" in rug.get_image_name(), "rug image should change to Ravenclaw theme"
        assert mock_dumbledores_office["send_grid_called"], "send_grid_to_players should be called"
        assert len(messages) > 0, "update_house should return messages from send_grid_to_players"

    def test_update_house_to_slytherin(self, rug, mock_dumbledores_office):
        """Test that update_house changes rug to Slytherin theme."""
        # Act - update to Slytherin house
        messages = rug.update_house(House.SLYTHERIN)

        # Assert: verify image update, grid update call, and messages returned
        assert "rug_slytherin" in rug.get_image_name(), "rug image should change to Slytherin theme"
        assert mock_dumbledores_office["send_grid_called"], "send_grid_to_players should be called"
        assert len(messages) > 0, "update_house should return messages from send_grid_to_players"

    def test_update_house_to_null(self, rug, mock_dumbledores_office):
        """Test that update_house changes rug back to neutral when house is None."""
        # First, set to a house to verify change
        rug.update_house(House.GRYFFINDOR)

        # Reset the tracker
        mock_dumbledores_office["send_grid_called"] = False

        # Act - update to None
        messages = rug.update_house(None)

        # Assert: verify image reverts, grid update call, and messages returned
        assert "rug_neutral" in rug.get_image_name(), "rug image should change back to neutral theme"

        assert mock_dumbledores_office["send_grid_called"], "send_grid_to_players should be called"

        assert len(messages) > 0, "update_house should return messages from send_grid_to_players"

    def test_multiple_house_changes(self, rug, mock_dumbledores_office):
        """Test that update_house handles multiple house changes correctly."""
        # Update through all houses to ensure transitions work
        rug.update_house(House.GRYFFINDOR)
        assert "rug_gryffindor" in rug.get_image_name(), "rug should change to Gryffindor first"

        rug.update_house(House.HUFFLEPUFF)
        assert "rug_hufflepuff" in rug.get_image_name(), "rug should change to Hufflepuff second"

        rug.update_house(House.RAVENCLAW)
        assert "rug_ravenclaw" in rug.get_image_name(), "rug should change to Ravenclaw third"

        rug.update_house(House.SLYTHERIN)
        assert "rug_slytherin" in rug.get_image_name(), "rug should change to Slytherin fourth"

        rug.update_house(None)
        assert "rug_neutral" in rug.get_image_name(), "rug should change back to neutral last"

    def test_rug_added_as_house_observer(self, monkeypatch):
        """Test that rug is added as a house observer when office is initialized."""
        # Track observer additions
        tracker = {"observers_added": []}

        original_add_house_observer = DumbledoresOffice.add_house_observer

        def mock_add_house_observer(self, observer):
            tracker["observers_added"].append(observer)
            # Call original to maintain functionality
            original_add_house_observer(self, observer)

        # Apply mock
        monkeypatch.setattr(DumbledoresOffice, "add_house_observer", mock_add_house_observer)

        # Create a fresh DumbledoresOffice to trigger initialization
        office = DumbledoresOffice()

        # Check if any Rug observer was added
        rug_observers = [obs for obs in tracker["observers_added"] if isinstance(obs, Rug)]
        assert len(rug_observers) > 0, "At least one rug should be added as house observer"
