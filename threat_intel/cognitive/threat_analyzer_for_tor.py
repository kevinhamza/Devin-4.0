# Devin/threat_intel/cognitive/threat_analyzer.py
# Purpose: An AI-powered tool to analyze unstructured text and extract
#          structured threat intelligence indicators.

import logging
import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# --- CRITICAL SAFETY AND LEGAL NOTE ---
# This module is designed for DEFENSIVE security analysis of text to DETECT
# potential social engineering attacks. It does NOT generate any malicious
# or deceptive content. Accessing dark web forums or illicit marketplaces
# can have serious legal consequences and expose you to harmful material.
# This tool does NOT provide any functionality to connect to or scrape such sources.
# ----------------------------------------

try:
    from modules.all_ais_modules import AIAgent, AIProvider
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("AIThreatAnalyzer")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
logger.propagate = False

@dataclass
class IndicatorOfThreat:
    """A structured representation of a potential threat extracted from text."""
    indicator_type: str
    summary: str
    confidence_score: float
    extracted_cve: Optional[str] = None
    potential_impact: str = "Not assessed"
    raw_data: Dict = field(repr=False, default_factory=dict)

class AIThreatAnalyzer:
    """Uses an LLM to perform threat intelligence analysis on text."""
    def __init__(self, ai_agent: AIAgent):
        if not DEVIN_CORE_AVAILABLE:
            raise ImportError(f"A core Devin module is missing. Error: {_import_error}")
        self.agent = ai_agent

    def analyze_text_for_threats(self, text: str) -> List[IndicatorOfThreat]:
        """Analyzes a block of text and extracts a list of threat indicators."""
        logger.info("Analyzing text for threat indicators using the AI Agent...")
        prompt = (
            "You are a senior cybersecurity threat intelligence analyst. Your task is to analyze the following text "
            "and extract structured indicators of potential threats. Identify mentions of new malware, sales of stolen data, "
            "discussions of software vulnerabilities (including CVEs), or offers of hacking services.\n\n"
            "For each distinct threat you identify, provide a JSON object in a list. Each object must have the following keys:\n"
            "- \"indicator_type\": One of [\"MALWARE_MENTION\", \"VULNERABILITY_DISCUSSED\", \"DATA_LEAK_OFFERED\", \"SERVICE_OFFERED\"].\n"
            "- \"summary\": A one-sentence summary of the threat.\n"
            "- \"confidence_score\": Your confidence (0.0 to 1.0) that this is a credible, actionable threat.\n"
            "- \"extracted_cve\": The CVE identifier (e.g., \"CVE-2021-44228\") if one is mentioned, otherwise null.\n"
            "- \"potential_impact\": A brief assessment of the potential impact.\n\n"
            "If no threats are found, respond with an empty list []. Respond ONLY with the valid JSON list.\n\n"
            f"--- TEXT TO ANALYZE ---\n{text}\n--- END OF TEXT ---"
        )
        
        try:
            response_str = self.agent.get_general_chat_response([{"role": "user", "content": prompt}], AIProvider.OPENAI)
            raw_indicators = json.loads(response_str)
            
            # Validate and convert to dataclasses
            parsed_indicators = []
            for raw_ind in raw_indicators:
                parsed_indicators.append(IndicatorOfThreat(
                    indicator_type=raw_ind.get("indicator_type", "UNKNOWN"),
                    summary=raw_ind.get("summary", ""),
                    confidence_score=raw_ind.get("confidence_score", 0.0),
                    extracted_cve=raw_ind.get("extracted_cve"),
                    potential_impact=raw_ind.get("potential_impact", ""),
                    raw_data=raw_ind
                ))
            logger.info(f"Analysis complete. Extracted {len(parsed_indicators)} threat indicators.")
            return parsed_indicators
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to parse LLM response for threat analysis: {e}")
            return []

# --- Example Usage ---
if __name__ == "__main__":
    import os
    print("=========================================================")
    print("=== AI Threat Analyzer Demo 🕵️‍♂️ ===")
    print("=========================================================")

    # This is a SAFE, FABRICATED text sample for demonstration purposes.
    # It is designed to look like a forum post to test the AI's analytical capabilities.
    SAFE_SIMULATED_TEXT = """
    Title: New goodies for sale! Fresh DB and toolkit!

    Hey everyone,

    Got some new stuff available. First up, the new 'DataShredder 2.0' ransomware. It's written in Rust, fully undetectable. Bypasses EDR. Price is 0.5 BTC.

    Also, we've been having success with the recent Log4j vulnerability (CVE-2021-44228) on unpatched enterprise systems. We're offering a scanning and exploitation service, guaranteed access or no fee.

    Finally, I have a fresh database from a major US retailer. 500k user records with PII, including name, address, and salted passwords. Make me an offer. DM for samples.
    """
    
    if not DEVIN_CORE_AVAILABLE or not os.getenv("OPENAI_API_KEY"):
        print("\nERROR: This demo requires the full Devin core and an OPENAI_API_KEY environment variable.")
    else:
        try:
            agent = AIAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))
            analyzer = AIThreatAnalyzer(ai_agent=agent)
            
            print("--- Analyzing a simulated threat intelligence post... ---")
            indicators = analyzer.analyze_text_for_threats(SAFE_SIMULATED_TEXT)
            
            if indicators:
                print("\n--- Extracted Threat Indicators ---")
                for i, ind in enumerate(indicators):
                    print(f"\nIndicator #{i+1}:")
                    print(f"  Type:     {ind.indicator_type}")
                    print(f"  Summary:  {ind.summary}")
                    print(f"  CVE:      {ind.extracted_cve or 'N/A'}")
                    print(f"  Impact:   {ind.potential_impact}")
                    print(f"  Confidence: {ind.confidence_score:.0%}")
            else:
                print("No threat indicators were extracted from the text.")

        except Exception as e:
            logger.error(f"Demo failed to run: {e}", exc_info=True)

    print("\n=========================================================")
    print("=== AI Threat Analyzer Demo Complete ===")
    print("=========================================================")
