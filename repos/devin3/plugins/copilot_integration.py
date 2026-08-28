# Devin/plugins/copilot_integration.py
# Purpose: An AI-powered code generation engine, similar to GitHub Copilot,
#          that can write, validate, and refine scripts on demand.

import logging
import os
import re
import ast
from typing import Optional, Dict, Any

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("Copilot")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class Copilot:
    """
    An AI engine for generating and refining code.
    """
    def __init__(self, openai_api_key: Optional[str] = None):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not installed. Please 'pip install openai'.")
            
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            self.client = openai.OpenAI(api_key=self.openai_api_key)
            logger.info("OpenAI client initialized for Copilot plugin.")
        else:
            self.client = None
            raise ValueError("OPENAI_API_KEY environment variable not set.")

    def _clean_llm_code_output(self, raw_output: str) -> str:
        """Strips Markdown fences and other text from the LLM's code response."""
        # Pattern to find code inside ```python ... ``` or ``` ... ```
        match = re.search(r"```(?:python\n)?(.*)```", raw_output, re.DOTALL)
        if match:
            return match.group(1).strip()
        # Fallback if no markdown fences are found
        return raw_output.strip()

    def _validate_python_syntax(self, code: str) -> bool:
        """Checks if the generated code is syntactically valid Python."""
        try:
            ast.parse(code)
            logger.info("Generated code passed syntax validation.")
            return True
        except SyntaxError as e:
            logger.error(f"Generated code has a syntax error: {e}")
            return False

    def _call_llm_for_code(self, prompt: str) -> str:
        """Helper function to call the LLM with a specific code-gen system prompt."""
        system_prompt = (
            "You are an expert programmer and your sole purpose is to write clean, efficient, and correct code based on a user's request. "
            "You must only respond with the code itself. Do not include any explanations, greetings, or conversational text. "
            "Wrap Python code in ```python ... ``` markdown fences."
        )
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return f"# Error generating code: {e}"

    def generate_code(self, task_description: str, language: str = "python") -> Optional[str]:
        """
        Generates a script based on a natural language description.
        """
        logger.info(f"Generating {language} code for task: '{task_description[:50]}...'")
        prompt = f"Write a complete, executable {language} script that performs the following task:\n\n{task_description}"
        
        raw_code = self._call_llm_for_code(prompt)
        cleaned_code = self._clean_llm_code_output(raw_code)
        
        if self._validate_python_syntax(cleaned_code):
            return cleaned_code
        else:
            # Optional: Add a retry mechanism here to ask the AI to fix its own error.
            return None

    def refine_code(self, original_code: str, refinement_request: str) -> Optional[str]:
        """

        Takes existing code and a modification request, and returns the refined code.
        """
        logger.info(f"Refining code with request: '{refinement_request[:50]}...'")
        prompt = (
            "Here is an existing Python script:\n"
            "--- START CODE ---\n"
            f"{original_code}\n"
            "--- END CODE ---\n\n"
            "Please modify this script to incorporate the following change or feature. "
            "Return only the complete, updated script.\n\n"
            f"Modification Request: {refinement_request}"
        )
        
        raw_code = self._call_llm_for_code(prompt)
        cleaned_code = self._clean_llm_code_output(raw_code)

        if self._validate_python_syntax(cleaned_code):
            return cleaned_code
        else:
            return None

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== AI Copilot Code Generation Prototype 🤖💻 ===")
    print("=========================================================")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable is not set. This demo cannot run.")
    else:
        copilot = Copilot()
        
        # --- 1. Initial Code Generation Demo ---
        print("\n--- 1. Generating a new script ---")
        initial_prompt = (
            "Write a Python script that takes a URL as a single command-line argument. "
            "The script should use the 'requests' and 'BeautifulSoup4' libraries to download the HTML from the URL "
            "and print the total number of '<a>' tags found on the page."
        )
        generated_code = copilot.generate_code(initial_prompt)
        
        if generated_code:
            print("\nSuccessfully generated and validated the following script:")
            print("-" * 25 + " SCRIPT 1 " + "-" * 25)
            print(generated_code)
            print("-" * 60)
            
            # --- 2. Code Refinement Demo ---
            print("\n--- 2. Refining the generated script ---")
            refinement_prompt = (
                "Now, modify the script to add robust error handling. "
                "Specifically, it should handle cases where the URL is not provided, the URL is invalid, "
                "or the web request fails (e.g., a 404 error or a connection timeout). "
                "Print a user-friendly error message for each case."
            )
            refined_code = copilot.refine_code(generated_code, refinement_prompt)
            
            if refined_code:
                print("\nSuccessfully refined the script as follows:")
                print("-" * 25 + " SCRIPT 2 (REFINED) " + "-" * 25)
                print(refined_code)
                print("-" * 60)
            else:
                print("\nFailed to refine the code.")
        else:
            print("\nFailed to generate the initial code.")

    print("\n=========================================================")
    print("=== Copilot Prototype Complete ===")
    print("=========================================================")
