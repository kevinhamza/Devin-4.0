import unittest
from modules.ai_module import AIModelManager

class TestAIModels(unittest.TestCase):
    """Unit tests for AI models in the AI module."""

    def setUp(self):
        """Initialize test setup."""
        self.model_manager = AIModelManager()

    def test_model_loading(self):
        """Test if AI models load successfully."""
        model_name = "test_model"
        self.model_manager.load_model(model_name)
        self.assertIn(model_name, self.model_manager.loaded_models)
        self.assertIsNotNone(self.model_manager.get_model(model_name))

    def test_model_prediction(self):
        """Test AI model prediction functionality."""
        model_name = "test_model"
        input_data = {"text": "Hello, world!"}
        self.model_manager.load_model(model_name)
        prediction = self.model_manager.predict(model_name, input_data)
        self.assertIsInstance(prediction, dict)
        self.assertIn("result", prediction)

    def test_model_unloading(self):
        """Test unloading AI models."""
        model_name = "test_model"
        self.model_manager.load_model(model_name)
        self.model_manager.unload_model(model_name)
        self.assertNotIn(model_name, self.model_manager.loaded_models)

    def test_invalid_model_loading(self):
        """Test behavior when attempting to load an invalid model."""
        with self.assertRaises(Exception):
            self.model_manager.load_model("invalid_model")

    def test_model_training(self):
        """Test AI model training."""
        model_name = "trainable_model"
        training_data = [{"input": "Hello", "output": "Hi"}]
        self.model_manager.load_model(model_name, trainable=True)
        training_result = self.model_manager.train_model(model_name, training_data)
        self.assertTrue(training_result)
        self.assertIn("accuracy", training_result)

    def tearDown(self):
        """Clean up after tests."""
        self.model_manager.clear_all_models()

if __name__ == "__main__":
    unittest.main()
