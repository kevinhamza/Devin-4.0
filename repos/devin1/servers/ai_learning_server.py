"""ai_learning_server.py
This module implements reinforcement and supervised learning capabilities
for the AI system, allowing real-time updates and learning based on user
interactions and predefined datasets.
"""

import os
import time
import logging
import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
from modules.data_loader import load_training_data
from modules.reinforcement_agent import ReinforcementAgent
from modules.supervised_model import SupervisedModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AILearningServer")

class AILearningServer:
    """Server handling reinforcement and supervised learning models."""

    def __init__(self, config):
        self.config = config
        self.reinforcement_agent = None
        self.supervised_model = None
        self.load_models()

    def load_models(self):
        """Initialize or load the models."""
        logger.info("Initializing learning models...")

        # Load reinforcement learning agent
        self.reinforcement_agent = ReinforcementAgent(self.config['rl_config'])
        
        # Load supervised learning model
        self.supervised_model = SupervisedModel(self.config['sl_config'])

        logger.info("Models initialized successfully.")

    def train_supervised(self, data_path):
        """Train the supervised learning model."""
        logger.info("Loading training data for supervised learning...")
        
        X, y = load_training_data(data_path)
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

        logger.info("Training supervised model...")
        self.supervised_model.train(X_train, y_train, validation_data=(X_val, y_val))
        
        logger.info("Supervised model training completed.")

    def train_reinforcement(self, environment):
        """Train the reinforcement learning agent."""
        logger.info("Starting reinforcement learning training...")
        
        episodes = self.config['rl_config']['episodes']
        for episode in range(episodes):
            logger.info(f"Episode {episode + 1}/{episodes}")
            reward = self.reinforcement_agent.train(environment)
            logger.info(f"Episode reward: {reward}")
        
        logger.info("Reinforcement learning training completed.")

    def evaluate_models(self):
        """Evaluate both models."""
        logger.info("Evaluating supervised model...")
        sl_accuracy = self.supervised_model.evaluate()
        logger.info(f"Supervised model accuracy: {sl_accuracy}")

        logger.info("Evaluating reinforcement learning agent...")
        rl_performance = self.reinforcement_agent.evaluate()
        logger.info(f"Reinforcement learning performance: {rl_performance}")

    def save_models(self):
        """Save models to disk."""
        logger.info("Saving models...")
        self.reinforcement_agent.save(self.config['rl_config']['save_path'])
        self.supervised_model.save(self.config['sl_config']['save_path'])
        logger.info("Models saved successfully.")

if __name__ == "__main__":
    config = {
        'rl_config': {
            'save_path': 'models/reinforcement_agent',
            'episodes': 1000
        },
        'sl_config': {
            'save_path': 'models/supervised_model',
            'learning_rate': 0.001
        }
    }

    server = AILearningServer(config)

    # Example workflow
    try:
        server.train_supervised("data/supervised_training_data.csv")
        server.train_reinforcement("environments/simulation_env")
        server.evaluate_models()
        server.save_models()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
