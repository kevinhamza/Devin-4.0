# Devin/modules/ai_tools/recommendations.py
# Purpose: A proactive AI engine that analyzes the current state of an
#          assessment and recommends logical next steps.

import logging
import os
import json
from typing import List, Dict, Optional, Any

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Import other Devin AI modules for integration
from modules.ai_tools.ai_learning import AILearning

# Configure basic logging
logger = logging.getLogger("RecommendationEngine")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class RecommendationEngine:
    """
    Analyzes assessment context and uses an LLM to recommend next steps.
    """
    def __init__(self, memory_db_path: str, openai_api_key: Optional[str] = None):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not installed. Please 'pip install openai'.")
        
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
            logger.info("OpenAI client initialized for Recommendation Engine.")
        else:
            self.openai_client = None
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        
        # This engine needs access to the project's memory
        self.memory = AILearning(db_path=memory_db_path)
        
        # This defines the "actions" the recommender knows how to suggest.
        # It mirrors the tool schema from the chatbot engine.
        self.known_tools = [
            "run_subdomain_enumeration",
            "run_port_scan",
            "run_vulnerability_assessment",
            "run_web_scan",
            "exploit_cve",
        ]

    def _generate_recommendation_prompt(self, context_summary: str) -> str:
        """Constructs the master prompt for the LLM to reason about next steps."""
        
        prompt = (
            "You are 'Devin', an expert penetration testing strategist. Your task is to analyze the summary of an ongoing assessment "
            "and recommend the top 3 most logical next steps. Your recommendations must be actionable and follow a standard pentesting methodology "
            "(Recon -> Scanning -> Gaining Access -> Maintaining Access -> Covering Tracks).\n\n"
            "Here is a summary of what has been done so far:\n"
            f"---CONTEXT---\n{context_summary}\n---END CONTEXT---\n\n"
            "Based on this context, provide your top 3 recommendations. For each recommendation, provide a 'rationale' explaining why it's the logical next step, "
            "and a 'command' object representing the tool to run. The command must be one of the known tools.\n\n"
            f"Known Tools: {', '.join(self.known_tools)}\n\n"
            "Your response MUST be a valid JSON array of objects, with no other text or explanations. Format it like this:\n"
            '[\n'
            '  {\n'
            '    "rationale": "Your reasoning for the first recommendation.",\n'
            '    "command": {"tool_name": "name_of_tool", "parameters": {"param1": "value1"}}\n'
            '  },\n'
            '  {\n'
            '    "rationale": "Your reasoning for the second recommendation.",\n'
            '    "command": {"tool_name": "name_of_tool", "parameters": {"param1": "value1"}}\n'
            '  }\n'
            ']'
        )
        return prompt

    def get_next_step_recommendations(self, context_query: str) -> List[Dict[str, Any]]:
        """
        The main method to generate next-step recommendations.
        
        Args:
            context_query (str): A simple query describing the project, used to retrieve memories.
                                 (e.g., "Project AcmeCorp" or "target 10.0.0.1").
        """
        logger.info(f"Generating recommendations based on context query: '{context_query}'")
        
        # 1. Gather all relevant memories for the current context
        # In a real app, we'd filter by a project_id in the metadata.
        memories = self.memory.retrieve_memories(query=context_query, n_results=10)
        
        if not memories:
            return [{
                "rationale": "No context found. The first logical step is to discover subdomains or run a port scan on the primary target.",
                "command": {"tool_name": "run_subdomain_enumeration", "parameters": {"domain": "example.com"}}
            }]

        # 2. Create a concise summary of the memories for the prompt
        context_summary = "Key findings so far:\n" + "\n".join([f"- {mem['content']}" for mem in memories])
        
        # 3. Generate the prompt and call the LLM
        prompt = self._generate_recommendation_prompt(context_summary)
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.5
            )
            content = response.choices[0].message.content
            # The API can sometimes wrap the JSON array in a parent object.
            # We need to robustly extract the array.
            parsed_json = json.loads(content)
            # Find the first value in the dict that is a list (our recommendations)
            recommendations = next((v for v in parsed_json.values() if isinstance(v, list)), [])
            return recommendations

        except Exception as e:
            logger.error(f"Failed to get or parse recommendations from LLM: {e}")
            return []

# --- Example Usage ---
if __name__ == "__main__":
    import shutil
    
    print("=========================================================")
    print("=== AI Recommendation Engine Prototype 🤔💡 ===")
    print("=========================================================")
    
    if not (OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY")):
        print("ERROR: This demo requires 'openai' and an OPENAI_API_KEY environment variable.")
    else:
        memory_path = "./devin_recommendation_demo_mem"
        if os.path.exists(memory_path):
            shutil.rmtree(memory_path)
            
        try:
            # 1. Setup a memory database and add context for a simulated assessment
            # In a real app, the RecommendationEngine would take an existing AILearning instance.
            learner = AILearning(db_path=memory_path)
            learner.add_memory(
                content="Project 'WebAppTest' started against 'test-site.com'.",
                metadata={"project": "WebAppTest"}
            )
            learner.add_memory(
                content="Subdomain enumeration for 'test-site.com' found 'api.test-site.com'.",
                metadata={"project": "WebAppTest", "tool": "subdomain_enum"}
            )
            learner.add_memory(
                content="Port scan on 'api.test-site.com' (10.1.2.3) found port 443 open running Nginx 1.18.",
                metadata={"project": "WebAppTest", "tool": "network_scanner"}
            )
            
            # 2. Initialize the recommendation engine
            engine = RecommendationEngine(memory_db_path=memory_path)
            
            # 3. Get recommendations based on the current context
            recommendations = engine.get_next_step_recommendations(context_query="Project WebAppTest assessment")
            
            # 4. Print the results
            print("\n--- AI-Generated Next Step Recommendations ---")
            if recommendations:
                for i, rec in enumerate(recommendations):
                    print(f"\nRecommendation #{i+1}:")
                    print(f"  Rationale: {rec.get('rationale')}")
                    command = rec.get('command', {})
                    print(f"  Suggested Command: {command.get('tool_name')}({command.get('parameters', {})})")
            else:
                print("Could not generate recommendations.")

        finally:
            if os.path.exists(memory_path):
                shutil.rmtree(memory_path)
                logger.info(f"Cleaned up demo memory directory: {memory_path}")

    print("\n=========================================================")
    print("=== Recommendation Engine Prototype Complete ===")
    print("=========================================================")
