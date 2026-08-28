# Devin/plugins/seo_optimizer.py
# Purpose: A toolkit for analyzing and optimizing a webpage's on-page SEO
#          using web scraping and AI-powered recommendations.

import logging
import requests
from urllib.parse import urljoin, urlparse
from collections import Counter
import re

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    # This plugin uses the AIComposer for content generation
    from plugins.ai_composer import AIComposer
    AI_COMPOSER_AVAILABLE = True
except ImportError:
    AI_COMPOSER_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("SEO_Optimizer")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class SEO_Optimizer:
    """
    Analyzes and provides recommendations for on-page SEO factors.
    """
    def __init__(self, openai_api_key: Optional[str] = None):
        if not BS4_AVAILABLE:
            raise ImportError("BeautifulSoup4 is required. 'pip install beautifulsoup4'")
        
        self.headers = {'User-Agent': 'Devin-SEO-Optimizer/1.0'}
        self.ai_composer = None
        if AI_COMPOSER_AVAILABLE and (openai_api_key or os.getenv("OPENAI_API_KEY")):
            self.ai_composer = AIComposer(openai_api_key)
            # Add SEO-specific templates to our composer instance
            self.ai_composer.prompt_templates['seo_title'] = (
                "You are an expert SEO copywriter. Your task is to write a compelling, keyword-rich title tag under 60 characters. "
                "The title should be engaging to encourage clicks while being relevant to the keyword.\n\n"
                "**Target Keyword:** {keyword}\n"
                "**Original Title:** {original_title}\n\n"
                "Generate a new, optimized title tag."
            )
            self.ai_composer.prompt_templates['seo_meta_description'] = (
                "You are an expert SEO copywriter. Your task is to write an engaging meta description between 150-160 characters. "
                "It should accurately summarize the content and include a strong call-to-action.\n\n"
                "**Target Keyword:** {keyword}\n"
                "**Page Content Summary:** {content_summary}\n\n"
                "Generate a new, optimized meta description."
            )

    def analyze_onpage_seo(self, url: str, keyword: str) -> Optional[dict]:
        """Scrapes and analyzes key on-page SEO factors for a given URL and keyword."""
        logger.info(f"Analyzing on-page SEO for {url} with keyword '{keyword}'")
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch URL {url}: {e}")
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract text content for analysis
        text_content = ' '.join(t.strip() for t in soup.stripped_strings)
        words = re.findall(r'\b\w+\b', text_content.lower())
        word_count = len(words)
        keyword_count = words.count(keyword.lower())
        keyword_density = (keyword_count / word_count * 100) if word_count > 0 else 0

        analysis = {
            "url": url,
            "keyword": keyword,
            "title": soup.title.string.strip() if soup.title else "Not found",
            "meta_description": soup.find('meta', attrs={'name': 'description'})['content'].strip() if soup.find('meta', attrs={'name': 'description'}) else "Not found",
            "h1_tags": [h.get_text(strip=True) for h in soup.find_all('h1')],
            "h2_tags": [h.get_text(strip=True) for h in soup.find_all('h2')],
            "images_missing_alt": [img.get('src') for img in soup.find_all('img') if not img.get('alt', '').strip()],
            "word_count": word_count,
            "keyword_density_percent": round(keyword_density, 2)
        }
        return analysis

    def get_seo_recommendations(self, analysis_data: dict) -> Optional[str]:
        """Uses the AI Composer to generate SEO recommendations based on analysis data."""
        if not self.ai_composer:
            return "AI Composer not available to generate recommendations."
        
        logger.info("Generating AI-powered SEO recommendations...")
        # Create a new template on-the-fly for this specific task
        self.ai_composer.prompt_templates['seo_audit'] = (
            "You are a world-class SEO expert conducting an audit. Based on the following on-page SEO data, "
            "provide a prioritized list of actionable recommendations to improve the page's ranking for the target keyword. "
            "Focus on the most impactful changes first.\n\n"
            "**URL:** {url}\n"
            "**Target Keyword:** {keyword}\n"
            "**Title:** {title}\n"
            "**Meta Description:** {meta_description}\n"
            "**H1 Tags:** {h1_tags}\n"
            "**Keyword Density:** {keyword_density_percent}%\n"
            "**Images Missing Alt Text:** {images_missing_alt_count}\n\n"
            "Provide your audit recommendations in a clear, bulleted list."
        )
        
        # Create context for the prompt
        audit_context = analysis_data.copy()
        audit_context['images_missing_alt_count'] = len(audit_context.get('images_missing_alt', []))

        return self.ai_composer.compose('seo_audit', audit_context)

    def generate_seo_title(self, original_title: str, keyword: str) -> Optional[str]:
        """Uses AI Composer to generate an optimized title tag."""
        if not self.ai_composer: return "AI Composer not available."
        return self.ai_composer.compose('seo_title', {'original_title': original_title, 'keyword': keyword})

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== AI-Powered SEO Optimizer Prototype 📈🔍 ===")
    print("=========================================================")
    
    # We need AI Composer for this demo's full functionality.
    if not AI_COMPOSER_AVAILABLE or not os.getenv("OPENAI_API_KEY"):
        print("ERROR: This demo requires the AIComposer plugin and an OPENAI_API_KEY.")
    else:
        # Example blog post URL. Replace with any other URL you want to analyze.
        TARGET_URL = "https://www.backlinko.com/seo-techniques"
        TARGET_KEYWORD = "seo techniques"
        
        optimizer = SEO_Optimizer()
        
        # --- 1. Perform On-Page SEO Analysis ---
        print(f"\n--- 1. Analyzing On-Page SEO for '{TARGET_URL}' ---")
        analysis = optimizer.analyze_onpage_seo(TARGET_URL, TARGET_KEYWORD)
        
        if analysis:
            print(f"Title: {analysis['title']}")
            print(f"Meta Description: {analysis['meta_description'][:100]}...")
            print(f"H1 Tags: {analysis['h1_tags']}")
            print(f"Word Count: {analysis['word_count']}")
            print(f"Keyword Density: {analysis['keyword_density_percent']}%")
            print(f"Images Missing Alt Text: {len(analysis['images_missing_alt'])}")
            
            # --- 2. Get AI-Powered Recommendations ---
            print("\n--- 2. Generating AI SEO Recommendations ---")
            recommendations = optimizer.get_seo_recommendations(analysis)
            if recommendations:
                print(recommendations)
                
            # --- 3. Generate a new, optimized Title ---
            print("\n--- 3. Generating a New SEO Title with AI ---")
            new_title = optimizer.generate_seo_title(analysis['title'], TARGET_KEYWORD)
            if new_title:
                print(f"Original Title: {analysis['title']}")
                print(f"AI Suggestion: {new_title}")
        else:
            print("Failed to analyze the URL.")

    print("\n=========================================================")
    print("=== SEO Optimizer Prototype Complete ===")
    print("=========================================================")
