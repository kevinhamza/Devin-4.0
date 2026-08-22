# Devin/privacy/data_obfuscation.py
# Purpose: A toolkit for detecting and anonymizing Personally Identifiable
#          Information (PII) in text data using Microsoft Presidio.

import logging
import os
import sys
from typing import List, Dict, Optional

# --- Core PII Detection Libraries ---
try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig, RecognizerResult
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False

# --- Library for generating fake data ---
try:
    from faker import Faker
    FAKER_AVAILABLE = True
except ImportError:
    FAKER_AVAILABLE = False

# --- spaCy is a dependency for Presidio's default model ---
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("DataObfuscator")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

class DataObfuscator:
    """
    Detects and anonymizes PII in text using various strategies.
    """
    def __init__(self):
        if not all([PRESIDIO_AVAILABLE, FAKER_AVAILABLE, SPACY_AVAILABLE]):
            raise ImportError("Required libraries missing. 'pip install presidio-analyzer presidio-anonymizer Faker spacy'")
        
        # Check for spaCy model and provide instructions if missing
        try:
            spacy.load("en_core_web_lg")
        except OSError:
            logger.error("spaCy model 'en_core_web_lg' not found.")
            logger.error("Please run: python -m spacy download en_core_web_lg")
            raise
            
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self.faker = Faker()

    def analyze_pii(self, text: str) -> List[RecognizerResult]:
        """
        Analyzes text to find Personally Identifiable Information (PII).
        
        Returns:
            A list of Presidio RecognizerResult objects.
        """
        logger.info("Analyzing text for PII...")
        return self.analyzer.analyze(text=text, language="en")

    def redact(self, text: str) -> str:
        """
        Redacts detected PII by replacing it with the entity type (e.g., <PERSON>).
        """
        logger.info("Redacting PII from text...")
        analyzer_results = self.analyze_pii(text)
        
        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results
        )
        return anonymized_result.text

    def pseudonymize_with_faker(self, text: str) -> str:
        """
        Anonymizes PII by replacing it with realistic fake data from Faker.
        """
        logger.info("Pseudonymizing PII with realistic fake data...")
        analyzer_results = self.analyze_pii(text)
        
        # Define custom faker operators for the anonymizer
        faker_operators = {
            "PERSON": OperatorConfig("custom", {"lambda": lambda x: self.faker.name()}),
            "EMAIL_ADDRESS": OperatorConfig("custom", {"lambda": lambda x: self.faker.email()}),
            "PHONE_NUMBER": OperatorConfig("custom", {"lambda": lambda x: self.faker.phone_number()}),
            "LOCATION": OperatorConfig("custom", {"lambda": lambda x: self.faker.city()}),
            "IP_ADDRESS": OperatorConfig("custom", {"lambda": lambda x: self.faker.ipv4()}),
        }

        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results,
            operators=faker_operators
        )
        return anonymized_result.text

# --- Example Usage ---
if __name__ == "__main__":
    if not all([PRESIDIO_AVAILABLE, FAKER_AVAILABLE, SPACY_AVAILABLE]):
        print("\nERROR: One or more required libraries are missing.")
        print("Please run: pip install presidio-analyzer presidio-anonymizer Faker spacy")
        sys.exit(1)

    print("=========================================================")
    print("=== Data Obfuscation & Privacy Prototype 🛡️🔒 ===")
    print("=========================================================")
    
    try:
        obfuscator = DataObfuscator()

        sample_text = (
            "Contact person: John Doe. You can reach him at john.doe@email.com or by phone at (555) 867-5309. "
            "The incident occurred near our office in New York. The source IP was 192.168.1.101."
        )
        print("--- Original Text ---")
        print(sample_text)
        
        # 1. PII Analysis Demo
        print("\n\n--- 1. PII Analysis Results ---")
        pii_results = obfuscator.analyze_pii(sample_text)
        if pii_results:
            for result in pii_results:
                print(f"  - Found '{result.entity_type}' from character {result.start} to {result.end} with score {result.score:.2f}")
        else:
            print("No PII found.")
            
        # 2. Redaction Demo
        print("\n\n--- 2. Redacted Text ---")
        redacted_text = obfuscator.redact(sample_text)
        print(redacted_text)
        
        # 3. Pseudonymization Demo
        print("\n\n--- 3. Pseudonymized Text (with Faker) ---")
        faker_text = obfuscator.pseudonymize_with_faker(sample_text)
        print(faker_text)

    except Exception as e:
        logger.error(f"Demo failed to run. Have you downloaded the spaCy model? Error: {e}")
        print("\nReminder: Please ensure you have downloaded the required spaCy model by running:")
        print("python -m spacy download en_core_web_lg")
    
    print("\n=========================================================")
    print("=== Data Obfuscation Prototype Complete ===")
    print("=========================================================")
