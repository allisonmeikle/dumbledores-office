import pytest
from typing import TYPE_CHECKING

# Relative import to access the imports.py bridge
from ..imports import *

# Relative imports for our project files
from ..text_bubble import TextBubble, TextBubbleImage, THINKING_IMAGES

if TYPE_CHECKING:
    from coord import Coord
    from Player import HumanPlayer

class TestTextBubble:
    
    """
    Test suite for the TextBubble class.
    Tests the initialization, visibility state management, and image management of text bubbles.
    """
    
    @pytest.fixture(autouse=True)
    def setup_environment(self, monkeypatch):
        """Setup necessary environment variables for tests."""
        # Sets up environment variables needed for API calls in the background
        monkeypatch.setenv("GITHUB_LOGIN", "test_user")
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")
    
    @pytest.fixture
    def chat_bubble(self):
        """Create a TextBubble with CHAT image."""
        return TextBubble(TextBubbleImage.CHAT)
    
    @pytest.fixture
    def space_bubble(self):
        """Create a TextBubble with SPACE image."""
        return TextBubble(TextBubbleImage.SPACE)
    
    @pytest.fixture
    def book_bubble(self):
        """Create a TextBubble with BOOK image."""
        return TextBubble(TextBubbleImage.BOOK)
    
    @pytest.fixture
    def thinking_bubble(self):
        """Create a TextBubble with THINKING1 image."""
        return TextBubble(TextBubbleImage.THINKING1)
    
    # INITIALIZATION TESTS
    
    def test_initialization_chat(self, chat_bubble):
        """Test that a TextBubble initializes correctly with CHAT image."""
        # Check initial state
        assert chat_bubble._is_visible is False, "New bubble should not be visible"
        assert chat_bubble._default_image == TextBubbleImage.CHAT, "Default image should be CHAT"
        assert chat_bubble.get_image_name() == f"tile/object/message/{TextBubbleImage.BLANK.value}", "Initial image name should be BLANK"
        assert chat_bubble.is_passable() is True, "TextBubble should be passable"
        assert chat_bubble.get_z_index() == 3, "TextBubble should have z-index 3"
    
    def test_initialization_space(self, space_bubble):
        """Test that a TextBubble initializes correctly with SPACE image."""
        # Check initial state
        assert space_bubble._is_visible is False, "New bubble should not be visible"
        assert space_bubble._default_image == TextBubbleImage.SPACE, "Default image should be SPACE"
        assert space_bubble.get_image_name() == f"tile/object/message/{TextBubbleImage.BLANK.value}", "Initial image name should be BLANK"
    
    def test_initialization_book(self, book_bubble):
        """Test that a TextBubble initializes correctly with BOOK image."""
        # Check initial state
        assert book_bubble._is_visible is False, "New bubble should not be visible"
        assert book_bubble._default_image == TextBubbleImage.BOOK, "Default image should be BOOK"
        assert book_bubble.get_image_name() == f"tile/object/message/{TextBubbleImage.BLANK.value}", "Initial image name should be BLANK"
    
    def test_initialization_thinking(self, thinking_bubble):
        """Test that a TextBubble initializes correctly with THINKING1 image."""
        # Check initial state
        assert thinking_bubble._is_visible is False, "New bubble should not be visible"
        assert thinking_bubble._default_image == TextBubbleImage.THINKING1, "Default image should be THINKING1"
        assert thinking_bubble.get_image_name() == f"tile/object/message/{TextBubbleImage.BLANK.value}", "Initial image name should be BLANK"
    
    # VISIBILITY TESTS
    
    def test_show_when_hidden(self, chat_bubble):
        """Test that show() makes a hidden bubble visible."""
        # Initially bubble is hidden
        assert chat_bubble.is_visible() is False
        
        # Show the bubble
        chat_bubble.show()
        
        # Check state after showing
        assert chat_bubble.is_visible() is True, "Bubble should be visible after show()"
        assert chat_bubble.get_image_name() == f"tile/object/message/{TextBubbleImage.CHAT.value}", "Image should be updated to CHAT"
    
    def test_show_when_already_visible(self, chat_bubble):
        """Test that show() doesn't change state when bubble is already visible."""
        # Make the bubble visible first
        chat_bubble.show()
        
        # Call show again
        chat_bubble.show()
        
        # Check state; should still be visible with same image
        assert chat_bubble.is_visible() is True, "Bubble should remain visible"
        assert chat_bubble.get_image_name() == f"tile/object/message/{TextBubbleImage.CHAT.value}", "Image should remain as CHAT"
    
    def test_hide_when_visible(self, chat_bubble):
        """Test that hide() makes a visible bubble hidden."""
        # Make the bubble visible first
        chat_bubble.show()
        assert chat_bubble.is_visible() is True
        
        # Hide the bubble
        chat_bubble.hide()
        
        # Check state after hiding
        assert chat_bubble.is_visible() is False, "Bubble should be hidden after hide()"
        assert chat_bubble.get_image_name() == f"tile/object/message/{TextBubbleImage.BLANK.value}", "Image should be updated to BLANK"
    
    def test_hide_when_already_hidden(self, chat_bubble):
        """Test that hide() doesn't change state when bubble is already hidden."""
        # Initially bubble is hidden
        assert chat_bubble.is_visible() is False
        
        # Call hide
        chat_bubble.hide()
        
        # Check state - should still be hidden with BLANK image
        assert chat_bubble.is_visible() is False, "Bubble should remain hidden"
        assert chat_bubble.get_image_name() == f"tile/object/message/{TextBubbleImage.BLANK.value}", "Image should remain BLANK"
    
    def test_is_visible_when_visible(self, chat_bubble):
        """Test that is_visible() returns True when bubble is visible."""
        # Make the bubble visible
        chat_bubble.show()
        
        # Check is_visible result
        assert chat_bubble.is_visible() is True, "is_visible() should return True for visible bubble"
    
    def test_is_visible_when_hidden(self, chat_bubble):
        """Test that is_visible() returns False when bubble is hidden."""
        # Check is_visible result (initial state is hidden)
        assert chat_bubble.is_visible() is False, "is_visible() should return False for hidden bubble"
    
    # IMAGE MANAGEMENT TESTS
    
    def test_set_to_default_when_hidden(self, chat_bubble):
        """Test that set_to_default() sets the image correctly when bubble is hidden."""
        # Call set_to_default on hidden bubble
        chat_bubble.set_to_default()
        
        # Check the image is updated but bubble remains hidden
        assert chat_bubble.get_image_name() == f"tile/object/message/{TextBubbleImage.CHAT.value}", "Image should be updated to CHAT"
        # note: set_to_default doesn't change visibility state, only the image
    
    def test_set_to_default_when_visible(self, chat_bubble):
        """Test that set_to_default() sets the image correctly when bubble is visible."""
        # Make bubble visible first
        chat_bubble.show()
        
        # Change the image to something else
        chat_bubble.set_image_name(f"tile/object/message/{TextBubbleImage.BOOK.value}")
        
        # Call set_to_default
        chat_bubble.set_to_default()
        
        # Check the image is restored to default
        assert chat_bubble.get_image_name() == f"tile/object/message/{TextBubbleImage.CHAT.value}", "Image should be restored to CHAT"
        assert chat_bubble.is_visible() is True, "Bubble should remain visible"
    
    def test_get_image(self, chat_bubble):
        """Test that get_image() returns the correct TextBubbleImage enum value."""
        # First show the bubble to set it to its default image (CHAT)
        chat_bubble.show()
        
        # Check get_image result
        assert chat_bubble.get_image() == TextBubbleImage.CHAT, "get_image() should return the CHAT enum value"
    
    def test_get_image_when_blank(self, chat_bubble):
        """Test that get_image() returns BLANK when the bubble is hidden."""
        # Bubble is initially hidden with BLANK image
        assert chat_bubble.get_image() == TextBubbleImage.BLANK, "get_image() should return BLANK for hidden bubble"
    
    def test_get_image_with_different_images(self):
        """Test that get_image() returns the correct enum value for different bubble types."""
        # Create bubbles with different images
        space_bubble = TextBubble(TextBubbleImage.SPACE)
        book_bubble = TextBubble(TextBubbleImage.BOOK)
        thinking_bubble = TextBubble(TextBubbleImage.THINKING1)
        
        # Show the bubbles to set their images
        space_bubble.show()
        book_bubble.show()
        thinking_bubble.show()
        
        # Check get_image results
        assert space_bubble.get_image() == TextBubbleImage.SPACE, "get_image() should return SPACE for space bubble"
        assert book_bubble.get_image() == TextBubbleImage.BOOK, "get_image() should return BOOK for book bubble"
        assert thinking_bubble.get_image() == TextBubbleImage.THINKING1, "get_image() should return THINKING1 for thinking bubble"
    
    # THINKING IMAGES TESTS
    
    def test_thinking_images_enum(self):
        """Test that THINKING_IMAGES contains the correct sequence of thinking bubble images."""
        # Check THINKING_IMAGES constant
        assert THINKING_IMAGES == [TextBubbleImage.THINKING1, TextBubbleImage.THINKING2, TextBubbleImage.THINKING3], "THINKING_IMAGES should contain the three thinking image enums in sequence"
    
    # EDGE CASE TESTS
    
    def test_image_paths_construction(self):
        """Test that image paths are constructed correctly for different bubble types."""
        # Test with each enum value
        for image_enum in TextBubbleImage:
            bubble = TextBubble(image_enum)
            bubble.show()  # Make visible to set the actual image
            expected_path = f"tile/object/message/{image_enum.value}"
            assert bubble.get_image_name() == expected_path, f"Image path for {image_enum.name} should be {expected_path}"
