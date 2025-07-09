#!/bin/bash
# Complete Raspberry Pi setup script for fresh RPi OS 64-bit install

set -e

echo "🏠 HouseAI Raspberry Pi Setup"
echo "============================="
echo "Setting up voice assistant with wake word detection"
echo ""

# Update system
echo "📦 Updating system..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "🔧 Installing system dependencies..."
sudo apt install -y \
    git \
    docker.io \
    docker-compose \
    python3-pip \
    curl \
    wget \
    vim \
    htop

# Add user to docker group
echo "🐳 Setting up Docker permissions..."
sudo usermod -aG docker $USER

# Enable audio permissions
echo "🎤 Setting up audio permissions..."
sudo usermod -aG audio $USER

# Clone repository
echo "📥 Cloning HouseAI repository..."
cd /home/pi
if [ -d "HouseAI" ]; then
    echo "Repository already exists, updating..."
    cd HouseAI
    git pull
else
    git clone https://github.com/mufasadb/HouseAI.git
    cd HouseAI
fi

# Copy and configure environment
echo "⚙️ Setting up configuration..."
cp deploy/pi_config.env .env
echo "📝 Please edit .env file with your settings:"
echo "   - OLLAMA_URL (your main server)"
echo "   - FASTER_WHISPER_URL (your STT server)"
echo "   - WAKE_WORD (porcupine, alexa, computer, etc.)"
echo ""
echo "Press Enter when done editing .env..."
read -p ""

# Test audio
echo "🎵 Testing audio system..."
if command -v arecord &> /dev/null; then
    echo "✅ Audio recording available"
    echo "🎤 Testing microphone (3 second test)..."
    timeout 3s arecord -f cd -t wav /tmp/test.wav 2>/dev/null || echo "⚠️ Microphone test failed"
    rm -f /tmp/test.wav
else
    echo "❌ Audio recording not available"
fi

# Create systemd service for Docker
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/houseai.service > /dev/null <<EOF
[Unit]
Description=HouseAI Wake Word Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/pi/HouseAI
ExecStart=/usr/bin/docker-compose -f docker-compose.rpi.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.rpi.yml down
TimeoutStartSec=0
User=pi

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Reboot: sudo reboot"
echo "2. After reboot, start service: sudo systemctl start houseai"
echo "3. Enable auto-start: sudo systemctl enable houseai"
echo "4. Check logs: docker logs houseai-wake-word"
echo ""
echo "🎤 Your wake word voice assistant will be ready!"
echo "Default wake word: 'porcupine'"
echo ""
echo "🔧 Manual commands:"
echo "- Start: docker-compose -f docker-compose.rpi.yml up -d"
echo "- Stop: docker-compose -f docker-compose.rpi.yml down"
echo "- Logs: docker logs -f houseai-wake-word"