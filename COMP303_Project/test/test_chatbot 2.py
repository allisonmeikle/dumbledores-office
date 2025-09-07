import pytest
import os
import requests
from typing import TYPE_CHECKING, Dict, Any

from ..imports import *
from ..chatbot import ChatBot, ConversationStrategy, NullConversationStrategy
from ..house import House

class MockTimeout:
    """
    Mock implementation of the Timeout context manager used in ChatBot.
    
    This class simulates the behavior of the Timeout class from gevent
    allowing tests to run without requiring the actual gevent library.
    It implements the context manager protocol (__enter__, __exit__).
    """
    def __init__(self, seconds):
        self.seconds = seconds
    
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

class TestChatBot:
    """
    Tests for the Chatbot class.

    The Chatbot class implements a singleton pattern to interface with an LLM API for generating responses for various conversations in Dumbledore's office.
    """

    @pytest.fixture(autouse=True)
    def setup_environment(self, monkeypatch):
        """Setup Environment Variables For All Tests."""
        # Mock API key for testing
        monkeypatch.setenv("OPEN_ROUTER_API_KEY", "test_api_key")
        
        # Reset singleton instance before each test
        ChatBot._ChatBot__instance = None

    @pytest.fixture
    def chatbot_instance(self):
        """Create A Chatbot Instance For Testing."""
        return ChatBot.get_instance()

    @pytest.fixture
    def mock_requests_post(self, monkeypatch):
        """Mock Requests.Post To Avoid Actual Api Calls."""
        mock_tracker = {
            "called": False,
            "url": None,
            "headers": None,
            "json_data": None,
            "timeout": None,
            "response_content": "Test response from API",
            "raise_exception": False,
            "exception_type": None
        }

        class MockResponse:
            def __init__(self, content, status_code=200):
                self.content = content
                self.status_code = status_code
                self.text = "Mock response text"
            
            def json(self):
                return {
                    "choices": [
                        {
                            "message": {
                                "content": mock_tracker["response_content"]
                            }
                        }
                    ]
                }
            
            def raise_for_status(self):
                if mock_tracker["raise_exception"]:
                    exception_class = mock_tracker["exception_type"] or requests.exceptions.HTTPError
                    raise exception_class("Mock HTTP error")

        def mock_post(url, headers=None, json=None, timeout=None):
            mock_tracker["called"] = True
            mock_tracker["url"] = url
            mock_tracker["headers"] = headers
            mock_tracker["json_data"] = json
            mock_tracker["timeout"] = timeout
            
            if mock_tracker["raise_exception"]:
                if mock_tracker["exception_type"] == TimeoutError:
                    raise TimeoutError("Mock timeout error")
                elif mock_tracker["exception_type"] == Exception:
                    raise Exception("Mock general exception")
            
            return MockResponse(mock_tracker["response_content"])
        
        monkeypatch.setattr(requests, "post", mock_post)
        return mock_tracker

    @pytest.fixture
    def mock_timeout(self, monkeypatch):
        """Mock the Timeout class used in the ChatBot module."""
        monkeypatch.setattr("COMP303_Project.chatbot.Timeout", MockTimeout)
        return MockTimeout

    @pytest.fixture
    def test_strategy(self):
        """Create A Test Conversation Strategy."""
        class TestStrategy(ConversationStrategy):
            def __init__(self):
                self.house = "TestHouse"

            def _opening_message(self) -> str:
                return "This is a test opening message"

            def get_house(self) -> str:
                return self.house
        
        return TestStrategy()

    @pytest.fixture
    def chatbot_api_request(self, chatbot_instance, test_strategy, mock_requests_post):
        """Make A Get_Response Api Call And Return The Request Details."""
        # Call get_response
        chatbot_instance.get_response(test_strategy, "test input")
        
        # Return the request details
        return {
            "prompt": mock_requests_post["json_data"]["messages"][0]["content"],
            "url": mock_requests_post["url"],
            "headers": mock_requests_post["headers"],
            "model": mock_requests_post["json_data"]["model"],
            "called": mock_requests_post["called"]
        }

    @pytest.fixture
    def description_api_request(self, chatbot_instance, mock_requests_post, mock_timeout):
        """Make A Get_Description Api Call And Return The Request Details."""
        # call get_description
        chatbot_instance.get_description("Test Book Title")
        
        # check if json_data is properly populated
        if mock_requests_post["json_data"] is not None:
            return {
                "prompt": mock_requests_post["json_data"]["messages"][0]["content"],
                "url": mock_requests_post["url"],
                "headers": mock_requests_post["headers"],
                "model": mock_requests_post["json_data"]["model"],
                "called": mock_requests_post["called"]
            }
        else:
            # if json_data is None, return a simplified result
            return {
                "prompt": "",
                "url": mock_requests_post["url"],
                "headers": mock_requests_post["headers"],
                "model": "",
                "called": mock_requests_post["called"]
            }

    @pytest.fixture
    def error_response(self, mock_requests_post):
        """Configure Mock To Raise Exceptions And Return The Tracker."""
        def set_error(error_type):
            mock_requests_post["raise_exception"] = True
            mock_requests_post["exception_type"] = error_type
            return mock_requests_post
        return set_error

    # SINGLETON TESTS

    def test_singleton_pattern(self):
        """Tests That Chatbot Follows Singleton Pattern."""
        instance1 = ChatBot()
        instance2 = ChatBot()
        
        assert instance1 is instance2, "Different instances should reference the same object"

    def test_get_instance_method(self):
        """Tests That Get_Instance Returns The Same Instance."""
        instance1 = ChatBot()
        instance2 = ChatBot.get_instance()
        
        assert instance1 is instance2, "get_instance should return the same instance"

    def test_initialization_loads_api_key(self):
        """Tests That Api Key Is Loaded From Environment."""
        instance = ChatBot()
        
        assert instance.api_key == "test_api_key", "Api key should be loaded from environment"

    def test_initialization_missing_api_key(self, monkeypatch):
        """Tests That Exception Is Raised When Api Key Is Not Found."""
        # Remove API key from environment
        monkeypatch.delenv("OPEN_ROUTER_API_KEY", raising=False)
        
        # Reset singleton instance
        ChatBot._ChatBot__instance = None
        
        with pytest.raises(Exception) as excinfo:
            ChatBot()
        
        assert "API key was not found" in str(excinfo.value), "Proper error message should be shown"

    # GET_RESPONSE TESTS

    def test_get_response_formatting(self, chatbot_api_request):
        """Tests That Get_Response Correctly Formats The Prompt."""
        prompt = chatbot_api_request["prompt"]
        
        assert "This is a test opening message" in prompt, "Opening message should be in prompt"
        assert "TestHouse" in prompt, "House should be in prompt"
        assert "test input" in prompt, "User input should be in prompt"

    def test_get_response_api_call(self, chatbot_api_request):
        """Tests That Get_Response Correctly Calls The Api."""
        assert chatbot_api_request["called"], "requests.post should be called"
        assert "openrouter.ai/api" in chatbot_api_request["url"], "API URL should be openrouter.ai"
        assert chatbot_api_request["headers"]["Authorization"] == "Bearer test_api_key", "Api key should be in headers"
        assert chatbot_api_request["model"] == "deepseek/deepseek-chat-v3-0324:free", "Correct model should be used"

    def test_get_response_returns_api_response(self, chatbot_instance, test_strategy, mock_requests_post):
        """Tests That Get_Response Returns The Response From The Api."""
        mock_requests_post["response_content"] = "This is a mock API response"
        
        response = chatbot_instance.get_response(test_strategy, "test input")
        
        assert response == "This is a mock API response", "Response from api should be returned"

    def test_get_response_http_error(self, chatbot_instance, test_strategy, error_response):
        """Tests Get_Response Handling Of Http Errors."""
        error_response(requests.exceptions.HTTPError)
        
        response = chatbot_instance.get_response(test_strategy, "test input")
        
        assert "HTTP error occurred" in response, "Http error should be handled"

    def test_get_response_general_exception(self, chatbot_instance, test_strategy, error_response):
        """Tests Get_Response Handling Of General Exceptions."""
        error_response(Exception)
        
        response = chatbot_instance.get_response(test_strategy, "test input")
        
        assert "Error calling LLM via OpenRouter.ai" in response, "General error should be handled"

    def test_get_response_timeout(self, chatbot_instance, test_strategy, error_response):
        """Tests Get_Response Handling Of Timeout Exceptions."""
        error_response(TimeoutError)
        
        response = chatbot_instance.get_response(test_strategy, "test input")
        
        assert "Error calling LLM via OpenRouter.ai" in response, "Timeout error should be handled"

    def test_get_response_api_timeout_class(self, chatbot_instance, test_strategy, mock_requests_post, monkeypatch):
        """Tests Get_Response Handling Of Timeout Class Exception."""
        class Timeout(Exception):
            pass

        def mock_post_timeout(*args, **kwargs):
            raise Timeout("Mock timeout exception")
        
        monkeypatch.setattr(requests, "post", mock_post_timeout)
        
        response = chatbot_instance.get_response(test_strategy, "test input")
        
        assert "Error calling LLM via OpenRouter.ai" in response, "Timeout exception should be handled"

    # GET_DESCRIPTION TESTS

    def test_get_description_formatting(self, chatbot_instance, mock_requests_post, mock_timeout):
        """Tests That Get_Description Correctly Formats The Prompt."""
        # directly make the call and examine the request
        chatbot_instance.get_description("Test Book Title")
        
        # verify the request data
        assert mock_requests_post["called"], "requests.post should be called"
        if mock_requests_post["json_data"] is not None:
            assert "Test Book Title" in mock_requests_post["json_data"]["messages"][0]["content"], "Book title should be in prompt"
            assert "Harry Potter universe" in mock_requests_post["json_data"]["messages"][0]["content"], "Harry Potter reference should be in prompt"

    def test_get_description_api_call(self, chatbot_instance, mock_requests_post, mock_timeout):
        """Tests That Get_Description Correctly Calls The Api."""
        # directly make the call and examine the request
        chatbot_instance.get_description("Test Book Title")
        
        # verify API call details
        assert mock_requests_post["called"], "requests.post should be called"
        assert "openrouter.ai/api" in mock_requests_post["url"], "Api url should be openrouter.ai"
        assert mock_requests_post["headers"]["Authorization"] == "Bearer test_api_key", "Api key should be in headers"
        if mock_requests_post["json_data"] is not None:
            assert mock_requests_post["json_data"]["model"] == "deepseek/deepseek-chat-v3-0324:free", "Correct model should be used"

    def test_get_description_returns_api_response(self, chatbot_instance, mock_requests_post, mock_timeout):
        """Tests That Get_Description Returns The Response From The Api."""
        # set the expected response content
        mock_requests_post["response_content"] = "This is a book description"
        
        # make the call
        response = chatbot_instance.get_description("Test Book Title")
        
        # verify the response
        assert response == "This is a book description", "Description from api should be returned"

    def test_get_description_http_error(self, chatbot_instance, error_response, mock_timeout):
        """Tests Get_Description Handling Of Http Errors."""
        # set up the error
        error_response(requests.exceptions.HTTPError)
        
        # make the call
        response = chatbot_instance.get_description("Test Book Title")
        
        # verify error handling
        assert "HTTP error occurred" in response, "Http error should be handled"

    def test_get_description_timeout(self, chatbot_instance, error_response, mock_timeout):
        """Tests Get_Description Handling Of Timeout Exceptions."""
        error_response(TimeoutError)
        
        response = chatbot_instance.get_description("Test Book Title")
        
        assert "Error calling LLM via OpenRouter.ai" in response, "Timeout error should be handled"


