"""
AI Learning Module
Provides functionalities for reinforcement learning and supervised learning.
"""

import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from typing import Tuple, List, Any


class SupervisedLearning:
    """
    Implements supervised learning functionalities using TensorFlow and scikit-learn.
    """

    def __init__(self):
        self.model = None

    def build_model(self, input_shape: int, output_shape: int, layers: List[int], activation: str = "relu") -> None:
        """
        Build a neural network for supervised learning.

        Args:
            input_shape (int): Number of input features.
            output_shape (int): Number of output classes.
            layers (List[int]): Number of units in each hidden layer.
            activation (str): Activation function for hidden layers.
        """
        self.model = tf.keras.Sequential()
        self.model.add(tf.keras.layers.InputLayer(input_shape=(input_shape,)))

        for units in layers:
            self.model.add(tf.keras.layers.Dense(units, activation=activation))

        self.model.add(tf.keras.layers.Dense(output_shape, activation="softmax"))
        self.model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])

    def train(self, X_train: np.ndarray, y_train: np.ndarray, epochs: int = 10, batch_size: int = 32) -> None:
        """
        Train the model using the provided training data.

        Args:
            X_train (np.ndarray): Training features.
            y_train (np.ndarray): Training labels.
            epochs (int): Number of training epochs.
            batch_size (int): Size of each training batch.
        """
        if self.model is None:
            raise ValueError("Model is not built. Call build_model() first.")
        self.model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=1)

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> float:
        """
        Evaluate the model on test data.

        Args:
            X_test (np.ndarray): Test features.
            y_test (np.ndarray): Test labels.

        Returns:
            float: Accuracy of the model on test data.
        """
        if self.model is None:
            raise ValueError("Model is not built. Call build_model() first.")
        _, accuracy = self.model.evaluate(X_test, y_test, verbose=0)
        return accuracy

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict outcomes for the given input data.

        Args:
            X (np.ndarray): Input data.

        Returns:
            np.ndarray: Predicted probabilities.
        """
        if self.model is None:
            raise ValueError("Model is not built. Call build_model() first.")
        return self.model.predict(X)


class ReinforcementLearning:
    """
    Implements basic reinforcement learning using Q-learning.
    """

    def __init__(self, state_space: int, action_space: int, learning_rate: float = 0.1, discount_factor: float = 0.9):
        self.state_space = state_space
        self.action_space = action_space
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.q_table = np.zeros((state_space, action_space))

    def choose_action(self, state: int, epsilon: float = 0.1) -> int:
        """
        Choose an action based on the epsilon-greedy strategy.

        Args:
            state (int): Current state.
            epsilon (float): Exploration rate.

        Returns:
            int: Chosen action.
        """
        if np.random.rand() < epsilon:
            return np.random.choice(self.action_space)
        return np.argmax(self.q_table[state, :])

    def update_q_table(self, state: int, action: int, reward: float, next_state: int) -> None:
        """
        Update the Q-table using the Bellman equation.

        Args:
            state (int): Current state.
            action (int): Performed action.
            reward (float): Reward received.
            next_state (int): Next state after the action.
        """
        best_next_action = np.argmax(self.q_table[next_state, :])
        td_target = reward + self.discount_factor * self.q_table[next_state, best_next_action]
        self.q_table[state, action] += self.learning_rate * (td_target - self.q_table[state, action])


def load_sample_data() -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Load a sample dataset for testing supervised learning functionality.

    Returns:
        Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]: Training and test datasets.
    """
    from sklearn.datasets import load_iris
    iris = load_iris()
    X_train, X_test, y_train, y_test = train_test_split(iris.data, iris.target, test_size=0.2, random_state=42)
    return X_train, X_test, y_train, y_test


# Example Usage
if __name__ == "__main__":
    # Supervised Learning Example
    X_train, X_test, y_train, y_test = load_sample_data()
    supervised = SupervisedLearning()
    supervised.build_model(input_shape=X_train.shape[1], output_shape=len(set(y_train)), layers=[64, 64])
    supervised.train(X_train, y_train, epochs=50)
    print(f"Supervised Learning Accuracy: {supervised.evaluate(X_test, y_test):.2f}")

    # Reinforcement Learning Example
    rl = ReinforcementLearning(state_space=5, action_space=3)
    state = 0
    for _ in range(1000):
        action = rl.choose_action(state)
        reward = np.random.rand()
        next_state = (state + action) % 5
        rl.update_q_table(state, action, reward, next_state)
        state = next_state
    print("Reinforcement Learning Q-Table:")
    print(rl.q_table)
