import pytest
from typing import TYPE_CHECKING

# Relative import to access the imports.py bridge
from ..imports import *

# Relative imports for our project files
from ..dumbledores_office import DumbledoresOffice, SortingHat, TextBubble, TextBubbleImage
from ..house import House
from ..util import get_custom_dialogue_message

if TYPE_CHECKING:
    from coord import Coord
    from Player import HumanPlayer

class TestSortingHat:
    @pytest.fixture(autouse=True)
    def setup_environment(self, monkeypatch):
        """Setup necessary environment variables for tests."""
        # sets up environment variables needed for API calls in the background
        monkeypatch.setenv("GITHUB_LOGIN", "test_user")
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")

    @pytest.fixture
    def sorting_hat(self):
        """Fixture to create a SortingHat instance for testing."""
        # creates a fresh sorting hat instance with a text bubble for each test
        text_bubble = TextBubble(TextBubbleImage.SPACE)
        return SortingHat([Coord(12, 7), Coord(12, 8)], "sorting_hat", text_bubble)

    @pytest.fixture
    def player(self):
        """Fixture to create a real HumanPlayer for testing."""
        # creates a clean player with default state for testing
        player = HumanPlayer("test_player")
        
        # initialize any necessary state
        player.set_state("sorting_in_progress", False)
        player.set_state("sorting_answers", [])
        return player

    @pytest.fixture
    def mock_text_bubble(self, monkeypatch):
        """Fixture to mock TextBubble methods and track calls to them."""
        # this fixture creates a mock object to track calls to the text bubble methods
        text_bubble = TextBubble(TextBubbleImage.SPACE)
        
        # create trackers for method calls
        text_bubble_tracker = {
            "text_bubble": text_bubble,
            "show_called": False,
            "hide_called": False,
            "is_visible_return": False
        }
        
        # mock the methods we care about
        def mock_show():
            text_bubble_tracker["show_called"] = True
            text_bubble._is_visible = True
            
        def mock_hide():
            text_bubble_tracker["hide_called"] = True
            text_bubble._is_visible = False
            
        def mock_is_visible():
            return text_bubble_tracker["is_visible_return"]
        
        # apply mocks
        monkeypatch.setattr(text_bubble, "show", mock_show)
        monkeypatch.setattr(text_bubble, "hide", mock_hide)
        monkeypatch.setattr(text_bubble, "is_visible", mock_is_visible)
        
        return text_bubble_tracker

    @pytest.fixture
    def mock_house_functions(self, monkeypatch, player):
        """Fixture to mock DumbledoresOffice functions that have side effects."""
        # prevents house updates from affecting the real game state
        # but still maintains correct House assignment for testing
        dumbledores_office = DumbledoresOffice.get_instance()
        
        # need to ensure we don't interfere with the player's house state
        # being set directly in the _calculate_result method
        def mock_update_theme(house=None):
            # no need to set the house here as it's already set in _calculate_result
            return []
        
        monkeypatch.setattr(dumbledores_office, "update_theme", mock_update_theme)
        monkeypatch.setattr(dumbledores_office, "send_message_to_players", lambda message: [])
        monkeypatch.setattr(dumbledores_office, "send_grid_to_players", lambda: [])
        monkeypatch.setattr(dumbledores_office, "get_player", lambda: player)
        
        return dumbledores_office

    @pytest.fixture
    def sorting_player(self, player):
        """Fixture to create a player that's in the sorting process."""
        # Shorthand for a player who's already in the sorting process
        player.set_state("sorting_in_progress", True)
        player.set_state("sorting_answers", [])
        return player

    @pytest.fixture
    def mock_answer_question(self, sorting_hat, monkeypatch):
        """Fixture to mock the answer_question method and track its calls."""
        # Tracks calls to answer_question to verify select_option behavior
        call_tracker = {
            "called": False,
            "player": None,
            "question_index": None,
            "answer_index": None
        }
        
        def mock_func(p, q_idx, a_idx):
            call_tracker["called"] = True
            call_tracker["player"] = p
            call_tracker["question_index"] = q_idx
            call_tracker["answer_index"] = a_idx
            return ["mocked response"]
        
        monkeypatch.setattr(sorting_hat, "_answer_question", mock_func)
        return call_tracker
    
    @pytest.fixture
    def mock_sorting_completion(self, sorting_hat, player, monkeypatch):
        """
        Fixture to set up mocks for testing the update method with sorting completion.
        Returns a dictionary containing all objects needed for assertions.
        """
        # Mock DumbledoresOffice
        office = DumbledoresOffice.get_instance()
        
        # Create a state tracker for test data
        state_tracker = {
            "timer_value": 2,  # Default value
            "calculate_result_called": False
        }
        
        # Mock player state methods for getting and setting
        def mock_get_state(key, default=None):
            if key == "sorting_in_progress":
                return True
            elif key == "on_last_question":
                return True
            elif key == "sorting_delay_timer":
                return state_tracker["timer_value"]
            return default
            
        def mock_set_state(key, value):
            if key == "sorting_delay_timer":
                state_tracker["timer_value"] = value
                
        # Mock get_player_state to check appropriate conditions
        def mock_get_player_state(state, default=None): 
            return (
                state == "sorting_in_progress" or 
                state == "on_last_question" or 
                (state == "sorting_delay_timer" and state_tracker["timer_value"])
            )
        
        # Mock calculate_result to track calls
        def mock_calculate_result(p):
            state_tracker["calculate_result_called"] = True
            return ["Result calculated"]
            
        # Apply all mocks
        monkeypatch.setattr(player, "get_state", mock_get_state)
        monkeypatch.setattr(player, "set_state", mock_set_state)
        monkeypatch.setattr(office, "get_player", lambda: player)
        monkeypatch.setattr(office, "get_player_state", mock_get_player_state)
        monkeypatch.setattr(office, "set_player_state", mock_set_state)
        monkeypatch.setattr(sorting_hat, "_calculate_result", mock_calculate_result)
        
        # Return the tracker for assertions and any needed objects
        return state_tracker
            
    # SORTING QUIZ TESTS
    
    def test_is_player_sorted_when_player_has_no_house(self, sorting_hat, player):
        """Test is_player_sorted returns False when player has no house assigned."""
        # Arrange
        player.set_state("House", "")
        
        # Act
        result = sorting_hat.is_player_sorted(player)
        
        # Assert
        assert result is False, "Player without house should not be considered sorted"
    
    def test_is_player_sorted_when_player_has_house(self, sorting_hat, player):
        """Test is_player_sorted returns True when player has a house assigned."""
        player.set_state("House", "GRYFFINDOR")
        
        # Act
        result = sorting_hat.is_player_sorted(player)
        
        # Assert
        assert result is True, "Player with house should be considered sorted"
        
    def test_get_name_returns_sorting_hat(self, sorting_hat):
        """Test that get_name returns 'SORTING HAT'."""
        # Call get_name
        result = sorting_hat.get_name()
        assert result == "SORTING HAT", "get_name should return 'SORTING HAT'"
        
    def test_is_sorting_in_progress_when_true(self, sorting_hat, player):
        """Test that is_sorting_in_progress returns True when state is set."""
        # Arrange
        player.set_state("sorting_in_progress", True)
        
        # Act
        result = sorting_hat.is_sorting_in_progress(player)
        
        # Assert
        assert result is True, "is_sorting_in_progress should return True when sorting_in_progress is set to True"

    def test_is_sorting_in_progress_when_false(self, sorting_hat, player):
        """Test that is_sorting_in_progress returns False when not set."""
        # Arrange
        player.set_state("sorting_in_progress", False)
        
        # Act
        result = sorting_hat.is_sorting_in_progress(player)
        
        # Assert
        assert result is False, "is_sorting_in_progress should return False when sorting_in_progress is set to False"

    def test_player_left_when_sorting_in_progress(self, sorting_hat, player):
        """Test that sorting states are reset when player leaves."""
        # Arrange
        player.set_state("sorting_in_progress", True)
        player.set_state("sorting_answers", [1, 2, 3])
        
        # Act
        messages = sorting_hat.player_left(player)
        
        # Assert
        assert player.get_state("sorting_in_progress") is False, "sorting_in_progress should be False after player_left"
        assert player.get_state("sorting_answers") == [], "sorting_answers should be reset after player_left"
        assert messages == [], "player_left should return an empty list of messages"
    
    def test_answer_question_stores_answer(self, sorting_hat, player):
        """Test that answer is added to player's state."""
        # Arrange
        player.set_state("sorting_answers", [0, 2])  # Two answers already recorded
        question_index = 2  # We're answering the third question
        answer_index = 1    # Selecting the second option
        
        # Act
        sorting_hat._answer_question(player, question_index, answer_index)
        
        # Assert
        answers = player.get_state("sorting_answers")
        assert len(answers) == 3, "There should be 3 answers after answering a third question"
        assert answers == [0, 2, 1], "The new answer should be appended to the existing answers"
    
    def test_show_question_first_question(self, sorting_hat, player):
        """Test special intro message for first question."""
        # Arrange
        question_index = 0  # First question
        
        # Act
        messages = sorting_hat._show_question(player, question_index)
        
        # Assert
        assert len(messages) >= 3, "First question should include intro, question, and menu messages"
    
    def test_show_question_later_questions(self, sorting_hat, player):
        """Test standard message format for subsequent questions."""
        # Arrange
        question_index = 2  # Not the first question
        
        # Act
        messages = sorting_hat._show_question(player, question_index)
        
        # Assert
        assert len(messages) >= 2, "Later questions should include at least question and menu messages"
    
    def test_show_question_final_processing(self, sorting_hat, player):
        """Test behavior when all questions are answered (delay timer setup)."""
        # Arrange
        question_index = 5  # Beyond the last question index
        
        # Act
        messages = sorting_hat._show_question(player, question_index)
        
        # Assert
        assert player.get_state("on_last_question") is True, "on_last_question should be set to True"
        assert player.get_state("sorting_delay_timer") == 2, "sorting_delay_timer should be set to 2"
        assert len(messages) == 1, "Should return a single 'thinking' message"
        
    # HOUSE ASSIGNMENT TESTS
    
    def test_calculate_result_assigns_gryffindor(self, sorting_hat, player, mock_house_functions):
        """Test that a player is assigned to Gryffindor when majority of answers point to it."""
        # Arrange
        player.set_state("sorting_answers", [0, 0, 0, 1, 2])
        player.set_state("sorting_in_progress", True)
        player.set_state("on_last_question", True)
        
        # Act
        messages = sorting_hat._calculate_result(player)
        
        # Assert
        assert player.get_state("House") == "GRYFFINDOR", "Player should be assigned to Gryffindor based on answers"
        assert player.get_state("sorting_in_progress") is False, "Sorting should be marked as complete"
        assert player.get_state("on_last_question") is False, "Last question flag should be reset"
        assert len(messages) > 0, "Should return messages announcing the house"
    
    def test_calculate_result_assigns_hufflepuff(self, sorting_hat, player, mock_house_functions):
        """Test that a player is assigned to Hufflepuff when majority of answers point to it."""
        # Arrange
        player.set_state("sorting_answers", [1, 1, 1, 0, 2])
        player.set_state("sorting_in_progress", True)
        player.set_state("on_last_question", True)
        
        # Act
        messages = sorting_hat._calculate_result(player)
        
        # Assert
        assert player.get_state("House") == "HUFFLEPUFF", "Player should be assigned to Hufflepuff based on answers"
        assert player.get_state("sorting_in_progress") is False, "Sorting should be marked as complete"
        assert len(messages) > 0, "Should return messages announcing the house"

    def test_calculate_result_assigns_ravenclaw(self, sorting_hat, player, mock_house_functions):
        """Test that a player is assigned to Ravenclaw when majority of answers point to it."""
        # Arrange
        player.set_state("sorting_answers", [2, 2, 2, 0, 1])
        player.set_state("sorting_in_progress", True)
        player.set_state("on_last_question", True)
        
        # Act
        messages = sorting_hat._calculate_result(player)
        
        # Assert
        assert player.get_state("House") == "RAVENCLAW", "Player should be assigned to Ravenclaw based on answers"
        assert player.get_state("sorting_in_progress") is False, "Sorting should be marked as complete"
        assert len(messages) > 0, "Should return messages announcing the house"

    def test_calculate_result_assigns_slytherin(self, sorting_hat, player, mock_house_functions):
        """Test that a player is assigned to Slytherin when majority of answers point to it."""
        # Arrange
        player.set_state("sorting_answers", [3, 3, 3, 0, 1])
        player.set_state("sorting_in_progress", True)
        player.set_state("on_last_question", True)
        
        # Act
        messages = sorting_hat._calculate_result(player)
        
        # Assert
        assert player.get_state("House") == "SLYTHERIN", "Player should be assigned to Slytherin based on answers"
        assert player.get_state("sorting_in_progress") is False, "Sorting should be marked as complete"
        assert len(messages) > 0, "Should return messages announcing the house"
    
    def test_calculate_result_handles_tie(self, sorting_hat, player, mock_house_functions):
        """Test that the first highest-scoring house is chosen in case of a tie."""
        # Arrange
        player.set_state("sorting_answers", [0, 1, 0, 1, 2])
        player.set_state("sorting_in_progress", True)
        player.set_state("on_last_question", True)
        
        # Act
        messages = sorting_hat._calculate_result(player)
        
        # Assert
        house = player.get_state("House")
        assert house is not None, "A house should be assigned in case of a tie"
        assert house in ["GRYFFINDOR", "HUFFLEPUFF"], "One of the tied houses should be assigned"
        assert player.get_state("sorting_in_progress") is False, "Sorting should be marked as complete"
        assert len(messages) > 0, "Should return messages announcing the house"

    def test_calculate_result_cleans_up_state(self, sorting_hat, player, mock_house_functions):
        """Test that sorting states are properly reset."""
        # Arrange
        player.set_state("sorting_answers", [0, 1, 2, 3, 0])
        player.set_state("sorting_in_progress", True)
        player.set_state("on_last_question", True)
        player.set_state("sorting_delay_timer", 1)
        
        # Act
        sorting_hat._calculate_result(player)
        
        # Assert
        assert player.get_state("sorting_in_progress") is False, "sorting_in_progress should be reset"
        assert player.get_state("on_last_question") is False, "on_last_question should be reset"
    
    def test_player_interacted_starts_sorting_quiz(self, sorting_hat, player, monkeypatch):
        """Test that player_interacted starts the sorting quiz for a player who isn't sorted."""
        # Arrange
        active_position = Coord(12, 7)  # One of the positions defined in active_positions
        monkeypatch.setattr(player, "get_current_position", lambda: active_position)
        player.set_state("sorting_in_progress", False)
        player.set_state("sorting_answers", [])
        
        # Act
        messages = sorting_hat.player_interacted(player)
        
        # Assert
        assert player.get_state("sorting_in_progress") is True, "Sorting should be marked as in progress"
        assert isinstance(player.get_state("sorting_answers"), list), "Sorting answers should be initialized as list"
        assert len(messages) > 0, "Should return messages to start the sorting"

    def test_player_interacted_already_sorted(self, sorting_hat, player, monkeypatch):
        """Test that player_interacted allows re-sorting for a player who is already sorted."""
        # Arrange
        active_position = Coord(12, 7)  # One of the positions defined in active_positions
        monkeypatch.setattr(player, "get_current_position", lambda: active_position)
        player.set_state("House", "GRYFFINDOR")
        player.set_state("sorting_in_progress", False)
        
        # Act
        messages = sorting_hat.player_interacted(player)
        
        # Assert
        assert player.get_state("sorting_in_progress") is True, "Sorting should be marked as in progress even for already sorted player"
        assert isinstance(player.get_state("sorting_answers"), list), "Sorting answers should be initialized as list"
        assert len(messages) > 0, "Should return messages to start the sorting"

    def test_player_interacted_when_player_not_in_active_position(self, sorting_hat, player, monkeypatch):
        """Test return of empty list when player not in active position."""
        # Arrange
        inactive_position = Coord(5, 5)  # Position outside active range
        monkeypatch.setattr(player, "get_current_position", lambda: inactive_position)
        
        # Act
        messages = sorting_hat.player_interacted(player)
        
        # Assert
        assert messages == [], "Empty list should be returned when player not in active position"

    def test_player_already_sorting_in_progress(self, sorting_hat, player, monkeypatch):
        """Test that player_interacted handles case where sorting is already in progress."""
        # Arrange
        active_position = Coord(12, 7)  # One of the positions defined in active_positions
        monkeypatch.setattr(player, "get_current_position", lambda: active_position)
        player.set_state("sorting_in_progress", True)
        
        # Act
        messages = sorting_hat.player_interacted(player)
        
        # Assert
        assert len(messages) > 0, "Should return a message indicating sorting is already in progress"
        assert player.get_state("sorting_in_progress") is True, "Sorting status should remain True"
        
    # POSITION OBSERVER TESTS
        
    def test_update_position_when_player_in_active_position(self, sorting_hat, mock_text_bubble, monkeypatch):
        """Test that text bubble is shown when player is in an active position."""
        # Arrange
        office = DumbledoresOffice.get_instance()
        monkeypatch.setattr(office, "set_player_state", lambda state, val: None)
        monkeypatch.setattr(office, "send_grid_to_players", lambda: [])
        sorting_hat._text_bubble = mock_text_bubble["text_bubble"]
        sorting_hat._message_displayed = False
        mock_text_bubble["is_visible_return"] = False
        
        # Act
        active_position = Coord(12, 7)
        sorting_hat.update_position(active_position)
        
        # Assert
        assert mock_text_bubble["show_called"], "Text bubble should be shown when player is in active position"

    def test_update_position_when_player_not_in_active_position(self, sorting_hat, mock_text_bubble, monkeypatch):
        """Test that text bubble is hidden when player isn't in active position."""
        # Arrange
        office = DumbledoresOffice.get_instance()
        monkeypatch.setattr(office, "set_player_state", lambda state, val: None)
        monkeypatch.setattr(office, "send_grid_to_players", lambda: [])
        sorting_hat._text_bubble = mock_text_bubble["text_bubble"]
        sorting_hat._message_displayed = True
        mock_text_bubble["is_visible_return"] = True
        
        # Act
        inactive_position = Coord(5, 5)
        sorting_hat.update_position(inactive_position)
        
        # Assert
        assert mock_text_bubble["hide_called"], "Text bubble should be hidden when player is not in active position"
        assert sorting_hat._message_displayed is False, "message_displayed should be set to False"
        
    def test_update_position_when_text_bubble_already_visible(self, sorting_hat, mock_text_bubble, monkeypatch):
        """Test behavior when text bubble is already visible."""
        # Arrange
        office = DumbledoresOffice.get_instance()
        monkeypatch.setattr(office, "set_player_state", lambda state, val: None)
        monkeypatch.setattr(office, "send_grid_to_players", lambda: [])
        sorting_hat._text_bubble = mock_text_bubble["text_bubble"]
        sorting_hat._message_displayed = True
        mock_text_bubble["is_visible_return"] = True
        
        # Act
        active_position = Coord(12, 7)
        sorting_hat.update_position(active_position)
        
        # Assert
        assert mock_text_bubble["show_called"], "Text bubble's show should be called even when already visible"
        assert sorting_hat._message_displayed, "message_displayed should remain True"
        
    # OPTION SELECTION TESTS
    
    def test_select_option_when_not_sorting(self, sorting_hat, player):
        """Test that select_option returns empty list when player is not in sorting."""
        # Arrange
        player.set_state("sorting_in_progress", False)
        
        # Act
        messages = sorting_hat.select_option(player, "a) Bravery")
        
        # Assert
        assert messages == [], "select_option should return empty list when player is not in sorting"

    def test_select_option_parses_option_correctly(self, sorting_hat, sorting_player, mock_answer_question):
        """Test that option string is correctly parsed to the right index."""
        # Act & Assert
        sorting_hat.select_option(sorting_player, "a) Bravery")
        assert mock_answer_question["answer_index"] == 0, "Option 'a' should be parsed to index 0"
        
        sorting_hat.select_option(sorting_player, "b) Loyalty")
        assert mock_answer_question["answer_index"] == 1, "Option 'b' should be parsed to index 1"
        
        sorting_hat.select_option(sorting_player, "c) Intelligence")
        assert mock_answer_question["answer_index"] == 2, "Option 'c' should be parsed to index 2"
        
        sorting_hat.select_option(sorting_player, "d) Ambition")
        assert mock_answer_question["answer_index"] == 3, "Option 'd' should be parsed to index 3"

    def test_select_option_calls_answer_question(self, sorting_hat, player, mock_answer_question):
        """Test that select_option properly calls answer_question with correct parameters."""
        # Arrange
        player.set_state("sorting_in_progress", True)
        player.set_state("sorting_answers", [0, 1])  # Already answered 2 questions
        
        # Act
        messages = sorting_hat.select_option(player, "c) Intelligence")
        
        # Assert
        assert mock_answer_question["called"], "_answer_question should be called"
        assert mock_answer_question["player"] == player, "Player object should be passed to _answer_question"
        assert mock_answer_question["question_index"] == 2, "Question index should be based on number of existing answers"
        assert mock_answer_question["answer_index"] == 2, "Answer index should match the selected option (c = 2)"
        assert messages == ["mocked response"], "Messages from _answer_question should be returned"
    
    # UPDATE METHOD TESTS

    def test_update_method_normal_case(self, sorting_hat, player, monkeypatch):
        """Test the update method during normal operation."""
        # Arrange
        office = DumbledoresOffice.get_instance()
        monkeypatch.setattr(office, "get_player", lambda: player)
        monkeypatch.setattr(office, "get_player_state", lambda state, default=None: False)
        
        # Act
        messages = sorting_hat.update()
        
        # Assert
        assert messages == [], "Update should return empty list when no sorting is in progress"
        
    def test_update_method_with_sorting_delay_timer_decrement(self, sorting_hat, mock_sorting_completion):
        """Test that the sorting delay timer is decremented in update."""
        # Assert initial timer value
        assert mock_sorting_completion["timer_value"] == 2, "Timer should start at 2"
        
        # Act
        sorting_hat.update()
        
        # Assert
        assert mock_sorting_completion["timer_value"] == 1, "Timer should be decremented from 2 to 1"
        assert not mock_sorting_completion["calculate_result_called"], "calculate_result should not be called when timer > 0"

    def test_update_method_with_last_question_complete(self, sorting_hat, mock_sorting_completion):
        """Test the update method when the last question is complete and timer is done."""
        # Arrange
        mock_sorting_completion["timer_value"] = 0
        
        # Act
        messages = sorting_hat.update()
        
        # Assert
        assert mock_sorting_completion["calculate_result_called"], "calculate_result should be called when sorting is complete"
        assert messages == ["Result calculated"], "Messages from calculate_result should be returned"
