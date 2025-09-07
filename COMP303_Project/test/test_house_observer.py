import pytest
from typing import TYPE_CHECKING, Optional, List

from ..imports import *
from ..house_observer import HouseObserver
from ..house import House
from ..dumbledores_office import DumbledoresOffice

if TYPE_CHECKING:
    from message import Message, DialogueMessage
    from coord import Coord
    from Player import HumanPlayer


class MockHouseObserver(HouseObserver):
    """
    Concrete implementation of HouseObserver for testing.
    """
    def __init__(self, message: str = "House changed to {house}"):
        self._message_template = message
        self._current_house = None
        self._message_displayed = False

    def update_house(self, house: Optional[House]) -> List['Message']:
        """Implementation of the abstract method for testing."""
        messages = []

        if house != self._current_house:
            self._current_house = house
            if house is not None:
                display_message = self._message_template.format(house=house.name)
                self._message_displayed = True
                # call utility function to create message
                messages.append(self._create_message(display_message))
            else:
                self._message_displayed = False

        # always append grid update messages
        messages.extend(DumbledoresOffice.get_instance().send_grid_to_players())
        return messages

    def _create_message(self, text):
        """Helper method to create a message."""
        from ..util import get_custom_dialogue_message

        return get_custom_dialogue_message(
            DumbledoresOffice.get_instance(),
            DumbledoresOffice.get_instance().get_player(),
            text
        )


class TestHouseObserver:
    """
    Test suite for the HouseObserver abstract class.
    Tests the update_house method behavior in various scenarios.
    """

    @pytest.fixture(autouse=True)
    def setup_environment(self, monkeypatch):
        """Setup necessary environment variables for tests."""
        monkeypatch.setenv("GITHUB_LOGIN", "test_user")
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")

    @pytest.fixture
    def house_observer(self):
        """Fixture to create a MockHouseObserver for testing."""
        return MockHouseObserver()

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

        monkeypatch.setattr(dumbledores_office, "get_player", lambda: mock_player)
        monkeypatch.setattr(dumbledores_office, "send_grid_to_players", lambda: [mock_message])

        def mock_get_instance():
            return dumbledores_office
        
        monkeypatch.setattr(DumbledoresOffice, "get_instance", mock_get_instance)
        return dumbledores_office

    @pytest.fixture
    def mock_dialogue_message(self, monkeypatch):
        """Fixture to mock DialogueMessage creation."""
        from ..util import get_custom_dialogue_message

        # track if the function was called
        dialogue_tracker = {"called": False, "message": None}

        def mock_get_dialogue(sender, recipient, text, image="", font='harryp',
                              bg_color=(0, 0, 0), text_color=(255, 255, 255),
                              press_enter=True, auto_delay=500):
            dialogue_tracker["called"] = True
            dialogue_tracker["message"] = text
            return DialogueMessage(sender, recipient, text, image, font, bg_color, text_color, press_enter, auto_delay)
        
        monkeypatch.setattr("COMP303_Project.util.get_custom_dialogue_message", mock_get_dialogue)
        return dialogue_tracker

    def test_update_house_from_none_to_gryffindor(self, house_observer, mock_dumbledores_office, mock_dialogue_message):
        """Test update_house when changing from None to Gryffindor."""
        messages = house_observer.update_house(House.GRYFFINDOR)

        assert house_observer._current_house == House.GRYFFINDOR, "house should be updated to gryffindor"
        assert house_observer._message_displayed, "message should be displayed"
        assert mock_dialogue_message["called"], "get_custom_dialogue_message should be called"
        assert "GRYFFINDOR" in mock_dialogue_message["message"], "message should mention gryffindor"
        assert len(messages) > 0, "should return at least one message"

    def test_update_house_from_gryffindor_to_slytherin(self, house_observer, mock_dumbledores_office, mock_dialogue_message):
        """Test update_house when changing from Gryffindor to Slytherin."""
        # set initial house to gryffindor
        house_observer.update_house(House.GRYFFINDOR)

        # reset dialogue tracker
        mock_dialogue_message["called"] = False

        # update to slytherin
        messages = house_observer.update_house(House.SLYTHERIN)

        assert house_observer._current_house == House.SLYTHERIN, "house should be updated to slytherin"
        assert house_observer._message_displayed, "message should be displayed"
        assert mock_dialogue_message["called"], "get_custom_dialogue_message should be called"
        assert "SLYTHERIN" in mock_dialogue_message["message"], "message should mention slytherin"
        assert len(messages) > 0, "should return at least one message"

    def test_update_house_to_same_house(self, house_observer, mock_dumbledores_office, mock_dialogue_message):
        """Test update_house when updating to the same house."""
        # set initial house to ravenclaw
        house_observer.update_house(House.RAVENCLAW)

        # reset dialogue tracker
        mock_dialogue_message["called"] = False

        # update to ravenclaw again
        messages = house_observer.update_house(House.RAVENCLAW)

        assert house_observer._current_house == House.RAVENCLAW, "house should remain ravenclaw"
        assert not mock_dialogue_message["called"], "get_custom_dialogue_message should not be called"
        assert len(messages) > 0, "should return at least one message (grid update)"

    def test_update_house_to_none(self, house_observer, mock_dumbledores_office, mock_dialogue_message):
        """Test update_house when changing to None (no house)."""
        # set initial house to hufflepuff
        house_observer.update_house(House.HUFFLEPUFF)

        # reset dialogue tracker
        mock_dialogue_message["called"] = False

        # update to none
        messages = house_observer.update_house(None)

        assert house_observer._current_house is None, "house should be updated to none"
        assert not house_observer._message_displayed, "message should not be displayed"
        assert not mock_dialogue_message["called"], "get_custom_dialogue_message should not be called"
        assert len(messages) > 0, "should return at least one message (grid update)"

    def test_update_house_from_none_to_none(self, house_observer, mock_dumbledores_office, mock_dialogue_message):
        """Test update_house when updating from None to None."""
        # update to none when already none
        messages = house_observer.update_house(None)
        
        assert house_observer._current_house is None, "house should remain none"
        assert not house_observer._message_displayed, "message should not be displayed"
        assert not mock_dialogue_message["called"], "get_custom_dialogue_message should not be called"
        assert len(messages) > 0, "should return at least one message (grid update)"