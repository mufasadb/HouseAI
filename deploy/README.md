# Raspberry Pi 4 Voice Orchestration Agent

Deploy the voice orchestration agent on a Raspberry Pi 4 for edge voice processing.

## 🔧 Hardware Requirements

- **Raspberry Pi 4** (4GB+ RAM recommended)
- **microSD card** (32GB+ Class 10)
- **USB microphone** or **USB audio adapter + microphone**
- **Internet connection** (WiFi or Ethernet)

## 📦 Installation

### 1. Prepare Raspberry Pi

```bash
# Flash Raspberry Pi OS to SD card
# Enable SSH and configure WiFi if needed

# SSH into your Pi
ssh pi@your-pi-ip-address
```

### 2. Run Setup Script

```bash
# Download and run setup script
curl -O https://your-server/pi_setup.sh
chmod +x pi_setup.sh
./pi_setup.sh
```

### 3. Copy Agent Files

```bash
# Copy the deployment files to your Pi
scp deploy/pi_voice_agent.py pi@your-pi-ip:~/voice_agent/
scp deploy/pi_service.py pi@your-pi-ip:~/voice_agent/
scp deploy/pi_config.env pi@your-pi-ip:~/voice_agent/.env
```

### 4. Configure Environment

Edit `.env` file on your Pi:

```bash
cd ~/voice_agent
nano .env

# Update with your server addresses:
OLLAMA_URL=http://YOUR_SERVER_IP:11434
FASTER_WHISPER_URL=http://YOUR_SERVER_IP:8003
```

## 🎤 Audio Setup

### Configure USB Microphone

```bash
# List audio devices
arecord -l

# Test microphone
arecord -f cd -t wav -d 3 test.wav
aplay test.wav

# If needed, set default audio device
sudo nano /etc/asound.conf
```

Add to `/etc/asound.conf`:
```
pcm.!default {
    type asym
    capture.pcm "mic"
}
pcm.mic {
    type plug
    slave {
        pcm "hw:1,0"  # Adjust based on your USB mic
    }
}
```

## 🚀 Usage

### Single File Processing

```bash
cd ~/voice_agent
source venv/bin/activate
python pi_voice_agent.py recording.m4a
```

### Record and Process

```bash
# Record 5 seconds and process
python pi_service.py record 5

# Record 10 seconds and process
python pi_service.py record 10
```

### Continuous Voice Processing

```bash
# Continuous recording mode
python pi_service.py continuous
```

### Directory Watching

```bash
# Watch for new audio files
python pi_service.py watch ./audio_input
```

## 🔄 Running as System Service

Create systemd service for auto-start:

```bash
sudo nano /etc/systemd/system/voice-agent.service
```

```ini
[Unit]
Description=Voice Orchestration Agent
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/voice_agent
Environment=PATH=/home/pi/voice_agent/venv/bin
ExecStart=/home/pi/voice_agent/venv/bin/python pi_service.py continuous
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable voice-agent.service
sudo systemctl start voice-agent.service
sudo systemctl status voice-agent.service
```

## 📊 Monitoring

### Check Service Status

```bash
# Service status
sudo systemctl status voice-agent.service

# View logs
sudo journalctl -u voice-agent.service -f

# System resources
htop
```

### Performance Optimization

```bash
# Increase GPU memory split for better performance
sudo raspi-config
# Advanced Options > Memory Split > 128

# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable cups
```

## 🌐 Network Architecture

```
[Raspberry Pi 4]           [Main Server]
┌─────────────────┐       ┌──────────────────┐
│ Voice Agent     │  ───► │ Ollama (11434)   │
│ - Audio Record  │       │ STT (8003)       │
│ - Preprocessing │       │ Home Assistant   │
│ - Result Display│       └──────────────────┘
└─────────────────┘
```

## 🔧 Troubleshooting

### Audio Issues

```bash
# Check audio devices
arecord -l
lsusb | grep -i audio

# Test recording
arecord -f cd -t wav -d 3 test.wav

# Adjust volume
alsamixer
```

### Network Issues

```bash
# Test connectivity to services
curl http://YOUR_SERVER_IP:11434/api/tags
curl http://YOUR_SERVER_IP:8003/health

# Check DNS
nslookup YOUR_SERVER_IP
```

### Performance Issues

```bash
# Monitor resources
htop
iotop
vcgencmd measure_temp

# Check memory
free -h
df -h
```

## 🎯 Use Cases

1. **Smart Home Voice Control**: Place near living areas for voice commands
2. **Voice Assistant**: Always-on voice processing
3. **Audio Logging**: Record and transcribe conversations
4. **Edge AI**: Local preprocessing before cloud processing
5. **IoT Integration**: Connect with other home automation systems

## 🔒 Security Considerations

- Change default Pi password
- Enable SSH key authentication
- Configure firewall (ufw)
- Use VPN for remote access
- Regular system updates

```bash
# Basic security setup
sudo passwd pi
sudo ufw enable
sudo ufw allow ssh
sudo apt update && sudo apt upgrade -y
```

This setup gives you a powerful edge voice processing device that leverages your existing server infrastructure!