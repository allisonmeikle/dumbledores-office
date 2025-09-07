import pytest
from typing import TYPE_CHECKING, Dict, Any, cast, List

from ..imports import *
from ..dumbledores_office import DumbledoresOffice, SortingHat, Rug, ChatObject, Phoenix, Book, Bookshelf, MapObject
from ..text_bubble import TextBubble, TextBubbleImage
from ..house import House
from ..position_observer import PositionObserver
from ..house_observer import HouseObserver
from ..util import get_custom_dialogue_message

if TYPE_CHECKING:
    from coord import Coord
    from Player import HumanPlayer
    from maps.base import Message, Map
    from message import ServerMessage


class TestDumbledoresOffice:
    @pytest.fixture(autouse=True)
    def setup_environment(self, monkeypatch):
        """Setup necessary environment variables for tests."""
        # Sets up environment variables needed for api calls in the background
        monkeypatch.setenv("GITHUB_LOGIN", "test_user")
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")
        monkeypatch.setenv("OPEN_ROUTER_API_KEY", "dummy_key")

    @pytest.fixture
    def dumbledores_office(self, monkeypatch):
        """Fixture to create a clean instance of dumbledores_office for testing."""
        # Reset singleton instance to ensure clean state
        office = DumbledoresOffice.get_instance()
        # Mock send_grid_to_players to avoid side effects
        monkeypatch.setattr(office, "send_grid_to_players", lambda: [])
        monkeypatch.setattr(office, "send_message_to_players", lambda message: [])
        # Reset internal state
        office._DumbledoresOffice__current_house = None
        office._DumbledoresOffice__house_observers = set()
        office._DumbledoresOffice__position_observers = set()
        return office

    @pytest.fixture
    def player(self):
        """Fixture to create a player with default state for testing."""
        player = HumanPlayer("test_player")
        player.set_state("House", "")
        player._current_position = Coord(5, 5)
        return player

    @pytest.fixture
    def mock_house_observer(self):
        """Fixture to create a mock house observer that tracks calls."""
        class MockHouseObserver(HouseObserver):
            def __init__(self):
                self.update_house_called = False
                self.last_house = None

            def update_house(self, house):
                self.update_house_called = True
                self.last_house = house
                return []

        return MockHouseObserver()

    @pytest.fixture
    def mock_position_observer(self):
        """Fixture to create a mock position observer that tracks calls."""
        class MockPositionObserver(PositionObserver):
            def __init__(self):
                self._message = "Test message"
                self._text_bubble = TextBubble(TextBubbleImage.BLANK)
                self._active_positions = [Coord(3, 3)]
                self._message_displayed = False
                self.last_position = None
                self.update_position_called = False

            def update_position(self, position):
                self.update_position_called = True
                self.last_position = position
                return super().update_position(position)

        return MockPositionObserver()

    @pytest.fixture
    def setup_office_with_player(self, dumbledores_office, player, monkeypatch):
        """Fixture to setup an office with a player inside."""
        # Mock get_human_players to return our test player
        monkeypatch.setattr(dumbledores_office, "get_human_players", lambda: [player])
        return dumbledores_office

    @pytest.fixture
    def setup_empty_office(self, dumbledores_office, monkeypatch):
        """Fixture to setup an empty office with no players."""
        # Mock get_human_players to return empty list
        monkeypatch.setattr(dumbledores_office, "get_human_players", lambda: [])
        return dumbledores_office

    @pytest.fixture
    def mock_sorting_hat(self, monkeypatch):
        """Fixture to create a mock sorting hat for testing."""
        sorting_hat = SortingHat(
            [Coord(12, 7), Coord(12, 8)],
            "sorting_hat",
            TextBubble(TextBubbleImage.SPACE)
        )
        # Track method calls
        sorting_hat.is_player_sorted_called = False
        sorting_hat.is_sorting_in_progress_called = False
        sorting_hat.player_left_called = False

        # Mock methods to avoid side effects and track calls
        def mock_is_player_sorted(player):
            sorting_hat.is_player_sorted_called = True
            return player.get_state("House", "") != ""

        def mock_is_sorting_in_progress(player):
            sorting_hat.is_sorting_in_progress_called = True
            return player.get_state("sorting_in_progress", False)

        def mock_player_left(player):
            sorting_hat.player_left_called = True
            return []

        monkeypatch.setattr(sorting_hat, "is_player_sorted", mock_is_player_sorted)
        monkeypatch.setattr(sorting_hat, "is_sorting_in_progress", mock_is_sorting_in_progress)
        monkeypatch.setattr(sorting_hat, "player_left", mock_player_left)
        # register the sorting hat to be accessible via its name
        MapObject.register_obj("sorting_hat", sorting_hat)
        return sorting_hat

    @pytest.fixture
    def mock_super_move(self, monkeypatch):
        """Fixture to mock the parent class's move method and track calls."""
        move_called = {"value": False}

        def mock_move(self, player, direction):
            move_called["value"] = True
            return []

        monkeypatch.setattr(Map, "move", mock_move)
        return move_called

    @pytest.fixture
    def mock_notify_position_observers(self, dumbledores_office, monkeypatch):
        """Fixture to mock notify_position_observers and track calls."""
        notify_data = {
            "called": False,
            "position": None,
            "messages": []
        }

        def mock_notify(position):
            notify_data["called"] = True
            notify_data["position"] = position
            return notify_data["messages"]

        monkeypatch.setattr(dumbledores_office, "notify_position_observers", mock_notify)
        return notify_data

    @pytest.fixture
    def mock_chat_message(self, monkeypatch):
        """Fixture to mock ChatMessage without external dependencies."""
        class MockChatMessage:
            def __init__(self, sender, recipient, text):
                self.sender = sender
                self.recipient = recipient
                self.text = text

        monkeypatch.setattr("COMP303_Project.dumbledores_office.ChatMessage", MockChatMessage)

    @pytest.fixture
    def mock_house_sorting(self, monkeypatch):
        """Fixture to set up a sorting hat with appropriate mocks for testing sorting restrictions."""
        sorting_hat = SortingHat(
            [Coord(12, 7), Coord(12, 8)],
            "sorting_hat",
            TextBubble(TextBubbleImage.SPACE)
        )
        # force is_player_sorted to return False for testing sorting restriction
        def mock_is_player_sorted(p):
            return False

        monkeypatch.setattr(sorting_hat, "is_player_sorted", mock_is_player_sorted)

        # mock the get_obj method to return our sorting hat
        def mock_get_obj(name):
            if name == "sorting_hat":
                return sorting_hat
            return None

        monkeypatch.setattr(MapObject, "get_obj", mock_get_obj)
        return sorting_hat

    @pytest.fixture
    def theme_message_tracker(self, setup_office_with_player, monkeypatch):
        """Fixture to track theme messages sent by update_theme."""
        message_tracker = {"sent_message": ""}

        def mock_send_message(message):
            message_tracker["sent_message"] = message
            return []

        monkeypatch.setattr(setup_office_with_player, "send_message_to_players", mock_send_message)
        return message_tracker

    # singleton tests

    def test_singleton_pattern(self):
        """Test that two instances of dumbledores_office are the same object."""
        office1 = DumbledoresOffice()
        office2 = DumbledoresOffice.get_instance()
        assert office1 is office2, "dumbledores_office should implement the singleton pattern"

    def test_get_instance_returns_same_object(self):
        """Test that get_instance() always returns the same object."""
        office1 = DumbledoresOffice.get_instance()
        office2 = DumbledoresOffice.get_instance()
        office3 = DumbledoresOffice.get_instance()
        assert office1 is office2 is office3, "get_instance should always return the same object"

    # player management tests

    def test_is_occupied_with_player(self, setup_office_with_player):
        """Test is_occupied returns true when a player is in the office."""
        assert setup_office_with_player.is_occupied() is True

    def test_is_occupied_without_player(self, setup_empty_office):
        """Test is_occupied returns false when no player is in the office."""
        assert setup_empty_office.is_occupied() is False

    def test_get_player_with_player(self, setup_office_with_player, player):
        """Test get_player returns the player when one is in the office."""
        assert setup_office_with_player.get_player() is player

    def test_get_player_without_player(self, setup_empty_office):
        """Test get_player returns null_player when no player is in the office."""
        assert setup_empty_office.get_player() is DumbledoresOffice.NULL_PLAYER

    def test_get_player_name(self, setup_office_with_player):
        """Test get_player_name returns the name of the player in the office."""
        assert setup_office_with_player.get_player_name() == "test_player"

    def test_get_player_position(self, setup_office_with_player, player):
        """Test get_player_position returns the position of the player in the office."""
        player._current_position = Coord(3, 4)
        assert setup_office_with_player.get_player_position() == Coord(3, 4)

    def test_get_player_state(self, setup_office_with_player, player):
        """Test get_player_state returns the state of the player."""
        player.set_state("test_key", "test_value")
        assert setup_office_with_player.get_player_state("test_key") == "test_value"

    def test_get_player_state_with_default(self, setup_office_with_player):
        """Test get_player_state returns the default value when state doesn't exist."""
        result = setup_office_with_player.get_player_state("non_existent_key", "default_value")
        assert result == "default_value"

    def test_set_player_state(self, setup_office_with_player, player):
        """Test set_player_state updates the player's state."""
        setup_office_with_player.set_player_state("test_key", "new_value")
        assert player.get_state("test_key") == "new_value"

    # house observer tests

    def test_add_house_observer(self, dumbledores_office, mock_house_observer):
        """Test add_house_observer adds observer to the list and calls update."""
        dumbledores_office.add_house_observer(mock_house_observer)
        assert mock_house_observer in dumbledores_office._DumbledoresOffice__house_observers
        assert mock_house_observer.update_house_called

    def test_remove_house_observer(self, dumbledores_office, mock_house_observer):
        """Test remove_house_observer removes observer from the list."""
        dumbledores_office._DumbledoresOffice__house_observers.add(mock_house_observer)
        dumbledores_office.remove_house_observer(mock_house_observer)
        assert mock_house_observer not in dumbledores_office._DumbledoresOffice__house_observers

    def test_remove_house_observer_not_in_list(self, dumbledores_office, mock_house_observer):
        """Test remove_house_observer handles case when observer isn't in the list."""
        dumbledores_office._DumbledoresOffice__house_observers.clear()
        dumbledores_office.remove_house_observer(mock_house_observer)
        assert mock_house_observer not in dumbledores_office._DumbledoresOffice__house_observers

    def test_notify_house_observers(self, dumbledores_office, mock_house_observer):
        """Test notify_house_observers calls update_house on all observers."""
        observer1 = mock_house_observer
        observer2 = type(mock_house_observer)()
        dumbledores_office._DumbledoresOffice__house_observers.add(observer1)
        dumbledores_office._DumbledoresOffice__house_observers.add(observer2)
        dumbledores_office.notify_house_observers(House.GRYFFINDOR)
        assert observer1.update_house_called and observer2.update_house_called
        assert observer1.last_house == observer2.last_house == House.GRYFFINDOR

    # position observer tests

    def test_add_position_observer(self, setup_office_with_player, mock_position_observer):
        """Test add_position_observer adds observer to the list and calls update."""
        setup_office_with_player.add_position_observer(mock_position_observer)
        assert mock_position_observer in setup_office_with_player._DumbledoresOffice__position_observers
        assert mock_position_observer.update_position_called

    def test_remove_position_observer(self, dumbledores_office, mock_position_observer):
        """Test remove_position_observer removes observer from the list."""
        dumbledores_office._DumbledoresOffice__position_observers.add(mock_position_observer)
        dumbledores_office.remove_position_observer(mock_position_observer)
        assert mock_position_observer not in dumbledores_office._DumbledoresOffice__position_observers

    def test_remove_position_observer_not_in_list(self, dumbledores_office, mock_position_observer):
        """Test remove_position_observer handles case when observer isn't in the list."""
        dumbledores_office._DumbledoresOffice__position_observers.clear()
        dumbledores_office.remove_position_observer(mock_position_observer)
        assert mock_position_observer not in dumbledores_office._DumbledoresOffice__position_observers

    def test_notify_position_observers(self, dumbledores_office, mock_position_observer):
        """Test notify_position_observers calls update_position on all observers."""
        observer1 = mock_position_observer
        observer2 = type(mock_position_observer)()
        dumbledores_office._DumbledoresOffice__position_observers.add(observer1)
        dumbledores_office._DumbledoresOffice__position_observers.add(observer2)
        position = Coord(3, 4)
        dumbledores_office.notify_position_observers(position)
        assert observer1.update_position_called and observer2.update_position_called
        assert observer1.last_position == observer2.last_position == position

    # theme update tests

    def test_update_theme_with_house(self, setup_office_with_player, player, mock_house_observer):
        """Test update_theme sets player's house state and notifies observers."""
        observer = mock_house_observer
        office = setup_office_with_player
        office._DumbledoresOffice__house_observers.add(observer)
        
        # set the player's house state directly since update_theme no longer accepts a house parameter
        player.set_state("House", "HUFFLEPUFF")
        
        # call update_theme without parameters
        office.update_theme()
        
        # check that the house observers were notified with the correct house
        assert observer.update_house_called
        assert observer.last_house == House.HUFFLEPUFF

    def test_update_theme_with_null_house(self, setup_office_with_player, player, mock_house_observer):
        """Test update_theme with null house still notifies observers."""
        observer = mock_house_observer
        office = setup_office_with_player
        office._DumbledoresOffice__house_observers.add(observer)
        
        # clear the player's house state
        player.set_state("House", "")
        
        # call update_theme without parameters
        office.update_theme()
        
        # check that the house observers were notified with None
        assert observer.update_house_called
        assert observer.last_house is None

    def test_update_theme_with_house_no_player(self, setup_empty_office, mock_house_observer):
        """Test update_theme when there's no player in the office."""
        office = setup_empty_office
        observer = mock_house_observer
        office._DumbledoresOffice__house_observers.add(observer)
        
        # call update_theme without parameters
        office.update_theme()
        
        # check that house observers were notified with None since there's no player
        assert observer.update_house_called
        assert observer.last_house is None

    def test_update_theme_messages(self, theme_message_tracker):
        """Test that update_theme sends the correct theme message for each house."""
        office = DumbledoresOffice.get_instance()
        player = office.get_player()
        
        # test each house's theme message
        for house, expected_text in {
            House.GRYFFINDOR: "scarlet and gold",
            House.HUFFLEPUFF: "yellow and black",
            House.RAVENCLAW: "blue and bronze",
            House.SLYTHERIN: "green and silver"
        }.items():
            # set the player's house directly
            player.set_state("House", house.name)
            
            # call update_theme
            office.update_theme()
            
            # check that the correct message was sent
            assert expected_text in theme_message_tracker["sent_message"].lower()

    # player movement tests

    def test_move_with_normal_movement(self, dumbledores_office, player, mock_super_move):
        """Test move handles normal player movement."""
        dumbledores_office.move(player, "up")
        assert mock_super_move["value"], "super().move should be called for normal movement"

    def test_move_onto_door_blocks_exit(self, dumbledores_office, player, mock_super_move, monkeypatch):
        """Test move blocks player exit through the door."""
        player._current_position = Coord(13, 7)  # door position
        messages = dumbledores_office.move(player, "right")  # try to exit
        assert not mock_super_move["value"], "super().move should not be called when trying to exit directly"
        assert len(messages) == 1, "should return a message about not being able to exit"
        assert isinstance(messages[0], ServerMessage), "message should be a ServerMessage"
        assert messages[0]._Message__recipient is player, "message should be directed to the player"

    def test_move_with_sorting_restriction(self, dumbledores_office, player, mock_house_sorting, mock_chat_message):
        """Test move blocks player from exploring room before sorting."""
        player._current_position = Coord(12, 7)  # Position adjacent to sorting hat
        player.set_state("in_sorting_range", True)
        player.set_state("House", "")  # Not sorted yet
        player.set_state("sorting_in_progress", False)  # Not currently sorting
        messages = dumbledores_office.move(player, "left")  # Try to move past sorting hat
        assert len(messages) == 1, "should return a message about needing to be sorted"
        assert hasattr(messages[0], "text"), "message should have text attribute"
        assert "i can't let you explore" in messages[0].text.lower(), "message should explain need to be sorted"

    def test_move_notifies_position_observers(self, dumbledores_office, player, mock_position_observer, mock_super_move, monkeypatch):
        """Test move notifies position observers after successful movement."""
        observer = mock_position_observer
        dumbledores_office._DumbledoresOffice__position_observers.add(observer)
        monkeypatch.setattr(dumbledores_office, "get_human_players", lambda: [player])
        new_position = Coord(6, 6)
        monkeypatch.setattr(player, "get_current_position", lambda: new_position)
        dumbledores_office.move(player, "up")
        assert observer.update_position_called, "position observers should be notified after move"
        assert observer.last_position == new_position, "new position should be passed to observers"

    def test_move_with_non_tracked_player(self, dumbledores_office, player, mock_notify_position_observers, mock_super_move, monkeypatch):
        """Test move with a player that's not the tracked player."""
        other_player = HumanPlayer("other_player")
        
        # ensure we can identify who is the tracked player
        monkeypatch.setattr(dumbledores_office, "get_player", lambda: player)
        
        # track if super().move was called
        mock_super_move["value"] = False
        
        # reset the notification tracker
        mock_notify_position_observers["called"] = False
        
        # try to move another player
        dumbledores_office.move(other_player, "up")
        
        # verify super().move was called
        assert mock_super_move["value"], "super().move should be called for any player movement"
        assert mock_notify_position_observers["called"], "Position observers are currently notified for all players, including non-tracked players"

    def test_move_returns_observer_messages(self, dumbledores_office, player, mock_notify_position_observers, mock_super_move, monkeypatch):
        """Test that messages from observers are included in the return value of move."""
        observer_message = ServerMessage(player, "Test observer message")
        mock_notify_position_observers["messages"] = [observer_message]
        monkeypatch.setattr(dumbledores_office, "get_human_players", lambda: [player])
        monkeypatch.setattr(dumbledores_office, "get_player_name", lambda: player.get_name())
        messages = dumbledores_office.move(player, "up")
        assert observer_message in messages, "Messages from position observers should be included in return value"

    # OTHER FUNCTIONALITIES TEST
    
    def test_get_name(self, dumbledores_office):
        """Test get_name returns the correct name."""
        assert dumbledores_office.get_name() == "DUMBLEDORE'S OFFICE"

    def test_get_objects_creates_all_required_objects(self, dumbledores_office):
        """Test get_objects returns all the required objects for the office."""
        objects = dumbledores_office.get_objects()
        # Check that objects list contains expected types
        object_types = [type(obj[0]).__name__ for obj in objects]
        expected_types = ["InteriorDoor", "Rug", "TextBubble", "SortingHat", "TextBubble", "Bookshelf",
                          "TextBubble", "ChatObject", "TextBubble", "ChatObject", "TextBubble", "ChatObject",
                          "TextBubble", "ChatObject", "TextBubble", "ChatObject", "TextBubble", "Phoenix",
                          "Decor", "Decor", "Decor", "Decor", "Decor", "Decor", "Candle", "Candle", "Candle", "Candle"]
        # Count occurrences of each type
        type_counts = {}
        for t in object_types:
            type_counts[t] = type_counts.get(t, 0) + 1
        # Check that we have at least one of each expected type
        for expected_type in set(expected_types):
            assert expected_type in type_counts, f"Should create at least one {expected_type}"
        # Check specific counts for main interactive elements
        assert type_counts.get("Rug", 0) == 1, "Should create exactly one Rug"
        assert type_counts.get("SortingHat", 0) == 1, "Should create exactly one SortingHat"
        assert type_counts.get("ChatObject", 0) >= 4, "Should create at least 4 ChatObjects (portraits + pensieve)"
        assert type_counts.get("Phoenix", 0) == 1, "Should create exactly one Phoenix"
        assert type_counts.get("Bookshelf", 0) == 1, "Should create exactly one Bookshelf"