import pytest
from typing import TYPE_CHECKING

from ..imports import *
from ..dumbledores_office import DumbledoresOffice, Decor, MapObject

if TYPE_CHECKING:
    from coord import Coord
    from Player import HumanPlayer


class TestDecor:
    """
    Test suite for the Decor class.
    Tests the initialization and behavior of the Decor implementation of MapObject.
    """

    @pytest.fixture(autouse=True)
    def setup_environment(self, monkeypatch):
        """Setup necessary environment variables for tests."""
        # Sets up environment variables needed for API calls in the background
        monkeypatch.setenv("GITHUB_LOGIN", "test_user")
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")

    @pytest.fixture
    def mock_tilemap(self, monkeypatch):
        """
        Fixture to mock the _get_tilemap method of MapObject.
        This prevents file not found errors during tests.
        """
        def mock_get_tilemap(*args, **kwargs):
            # Return dummy values suitable for testing
            return [[None]], 1, 1

        # Apply the mock
        monkeypatch.setattr(MapObject, "_get_tilemap", mock_get_tilemap)

    @pytest.fixture
    def default_decor(self, mock_tilemap):
        """Fixture to create a Decor instance with default parameters."""
        # Creates a fresh Decor instance with default values
        return Decor("desk")

    @pytest.fixture
    def custom_decor(self, mock_tilemap):
        """Fixture to create a Decor instance with custom parameters."""
        # Creates a Decor with custom passable and z-index values
        return Decor("right_wall", True, 2)

    # Initialization tests

    def test_decor_initialization_with_defaults(self, default_decor):
        """Test that a Decor object is properly initialized with default values."""
        # Verify the image name format
        assert default_decor.get_image_name() == "tile/decor/desk", "Decor should have correct image name format"
        # Verify default passable flag (False)
        assert default_decor.is_passable() is False, "Decor should initialize as not passable by default"
        # Verify default z-index (0)
        assert default_decor.get_z_index() == 0, "Decor should initialize with default z-index of 0"

    def test_decor_initialization_with_custom_values(self, custom_decor):
        """Test that a Decor object can be initialized with custom values."""
        # Verify custom image name format
        assert custom_decor.get_image_name() == "tile/decor/right_wall", "Decor should have correct image name format with custom name"
        # Verify custom passable flag (True)
        assert custom_decor.is_passable() is True, "Decor should use custom passable flag"
        # Verify custom z-index (2)
        assert custom_decor.get_z_index() == 2, "Decor should use custom z-index"

    # Property tests

    def test_multiple_decor_instances_independence(self, mock_tilemap):
        """Test that multiple Decor instances maintain independent state."""
        # Create two different Decor instances
        decor1 = Decor("desk", False, 0)
        decor2 = Decor("front_wall_left", True, 1)
        # Verify they have independent properties
        assert decor1.get_image_name() == "tile/decor/desk", "First decor should maintain its image name"
        assert decor2.get_image_name() == "tile/decor/front_wall_left", "Second decor should maintain its image name"
        assert decor1.is_passable() is False, "First decor should maintain its passable state"
        assert decor2.is_passable() is True, "Second decor should maintain its passable state"
        assert decor1.get_z_index() == 0, "First decor should maintain its z-index"
        assert decor2.get_z_index() == 1, "Second decor should maintain its z-index"

    def test_setting_property_values(self, default_decor):
        """Test that Decor properties can be modified after initialization."""
        # Initial state verification
        assert default_decor.get_image_name() == "tile/decor/desk"
        assert default_decor.is_passable() is False
        assert default_decor.get_z_index() == 0
        # Modify properties
        default_decor.set_image_name("tile/decor/new_desk")
        default_decor.set_passability(True)
        default_decor.set_z_index(3)
        # Verify changes took effect
        assert default_decor.get_image_name() == "tile/decor/new_desk", "Image name should be updatable"
        assert default_decor.is_passable() is True, "Passable flag should be updatable"
        assert default_decor.get_z_index() == 3, "Z-index should be updatable"

    # Inheritance tests

    def test_decor_is_instance_of_map_object(self, default_decor):
        """Test that Decor is properly inheriting from MapObject."""
        assert isinstance(default_decor, MapObject), "Decor should be an instance of MapObject"

    def test_decor_inherits_map_object_methods(self, default_decor):
        """Test that Decor inherits and can use MapObject methods."""
        # Test position getting/setting (inherited from MapObject)
        position = Coord(5, 7)
        default_decor.set_position(position)
        assert default_decor.get_position() == position, "Decor should inherit position methods from MapObject"
        # Test that player_entered returns empty list (default inherited behavior)
        mock_player = object()  # Just a placeholder
        result = default_decor.player_entered(mock_player)
        assert result == [], "Decor should inherit default player_entered behavior returning empty list"