class TestConversationStrategy:
    
    @pytest.fixture
    def mock_chatbot(self, monkeypatch):
        """Mock Chatbot To Avoid Actual Api Calls."""
        mock_tracker = {
            "get_response_called": False,
            "strategy": None,
            "message": None,
            "return_value": "Mock response from ChatBot"
        }
        
        chatbot = ChatBot.get_instance()
        
        def mock_get_response(strategy, message):
            mock_tracker["get_response_called"] = True
            mock_tracker["strategy"] = strategy
            mock_tracker["message"] = message
            return mock_tracker["return_value"]
        
        monkeypatch.setattr(chatbot, "get_response", mock_get_response)
        
        return mock_tracker

    @pytest.fixture
    def test_strategy(self):
        """Create A Concrete Conversation Strategy For Testing."""
        class TestStrategy(ConversationStrategy):
            def _opening_message(self) -> str:
                return "Test opening message"
        return TestStrategy()

    def test_get_response_calls_chatbot(self, test_strategy, mock_chatbot):
        """Tests That Get_Response Calls The Chatbot With Correct Parameters."""
        response = test_strategy.get_response("test message")
        
        assert mock_chatbot["get_response_called"], "chatbot.get_response should be called"
        assert mock_chatbot["strategy"] is test_strategy, "strategy should be passed to chatbot"
        assert mock_chatbot["message"] == "test message", "message should be passed to chatbot"
        assert response == "Mock response from ChatBot", "response from chatbot should be returned"

    def test_get_response_with_empty_message(self, test_strategy, mock_chatbot):
        """Tests Get_Response With An Empty Message."""
        response = test_strategy.get_response("")
        
        assert not mock_chatbot["get_response_called"] and response == "It appears you didn't say anything. Please share your thoughts.", "Empty message handler should be called"

    def test_get_response_with_whitespace_message(self, test_strategy, mock_chatbot):
        """Tests Get_Response With A Whitespace-Only Message."""
        response = test_strategy.get_response("   ")
        
        assert not mock_chatbot["get_response_called"] and response == "It appears you didn't say anything. Please share your thoughts.", "Empty message handler should be called"

    def test_start_conversation(self, test_strategy):
        """Tests That Start_Conversation Returns Opening Message."""
        message = test_strategy.start_conversation()
        
        assert message == "Test opening message", "Should return opening message"

    def test_get_house_behavior(self):
        """Tests The Actual Behavior Of Get_House Method."""
        class CustomStrategy(ConversationStrategy):
            def _opening_message(self) -> str:
                return "Test opening message"
        strategy = CustomStrategy()
        house = strategy.get_house()
        
        assert house == "Strategy", "Should return the matched part of the class name"

    def test_get_house_no_match_case(self, monkeypatch):
        """Tests That Get_House Returns 'Unknown' When No Match Is Found In Class Name."""
        class TestConversationStrategyWithNoMatch(ConversationStrategy):
            def _opening_message(self) -> str:
                return "Test opening message"
        strategy = TestConversationStrategyWithNoMatch()
        
        def mock_search(pattern, string):
            return None
        
        import re
        monkeypatch.setattr(re, "search", mock_search)
        
        house = strategy.get_house()
        
        assert house == "Unknown", "Should return 'Unknown' when no match is found"


class TestNullConversationStrategy:
    
    @pytest.fixture
    def null_strategy(self):
        """Create A NullConversationStrategy Instance."""
        return NullConversationStrategy()

    def test_get_response_returns_empty(self, null_strategy):
        """Tests That Get_Response Returns Empty String."""
        response = null_strategy.get_response("test message")
        
        assert response == "", "Should return empty string"

    def test_start_conversation_returns_empty(self, null_strategy):
        """Tests That Start_Conversation Returns Empty String."""
        message = null_strategy.start_conversation()
        
        assert message == "", "Should return empty string"

    def test_get_house_returns_empty(self, null_strategy):
        """Tests That Get_House Returns Empty String."""
        house = null_strategy.get_house()
        
        assert house == "", "Should return empty string"

    def test_opening_message_returns_empty(self, null_strategy):
        """Tests That _Opening_Message Returns Empty String."""
        message = null_strategy._opening_message()
        
        assert message == "", "Should return empty string"

    def test_handle_empty_message_returns_empty(self, null_strategy):
        """Tests That _Handle_Empty_Message Returns Empty String."""
        message = null_strategy._handle_empty_message()
        
        assert message == "", "Should return empty string"