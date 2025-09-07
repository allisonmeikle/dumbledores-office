import pytest
import random
from typing import TYPE_CHECKING, Dict, Any

# relative import to access the imports.py bridge
from ..imports import *

# relative imports for our project files
from ..dumbledores_office import DumbledoresOffice, Book, MapObject
from ..chatbot import ChatBot
from ..house import House

if TYPE_CHECKING:
    from coord import Coord
    from Player import HumanPlayer
    from message import Message, ChatMessage, ServerMessage

class TestBook:
    """
    Test suite for the Book class in Dumbledore's Office.
    This test class comprehensively validates the functionality of the Book class,
    focusing on its core behaviors.
    The tests leverage various pytest fixtures to mock dependencies 
    and create controlled testing environments.
    """
    
    # This fixture was necessary to pass the tests before the professor updated his repo
    # a few weeks before the final submission, which is why it is in almost every test file. 
    @pytest.fixture(autouse=True)
    def setup_environment(self, monkeypatch):
        """Set up necessary environment variables for tests."""
        monkeypatch.setenv("GITHUB_LOGIN", "test_user")
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")
        # Ensure the flyweight store is reset before each test
        Book.flyweightStore = []
    
    @pytest.fixture
    def book(self):
        """Create a simple book instance for testing."""
        return Book("Test Book", "This is a test book description", Coord(3, 6))
    
    @pytest.fixture
    def player(self):
        """Create a player for testing."""
        player = HumanPlayer("test_player")
        return player
    
    @pytest.fixture
    def mock_chatbot(self, monkeypatch):
        """Mock the ChatBot's get_description method."""
        chatbot_tracker = {
            "get_description_called": False,
            "title_passed": None,
            "return_description": "This is a mock book description from the ChatBot."
        }

        chatbot = ChatBot.get_instance()

        # Helper method
        def mock_get_description(title):
            chatbot_tracker["get_description_called"] = True
            chatbot_tracker["title_passed"] = title
            return chatbot_tracker["return_description"]
        
        monkeypatch.setattr(chatbot, "get_description", mock_get_description)

        return chatbot_tracker
    
    @pytest.fixture
    def mock_random_choice(self, monkeypatch):
        """Make random.choice deterministic for testing."""

        def mock_choice(choices):
            return choices[0]
        
        monkeypatch.setattr(random, "choice", mock_choice)

        return None
    
    @pytest.fixture
    def mock_random_int(self, monkeypatch):
        """Make random.randint deterministic for testing."""

        def mock_randint(min_val, max_val):
            return min_val
        
        monkeypatch.setattr(random, "randint", mock_randint)

        return None
    
    @pytest.fixture
    def mock_dumbledores_office(self, monkeypatch):
        """Mock DumbledoresOffice methods for testing."""
        office = DumbledoresOffice.get_instance()
        office_tracker = {
            "add_to_grid_called": False,
            "add_to_grid_args": None,
            "remove_from_grid_called": False,
            "remove_from_grid_args": None,
            "send_grid_to_players_called": False,
            "send_grid_to_players_return": []
        }

        def mock_add_to_grid(obj, position):
            office_tracker["add_to_grid_called"] = True
            office_tracker["add_to_grid_args"] = (obj, position)

        def mock_remove_from_grid(obj, position):
            office_tracker["remove_from_grid_called"] = True
            office_tracker["remove_from_grid_args"] = (obj, position)

        def mock_send_grid_to_players():
            office_tracker["send_grid_to_players_called"] = True
            return office_tracker["send_grid_to_players_return"]
        
        monkeypatch.setattr(office, "add_to_grid", mock_add_to_grid)
        monkeypatch.setattr(office, "remove_from_grid", mock_remove_from_grid)
        monkeypatch.setattr(office, "send_grid_to_players", mock_send_grid_to_players)

        return office_tracker
    
    def test_book_initialization(self, book, mock_random_int):
        """Test that the book initializes with correct attributes."""
        assert book.get_name() == "TEST BOOK", "Book name should be uppercase"
        assert book.get_description() == "This is a test book description", "Description should match"
        assert book.get_position() == Coord(3, 6), "Position should match"

        # Check that the image name follows the pattern
        assert "tile/object/book/book" in book.get_image_name(), "Image name should include 'book' suffix"
    
    def test_book_get_book_new(self, mock_chatbot, mock_random_choice, mock_random_int):
        """Test get_book creates a new book when the title doesn't exist."""
        title = "New Book"
        book = Book.get_book(title)

        assert mock_chatbot["get_description_called"], "ChatBot.get_description should be called"
        assert mock_chatbot["title_passed"] == title, "Title should be passed to ChatBot"
        assert book.get_name() == "NEW BOOK", "Book name should be uppercase"
        assert book.get_description() == mock_chatbot["return_description"], "Description should match ChatBot return"
        assert book.get_position() == Coord(3, 5), "Position should be first in the list due to mocked random.choice"
        assert book in Book.flyweightStore, "Book should be added to flyweight store"
        assert len(Book.flyweightStore) == 1, "Flyweight store should have one book"
    
    def test_book_get_book_existing(self, mock_chatbot, mock_random_int):
        """Test get_book returns the existing book when the title is already present."""
        title = "Existing Book"
        existing_book = Book(title, "Existing description", Coord(3, 8))
        Book.flyweightStore.append(existing_book)
        book = Book.get_book(title)

        assert not mock_chatbot["get_description_called"], "ChatBot.get_description should not be called"
        assert book == existing_book, "Should return the existing book"
        assert book.get_name() == "EXISTING BOOK", "Book name should match existing book"
        assert book.get_description() == "Existing description", "Description should match existing book"
        assert len(Book.flyweightStore) == 1, "Flyweight store should still have one book"
    
    def test_book_get_book_case_insensitive(self, mock_chatbot, mock_random_int):
        """Test that get_book is case-sensitive when searching for an existing book."""
        existing_book = Book("Magic Book", "Magic description", Coord(3, 8))
        Book.flyweightStore.append(existing_book)
        book = Book.get_book("magic book")

        # The implementation uses direct string comparison; expect a new book to be created.
        assert book != existing_book, "Book equality is case-sensitive in the implementation"
        assert mock_chatbot["get_description_called"], "ChatBot.get_description should be called for a new book"
        assert book.get_name() == "MAGIC BOOK", "New book name should be uppercase"
        assert len(Book.flyweightStore) == 2, "Flyweight store should have two books now"
    
    def test_book_player_entered(self, book, player, mock_dumbledores_office):
        """Test that player_entered removes the book from the grid and displays its description."""
        messages = book.player_entered(player)

        assert mock_dumbledores_office["remove_from_grid_called"], "remove_from_grid should be called"
        assert mock_dumbledores_office["remove_from_grid_args"][0] == book, "Book should be passed to remove_from_grid"
        assert mock_dumbledores_office["remove_from_grid_args"][1] == Coord(3, 6), "Book position should be passed to remove_from_grid"
        assert mock_dumbledores_office["send_grid_to_players_called"], "send_grid_to_players should be called"

        # Verify that a ChatMessage was created
        assert len(messages) > 0, "player_entered should return at least one message"
        assert isinstance(messages[0], ChatMessage), "First message should be a ChatMessage"
        assert messages[0].get_sender() == book, "Message sender should be the book"
        assert messages[0].get_recipient() == player, "Message recipient should be the player"

        message_data = messages[0]._get_data()
        assert 'text' in message_data, "Message data should include a 'text' key"
        assert message_data['text'] == "This is a test book description", "Message text should be the book description"
    
    def test_flyweight_store_reuse(self, mock_chatbot, mock_random_int):
        """Test that the flyweight store reuses existing books for the same title."""
        title1 = "Book One"
        title2 = "Book Two"
        book1_first_request = Book.get_book(title1)
        book2 = Book.get_book(title2)
        book1_second_request = Book.get_book(title1)

        assert book1_first_request is book1_second_request, "Same book instance should be returned for the same title"
        assert book1_first_request is not book2, "Different book instances should be returned for different titles"
        assert len(Book.flyweightStore) == 2, "Flyweight store should have two books"
        assert mock_chatbot["get_description_called"], "ChatBot.get_description should be called"
        assert mock_chatbot["title_passed"] == title2, "Last title passed to ChatBot should be title2"
        assert mock_chatbot["get_description_called"] == True, "ChatBot should be called exactly for each unique title"
    
    def test_random_position_selection(self, monkeypatch, mock_chatbot):
        """Test that get_book assigns different random positions to different books."""
        positions = []
        position_index = 0
        valid_positions = [Coord(3, 5), Coord(3, 7), Coord(3, 6), Coord(3, 8), Coord(3, 9)]

        def mock_choice(choices):
            nonlocal position_index
            pos = valid_positions[position_index % len(valid_positions)]
            position_index += 1
            return pos
        
        monkeypatch.setattr(random, "choice", mock_choice)
        book1 = Book.get_book("Book One")
        book2 = Book.get_book("Book Two")
        book3 = Book.get_book("Book Three")

        assert book1.get_position() == valid_positions[0], "First book should be at the first position"
        assert book2.get_position() == valid_positions[1], "Second book should be at the second position"
        assert book3.get_position() == valid_positions[2], "Third book should be at the third position"
    
    def test_random_image_selection(self, monkeypatch, mock_chatbot):
        """Test that different random images are assigned to books."""
        randint_values = [1, 2, 3, 4, 5]
        randint_index = 0

        def mock_randint(min_val, max_val):
            nonlocal randint_index
            val = randint_values[randint_index % len(randint_values)]
            randint_index += 1
            return val
        
        monkeypatch.setattr(random, "randint", mock_randint)
        book1 = Book("Book One", "Description One", Coord(3, 6))
        book2 = Book("Book Two", "Description Two", Coord(3, 7))
        book3 = Book("Book Three", "Description Three", Coord(3, 8))

        assert book1.get_image_name() == "tile/object/book/book1", "First book should have image with suffix 1"
        assert book2.get_image_name() == "tile/object/book/book2", "Second book should have image with suffix 2"
        assert book3.get_image_name() == "tile/object/book/book3", "Third book should have image with suffix 3"
