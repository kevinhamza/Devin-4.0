# Devin/threat_intel/cognitive/meme_analysis_engine.py
# Purpose: An AI-powered engine to analyze viral media (memes) for the use
#          of psychological operations and propaganda techniques.

import logging
import json
import base64
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# --- CRITICAL NOTE ---
# This tool is for DEFENSIVE and EDUCATIONAL purposes to promote media literacy.
# It analyzes the techniques of persuasion, not the validity of the message.
# Analysis of viral content may expose you to controversial or offensive material.
# ----------------------------------------

try:
    from PIL import Image
    from io import BytesIO
    from modules.all_ais_modules import AIAgent, AIProvider
    from modules.user_interaction_module import UserInteractionManager
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("MemeAnalysisEngine")
# (Logger setup omitted for brevity, assumed to be configured)

@dataclass
class PsyopsTechnique:
    """A structured representation of a persuasive technique identified in content."""
    technique_name: str
    explanation: str
    confidence_score: float

class MemeAnalysisEngine:
    """Uses a multimodal LLM to detect psyops techniques in images and text."""
    def __init__(self, ai_agent: AIAgent, user_interaction_manager: UserInteractionManager):
        if not DEVIN_CORE_AVAILABLE:
            raise ImportError(f"A core Devin module is missing. Error: {_import_error}")
        self.agent = ai_agent
        self.uim = user_interaction_manager

    def analyze_meme(self, image_path: str, text_content: str) -> Optional[List[PsyopsTechnique]]:
        """Analyzes a meme's image and text for propaganda techniques."""
        
        consent_prompt = (
            "You are about to analyze media content for psychological operations.\n"
            "This may involve viewing controversial material. This tool is for educational purposes only.\n"
            "Do you consent to proceed with the analysis? (yes/no): "
        )
        if not self.uim.ask_for_confirmation(consent_prompt):
            logger.warning("Analysis aborted by user.")
            return None

        logger.info(f"Analyzing meme content from '{image_path}'...")
        
        try:
            with open(image_path, "rb") as image_file:
                b64_image = base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Could not read or encode image file: {e}")
            return None

        prompt = (
            "You are a world-class expert in media literacy, propaganda, and psychological operations. "
            "Your task is to analyze the provided image and its accompanying text. You must completely IGNORE the political or social "
            "viewpoint being expressed. Your ONLY focus is to identify the persuasive or manipulative techniques being used.\n\n"
            "Consider techniques such as: Ad Hominem, Appeal to Emotion, Bandwagon, Card Stacking, False Dichotomy, "
            "Glittering Generalities, Name-Calling, Plain Folks, Transfer, Whataboutism.\n\n"
            "Respond ONLY with a single, valid JSON object with a single key 'techniques'. This key should contain a list of objects, "
            "where each object represents one identified technique and has the following keys:\n"
            "- \"technique_name\": The name of the technique (e.g., \"Bandwagon\").\n"
            "- \"explanation\": A brief, neutral explanation of how this technique is used in the provided content.\n"
            "- \"confidence_score\": Your confidence (0.0 to 1.0) in this assessment.\n\n"
            "If no clear techniques are identified, return an empty list."
        )

        try:
            # Construct a multimodal request for the AIAgent
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "text", "text": f"Accompanying text: \"{text_content}\""},
                        {
                            "type": "image_url",
                            "image_url": { "url": f"data:image/png;base64,{b64_image}" }
                        }
                    ]
                }
            ]
            response_str = self.agent.get_general_chat_response(messages, AIProvider.OPENAI, config={"model": "gpt-4o"})
            data = json.loads(response_str)
            
            # Validate and convert to dataclasses
            techniques = [
                PsyopsTechnique(
                    technique_name=t.get("technique_name", "Unknown"),
                    explanation=t.get("explanation", ""),
                    confidence_score=t.get("confidence_score", 0.0)
                ) for t in data.get("techniques", [])
            ]
            logger.info(f"Analysis complete. Found {len(techniques)} potential techniques.")
            return techniques

        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to parse LLM response for meme analysis: {e}")
            return None

# --- Example Usage ---
if __name__ == "__main__":
    import os
    print("=========================================================")
    print("=== Meme Analysis Engine Demo (Defensive) 🧐🎭 ===")
    print("=========================================================")
    
    if not DEVIN_CORE_AVAILABLE or not os.getenv("OPENAI_API_KEY"):
        print("\nERROR: This demo requires the full Devin core, the 'Pillow' library, and an OPENAI_API_KEY.")
    else:
        # 1. Programmatically create a safe, non-political meme for analysis
        meme_path = Path("test_meme_bandwagon.png")
        img = Image.new('RGB', (600, 400), color = '#f0f0f0')
        draw = ImageDraw.Draw(img)
        # A simple visual element
        draw.rectangle([100, 150, 500, 250], fill='#33FF57')
        # This text clearly uses the "Bandwagon" technique
        meme_text = "EVERYONE is investing in DevCoin! Don't be the only one to miss out on the future of finance!"
        # In a real font-loading scenario, provide a path to a .ttf file
        # For simplicity, we'll use the default font if available, or skip text drawing
        try:
            from PIL import ImageFont
            font = ImageFont.truetype("arial.ttf", 20)
            draw.text((50, 50), "Join the Revolution!", fill='black', font=font)
        except IOError:
            print("Arial font not found, skipping text drawing on image. The analysis will use the text variable.")
        img.save(meme_path)
        
        print(f"Generated a safe test meme at '{meme_path}'.")
        print(f"Analyzing for propaganda techniques in the phrase: '{meme_text}'")
        
        try:
            agent = AIAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))
            uim = UserInteractionManager()
            engine = MemeAnalysisEngine(ai_agent=agent, user_interaction_manager=uim)

            techniques = engine.analyze_meme(str(meme_path), meme_text)
            
            if techniques is not None:
                if techniques:
                    print("\n--- Identified Persuasive Techniques ---")
                    for tech in techniques:
                        print(f"\n  Technique: {tech.technique_name} (Confidence: {tech.confidence_score:.0%})")
                        print(f"  Explanation: {tech.explanation}")
                else:
                    print("\n--- No clear persuasive techniques were identified. ---")
            
        except Exception as e:
            logger.error(f"Demo failed to run: {e}", exc_info=True)
        finally:
             # Clean up the generated meme
            if meme_path.exists():
                meme_path.unlink()

    print("\n=========================================================")
    print("=== Meme Analysis Demo Complete ===")
    print("=========================================================")
