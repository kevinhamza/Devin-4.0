# Devin/plugins/chatbot_tools.py
# Purpose: A suite of general-purpose utility tools for the main chatbot,
#          including web search, calculation, and timekeeping.

import logging
import os
from typing import Optional, Dict, List
from datetime import datetime

try:
    from googlesearch import search
    GOOGLESEARCH_AVAILABLE = True
except ImportError:
    GOOGLESEARCH_AVAILABLE = False

try:
    import requests
    from bs4 import BeautifulSoup
    WEB_LIBS_AVAILABLE = True
except ImportError:
    WEB_LIBS_AVAILABLE = False

try:
    import numexpr
    NUMEXPR_AVAILABLE = True
except ImportError:
    NUMEXPR_AVAILABLE = False
    
try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False

try:
    # This plugin uses the LanguageProcessor for summarizing search results
    from modules.ai_tools.language_processing import LanguageProcessor
    AI_TOOLS_AVAILABLE = True
except ImportError:
    AI_TOOLS_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("ChatbotTools")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

class ChatbotTools:
    """
    Provides a suite of general-purpose tools for the chatbot engine.
    """
    def __init__(self, openai_api_key: Optional[str] = None):
        if not all([GOOGLESEARCH_AVAILABLE, WEB_LIBS_AVAILABLE, NUMEXPR_AVAILABLE, PYTZ_AVAILABLE]):
            raise ImportError("One or more dependencies are missing. 'pip install googlesearch-python requests beautifulsoup4 numexpr pytz'")

        self.language_processor = None
        if AI_TOOLS_AVAILABLE and (openai_api_key or os.getenv("OPENAI_API_KEY")):
            self.language_processor = LanguageProcessor(openai_api_key)
        else:
            logger.warning("LanguageProcessor not available. Web search will return raw text.")

    def perform_web_search(self, query: str, num_results: int = 3) -> Dict[str, any]:
        """Performs a web search, scrapes top results, and returns a summary."""
        logger.info(f"Performing web search for: '{query}'")
        try:
            urls = list(search(query, num_results=num_results, sleep_interval=2))
            
            content = ""
            for url in urls:
                try:
                    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Get text and limit length to avoid huge prompts
                    content += soup.get_text(separator=' ', strip=True)[:2000] + "\n\n"
                except requests.RequestException as e:
                    logger.warning(f"Could not fetch URL {url}: {e}")
            
            summary = "Could not generate a summary."
            if self.language_processor and content:
                summary = self.language_processor.summarize_text(
                    f"Based on the following web search results, provide a clear and concise answer to the query: '{query}'\n\n{content}"
                )
            elif not self.language_processor:
                summary = content # Fallback to raw content
            
            return {"summary": summary, "sources": urls}

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return {"summary": "An error occurred during the web search.", "sources": []}

    def calculate_expression(self, expression: str) -> str:
        """Safely evaluates a mathematical expression string."""
        logger.info(f"Calculating expression: '{expression}'")
        try:
            # Using numexpr for safe evaluation
            result = numexpr.evaluate(expression).item()
            return f"The result of '{expression}' is {result}."
        except Exception as e:
            logger.error(f"Failed to evaluate expression: {e}")
            return "I'm sorry, I couldn't calculate that. Please ensure it's a valid mathematical expression."

    def get_current_time(self, timezone_str: str = "UTC") -> str:
        """Gets the current time in a specified timezone."""
        logger.info(f"Getting current time for timezone: {timezone_str}")
        try:
            tz = pytz.timezone(timezone_str)
            now = datetime.now(tz)
            return f"The current time in {timezone_str} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}."
        except pytz.UnknownTimeZoneError:
            logger.error(f"Unknown timezone: {timezone_str}")
            return f"I'm sorry, I don't recognize the timezone '{timezone_str}'."
        except Exception as e:
            logger.error(f"Failed to get time: {e}")
            return "An error occurred while fetching the time."


# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Chatbot General Tools Prototype 🛠️🌍 ===")
    print("=========================================================")

    try:
        tools = ChatbotTools()

        # --- 1. Calculator Demo ---
        print("\n--- 1. Calculator Tool ---")
        math_expr = "(2**10) / 4 - 50"
        calculation_result = tools.calculate_expression(math_expr)
        print(calculation_result)

        # --- 2. Time Tool Demo ---
        print("\n--- 2. Time Tool ---")
        # Let's use the current location for this demo from the user's context
        time_result = tools.get_current_time("Asia/Karachi") # Corresponds to Lahore, Pakistan
        print(time_result)

        # --- 3. Web Search Demo ---
        print("\n--- 3. Web Search Tool ---")
        if tools.language_processor:
            search_query = "What is Retrieval-Augmented Generation (RAG)?"
            search_result = tools.perform_web_search(search_query)
            print(f"Query: '{search_query}'")
            print("\nAI-Generated Summary:")
            print(search_result['summary'])
            print("\nSources:")
            for source in search_result['sources']:
                print(f"- {source}")
        else:
            print("Web search demo skipped: AI LanguageProcessor not available (likely missing OpenAI API key).")

    except (ImportError, ValueError) as e:
        logger.error(f"Initialization failed: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the demo: {e}")

    print("\n=========================================================")
    print("=== Chatbot Tools Prototype Complete ===")
    print("=========================================================")
