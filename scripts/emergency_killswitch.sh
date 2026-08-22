#!/bin/bash

# Devin AGI Emergency Killswitch
# WARNING: This script forcefully terminates all known Devin processes.
# This is an emergency measure and may result in data loss.

echo "--- ENGAGING DEVIN AGI EMERGENCY KILLSWITCH ---"

# Kill the main AGI process
echo "Stopping main.py process..."
pkill -f "python main.py"

# Kill all backend servers
echo "Stopping all backend servers..."
pkill -f "servers/cloud_integration_server.py"
pkill -f "servers/analytics_server.py"
pkill -f "servers/mobile_integration_server.py"
pkill -f "servers/ai_learning_server.py"

echo "--- All known processes terminated. ---"
