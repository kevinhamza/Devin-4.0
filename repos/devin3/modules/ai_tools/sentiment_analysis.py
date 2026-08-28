# Devin/modules/ai_tools/sentiment_analysis.py
# Purpose: An AI-powered tool for fine-grained sentiment analysis of text,
#          including overall sentiment, scoring, and topic-based analysis.

import logging
import os
import json
from dataclasses import dataclass, field
from typing import Dict, Optional, Any

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("SentimentAnalyzer")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

@dataclass
class SentimentResult:
    """Represents a detailed sentiment analysis of a piece of text."""
    overall_sentiment: str
    sentiment_score: float  # -1.0 (negative) to 1.0 (positive)
    rationale: str
    topic_sentiments: Dict[str, str] = field(default_factory=dict)

class SentimentAnalyzer:
    """
    Performs fine-grained sentiment analysis using an LLM.
    """
    def __init__(self, openai_api_key: Optional[str] = None):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not installed. Please 'pip install openai'.")
            
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            self.client = openai.OpenAI(api_key=self.openai_api_key)
            logger.info("OpenAI client initialized for Sentiment Analyzer.")
        else:
            self.client = None
            raise ValueError("OPENAI_API_KEY environment variable not set.")

    def _generate_analysis_prompt(self, text: str) -> str:
        """Constructs a detailed prompt to get a structured sentiment analysis."""
        
        return (
            "You are an expert sentiment analysis AI. Analyze the following text and provide a detailed sentiment breakdown. "
            "Your response MUST be a single, valid JSON object with no other text or explanations. The JSON object must have these exact keys:\n"
            '1. "overall_sentiment": A string, one of "Positive", "Negative", "Neutral", or "Mixed".\n'
            '2. "sentiment_score": A float between -1.0 (most negative) and 1.0 (most positive).\n'
            '3. "rationale": A brief string explaining the reasoning for your assessment.\n'
            '4. "topic_sentiments": A JSON object where keys are important topics/entities from the text and values are their specific sentiment ("Positive", "Negative", "Neutral").\n\n'
            f"Text to analyze:\n---\n{text}\n---\n\n"
            "JSON Output:"
        )

    def analyze(self, text: str) -> Optional[SentimentResult]:
        """
        Analyzes the sentiment of a given text and returns a structured result.
        """
        if not text.strip():
            logger.warning("Input text is empty. Cannot analyze sentiment.")
            return None
            
        prompt = self._generate_analysis_prompt(text)
        logger.info("Requesting sentiment analysis from LLM...")

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            content = response.choices[0].message.content
            
            # Parse the JSON response and create the dataclass
            data = json.loads(content)
            return SentimentResult(
                overall_sentiment=data.get("overall_sentiment", "Unknown"),
                sentiment_score=float(data.get("sentiment_score", 0.0)),
                rationale=data.get("rationale", ""),
                topic_sentiments=data.get("topic_sentiments", {})
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from LLM response: {e}")
            logger.error(f"Received content: {content}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during analysis: {e}")
            return None


# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== AI Sentiment Analysis Prototype 😃😠😐 ===")
    print("=========================================================")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable is not set. This demo cannot run.")
    else:
        analyzer = SentimentAnalyzer()
        
        # --- Define sample texts with varying sentiments ---
        texts_to_analyze = {
            "Positive": "I am thrilled with the new security patch! The performance is noticeably better and my concerns are completely addressed. Fantastic work by the development team.",
            "Negative": "This is a total disaster. The data breach is worse than they admit, the communication has been awful, and the so-called 'fix' doesn't work. I'm considering legal action.",
            "Neutral": "The update for version 4.2.1 will be deployed on Friday at 10:00 PM UTC. The deployment is expected to last approximately 15 minutes.",
            "Mixed": "While the new user interface is visually stunning and much more intuitive, the removal of the advanced export feature is a huge step backward for power users like me."
        }
        
        for sentiment_type, text in texts_to_analyze.items():
            print(f"\n--- Analyzing '{sentiment_type}' Text ---")
            print(f"Input: \"{text}\"")
            result = analyzer.analyze(text)
            
            if result:
                print("\nAnalysis Result:")
                print(f"  - Overall Sentiment: {result.overall_sentiment}")
                print(f"  - Sentiment Score:   {result.sentiment_score:.2f}")
                print(f"  - Rationale:         {result.rationale}")
                if result.topic_sentiments:
                    print("  - Topic Sentiments:")
                    for topic, sentiment in result.topic_sentiments.items():
                        print(f"    - '{topic}': {sentiment}")
            else:
                print("Analysis failed.")
            print("-" * 50)
            
    print("\n=========================================================")
    print("=== Sentiment Analysis Prototype Complete ===")
    print("=========================================================")
