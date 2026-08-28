"""
tests/integration/test_nlp_conversation.py
Integration tests for the Natural Language Processing (NLP) conversational capabilities.
"""

import pytest
from modules.natural_language_processing import NLPModule

@pytest.fixture
def nlp_module():
    """Fixture for initializing the NLP module."""
    return NLPModule()

def test_basic_conversation(nlp_module):
    """Test basic conversational flow."""
    user_input = "Hello!"
    expected_response = "Hi there! How can I assist you today?"
    response = nlp_module.process_input(user_input)
    assert response == expected_response, f"Expected '{expected_response}', got '{response}'"

def test_fallback_responses(nlp_module):
    """Test fallback responses for unknown input."""
    user_input = "Blah blah blah"
    expected_response = "I'm sorry, I didn't quite understand that. Can you rephrase?"
    response = nlp_module.process_input(user_input)
    assert response == expected_response, f"Expected '{expected_response}', got '{response}'"

def test_task_execution(nlp_module):
    """Test if NLP module can handle task-specific requests."""
    user_input = "Can you set a reminder for me?"
    expected_response = "Sure! What time should I set the reminder for?"
    response = nlp_module.process_input(user_input)
    assert response == expected_response, f"Expected '{expected_response}', got '{response}'"

def test_contextual_followup(nlp_module):
    """Test handling of contextual conversations."""
    nlp_module.process_input("What's the weather like today?")
    user_input = "What about tomorrow?"
    expected_response = "Could you specify the location for tomorrow's weather forecast?"
    response = nlp_module.process_input(user_input)
    assert response == expected_response, f"Expected '{expected_response}', got '{response}'"

def test_error_handling(nlp_module):
    """Test error handling within the NLP module."""
    with pytest.raises(ValueError):
        nlp_module.process_input(None)

def test_conversational_personalization(nlp_module):
    """Test personalized responses based on user data."""
    user_input = "What's my schedule for today?"
    expected_response = "You have 3 meetings today: 10 AM with John, 2 PM with the marketing team, and 4 PM with the product manager."
    response = nlp_module.process_input(user_input)
    assert response == expected_response, f"Expected '{expected_response}', got '{response}'"
