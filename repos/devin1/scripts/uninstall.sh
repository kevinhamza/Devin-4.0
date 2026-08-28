#!/bin/bash

# Uninstallation Script for the Devin Project
# Removes all installed components and cleans up the environment

echo "Starting the uninstallation process for the Devin project..."

# Check for root permissions
if [[ "$EUID" -ne 0 ]]; then
  echo "Please run this script as root or using sudo."
  exit 1
fi

# Define variables
PROJECT_DIR="/opt/devin"
CONFIG_DIR="$HOME/.devin_config"
LOG_DIR="/var/log/devin"
SYSTEMD_SERVICE="/etc/systemd/system/devin.service"
VIRTUAL_ENV="$PROJECT_DIR/venv"

# Stop the Devin service if running
if systemctl is-active --quiet devin; then
  echo "Stopping the Devin service..."
  systemctl stop devin
  systemctl disable devin
  echo "Devin service stopped and disabled."
else
  echo "Devin service is not running."
fi

# Remove systemd service file
if [[ -f "$SYSTEMD_SERVICE" ]]; then
  echo "Removing systemd service file..."
  rm -f "$SYSTEMD_SERVICE"
  systemctl daemon-reload
  echo "Systemd service file removed."
fi

# Delete the project directory
if [[ -d "$PROJECT_DIR" ]]; then
  echo "Removing project directory: $PROJECT_DIR"
  rm -rf "$PROJECT_DIR"
  echo "Project directory removed."
else
  echo "Project directory not found."
fi

# Remove configuration files
if [[ -d "$CONFIG_DIR" ]]; then
  echo "Removing configuration directory: $CONFIG_DIR"
  rm -rf "$CONFIG_DIR"
  echo "Configuration directory removed."
else
  echo "Configuration directory not found."
fi

# Remove log files
if [[ -d "$LOG_DIR" ]]; then
  echo "Removing log directory: $LOG_DIR"
  rm -rf "$LOG_DIR"
  echo "Log directory removed."
else
  echo "Log directory not found."
fi

# Remove virtual environment
if [[ -d "$VIRTUAL_ENV" ]]; then
  echo "Removing virtual environment..."
  rm -rf "$VIRTUAL_ENV"
  echo "Virtual environment removed."
fi

# Clean up any additional artifacts
echo "Searching for additional project artifacts..."
ARTIFACTS=(
  "/usr/local/bin/devin-cli"
  "/etc/devin/"
)

for ARTIFACT in "${ARTIFACTS[@]}"; do
  if [[ -e "$ARTIFACT" ]]; then
    echo "Removing artifact: $ARTIFACT"
    rm -rf "$ARTIFACT"
  fi
done

echo "All additional artifacts removed."

# Final confirmation
echo "Uninstallation complete. Devin project has been successfully removed."
echo "If you encounter any residual files, please delete them manually."

exit 0
