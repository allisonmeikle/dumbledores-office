import pytest
from typing import TYPE_CHECKING

from ..imports import *
from ..entryway import ExampleHouse, SinglePlayerDoor, CandleLobby, DobbyDecor
from ..dumbledores_office import DumbledoresOffice, Decor
from ..house import House

if TYPE_CHECKING:
    from coord import Coord
    from message import Message, DialogueMessage, SoundMessage, ServerMessage
    from maps.base import Map
    from tiles.map_objects import Door, MapObject
    from Player import HumanPlayer


class TestExampleHouse:
    @pytest.fixture(autouse=True)
    def setup_environment(self, monkeypatch):
        """Setup necessary environment variables for tests."""
        # Sets up environment variables needed for api calls in the background
        monkeypatch.setenv("GITHUB_LOGIN", "test_user")
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")

    @pytest.fixture
    def example_house(self):
        """Fixture to create an ExampleHouse instance for testing."""
        # Create a fresh ExampleHouse for each test
        return ExampleHouse.get_instance()

    @pytest.fixture
    def player(self):
        """Fixture to create a player for testing."""
        # Create a player with default state
        player = HumanPlayer("test_player")
        return player

    @pytest.fixture
    def mock_position_observer(self, monkeypatch):
        """Fixture to mock position observers and track updates."""
        # Tracker for position observer updates
        update_tracker = {
            "called": False,
            "position": None
        }

        class MockPositionObserver:
            def update_position(self, position):
                update_tracker["called"] = True
                update_tracker["position"] = position
                return []

        # Create observer instance
        observer = MockPositionObserver()

        return observer, update_tracker

    def test_singleton_instance(self):
        """Test that ExampleHouse follows the singleton pattern."""
        # Arrange - create two instances
        instance1 = ExampleHouse.get_instance()
        instance2 = ExampleHouse.get_instance()

        # Assert - verify they're the same instance
        assert instance1 is instance2, "ExampleHouse should follow singleton pattern"

    def test_get_name(self, example_house):
        """Test that get_name returns the correct name."""
        # Act
        result = example_house.get_name()

        # Assert
        assert result == "EXAMPLE HOUSE", "get_name should return 'EXAMPLE HOUSE'"

    def test_get_player_empty_room(self, example_house, monkeypatch):
        """Test that get_player returns nullplayer when room is empty."""
        # Arrange - mock get_human_players to return empty list
        monkeypatch.setattr(example_house, "get_human_players", lambda: [])

        # Act
        result = example_house.get_player()

        # Assert
        assert result.__class__.__name__ == "NullPlayer", "get_player should return nullplayer when room is empty"

    def test_get_player_with_players(self, example_house, player, monkeypatch):
        """Test that get_player returns the first player when room has players."""
        # Arrange - mock get_human_players to return list with player
        monkeypatch.setattr(example_house, "get_human_players", lambda: [player])

        # Act
        result = example_house.get_player()

        # Assert
        assert result == player, "get_player should return the first player in the room"

    def test_get_objects(self, example_house):
        """Test that get_objects returns the expected room objects."""
        # Act
        objects = example_house.get_objects()

        # Assert
        assert isinstance(objects, list), "get_objects should return a list"
        assert len(objects) > 0, "get_objects should return non-empty list"

        # Verify each object is a tuple of (MapObject, Coord)
        for obj in objects:
            assert isinstance(obj, tuple), "Each element should be a tuple"
            assert len(obj) == 2, "Each tuple should have 2 elements"
            assert isinstance(obj[0], MapObject), "First element should be a MapObject"
            assert isinstance(obj[1], Coord), "Second element should be a Coord"

        # Verify key objects are present
        object_types = [type(obj[0]) for obj in objects]
        assert SinglePlayerDoor in object_types, "SinglePlayerDoor should be in objects"
        assert Door in object_types, "Door should be in objects"
        assert Decor in object_types, "Decor should be in objects"
        assert DobbyDecor in object_types, "DobbyDecor should be in objects"
        assert CandleLobby in object_types, "CandleLobby should be in objects"

    def test_add_position_observer(self, example_house, mock_position_observer):
        """Test adding a position observer."""
        # Arrange
        observer, tracker = mock_position_observer
        player_pos = Coord(5, 5)

        # Mock get_human_players to return list with player at specific position
        mock_player = HumanPlayer("mock_player")
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(mock_player, "get_current_position", lambda: player_pos)
        monkeypatch.setattr(example_house, "get_human_players", lambda: [mock_player])

        # Act
        example_house.add_position_observer(observer)

        # Assert
        assert observer in example_house._ExampleHouse__position_observers, "Observer should be added to position_observers set"
        assert tracker["called"], "update_position should be called when adding observer"
        assert tracker["position"] == player_pos, "Observer should be updated with current player position"

    def test_remove_position_observer(self, example_house, mock_position_observer):
        """Test removing a position observer."""
        # Arrange
        observer, _ = mock_position_observer
        example_house.add_position_observer(observer)

        # Act
        example_house.remove_position_observer(observer)

        # Assert
        assert observer not in example_house._ExampleHouse__position_observers, "Observer should be removed from position_observers set"

    def test_notify_position_observers(self, example_house, mock_position_observer):
        """Test notifying position observers."""
        # Arrange
        observer, tracker = mock_position_observer
        example_house.add_position_observer(observer)
        tracker["called"] = False  # Reset tracker
        new_position = Coord(7, 7)

        # Act
        example_house.notify_position_observers(new_position)

        # Assert
        assert tracker["called"], "update_position should be called when notifying observers"
        assert tracker["position"] == new_position, "Observer should be updated with new position"

    def test_move_notifies_observers(self, example_house, mock_position_observer, monkeypatch):
        """Test that move notifies observers after movement."""
        # Arrange
        observer, tracker = mock_position_observer
        example_house.add_position_observer(observer)
        tracker["called"] = False  # Reset tracker
        player = HumanPlayer("test_player")
        new_position = Coord(8, 8)

        # Mock super().move to return empty list and simulate movement
        def mock_super_move(self, p, d):
            p._current_position = new_position  # Simulate movement
            return []

        monkeypatch.setattr(Map, "move", mock_super_move)

        # Act
        example_house.move(player, "up")

        # Assert
        assert tracker["called"], "Position observers should be notified after move"
        assert tracker["position"] == new_position, "Observers should be updated with player's new position"


