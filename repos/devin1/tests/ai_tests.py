"""
tests/ai_tests.py
-----------------
Comprehensive test suite for AI modules in the Devin project. This script
validates the accuracy, performance, and integration of various AI-based
capabilities, including NLP, vision, audio, and data processing.
"""

import unittest
import time
from modules.nlp_tools import TextSummarizer, TextTranslator, TextClassifier
from plugins.image_processing import ImageEnhancer
from plugins.speech_recognition import SpeechRecognizer
from plugins.text_generation import TextGenerator

class TestNLPTools(unittest.TestCase):
    def setUp(self):
        self.summarizer = TextSummarizer()
        self.translator = TextTranslator()
        self.classifier = TextClassifier()

    def test_text_summarization(self):
        text = "Artificial Intelligence is transforming industries worldwide."
        summary = self.summarizer.summarize(text)
        self.assertTrue(len(summary) < len(text), "Summary is not shorter than original text.")

    def test_text_translation(self):
        text = "Hello, how are you?"
        translation = self.translator.translate(text, target_language="es")
        self.assertEqual(translation, "Hola, ¿cómo estás?", "Translation failed.")

    def test_text_classification(self):
        text = "The stock market is seeing significant growth this quarter."
        classification = self.classifier.classify(text)
        self.assertIn(classification, ["Finance", "News"], "Classification result is invalid.")

class TestImageProcessing(unittest.TestCase):
    def setUp(self):
        self.image_processor = ImageEnhancer()

    def test_image_enhancement(self):
        test_image_path = "test_images/sample.jpg"
        enhanced_image = self.image_processor.enhance(test_image_path)
        self.assertTrue(enhanced_image, "Image enhancement failed.")

class TestSpeechRecognition(unittest.TestCase):
    def setUp(self):
        self.recognizer = SpeechRecognizer()

    def test_speech_to_text(self):
        audio_path = "test_audio/sample.wav"
        text = self.recognizer.recognize(audio_path)
        self.assertIsInstance(text, str, "Speech-to-text conversion failed.")

class TestTextGeneration(unittest.TestCase):
    def setUp(self):
        self.generator = TextGenerator()

    def test_text_generation(self):
        prompt = "Write a story about a robot learning to feel emotions."
        story = self.generator.generate(prompt)
        self.assertGreater(len(story), len(prompt), "Generated text is too short.")

class TestPerformance(unittest.TestCase):
    def test_nlp_performance(self):
        start_time = time.time()
        text = "This is a test input for performance evaluation."
        summarizer = TextSummarizer()
        summarizer.summarize(text)
        end_time = time.time()
        self.assertLess(end_time - start_time, 2, "NLP tools are too slow.")

if __name__ == "__main__":
    unittest.main()
