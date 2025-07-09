#!/bin/bash
# Raspberry Pi 4 Setup Script for Voice Orchestration Agent

echo "🤖 Setting up Voice Orchestration Agent on Raspberry Pi 4"
echo "========================================================"

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python 3.9+ and dependencies
echo "🐍 Installing Python and dependencies..."
sudo apt install -y python3 python3-pip python3-venv git curl

# Install audio dependencies
echo "🎵 Installing audio dependencies..."
sudo apt install -y portaudio19-dev python3-pyaudio alsa-utils pulseaudio

# Create project directory
echo "📁 Creating project directory..."
mkdir -p ~/voice_agent
cd ~/voice_agent

# Create virtual environment
echo "🌐 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python packages
echo "📚 Installing Python packages..."
pip install --upgrade pip
pip install requests python-dotenv pydantic openai

# Clone or copy the agent files
echo "📋 Setting up agent files..."
# Note: You'll need to copy your files here

echo "✅ Basic setup complete!"
echo ""
echo "Next steps:"
echo "1. Copy your voice orchestration agent files to ~/voice_agent/"
echo "2. Update the .env file with your server addresses"
echo "3. Test the agent with: python process_audio.py <audio_file>"