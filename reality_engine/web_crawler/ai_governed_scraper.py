# Devin/reality_engine/web_crawler/ai_governed_scraper.py
# Purpose: An intelligent web scraper that uses an LLM to extract structured
#          data from a webpage based on a user-defined schema.

import logging
import requests
import json
from typing import Dict, Any, Optional

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("AIGovernedScraper")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False


class AIGovernedScraper:
    """
    Uses an LLM to understand and extract data from HTML content.
    """
    def __init__(self, openai_api_key: Optional[str] = None):
        if not BS4_AVAILABLE or not OPENAI_AVAILABLE:
            raise ImportError("Required libraries missing. 'pip install beautifulsoup4 openai'")
            
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            self.client = openai.OpenAI(api_key=self.openai_api_key)
            logger.info("OpenAI client initialized for AI Scraper.")
        else:
            self.client = None
            raise ValueError("OPENAI_API_KEY environment variable not set.")

    def _fetch_and_clean_html(self, url: str) -> Optional[str]:
        """Fetches the HTML from a URL and cleans it for LLM processing."""
        try:
            response = requests.get(url, headers={'User-Agent': 'Devin-AIScraper/1.0'}, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style tags to reduce noise and token count
            for element in soup(["script", "style", "nav", "footer"]):
                element.decompose()
            
            # Return a simplified version of the body content
            body = soup.find('body')
            return ' '.join(body.get_text(separator=' ').split()) if body else ""

        except requests.RequestException as e:
            logger.error(f"Failed to fetch or process URL {url}: {e}")
            return None

    def _generate_extraction_prompt(self, html_content: str, data_schema: Dict) -> str:
        """Constructs the prompt for the LLM to extract data."""
        return (
            "You are an expert data extraction AI. Your task is to analyze the provided HTML content "
            "and extract the information that matches the structure of the given JSON schema. "
            "Pay close attention to the descriptions in the schema to understand the data you need to find. "
            "Your response MUST be a single, valid JSON object that strictly adheres to the provided schema, containing the extracted data. "
            "Do not include any other text, explanations, or apologies.\n\n"
            "## JSON Schema ##\n"
            f"{json.dumps(data_schema, indent=2)}\n\n"
            "## HTML Content ##\n"
            f"{html_content[:15000]}\n\n"  # Truncate to avoid exceeding token limits
            "## Extracted Data (JSON Output) ##"
        )

    def extract_structured_data(self, url: str, data_schema: Dict) -> Optional[Dict]:
        """
        The main method to scrape a URL and extract data according to a schema.
        """
        logger.info(f"Starting AI-governed scrape of {url}...")
        
        cleaned_html = self._fetch_and_clean_html(url)
        if not cleaned_html:
            return None
            
        prompt = self._generate_extraction_prompt(cleaned_html, data_schema)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0 # Be precise
            )
            content = response.choices[0].message.content
            extracted_data = json.loads(content)
            logger.info("Successfully extracted and parsed structured data from the page.")
            return extracted_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from LLM response: {e}")
            logger.error(f"Received content: {content}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during AI extraction: {e}")
            return None


# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== AI-Governed Web Scraper Prototype 🧠🕸️ ===")
    print("=========================================================")

    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable is not set. This demo cannot run.")
    else:
        # Use 'books.toscrape.com', a website designed for web scraping practice.
        TARGET_URL = "http://books.toscrape.com/"
        
        # Define the schema of the data we want to extract.
        # The descriptions help the AI understand what to look for.
        BOOK_SCHEMA = {
            "type": "object",
            "properties": {
                "books": {
                    "type": "array",
                    "description": "A list of all book objects found on the page.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "The full title of the book."},
                            "price": {"type": "number", "description": "The price of the book as a float, without the currency symbol."},
                            "rating": {"type": "integer", "description": "The star rating of the book, as an integer from 1 to 5."}
                        },
                         "required": ["title", "price", "rating"]
                    }
                }
            }
        }

        try:
            scraper = AIGovernedScraper()
            extracted_data = scraper.extract_structured_data(TARGET_URL, BOOK_SCHEMA)
            
            if extracted_data and 'books' in extracted_data:
                print(f"\n--- Successfully Extracted {len(extracted_data['books'])} Books ---")
                
                # Print the first 3 results for demonstration
                for i, book in enumerate(extracted_data['books'][:3]):
                    print(f"\nBook #{i+1}")
                    print(f"  Title:  {book.get('title')}")
                    print(f"  Price:  £{book.get('price')}")
                    print(f"  Rating: {book.get('rating')} / 5 stars")
            else:
                print("\nFailed to extract the desired data from the page.")
                
        except Exception as e:
            logger.error(f"An unexpected error occurred during the demo: {e}")

    print("\n=========================================================")
    print("=== AI Scraper Prototype Complete ===")
    print("=========================================================")
