"""
prototypes/neural_networks.py
=============================

This module contains custom deep learning experiments, including models,
training pipelines, and evaluation metrics. These experiments explore
state-of-the-art neural network architectures and approaches.
"""

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Flatten, Conv2D, MaxPooling2D
from tensorflow.keras.optimizers import Adam
from sklearn.model_selection import train_test_split
import numpy as np

# Custom dataset generation for experimentation
def generate_dataset(num_samples=1000, input_dim=784, num_classes=10):
    """Generates synthetic dataset for neural network experiments."""
    X = np.random.rand(num_samples, input_dim)
    y = np.random.randint(0, num_classes, size=(num_samples,))
    y = tf.keras.utils.to_categorical(y, num_classes)
    return X, y

# Define a simple CNN model for image classification
def create_cnn_model(input_shape=(28, 28, 1), num_classes=10):
    """Creates a Convolutional Neural Network (CNN) model."""
    model = Sequential([
        Conv2D(32, kernel_size=(3, 3), activation='relu', input_shape=input_shape),
        MaxPooling2D(pool_size=(2, 2)),
        Dropout(0.25),
        Flatten(),
        Dense(128, activation='relu'),
        Dropout(0.5),
        Dense(num_classes, activation='softmax'),
    ])
    return model

# Training pipeline
def train_model(model, X_train, y_train, X_test, y_test, epochs=10, batch_size=32):
    """Compiles and trains the given model."""
    model.compile(
        loss='categorical_crossentropy',
        optimizer=Adam(),
        metrics=['accuracy']
    )
    history = model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=epochs,
        batch_size=batch_size,
        verbose=1
    )
    return history

# Experiment execution
def run_experiment():
    """Runs a custom neural network experiment."""
    # Generate synthetic dataset
    X, y = generate_dataset()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Reshape data for CNN if required
    input_dim = X_train.shape[1]
    input_shape = (int(np.sqrt(input_dim)), int(np.sqrt(input_dim)), 1)
    X_train = X_train.reshape(-1, *input_shape)
    X_test = X_test.reshape(-1, *input_shape)

    # Create and train the CNN model
    model = create_cnn_model(input_shape=input_shape, num_classes=y_train.shape[1])
    print("Training the model...")
    history = train_model(model, X_train, y_train, X_test, y_test)

    # Evaluate model
    print("Evaluating the model...")
    loss, accuracy = model.evaluate(X_test, y_test)
    print(f"Test Loss: {loss:.4f}, Test Accuracy: {accuracy:.4f}")

# Main entry point
if __name__ == "__main__":
    run_experiment()
