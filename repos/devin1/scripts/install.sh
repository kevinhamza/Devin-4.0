#!/bin/bash

# Devin Installation Script
# This script installs all necessary dependencies and sets up the project
# for Linux and macOS systems.

echo "Starting the installation process for Devin Project..."

# Checking system compatibility
OS=$(uname -s)
if [[ "$OS" != "Linux" && "$OS" != "Darwin" ]]; then
  echo "Error: Unsupported Operating System."
  echo "This installation script supports only Linux and macOS."
  exit 1
fi

# Update system packages
echo "Updating system packages..."
if [[ "$OS" == "Linux" ]]; then
  sudo apt-get update -y || sudo yum update -y || sudo pacman -Syu
elif [[ "$OS" == "Darwin" ]]; then
  brew update
fi

# Install required system packages
echo "Installing required system packages..."
REQUIRED_PACKAGES=("python3" "python3-pip" "git" "curl" "wget")
for package in "${REQUIRED_PACKAGES[@]}"; do
  if [[ "$OS" == "Linux" ]]; then
    sudo apt-get install -y $package || sudo yum install -y $package || sudo pacman -S $package
  elif [[ "$OS" == "Darwin" ]]; then
    brew install $package
  fi
done

# Setting up Python environment
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Configuring environment variables
echo "Configuring environment variables..."
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Environment variables configured. Edit the .env file to customize settings."
fi

# Final steps
echo "Cleaning up..."
if [[ "$OS" == "Linux" ]]; then
  sudo apt-get autoremove -y || sudo yum autoremove -y || sudo pacman -Rns $(pacman -Qdtq)
elif [[ "$OS" == "Darwin" ]]; then
  brew cleanup
fi

echo "Installation complete! You can now run the Devin project using the main.py script."
echo "Run the following commands to start:"
echo "source venv/bin/activate"
echo "python main.py"

exit 0
