# Devin/modules/ai_tools/language_processing.py
# Purpose: A toolkit for advanced NLP tasks like entity extraction,
#          summarization, and translation, powered by an LLM.

import logging
import os
import json
import re
from typing import Dict, Optional, List

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

# Configure basic logging
logger = logging.getLogger("LanguageProcessor")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

class LanguageProcessor:
    """
    Performs specialized NLP tasks using a hybrid of regex and LLM.
    """
    def __init__(self, openai_api_key: Optional[str] = None):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not installed. Please 'pip install openai'.")
            
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            self.client = openai.OpenAI(api_key=self.openai_api_key)
            logger.info("OpenAI client initialized for Language Processor.")
        else:
            self.client = None
            raise ValueError("OPENAI_API_KEY environment variable not set.")

    def _call_llm(self, prompt: str, temperature: float = 0.2) -> str:
        """A generic helper to call the OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return f"Error communicating with AI: {e}"

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extracts security-relevant entities from a block of text.
        Uses a hybrid regex + LLM approach for best results.
        """
        logger.info("Extracting entities from text...")
        entities = {
            "ips": [],
            "domains": [],
            "cves": [],
            "urls": [],
            "files": []
        }
        
        # 1. Regex pass for common, well-structured entities
        entities["ips"] = list(set(re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', text)))
        entities["cves"] = list(set(re.findall(r'\bCVE-\d{4}-\d{4,7}\b', text, re.IGNORECASE)))
        entities['urls'] = list(set(re.findall(r'https?://[^\s/$.?#].[^\s]*', text)))

        # 2. LLM pass for more nuanced entities and context
        prompt = (
            "You are a security intelligence analyst. Your task is to extract specific entities from the following text. "
            "Focus on finding domain names (that are not part of a full URL) and file paths or file names. "
            "Provide your answer ONLY in a valid JSON object format with the keys 'domains' and 'files'. Do not add any other text or explanations.\n\n"
            f"Text to analyze:\n---\n{text}\n---\n\n"
            "JSON Output:"
        )
        
        llm_response = self._call_llm(prompt)
        try:
            llm_entities = json.loads(llm_response)
            if isinstance(llm_entities, dict):
                entities["domains"] = list(set(entities.get("domains", []) + llm_entities.get("domains", [])))
                entities["files"] = list(set(entities.get("files", []) + llm_entities.get("files", [])))
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from LLM entity response: {llm_response}")

        return entities

    def summarize_text(self, text: str, detail_level: str = 'medium') -> str:
        """
        Summarizes a block of text, focusing on security context.
        """
        logger.info(f"Summarizing text with detail level: {detail_level}...")
        
        length_instruction = {
            'short': 'in a single, concise sentence',
            'medium': 'in three key bullet points',
            'long': 'in a detailed paragraph'
        }.get(detail_level, 'in three key bullet points')

        prompt = (
            "You are a security analyst writing a briefing. Summarize the following text, focusing on the main threat, "
            f"vulnerability, or key takeaway. Present the summary {length_instruction}.\n\n"
            f"Text to summarize:\n---\n{text}\n---\n\n"
            "Summary:"
        )
        
        return self._call_llm(prompt, temperature=0.5)

    def translate_text(self, text: str, target_language: str) -> str:
        """Translates text to a target language."""
        logger.info(f"Translating text to {target_language}...")
        prompt = (
            f"Translate the following text into {target_language}. "
            "Provide ONLY the translated text in your response, with no extra explanations or phrases like 'Here is the translation'.\n\n"
            f"Text to translate:\n---\n{text}\n---"
        )
        return self._call_llm(prompt)


# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== AI Language Processing Toolkit Prototype 🗣️⚙️ ===")
    print("=========================================================")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable is not set. This demo cannot run.")
    else:
        processor = LanguageProcessor()
        
        # A mock security bulletin for testing
        sample_text = """
        Security Advisory - ZT-2025-001
        
        A critical remote code execution vulnerability, identified as CVE-2025-12345, has been discovered
        in the 'LogFusion' service, affecting all versions prior to 2.1.3. The vulnerability originates
        from the insecure processing of log files located in /var/logs/fusion.log.
        
        An unauthenticated attacker can exploit this by sending a specially crafted log entry to the
        server at 192.168.1.100. This triggers the vulnerability, allowing the attacker to run arbitrary
        commands. Our internal servers, including web.internal.corp and files.internal.corp, are potentially at risk.
        
        Administrators should immediately upgrade to version 2.1.3 or apply the patch available at
        https://vendor.com/patches/fusion_patch.zip.
        """
        
        # --- 1. Entity Extraction Demo ---
        print("\n--- 1. Extracting Entities ---")
        extracted_entities = processor.extract_entities(sample_text)
        print(json.dumps(extracted_entities, indent=2))
        
        # --- 2. Summarization Demo ---
        print("\n\n--- 2. Summarizing Text ---")
        summary = processor.summarize_text(sample_text, detail_level='medium')
        print(summary)
        
        # --- 3. Translation Demo ---
        print("\n\n--- 3. Translating Text ---")
        text_to_translate = "Administrators should immediately upgrade to version 2.1.3."
        translation = processor.translate_text(text_to_translate, "Spanish")
        print(f"Original: {text_to_translate}")
        print(f"Spanish: {translation}")


    print("\n=========================================================")
    print("=== Language Processing Toolkit Complete ===")
    print("=========================================================")