class TestSinglePlayerDoor:
    @pytest.fixture
    def door(self):
        """Fixture to create a SinglePlayerDoor for testing."""
        return SinglePlayerDoor('arch_bottom', 'Dumbledores Office')

    @pytest.fixture
    def player(self):
        """Fixture to create a player for testing."""
        return HumanPlayer("test_player")

    @pytest.fixture
    def mock_office(self, monkeypatch):
        """Fixture to mock Dumbledore's office."""
        office = DumbledoresOffice.get_instance()

        # Tracker for office method calls
        tracker = {
            "is_occupied_called": False,
            "is_occupied_return": False,
            "update_theme_called": False,
            "update_theme_house": None
        }

        # Mock is_occupied
        def mock_is_occupied():
            tracker["is_occupied_called"] = True
            return tracker["is_occupied_return"]

        # Mock update_theme
        def mock_update_theme(house):
            tracker["update_theme_called"] = True
            tracker["update_theme_house"] = house
            return []

        # Mock get_player_name
        def mock_get_player_name():
            return "dumbledore"

        # Apply mocks
        monkeypatch.setattr(office, "is_occupied", mock_is_occupied)
        monkeypatch.setattr(office, "update_theme", mock_update_theme)
        monkeypatch.setattr(office, "get_player_name", mock_get_player_name)

        return office, tracker

    @pytest.fixture
    def mock_door_parent(self, monkeypatch):
        """Fixture to mock door parent class player_entered method."""
        # Tracker for door parent method calls
        tracker = {
            "player_entered_called": False,
            "player_entered_return": ["mock message"]
        }

        # Mock parent player_entered
        def mock_player_entered(self, player):
            tracker["player_entered_called"] = True
            return tracker["player_entered_return"]

        # Using Door class from imports
        monkeypatch.setattr(Door, "player_entered", mock_player_entered)

        return tracker

    def test_player_entered_office_occupied(self, door, player, mock_office, mock_door_parent):
        """Test player_entered when office is occupied."""
        office, tracker = mock_office
        tracker["is_occupied_return"] = True
        messages = door.player_entered(player)

        assert tracker["is_occupied_called"], "Door should check if office is occupied"
        assert not mock_door_parent["player_entered_called"], "Parent player_entered should not be called when office is occupied"
        assert len(messages) == 1, "One message should be returned when office is occupied"        
        assert isinstance(messages[0], ServerMessage), "Message should be a ServerMessage"
        message_data = messages[0]._get_data()
        # verify the message text is contained in some part of the message data
        assert any("Sorry, Dumbledore is currently busy" in str(value) 
                for value in message_data.values()), "Message should indicate office is occupied"

    def test_player_entered_with_house(self, door, player, mock_office, mock_door_parent):
        """Test player_entered when player has a house."""
        # set office not occupied and player with house state
        office, tracker = mock_office
        tracker["is_occupied_return"] = False
        player.set_state("House", "GRYFFINDOR")
        
        # mock the needs_theme_update method
        tracker["needs_theme_update_called"] = False
        def mock_needs_theme_update(needs_update):
            tracker["needs_theme_update_called"] = True
            tracker["needs_theme_update_value"] = needs_update
        # monkeypatch the method
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(office, "needs_theme_update", mock_needs_theme_update)

        messages = door.player_entered(player)

        assert tracker["is_occupied_called"], "Door should check if office is occupied"
        assert mock_door_parent["player_entered_called"], "Parent player_entered should be called when office is not occupied"
        assert tracker["needs_theme_update_called"], "Door should call needs_theme_update"
        assert tracker["needs_theme_update_value"], "Door should set needs_theme_update to True"
        assert messages == mock_door_parent["player_entered_return"], "Messages from parent should be returned"
        assert player.get_state("sorting_in_progress") == False, "Player sorting_in_progress should be set to False"

    def test_player_entered_without_house(self, door, player, mock_office, mock_door_parent):
        """Test player_entered when player has no house."""
        # set office not occupied and player with no house state
        office, tracker = mock_office
        tracker["is_occupied_return"] = False
        player.set_state("House", "")
        
        # mock the needs_theme_update method
        tracker["needs_theme_update_called"] = False
        
        def mock_needs_theme_update(needs_update):
            tracker["needs_theme_update_called"] = True
            tracker["needs_theme_update_value"] = needs_update
        
        # monkeypatch the method
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(office, "needs_theme_update", mock_needs_theme_update)

        messages = door.player_entered(player)
        
        assert tracker["is_occupied_called"], "Door should check if office is occupied"
        assert mock_door_parent["player_entered_called"], "Parent player_entered should be called when office is not occupied"
        assert tracker["needs_theme_update_called"], "Door should call needs_theme_update"
        assert tracker["needs_theme_update_value"], "Door should set needs_theme_update to True"
        assert messages == mock_door_parent["player_entered_return"], "Messages from parent should be returned"
        assert player.get_state("sorting_in_progress") == False, "Player sorting_in_progress should be set to False"

