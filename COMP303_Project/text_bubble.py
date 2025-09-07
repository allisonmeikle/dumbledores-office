from .imports import *
from enum import Enum
from typing import TYPE_CHECKING

if (TYPE_CHECKING):
    from message import Message
    from tiles.base import MapObject

class TextBubbleImage(Enum):
    CHAT = "chat"
    CHAT_UP = "chat_up"
    SPACE = "space"
    SPACE_PHOENIX = "space_phoenix"
    BOOK = "book"
    BLANK = "blank"
    THINKING1 = "thinking1"
    THINKING2 = "thinking2"
    THINKING3 = "thinking3"

THINKING_IMAGES = [TextBubbleImage.THINKING1, TextBubbleImage.THINKING2, TextBubbleImage.THINKING3]

class TextBubble(MapObject):
    """
    Represents a text bubble that appears when the player is in proximity to an interactive object.
    """
    def __init__(self, default_image : TextBubbleImage) -> None:
        """
        Initializes the TextBubble object.

        Args:
            default_image (TextBubbleImage): The default image to display when the bubble is shown.
        """
        self._is_visible = False
        self._default_image = default_image
        super().__init__(f"tile/object/message/{TextBubbleImage.BLANK.value}", True, 3)

    def show(self) -> None:
        """
        Shows the text bubble if it is not already visible.
        Updates the image to the default bubble image.
        """
        # Check if the bubble is currently hidden
        if not self._is_visible:
            # If the bubble is not already visible, make it visible
            self._is_visible = True
            self.set_image_name(f"tile/object/message/{self._default_image.value}")
    
    def hide(self) -> None:
        """
        Hides the text bubble by setting its image to blank if currently visible.
        """
        if self._is_visible:
            self._is_visible = False
            self.set_image_name(f"tile/object/message/{TextBubbleImage.BLANK.value}")
    
    def is_visible(self) -> bool:
        """
        Checks if the text bubble is currently visible.

        Returns:
            bool: True if the bubble is visible; otherwise, False.
        """
        # Simply return the current visibility state
        return self._is_visible
    
    def set_to_default(self) -> None:
        """
        Sets the text bubble image back to its default.
        """
        self.set_image_name(f"tile/object/message/{self._default_image.value}")

    def get_image(self) -> TextBubbleImage:
        """
        Retrieves the currently displayed TextBubbleImage.

        Returns:
            TextBubbleImage: The current image being displayed by the bubble.
        """
        return TextBubbleImage(self.get_image_name().split("/")[-1])