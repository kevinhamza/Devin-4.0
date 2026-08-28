# Devin/plugins/ai_composer.py
# Purpose: An AI-powered content creation engine for generating various types
#          of text content, such as phishing emails and report sections.

import logging
import os
from typing import Optional, Dict, Any

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("AIComposer")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class AIComposer:
    """
    Uses an LLM with specialized templates to compose various types of text content.
    """
    def __init__(self, openai_api_key: Optional[str] = None):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not installed. Please 'pip install openai'.")
            
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            self.client = openai.OpenAI(api_key=self.openai_api_key)
            logger.info("OpenAI client initialized for AI Composer plugin.")
        else:
            self.client = None
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        
        # --- Prompt Template Library ---
        self.prompt_templates = {
            "phishing_email": (
                "You are a social engineering expert. Your task is to craft a highly convincing phishing email. "
                "Adopt the specified persona and create a sense of urgency or curiosity to entice the target to click a link. "
                "The link should be clearly marked with `[PHISHING_LINK]`.\n\n"
                "**Target Name:** {target_name}\n"
                "**Target Department:** {target_department}\n"
                "**Sender Persona:** {sender_persona}\n"
                "**Email Subject:** {subject}\n"
                "**Core Topic/Premise:** {topic}\n\n"
                "Compose the email now."
            ),
            "report_vulnerability_description": (
                "You are a professional cybersecurity report writer. Your task is to write a clear, formal description for a vulnerability finding. "
                "The description should include a summary of the vulnerability, the potential impact, and a brief technical overview.\n\n"
                "**Vulnerability Name:** {vulnerability_name}\n"
                "**Severity:** {severity}\n"
                "**Target URL/Asset:** {target_asset}\n\n"
                "Compose the detailed vulnerability description now."
            ),
            "code_documentation": (
                "You are a senior software developer writing technical documentation. Your task is to analyze the following code snippet and generate clear, user-friendly documentation for it. "
                "The documentation should include a description of the function's purpose, its parameters (with types and descriptions), what it returns, and a simple usage example.\n\n"
                "**Code Snippet:**\n```python\n{code_snippet}\n```\n\n"
                "Generate the documentation in Markdown format now."
            )
        }

    def compose(self, content_type: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Composes text content based on a specified type and context.

        Args:
            content_type (str): The key for the desired prompt template (e.g., 'phishing_email').
            context (Dict[str, Any]): A dictionary with values to format the prompt template.

        Returns:
            The AI-generated text content as a string, or None on failure.
        """
        logger.info(f"Composing content of type '{content_type}'...")
        
        template = self.prompt_templates.get(content_type)
        if not template:
            logger.error(f"No template found for content type: {content_type}")
            return None
            
        try:
            prompt = template.format(**context)
        except KeyError as e:
            logger.error(f"Missing key in context for template '{content_type}': {e}")
            return None

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6 # Allow for more creativity in writing
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return None

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== AI Composer Content Creation Prototype ✍️📜 ===")
    print("=========================================================")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable is not set. This demo cannot run.")
    else:
        composer = AIComposer()
        
        # --- 1. Phishing Email Generation Demo ---
        print("\n--- 1. Generating a Phishing Email ---")
        phishing_context = {
            "target_name": "Alice",
            "target_department": "Accounting",
            "sender_persona": "IT Help Desk",
            "subject": "Urgent: Action Required on Invoice System",
            "topic": "We are rolling out a mandatory update to the company's invoice processing software. All employees must log in to the new portal to migrate their accounts before end of day to avoid disruption."
        }
        phishing_email = composer.compose("phishing_email", phishing_context)
        if phishing_email:
            print(phishing_email)
        
        # --- 2. Code Documentation Demo ---
        print("\n\n" + "="*50 + "\n")
        print("--- 2. Generating Code Documentation ---")
        code_context = {
            "code_snippet": "def get_user_by_id(user_id: int, db_session) -> dict:\n    # ... function logic ...\n    return {'id': user_id, 'name': 'John Doe'}"
        }
        code_docs = composer.compose("code_documentation", code_context)
        if code_docs:
            print(code_docs)
            
        # --- 3. Vulnerability Description Demo ---
        print("\n\n" + "="*50 + "\n")
        print("--- 3. Generating a Vulnerability Report Description ---")
        vuln_context = {
            "vulnerability_name": "Stored Cross-Site Scripting (XSS)",
            "severity": "High",
            "target_asset": "User profile page, 'bio' field"
        }
        vuln_desc = composer.compose("report_vulnerability_description", vuln_context)
        if vuln_desc:
            print(vuln_desc)

    print("\n=========================================================")
    print("=== AI Composer Prototype Complete ===")
    print("=========================================================")