class TestCandleLobby:
    @pytest.fixture
    def candle(self):
        """Fixture to create a CandleLobby for testing."""
        return CandleLobby()

    @pytest.fixture
    def mock_example_house(self, monkeypatch):
        """Fixture to mock ExampleHouse for the candle updates."""
        example_house = ExampleHouse.get_instance()

        # Mock send_grid_to_players
        monkeypatch.setattr(example_house, "send_grid_to_players", lambda: ["mock_grid_message"])

        return example_house

    def test_candle_initialization(self, candle):
        """Test candle initialization."""
        # Assert
        assert candle.get_image_name() == "tile/decor/candle/candelabrum_small_1", "Candle should have correct initial image"
        assert candle._CandleLobby__image_name_index == 1, "Candle should have correct initial image index"

    def test_candle_update(self, candle, mock_example_house):
        """Test candle update changes image and returns grid update."""
        # Act
        messages = candle.update()

        # Assert
        assert candle._CandleLobby__image_name_index == 2, "Image index should be incremented"
        assert candle.get_image_name() == "tile/decor/candle/candelabrum_small_2", "Image should be updated"
        assert messages == ["mock_grid_message"], "Update should return grid update message"

    def test_candle_update_cycles_images(self, candle, mock_example_house):
        """Test candle update cycles through all images."""
        # Arrange - set index to last value
        candle._CandleLobby__image_name_index = 5

        # Act
        messages = candle.update()

        # Assert
        assert candle._CandleLobby__image_name_index == 0, "Image index should cycle back to 0"
        assert candle.get_image_name() == "tile/decor/candle/candelabrum_small_0", "Image should be updated"


