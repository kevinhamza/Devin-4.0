# Devin/security/ai_security/adversarial_defense.py
# Purpose: A toolkit for defending ML models against adversarial examples
#          using the adversarial training technique.

import logging
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, models, transforms
import numpy as np
import matplotlib.pyplot as plt

# Configure basic logging
logger = logging.getLogger("AdversarialDefense")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

class AdversarialDefense:
    """
    Implements adversarial training to make a PyTorch model more robust.
    """
    def __init__(self):
        # Check for PyTorch availability
        if not all(['torch' in globals(), 'torchvision' in globals()]):
            raise ImportError("PyTorch and Torchvision are required. 'pip install torch torchvision'")
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        # Load a pre-trained model
        self.model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT).to(self.device)
        self.model.eval() # Set to evaluation mode initially
        self.loss_fn = nn.CrossEntropyLoss()

    def _fgsm_attack(self, image: torch.Tensor, epsilon: float, data_grad: torch.Tensor) -> torch.Tensor:
        """Generates an adversarial example using the Fast Gradient Sign Method."""
        sign_data_grad = data_grad.sign()
        perturbed_image = image + epsilon * sign_data_grad
        # Clip the image to maintain the original data range [0, 1]
        perturbed_image = torch.clamp(perturbed_image, 0, 1)
        return perturbed_image

    def evaluate_robustness(self, data_loader: torch.utils.data.DataLoader, epsilon: float) -> tuple[float, float]:
        """Evaluates model accuracy on both clean and adversarial examples."""
        correct_clean = 0
        correct_adv = 0
        total = 0

        for images, labels in data_loader:
            images, labels = images.to(self.device), labels.to(self.device)
            images.requires_grad = True # Needed to compute gradients for the attack
            total += len(labels)
            
            # --- Test on clean images ---
            outputs_clean = self.model(images)
            _, predicted_clean = torch.max(outputs_clean.data, 1)
            correct_clean += (predicted_clean == labels).sum().item()

            # --- Generate adversarial images and test ---
            loss = self.loss_fn(outputs_clean, labels)
            self.model.zero_grad()
            loss.backward()
            data_grad = images.grad.data
            
            perturbed_images = self._fgsm_attack(images, epsilon, data_grad)
            outputs_adv = self.model(perturbed_images)
            _, predicted_adv = torch.max(outputs_adv.data, 1)
            correct_adv += (predicted_adv == labels).sum().item()

        clean_accuracy = 100 * correct_clean / total
        adv_accuracy = 100 * correct_adv / total
        
        logger.info(f"Accuracy on clean images: {clean_accuracy:.2f}%")
        logger.info(f"Accuracy on adversarial images (epsilon={epsilon}): {adv_accuracy:.2f}%")
        return clean_accuracy, adv_accuracy

    def adversarial_training(self, data_loader: torch.utils.data.DataLoader, epochs: int, epsilon: float):
        """Fine-tunes the model using on-the-fly adversarial examples."""
        self.model.train() # Set model to training mode
        optimizer = optim.Adam(self.model.parameters(), lr=0.001)

        for epoch in range(epochs):
            logger.warning(f"Starting Adversarial Training Epoch {epoch + 1}/{epochs}...")
            for i, (images, labels) in enumerate(data_loader):
                images, labels = images.to(self.device), labels.to(self.device)
                images.requires_grad = True

                # Forward pass on clean data to get gradients
                outputs = self.model(images)
                loss = self.loss_fn(outputs, labels)
                self.model.zero_grad()
                loss.backward()
                data_grad = images.grad.data
                
                # Generate adversarial examples
                perturbed_images = self._fgsm_attack(images, epsilon, data_grad)
                
                # Combine clean and adversarial images for training
                combined_images = torch.cat([images, perturbed_images], dim=0)
                combined_labels = torch.cat([labels, labels], dim=0)
                
                # Training step on the combined batch
                optimizer.zero_grad()
                outputs_combined = self.model(combined_images)
                loss_combined = self.loss_fn(outputs_combined, combined_labels)
                loss_combined.backward()
                optimizer.step()
                
                if (i + 1) % 100 == 0:
                    logger.info(f"  Epoch [{epoch+1}/{epochs}], Step [{i+1}/{len(data_loader)}], Loss: {loss_combined.item():.4f}")
        
        self.model.eval() # Set back to evaluation mode
        logger.warning("Adversarial training complete.")

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Adversarial Training Defense Prototype 🛡️🤖 ===")
    print("=========================================================")
    
    try:
        # 1. Prepare the dataset (CIFAR-10)
        transform = transforms.Compose([
            transforms.Resize((224, 224)), # MobileNetV2 expects 224x224 images
            transforms.ToTensor(),
        ])
        # Use a small subset of the data for a quick demo
        train_dataset = datasets.CIFAR10(root='./data', train=True, download=True, transform=transform)
        test_dataset = datasets.CIFAR10(root='./data', train=False, download=True, transform=transform)
        train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=32, shuffle=True)
        test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=32, shuffle=False)

        defense = AdversarialDefense()
        
        # 2. Evaluate the robustness of the ORIGINAL, undefended model
        print("\n--- 1. Evaluating the original pre-trained model ---")
        defense.evaluate_robustness(test_loader, epsilon=0.05)

        # 3. Perform adversarial training to harden the model
        print("\n--- 2. Performing adversarial training (1 epoch) ---")
        # For a real scenario, more epochs are needed. For the demo, 1 is sufficient to show an effect.
        # We also limit the training loader to a few batches to speed up the demo.
        limited_train_loader = torch.utils.data.DataLoader(
            torch.utils.data.Subset(train_dataset, range(500 * 32)), # Use ~500 batches
            batch_size=32, shuffle=True
        )
        defense.adversarial_training(limited_train_loader, epochs=1, epsilon=0.02)
        
        # 4. Evaluate the robustness of the NEW, hardened model
        print("\n--- 3. Evaluating the hardened model ---")
        defense.evaluate_robustness(test_loader, epsilon=0.05)
        
        print("\n[SUCCESS] Note the significant increase in accuracy on adversarial images after training.")

    except ImportError:
        print("\nERROR: PyTorch or Torchvision is not installed. Please run: pip install torch torchvision")
    except Exception as e:
        logger.error(f"An error occurred during the demo: {e}", exc_info=True)
    
    print("\n=========================================================")
    print("=== Adversarial Defense Prototype Complete ===")
    print("=========================================================")
