#!/bin/bash
# Raspberry Pi Docker Setup Script for Voice Orchestration Agent

set -e

echo "🐳 Setting up Docker on Raspberry Pi 4 for Voice Agent"
echo "======================================================="

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker
echo "🐳 Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
echo "👥 Adding user to docker group..."
sudo usermod -aG docker $USER

# Install Docker Compose
echo "🔧 Installing Docker Compose..."
sudo apt install -y docker-compose

# Enable Docker service
echo "🚀 Enabling Docker service..."
sudo systemctl enable docker
sudo systemctl start docker

# Test Docker installation
echo "🧪 Testing Docker installation..."
docker --version
docker-compose --version

# Create project directory
echo "📁 Creating project directory..."
mkdir -p ~/voice-agent
cd ~/voice-agent

# Create audio directories
mkdir -p recordings audio_input logs

# Set up audio permissions
echo "🎤 Setting up audio permissions..."
sudo usermod -a -G audio $USER

# Create environment file template
cat > .env << EOF
# Voice Orchestration Agent Configuration
OLLAMA_URL=http://192.168.1.100:11434
FASTER_WHISPER_URL=http://192.168.1.100:8003
OPENAI_API_KEY=
GOOGLE_AI_STUDIO_KEY=
HASS_URL=
HASS_API=
EOF

echo "✅ Docker setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your server IP addresses:"
echo "   nano .env"
echo ""
echo "2. Clone/pull your voice agent repository:"
echo "   git clone https://github.com/yourusername/voice-orchestration-agent.git ."
echo ""
echo "3. Run the voice agent:"
echo "   docker-compose up -d"
echo ""
echo "4. Check logs:"
echo "   docker-compose logs -f"
echo ""
echo "5. Test with an audio file:"
echo "   cp your-audio.m4a audio_input/"
echo ""
echo "Note: You may need to logout and login again for docker group permissions to take effect."