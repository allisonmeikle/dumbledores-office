import pytest
import sys
from typing import TYPE_CHECKING

# Relative import to access the imports.py bridge
from ..imports import *

# Relative imports for our project files
from ..dumbledores_office import DumbledoresOffice
from ..house import House
from ..text_bubble import TextBubble, TextBubbleImage
from ..util import get_custom_dialogue_message

if TYPE_CHECKING:
    from coord import Coord
    from Player import HumanPlayer
    

class TestUtil:
    
    """Test suite for utility functions"""
    
    @pytest.fixture(autouse=True)
    def setup_environment(self, monkeypatch):
        """Setup necessary environment variables."""
        # Sets up environment variables needed for API calls in the background
        monkeypatch.setenv("GITHUB_LOGIN", "test_user")
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")
    
    @pytest.fixture
    def mock_sender(self):
        """Create a mock sender that implements SenderInterface."""
        return DumbledoresOffice.get_instance()
    
    @pytest.fixture
    def mock_recipient(self):
        """Create a mock recipient that implements RecipientInterface."""
        return HumanPlayer("test_player")
    
    @pytest.fixture
    def mock_dialogue_message(self, monkeypatch):
        """Create a mock DialogueMessage class and tracker."""
        # Create a tracker dictionary
        tracker = {
            "called": False,
            "sender": None,
            "recipient": None,
            "text": None,
            "image": None,
            "font": None,
            "bg_color": None,
            "text_color": None,
            "press_enter": None,
            "auto_delay": None
        }
        
        # Create a mock DialogueMessage constructor
        def mock_constructor(sender, recipient, text, image="", font='harryp', 
                            bg_color=(0, 0, 0), text_color=(255, 255, 255), 
                            press_enter=True, auto_delay=500):
            # Track the parameters
            tracker["called"] = True
            tracker["sender"] = sender
            tracker["recipient"] = recipient
            tracker["text"] = text
            tracker["image"] = image
            tracker["font"] = font
            tracker["bg_color"] = bg_color
            tracker["text_color"] = text_color
            tracker["press_enter"] = press_enter
            tracker["auto_delay"] = auto_delay
            
            # Return a dummy object that won't be used
            return object()
        
        # Get the module where DialogueMessage is imported
        util_module = sys.modules["COMP303_Project.util"]
        
        # Save the original
        original = util_module.DialogueMessage
        
        # Patch at the correct module level
        monkeypatch.setattr(util_module, "DialogueMessage", mock_constructor)
        
        # Return both the tracker and original for cleanup
        return tracker, original
    
    def test_get_custom_dialogue_message_with_default_parameters(self, mock_sender, mock_recipient, mock_dialogue_message):
        """Test creating a dialogue message with default parameters."""
        # Unpack the fixture return values
        tracker, _ = mock_dialogue_message
        
        # Test data
        test_text = "hello, wizard!"
        
        # Call the function
        get_custom_dialogue_message(mock_sender, mock_recipient, test_text)
        
        # Check parameters were correct
        assert tracker["called"], "The DialogueMessage constructor should have been called"
        assert tracker["sender"] == mock_sender
        assert tracker["recipient"] == mock_recipient
        assert tracker["text"] == test_text
        assert tracker["image"] == ""
        assert tracker["font"] == "harryp"
        assert tracker["bg_color"] == (0, 0, 0)
        assert tracker["text_color"] == (255, 255, 255)
        assert tracker["press_enter"] == True
        assert tracker["auto_delay"] == 500
    
    def test_get_custom_dialogue_message_with_custom_parameters(self, mock_sender, mock_recipient, mock_dialogue_message):
        """Test creating a dialogue message with custom parameters."""
        # Unpack the fixture return values
        tracker, _ = mock_dialogue_message
        
        # Test data
        test_text = "welcome to hogwarts!"
        test_image = "hogwarts.png"
        test_font = "arial"
        test_bg_color = (100, 100, 100)
        test_text_color = (200, 200, 200)
        test_press_enter = False
        test_auto_delay = 1000
        
        # Call the function
        get_custom_dialogue_message(
            mock_sender,
            mock_recipient,
            test_text,
            test_image,
            test_font,
            test_bg_color,
            test_text_color,
            test_press_enter,
            test_auto_delay
        )
        
        # Check parameters were correct
        assert tracker["called"], "The DialogueMessage constructor should have been called"
        assert tracker["sender"] == mock_sender
        assert tracker["recipient"] == mock_recipient
        assert tracker["text"] == test_text
        assert tracker["image"] == test_image
        assert tracker["font"] == test_font
        assert tracker["bg_color"] == test_bg_color
        assert tracker["text_color"] == test_text_color
        assert tracker["press_enter"] == test_press_enter
        assert tracker["auto_delay"] == test_auto_delay
    
    def test_get_custom_dialogue_message_with_partial_custom_parameters(self, mock_sender, mock_recipient, mock_dialogue_message):
        """Test creating a dialogue message with some custom parameters."""
        # Unpack the fixture return values
        tracker, _ = mock_dialogue_message
        
        # Test data
        test_text = "10 points to gryffindor!"
        test_image = "dumbledore.png"
        test_press_enter = False
        
        # Call the function
        get_custom_dialogue_message(
            mock_sender,
            mock_recipient,
            test_text,
            image=test_image,
            press_enter=test_press_enter
        )
        
        # Check parameters were correct
        assert tracker["called"], "The DialogueMessage constructor should have been called"
        assert tracker["sender"] == mock_sender
        assert tracker["recipient"] == mock_recipient
        assert tracker["text"] == test_text
        assert tracker["image"] == test_image
        assert tracker["font"] == 'harryp'  # Default
        assert tracker["bg_color"] == (0, 0, 0)  # Default
        assert tracker["text_color"] == (255, 255, 255)  # Default
        assert tracker["press_enter"] == test_press_enter
        assert tracker["auto_delay"] == 500  # Default
