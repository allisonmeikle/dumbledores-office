import pytest
from typing import TYPE_CHECKING

# Relative import to access the imports.py bridge
from ..imports import *

# Relative imports for our project files
from ..dumbledores_office import DumbledoresOffice, SortingHat, TextBubble, SortingOptionCommand
from ..house import House
from ..text_bubble import TextBubbleImage

if TYPE_CHECKING:
    from coord import Coord
    from Player import HumanPlayer
    from maps.base import Map, Message

class TestSortingOptionCommand:
    @pytest.fixture(autouse=True)
    def setup_environment(self, monkeypatch):
        """Setup necessary environment variables for tests."""
        # Sets up environment variables needed for API calls in the background
        monkeypatch.setenv("GITHUB_LOGIN", "test_user")
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")

    @pytest.fixture
    def sorting_hat(self):
        """Fixture to create a SortingHat instance for testing."""
        text_bubble = TextBubble(TextBubbleImage.SPACE)
        return SortingHat([Coord(12, 7), Coord(12, 8)], "sorting_hat", text_bubble)

    @pytest.fixture
    def player(self):
        """Fixture to create a HumanPlayer for testing."""
        # Creates a clean player with default state for testing
        player = HumanPlayer("test_player")
        player.set_state("sorting_in_progress", False)
        player.set_state("sorting_answers", [])
        return player
        
    @pytest.fixture
    def sorting_player(self, player):
        """Fixture to create a player that's in the sorting process."""
        player.set_state("sorting_in_progress", True)
        player.set_state("sorting_answers", [0, 1])  # Already answered two questions
        return player
        
    @pytest.fixture
    def mock_dumbledores_office(self, monkeypatch, player):
        """Fixture to mock DumbledoresOffice methods."""
        office = DumbledoresOffice.get_instance()
        
        # Mock methods to prevent side effects
        monkeypatch.setattr(office, "update_theme", lambda house: [])
        monkeypatch.setattr(office, "send_message_to_players", lambda message: [])
        monkeypatch.setattr(office, "send_grid_to_players", lambda: [])
        monkeypatch.setattr(office, "get_player", lambda: player)
        
        return office
        
    @pytest.fixture
    def mock_answer_question(self, sorting_hat, monkeypatch):
        """Fixture to mock the _answer_question method and track its calls."""
        call_tracker = {
            "called": False,
            "player": None,
            "question_index": None,
            "answer_index": None,
            "return_value": ["Test message"]
        }
        
        def mock_func(player, question_index, answer_index):
            call_tracker["called"] = True
            call_tracker["player"] = player
            call_tracker["question_index"] = question_index
            call_tracker["answer_index"] = answer_index
            return call_tracker["return_value"]
        
        monkeypatch.setattr(sorting_hat, "_answer_question", mock_func)
        return call_tracker
        
    @pytest.fixture
    def sorting_option_command(self, sorting_hat, player):
        """Fixture to create a SortingOptionCommand instance for testing."""
        return SortingOptionCommand(sorting_hat, player, 2, 1)
        
    def test_sorting_option_command_initialization_behavior(self, sorting_hat, player, mock_answer_question, mock_dumbledores_office):
        """Test that SortingOptionCommand behaves as expected after initialization with different parameters."""
        # Arrange
        question_index = 2
        answer_index = 1
        
        # Act
        command = SortingOptionCommand(sorting_hat, player, question_index, answer_index)
        command.execute(mock_dumbledores_office, player)
        
        # Assert
        assert mock_answer_question["player"] is player, "Command should use the player provided during initialization"
        assert mock_answer_question["question_index"] == question_index, "Command should use the question index provided during initialization"
        assert mock_answer_question["answer_index"] == answer_index, "Command should use the answer index provided during initialization"
        
    def test_execute_calls_answer_question(self, sorting_option_command, sorting_hat, player, mock_answer_question, mock_dumbledores_office):
        """Test that execute calls the sorting hat's _answer_question method with correct parameters."""
        
        messages = sorting_option_command.execute(mock_dumbledores_office, player)
        
        assert mock_answer_question["called"], "execute should call _answer_question on sorting hat"
        assert mock_answer_question["player"] is player, "Player should be passed to _answer_question"
        assert mock_answer_question["question_index"] == 2, "Question index should be passed to _answer_question"
        assert mock_answer_question["answer_index"] == 1, "Answer index should be passed to _answer_question"
        assert messages == mock_answer_question["return_value"], "execute should return messages from _answer_question"
        
    def test_execute_with_custom_values(self, sorting_hat, player, mock_answer_question, mock_dumbledores_office):
        """Test execute with different parameter values to ensure it passes them correctly."""
        # Testing with different question and answer indices
        command = SortingOptionCommand(sorting_hat, player, 3, 2)
        
        messages = command.execute(mock_dumbledores_office, player)
        
        assert mock_answer_question["called"], "execute should call _answer_question on sorting hat"
        assert mock_answer_question["question_index"] == 3, "Correct question index should be passed"
        assert mock_answer_question["answer_index"] == 2, "Correct answer index should be passed"
        
    def test_execute_different_context_player(self, sorting_option_command, sorting_hat, player, mock_answer_question, mock_dumbledores_office):
        """Test that execute uses stored player even if a different player is passed to execute."""
        different_player = HumanPlayer("different_player")
        
        messages = sorting_option_command.execute(mock_dumbledores_office, different_player)
        
        assert mock_answer_question["called"], "execute should call _answer_question on sorting hat"
        assert mock_answer_question["player"] is player, "Player from initialization should be used, not the one passed to execute"
        
    def test_execute_with_multiple_return_messages(self, sorting_hat, player, mock_answer_question, mock_dumbledores_office):
        """Test that execute correctly returns all messages from _answer_question."""
        command = SortingOptionCommand(sorting_hat, player, 0, 0)
        mock_answer_question["return_value"] = ["Message 1", "Message 2", "Message 3"]
        
        messages = command.execute(mock_dumbledores_office, player)
        
        assert messages == mock_answer_question["return_value"], "execute should return all messages from _answer_question"
        assert len(messages) == 3, "All messages should be returned"
        
    def test_integration_with_sorting_hat_answer_question(self, sorting_hat, player, monkeypatch, mock_dumbledores_office):
        """Integration test to verify that SortingOptionCommand correctly interacts with the actual SortingHat._answer_question method (without mocking)."""
        player.set_state("sorting_in_progress", True)
        player.set_state("sorting_answers", [])
        command = SortingOptionCommand(sorting_hat, player, 0, 2)  # First question, selecting Intelligence (Ravenclaw)
        
        # Patch the _show_question method to return predictable results
        monkeypatch.setattr(sorting_hat, "_show_question", lambda p, q_idx: [f"Question {q_idx}"])
        
        messages = command.execute(mock_dumbledores_office, player)
    
        # Check the answer was recorded correctly
        answers = player.get_state("sorting_answers", [])
        assert len(answers) == 1, "One answer should be recorded"
        assert answers[0] == 2, "Answer index 2 (Intelligence) should be recorded"
        
        # Check the expected message was returned
        assert messages == ["Question 1"], "Should return message for the next question (index 1)"
