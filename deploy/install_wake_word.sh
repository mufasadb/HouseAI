#!/bin/bash
# Install wake word detection dependencies on Raspberry Pi

echo "🤖 Installing Wake Word Detection Dependencies"
echo "=============================================="

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install audio dependencies
echo "🎤 Installing audio dependencies..."
sudo apt install -y \
    python3-pyaudio \
    portaudio19-dev \
    alsa-utils \
    pulseaudio \
    sox \
    libsox-fmt-all

# Install Python audio packages
echo "🐍 Installing Python audio packages..."
pip3 install pyaudio wave

# Install wake word detection libraries
echo "🔊 Installing wake word detection libraries..."

# Install Porcupine (recommended)
echo "Installing Porcupine..."
pip3 install pvporcupine

# Install OpenWakeWord (alternative)
echo "Installing OpenWakeWord..."
pip3 install openwakeword

# Install additional dependencies
echo "📚 Installing additional dependencies..."
pip3 install \
    numpy \
    requests \
    python-dotenv \
    pydantic

# Test audio system
echo "🎵 Testing audio system..."
if command -v arecord &> /dev/null; then
    echo "✅ Audio recording available"
    echo "🎤 Testing microphone (3 second test)..."
    timeout 3s arecord -f cd -t wav /tmp/test.wav || echo "⚠️ Microphone test failed"
    rm -f /tmp/test.wav
else
    echo "❌ Audio recording not available"
fi

# Set up systemd service (optional)
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/wake-word-agent.service > /dev/null <<EOF
[Unit]
Description=Wake Word Voice Agent
After=network.target sound.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/HouseAI/deploy
ExecStart=/usr/bin/python3 pi_wake_word_agent.py
Restart=always
RestartSec=5
Environment=PYTHONPATH=/home/pi/HouseAI/ai-lego-bricks

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Installation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Copy pi_config.env to .env and configure your settings"
echo "2. Test with: python3 pi_wake_word_agent.py"
echo "3. Enable service: sudo systemctl enable wake-word-agent"
echo "4. Start service: sudo systemctl start wake-word-agent"
echo ""
echo "🎤 Available wake words:"
echo "- Porcupine: porcupine, alexa, computer, hey google"
echo "- OpenWakeWord: alexa, hey_mycroft, hey_jarvis"