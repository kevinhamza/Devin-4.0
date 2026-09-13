# # Devin/modules/robotics/natural_language_processing.py
# # Purpose: Provides Natural Language Processing (NLP) to understand user
# #          commands by extracting intent and entities from raw text.

# import logging
# from enum import Enum, auto
# from dataclasses import dataclass, field
# from typing import List, Dict, Optional, Any

# try:
#     import spacy
#     from spacy.tokens.doc import Doc
#     SPACY_AVAILABLE = True
# except ImportError:
#     SPACY_AVAILABLE = False
#     spacy, Doc = None, None

# # Configure basic logging
# logger = logging.getLogger("NLPProcessor")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# class Intent(Enum):
#     """Enumeration of recognized user intents."""
#     FIND_OBJECT = auto()
#     PICK_UP_OBJECT = auto()
#     MOVE_ROBOT = auto()
#     QUERY_STATUS = auto()
#     GREETING = auto()
#     UNKNOWN = auto()

# @dataclass
# class StructuredCommand:
#     """A structured representation of a user's command."""
#     intent: Intent
#     entities: Dict[str, Any] = field(default_factory=dict)
#     original_text: str

# class NLPProcessor:
#     """
#     Processes natural language text to extract structured commands.
#     """
#     def __init__(self, spacy_model: str = "en_core_web_sm"):
#         """
#         Initializes the NLP processor by loading a spaCy model.
#         """
#         if not SPACY_AVAILABLE:
#             self.nlp = None
#             logger.error("spaCy library not found! Please run: 'pip install spacy'.")
#             logger.error("Then download the model: 'python -m spacy download en_core_web_sm'")
#             return
            
#         try:
#             logger.info(f"Loading spaCy model '{spacy_model}'...")
#             self.nlp = spacy.load(spacy_model)
#             logger.info("NLP Processor initialized successfully.")
#         except OSError:
#             logger.error(f"spaCy model '{spacy_model}' not found.")
#             logger.error(f"Please run: python -m spacy download {spacy_model}")
#             self.nlp = None
            
#         # Define keywords for intent mapping
#         self.intent_keywords = {
#             Intent.FIND_OBJECT: ["find", "locate", "where is", "see"],
#             Intent.PICK_UP_OBJECT: ["pick up", "get", "grab", "take", "retrieve"],
#             Intent.MOVE_ROBOT: ["move to", "go to", "navigate"],
#             Intent.QUERY_STATUS: ["status", "how are you", "report"],
#             Intent.GREETING: ["hello", "hi", "hey"],
#         }
        
#     def _determine_intent(self, doc: Doc) -> Intent:
#         """Determines the primary intent from the processed text."""
#         text = doc.text.lower()
#         for intent, keywords in self.intent_keywords.items():
#             for keyword in keywords:
#                 if keyword in text:
#                     return intent
#         return Intent.UNKNOWN
        
#     def _extract_entities(self, doc: Doc) -> Dict[str, Any]:
#         """Extracts entities using spaCy's NER and custom rule-based logic."""
#         entities = {}
        
#         # 1. Use spaCy's built-in Named Entity Recognition (NER)
#         for ent in doc.ents:
#             entities[ent.label_.lower()] = ent.text
            
#         # 2. Custom rule-based entity extraction
#         # This is where domain-specific knowledge is added.
#         colors = ["red", "blue", "green", "yellow", "black", "white"]
        
#         for token in doc:
#             # Extract color attributes
#             if token.lemma_ in colors:
#                 # Find the noun the color is describing
#                 head_noun = token.head
#                 if head_noun.pos_ == "NOUN":
#                      # Check if we already have an object, if not, add it
#                     if "object" not in entities:
#                         entities["object"] = head_noun.text
#                     # Add the color attribute
#                     entities["color"] = token.lemma_
                    
#             # A simple way to find the main object of a "pick up" command
#             if token.lemma_ in self.intent_keywords[Intent.PICK_UP_OBJECT]:
#                 # Find the direct object (dobj) of the verb
#                 for child in token.children:
#                     if child.dep_ == "dobj":
#                         entities["object"] = child.text
#                         break # Take the first direct object
                        
#         return entities

#     def process_command(self, text: str) -> Optional[StructuredCommand]:
#         """
#         Processes a raw text command into a structured format.

#         Returns:
#             Optional[StructuredCommand]: The structured command, or None if processing fails.
#         """
#         if not self.nlp:
#             logger.error("Cannot process command: NLP model not loaded.")
#             return None
            
#         logger.info(f"Processing text: '{text}'")
#         doc = self.nlp(text)
        
#         intent = self._determine_intent(doc)
#         entities = self._extract_entities(doc)
        
#         structured_command = StructuredCommand(
#             intent=intent,
#             entities=entities,
#             original_text=text
#         )
        
