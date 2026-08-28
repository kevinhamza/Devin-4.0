# 🦞 Devin AGI v2.0 - The Self-Operating System

Devin-2.0 is a next-generation AGI assistant designed to autonomously operate your computer. It combines advanced reasoning, persistent memory, and multimodal capabilities with a native Python implementation of OpenClaw's best features.

## 🌟 Key Features
- **Voice-First Interaction:** Command Devin using your voice with real-time speech-to-text.
- **Full OS Control:** Devin can move your mouse, click, type, and take screenshots to perform tasks just like a human.
- **Live Visual Canvas:** A real-time web workspace (Port 5005) to see Devin's thoughts, logs, and outputs.
- **Multi-Channel Messaging:** Control Devin remotely via Telegram.
- **Persistent Memory:** Local vector-based long-term memory using semantic embeddings.
- **Autonomous Reasoning:** A robust Regex-based planning engine that translates high-level goals into multi-step tool calls.

---

## 🚀 Step-by-Step Setup Guide

### 1. Prerequisites
Ensure you have Python 3.9 or higher installed. You will also need `pip` for package management.

### 2. Clone and Install
```bash
# Navigate to your git directory
mkdir -p ~/git && cd ~/git

# Clone the repository (if you haven't already)
git clone https://github.com/kevinhamza/Devin-2.0.git
cd Devin-2.0

# Install all required dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the root directory and add your API keys:
```env
# AI Providers
OPENAI_API_KEY=your_openai_key_here
GEMINI_API_KEY=your_gemini_key_here
PERPLEXITY_API_KEY=your_perplexity_key_here

# Messaging (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# System Settings
DEVIN_MODE=live  # Set to 'mock' for testing without API calls
```

### 4. Running Devin

#### **Text Mode (Standard)**
Run Devin in your terminal and type your goals.
```bash
python main.py
```

#### **Voice Mode (Human-Like Assistance)**
Talk directly to Devin to get things done.
```bash
python main.py --voice
```

### 5. Accessing the Live Canvas
Once Devin is running, open your web browser and navigate to:
`http://localhost:5005`

---

## 🛠️ Usage Examples
- **"Hey Devin, find the latest news about AI and summarize it in a new text file on my desktop."**
- **"Open Chrome, go to biselahore.com, and check if the results page is up."**
- **"Move my mouse to the top left corner and take a screenshot."**

---

## 🏗️ Architecture
- `main.py`: The entry point that orchestrates background servers and the AGI loop.
- `modules/tool_executor.py`: The "hands" of the system, executing OS and Web actions.
- `modules/messaging_gateway.py`: Handles Telegram and external communication.
- `modules/canvas_server.py`: Powers the live visual web interface.
- `ai_core/cognitive_arch/`: The "brain", containing reasoning, working memory, and persistent LTM.

---
**Author:** Kevin Devin / KevinHamza
**Version:** 2.0.0
**License:** MIT