class TestDobbyDecor:
    @pytest.fixture
    def active_positions(self):
        """Fixture to create test active positions."""
        return [
            Coord(7, 4),   # Left
            Coord(9, 4),   # Right
            Coord(8, 3),   # Above
            Coord(8, 5)    # Below
        ]

    @pytest.fixture
    def dobby(self, active_positions):
        """Fixture to create a Dobby instance for testing."""
        return DobbyDecor("dobby", active_positions)

    @pytest.fixture
    def player(self):
        """Fixture to create a player for testing."""
        return HumanPlayer("test_player")

    @pytest.fixture
    def mock_example_house(self, monkeypatch, player):
        """Fixture to mock ExampleHouse for Dobby updates."""
        example_house = ExampleHouse.get_instance()

        # Tracker for method calls
        tracker = {
            "get_player_called": False
        }

        # Mock get_player
        def mock_get_player():
            tracker["get_player_called"] = True
            return player

        # Apply mocks
        monkeypatch.setattr(example_house, "get_player", mock_get_player)

        return example_house, tracker

    def test_dobby_initialization(self, dobby, active_positions):
        """Test Dobby initialization."""
        # Assert
        assert dobby.get_image_name() == "tile/object/dobby", "Dobby should have correct image"
        # Access active_positions attribute without using name mangling
        assert getattr(dobby, "_DobbyDecor__active_positions") == active_positions, "Dobby should store active positions"
        assert getattr(dobby, "_DobbyDecor__has_interacted") is False, "Dobby should start with has_interacted as False"

    def test_dobby_initialization_default_positions(self):
        """Test Dobby initialization with default positions."""
        # Arrange
        dobby = DobbyDecor()

        # Assert
        assert len(getattr(dobby, "_DobbyDecor__active_positions")) == 4, "Dobby should have 4 default active positions"

    def test_update_position_inactive(self, dobby, active_positions):
        """Test update_position when player is not in active position."""
        # Arrange
        inactive_position = Coord(1, 1)  # Not in active positions

        # Act
        messages = dobby.update_position(inactive_position)

        # Assert
        assert messages == [], "No messages should be returned for inactive position"
        assert getattr(dobby, "_DobbyDecor__has_interacted") is False, "has_interacted should remain False"

    def test_update_position_active_first_time(self, dobby, active_positions, mock_example_house):
        """Test update_position when player is in active position for first time."""
        # Arrange
        example_house, tracker = mock_example_house
        active_position = active_positions[0]

        # Act
        messages = dobby.update_position(active_position)

        # Assert
        assert tracker["get_player_called"], "get_player should be called"
        assert getattr(dobby, "_DobbyDecor__has_interacted") is True, "has_interacted should be set to True"
        assert len(messages) == 2, "Two messages should be returned (sound and dialogue)"
        assert isinstance(messages[0], SoundMessage), "First message should be a sound message"
        assert isinstance(messages[1], DialogueMessage), "Second message should be a dialogue message"
        assert "dobby_free.mp3" in messages[0]._get_data()['sound_path'], "Sound message should contain correct sound file"
        assert "Dobby is freeeeeeeeeeeeeee" in messages[1]._get_data()['dialogue_text'], "Dialogue message should contain correct text"

    def test_update_position_active_subsequent(self, dobby, active_positions, mock_example_house):
        """Test update_position when player is in active position after first interaction."""
        # Arrange
        example_house, tracker = mock_example_house
        active_position = active_positions[0]
        setattr(dobby, "_DobbyDecor__has_interacted", True)  # Already interacted

        # Act
        messages = dobby.update_position(active_position)

        # Assert
        assert getattr(dobby, "_DobbyDecor__has_interacted") is True, "has_interacted should remain True"
        assert messages == [], "No messages should be returned for subsequent interaction"