#         logger.info(f"Processed command: Intent={intent.name}, Entities={entities}")
#         return structured_command

# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Natural Language Processing (NLP) Prototype 🧠💬 ===")
#     print("=========================================================")
    
#     if not SPACY_AVAILABLE:
#         print("\n'spaCy' library not found. Please install it and download a model to run this demo.")
#     else:
#         nlp_processor = NLPProcessor()
        
#         if nlp_processor.nlp:
#             commands_to_test = [
#                 "Devin, could you please pick up the red bottle for me?",
#                 "Where is the nearest charging station?",
#                 "Hey Devin, what's your status?",
#                 "Find a person near the desk.",
#                 "Move to the kitchen.",
#                 "Grab the wrench."
#             ]
            
#             print("\n--- Testing a series of commands ---")
#             for command in commands_to_test:
#                 result = nlp_processor.process_command(command)
#                 if result:
#                     print(f"\nOriginal: '{result.original_text}'")
#                     print(f"  -> Intent: {result.intent.name}")
#                     print(f"  -> Entities:")
#                     if result.entities:
#                         for key, value in result.entities.items():
#                             print(f"     - {key.capitalize()}: {value}")
#                     else:
#                         print("     - None")
#                     print("-" * 20)

#     print("\n=========================================================")
#     print("=== NLP Prototype Complete ===")
#     print("=========================================================")







# Devin/modules/robotics/natural_language_processing.py
# Purpose: Provides a hybrid NLU system to understand user commands, using
#          a local ML model for speed and an LLM for complex queries.

from __future__ import annotations

import logging
import json
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

try:
    import spacy
    from spacy.tokens.doc import Doc
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    # For the LLM fallback
    from modules.all_ais_modules import AIAgent, AIProvider
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("NLPProcessor")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

class Intent(Enum):
    FIND_OBJECT = auto()
    PICK_UP_OBJECT = auto()
    MOVE_ROBOT = auto()
    QUERY_STATUS = auto()
    UNKNOWN = auto()

@dataclass
class StructuredCommand:
    intent: Intent
    original_text: str
    entities: Dict[str, Any] = field(default_factory=dict)

