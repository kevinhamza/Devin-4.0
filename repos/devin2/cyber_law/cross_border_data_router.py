# Devin/cyber_law/cross_border_data_router.py
# Purpose: An AI-powered decision engine to recommend compliant data storage
#          regions based on the data's likely legal jurisdiction (GDPR, CCPA, etc.).

import logging
import json
from enum import Enum
from typing import Dict, Any, Optional, List

try:
    from modules.all_ais_modules import AIAgent, AIProvider
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("DataRouter")
# (Logger setup omitted for brevity)

class DataJurisdiction(Enum):
    EU_GDPR = "EU (GDPR)"
    CA_CCPA = "California (CCPA)"
    PK_PDPL = "Pakistan (PDPL)"
    GENERAL = "General/Unknown"

class DataRouter:
    """
    An AI-powered engine to make data routing decisions based on privacy laws.
    """
    def __init__(self, ai_agent: AIAgent):
        if not DEVIN_CORE_AVAILABLE:
            raise ImportError(f"A core Devin module is missing. Error: {_import_error}")
        self.agent = ai_agent
        
        # This policy maps a legal jurisdiction to compliant storage regions.
        self.routing_policy = {
            DataJurisdiction.EU_GDPR: ["eu-central-1", "europe-west1"],
            DataJurisdiction.CA_CCPA: ["us-west-1", "us-west-2"],
            DataJurisdiction.PK_PDPL: ["me-south-1"],
            DataJurisdiction.GENERAL: ["us-east-1"] # Default region
        }
        logger.info("DataRouter initialized with jurisdiction policies.")

    def _determine_jurisdiction(self, data_payload: Dict) -> DataJurisdiction:
        """Uses an LLM to determine the likely legal jurisdiction of a data payload."""
        # Create a string representation of the data, filtering out sensitive values
        context_str = json.dumps({k: v for k, v in data_payload.items() if k not in ['name', 'email', 'phone']})
        
        prompt = (
            "You are a data privacy compliance expert. Based on the following user data, determine the most likely "
            "legal data protection jurisdiction. The primary jurisdictions to consider are the EU (GDPR), California (CCPA), "
            "and Pakistan (PDPL).\n\n"
            "Respond with a single identifier from this list: [\"EU_GDPR\", \"CA_CCPA\", \"PK_PDPL\", \"GENERAL\"]. "
            "Choose 'GENERAL' if no specific jurisdiction can be determined.\n\n"
            f"Data to analyze: {context_str}"
        )
        
        try:
            response = self.agent.get_general_chat_response([{"role": "user", "content": prompt}], AIProvider.OPENAI)
            # Find the first valid enum key in the response
            for key in DataJurisdiction.__members__:
                if key in response:
                    return DataJurisdiction[key]
        except Exception as e:
            logger.error(f"AI call failed during jurisdiction check: {e}")
        
        return DataJurisdiction.GENERAL

    def get_routing_decision(self, data_payload: Dict[str, Any]) -> Dict:
        """
        Analyzes a data payload and returns a routing decision.
        """
        logger.info(f"Analyzing data payload for routing decision...")
        jurisdiction = self._determine_jurisdiction(data_payload)
        recommended_regions = self.routing_policy.get(jurisdiction, self.routing_policy[DataJurisdiction.GENERAL])
        
        decision = {
            "detected_jurisdiction": jurisdiction.value,
            "recommended_storage_region": recommended_regions[0],
            "compliant_regions": recommended_regions
        }
        logger.info(f"Routing decision: Jurisdiction is {jurisdiction.value}, recommending region {recommended_regions[0]}.")
        return decision

# --- Example Usage ---
if __name__ == "__main__":
    import os
    print("=========================================================")
    print("=== Cross-Border Data Router Demo 🌍⚖️ ===")
    print("=========================================================")
    
    if not DEVIN_CORE_AVAILABLE or not os.getenv("OPENAI_API_KEY"):
        print("\nERROR: This demo requires the full Devin core and an OPENAI_API_KEY environment variable.")
    else:
        try:
            agent = AIAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))
            router = DataRouter(ai_agent=agent)
            
            # --- Define Sample Data Payloads ---
            payloads = {
                "German User": {"user_id": 101, "country": "Germany", "preferences": {"lang": "de"}},
                "California User": {"user_id": 202, "state": "California", "zip_code": "90210"},
                "Pakistan User": {"user_id": 303, "city": "Lahore", "country": "Pakistan"},
                "Generic User": {"user_id": 404, "country": "Brazil"} # Assume no specific rule for Brazil
            }
            
            print("\n--- Analyzing data payloads for compliant routing ---")
            for name, payload in payloads.items():
                decision = router.get_routing_decision(payload)
                print(f"\n  Payload for: {name}")
                print(f"    -> Detected Jurisdiction: {decision['detected_jurisdiction']}")
                print(f"    -> Recommended Region:  {decision['recommended_storage_region']}")

        except Exception as e:
            logger.error(f"Demo failed to run: {e}", exc_info=True)

    print("\n=========================================================")
    print("=== Data Router Demo Complete ===")
    print("=========================================================")
