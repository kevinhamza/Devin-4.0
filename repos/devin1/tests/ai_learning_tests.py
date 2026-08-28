import unittest
from modules.ai_learning import LearningEngine

class TestAILearning(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = LearningEngine()
        cls.sample_data = [
            {"input": [0.1, 0.2, 0.3], "output": [0.6]},
            {"input": [0.5, 0.6, 0.1], "output": [1.2]},
            {"input": [0.9, 0.8, 0.7], "output": [2.4]},
        ]
        cls.invalid_data = {"input": [0.1, 0.2], "output": [0.5]}
    
    def test_model_training(self):
        initial_state = self.engine.model_state()
        self.engine.train(self.sample_data)
        new_state = self.engine.model_state()
        self.assertNotEqual(initial_state, new_state, "Model state should change after training.")

    def test_prediction(self):
        self.engine.train(self.sample_data)
        prediction = self.engine.predict([0.2, 0.4, 0.6])
        self.assertIsInstance(prediction, list, "Prediction should be a list.")
        self.assertEqual(len(prediction), 1, "Prediction should match expected output shape.")

    def test_invalid_data(self):
        with self.assertRaises(ValueError):
            self.engine.train([self.invalid_data])

    def test_model_save_and_load(self):
        self.engine.train(self.sample_data)
        self.engine.save_model("test_model.ai")
        self.engine.load_model("test_model.ai")
        prediction = self.engine.predict([0.3, 0.5, 0.7])
        self.assertIsInstance(prediction, list, "Prediction should work after loading the model.")

    @classmethod
    def tearDownClass(cls):
        cls.engine.cleanup()

if __name__ == "__main__":
    unittest.main()
import unittest
from modules.ai_learning import LearningEngine

class TestAILearning(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = LearningEngine()
        cls.sample_data = [
            {"input": [0.1, 0.2, 0.3], "output": [0.6]},
            {"input": [0.5, 0.6, 0.1], "output": [1.2]},
            {"input": [0.9, 0.8, 0.7], "output": [2.4]},
        ]
        cls.invalid_data = {"input": [0.1, 0.2], "output": [0.5]}
    
    def test_model_training(self):
        initial_state = self.engine.model_state()
        self.engine.train(self.sample_data)
        new_state = self.engine.model_state()
        self.assertNotEqual(initial_state, new_state, "Model state should change after training.")

    def test_prediction(self):
        self.engine.train(self.sample_data)
        prediction = self.engine.predict([0.2, 0.4, 0.6])
        self.assertIsInstance(prediction, list, "Prediction should be a list.")
        self.assertEqual(len(prediction), 1, "Prediction should match expected output shape.")

    def test_invalid_data(self):
        with self.assertRaises(ValueError):
            self.engine.train([self.invalid_data])

    def test_model_save_and_load(self):
        self.engine.train(self.sample_data)
        self.engine.save_model("test_model.ai")
        self.engine.load_model("test_model.ai")
        prediction = self.engine.predict([0.3, 0.5, 0.7])
        self.assertIsInstance(prediction, list, "Prediction should work after loading the model.")

    @classmethod
    def tearDownClass(cls):
        cls.engine.cleanup()

if __name__ == "__main__":
    unittest.main()