class NLPProcessor:
    """Processes natural language text into structured commands using a hybrid approach."""
    def __init__(self, spacy_model: str = "en_core_web_sm", llm_agent: Optional[AIAgent] = None):
        if not DEVIN_CORE_AVAILABLE:
            raise ImportError(f"A core Devin module is missing. Error: {_import_error}")
        
        self.llm_agent = llm_agent
        try:
            self.nlp = spacy.load(spacy_model)
        except OSError:
            raise RuntimeError(f"spaCy model '{spacy_model}' not found. Run: python -m spacy download {spacy_model}")

        self._train_intent_classifier()
        logger.info("NLP Processor initialized with trained intent classifier.")

    def _train_intent_classifier(self):
        """Trains a simple ML model to classify intents."""
        # Simple training data
        train_data = [
            ("find the red block", Intent.FIND_OBJECT), ("where is the screwdriver", Intent.FIND_OBJECT),
            ("pick up the box", Intent.PICK_UP_OBJECT), ("grab the blue cup", Intent.PICK_UP_OBJECT),
            ("go to the kitchen", Intent.MOVE_ROBOT), ("move forward two meters", Intent.MOVE_ROBOT),
            ("what is your status", Intent.QUERY_STATUS), ("report battery level", Intent.QUERY_STATUS),
        ]
        X_train = [text for text, intent in train_data]
        # scikit-learn's classifiers can't infer a target type from raw Enum
        # members (type_of_target returns "unknown" and fit() rejects it), so
        # train on the enum names and map back to Intent after predicting.
        y_train = [intent.name for text, intent in train_data]
        
        self.intent_classifier = Pipeline([
            ('tfidf', TfidfVectorizer()),
            # liblinear only supports binary classification; this has 4 intent
            # classes, so it needs a solver with native multiclass support.
            ('clf', LogisticRegression(solver='lbfgs', max_iter=1000)),
        ])
        self.intent_classifier.fit(X_train, y_train)
        logger.info("Local intent classifier trained successfully.")

    def _determine_intent_ml(self, text: str) -> Intent:
        """Determines intent using the trained scikit-learn model."""
        # The model returns a list with one item; it was trained on Intent
        # names (strings), so map the prediction back to the Intent enum.
        predicted_name = self.intent_classifier.predict([text.lower()])[0]
        return Intent[predicted_name]

    def _extract_entities(self, doc: Doc) -> Dict[str, Any]:
        """Extracts entities using spaCy's dependency parsing and NER."""
        entities = {}
        captured_adjectives = set()
        # Find the main object (noun chunks are great for this)
        for chunk in doc.noun_chunks:
            if "obj" in chunk.root.dep_: # direct object, object of preposition, etc.
                # Drop leading determiners ("the", "a") so callers composing
                # their own phrasing (e.g. "the {color} {object}") don't end
                # up with a duplicated article.
                content_tokens = [t for t in chunk if t.pos_ != "DET"]
                entities['object'] = " ".join(t.text for t in content_tokens) if content_tokens else chunk.text
                # Check for adjectives modifying the object
                for token in chunk:
                    if token.pos_ == "ADJ":
                        entities.setdefault('attributes', []).append(token.text)
                        captured_adjectives.add(token.i)
                break

        # Some modifiers (e.g. "the red one" in a follow-up clarification like
        # "find the ball" + "the red one") attach to a token that isn't part
        # of the object's own noun chunk, so noun-chunk scanning alone misses
        # them. Catch any adjectival modifier (amod) not already captured.
        for token in doc:
            if token.pos_ == "ADJ" and token.dep_ == "amod" and token.i not in captured_adjectives:
                entities.setdefault('attributes', []).append(token.text)

        # Find locations (GPE - Geopolitical Entity)
        for ent in doc.ents:
            if ent.label_ == "GPE":
                entities['location'] = ent.text
            elif ent.label_ == "CARDINAL" or ent.label_ == "QUANTITY":
                 entities['quantity'] = ent.text
        
        return entities

    def process_command(self, text: str) -> StructuredCommand:
        """Processes a raw text command into a structured format."""
        doc = self.nlp(text)
        intent = self._determine_intent_ml(text)
        entities = self._extract_entities(doc)

        # --- LLM Fallback for complex commands ---
        if intent == Intent.UNKNOWN and self.llm_agent:
            logger.warning("Local NLP model could not determine intent. Falling back to LLM...")
            llm_prompt = (
                "You are a Natural Language Understanding engine. Analyze the following user command and extract its "
                "intent and entities. The possible intents are: FIND_OBJECT, PICK_UP_OBJECT, MOVE_ROBOT, QUERY_STATUS. "
                "Respond ONLY with a single, valid JSON object with the keys 'intent' (as a string) and 'entities' (as a dictionary).\n\n"
                f"Command: \"{text}\""
            )
            response_str = self.llm_agent.get_general_chat_response(
                [{"role": "user", "content": llm_prompt}],
                provider=AIProvider.OPENAI
            )
            try:
                data = json.loads(response_str)
                intent = Intent[data.get("intent", "UNKNOWN")]
                entities = data.get("entities", {})
                logger.info(f"LLM successfully parsed command. Intent={intent.name}, Entities={entities}")
            except (json.JSONDecodeError, KeyError):
                logger.error(f"Failed to parse LLM response for NLP fallback: {response_str}")

        return StructuredCommand(intent=intent, entities=entities, original_text=text)

# --- Example Usage ---
if __name__ == "__main__":
    import os
    print("=========================================================")
    print("=== Hybrid NLP Processor (Live Demo) 🧠💬 ===")
    print("=========================================================")
    
    if not DEVIN_CORE_AVAILABLE:
        print(f"\nERROR: A core Devin module is missing. Error: {_import_error}")
    else:
        # For the LLM fallback demo, we need an AIAgent instance
        llm_agent = None
        if os.getenv("OPENAI_API_KEY"):
            from modules.all_ais_modules import AIAgent
            llm_agent = AIAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))
        else:
            print("WARNING: OPENAI_API_KEY not set. LLM fallback will be disabled for this demo.")
            
        try:
            nlp_processor = NLPProcessor(llm_agent=llm_agent)
            
            # --- 1. Simple Command (Handled by Local Model) ---
            print("\n--- 1. Testing a simple command (local model) ---")
            simple_cmd = "Devin, please grab the large blue screwdriver"
            result1 = nlp_processor.process_command(simple_cmd)
            print(f"  Original: '{result1.original_text}'")
            print(f"  --> Intent: {result1.intent.name}")
            print(f"  --> Entities: {result1.entities}")

            # --- 2. Complex Command (Should trigger LLM Fallback) ---
            print("\n\n--- 2. Testing a complex command (LLM fallback) ---")
            complex_cmd = "Hey Devin, could you navigate to the workshop and find me the wrench from the top drawer"
            result2 = nlp_processor.process_command(complex_cmd)
            print(f"  Original: '{result2.original_text}'")
            print(f"  --> Intent: {result2.intent.name}")
            print(f"  --> Entities: {result2.entities}")

        except (ImportError, RuntimeError, FileNotFoundError) as e:
            print(f"\nDemo failed to run. Have you downloaded the spaCy model? Error: {e}")
            print("  Run: python -m spacy download en_core_web_sm")

    print("\n=========================================================")
    print("=== NLP Prototype Complete ===")
    print("=========================================================")
