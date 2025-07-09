# 🥧 Raspberry Pi 4 Voice Orchestration Agent Deployment Guide

Complete deployment guide for running the Voice Orchestration Agent on Raspberry Pi 4 using Docker.

## 🎯 Overview

This setup deploys a lightweight voice processing agent on Raspberry Pi 4 that:
- Records audio locally on the Pi
- Transcribes audio using your STT server (100.83.40.11:8003)
- Classifies questions using your Ollama server (100.83.40.11:11434)
- Routes to specialized handlers (Japanese, Home Assistant, General)
- Returns intelligent responses

## 🔧 Hardware Requirements

- **Raspberry Pi 4** (4GB+ RAM recommended)
- **microSD card** (32GB+ Class 10)
- **USB microphone** or **USB audio adapter + microphone**
- **Stable internet connection** (WiFi or Ethernet)
- **Your existing server** running Ollama + STT services

## 📦 Quick Start Deployment

### 1. Prepare Raspberry Pi

```bash
# Flash Raspberry Pi OS to SD card using Raspberry Pi Imager
# Enable SSH and configure WiFi during imaging

# SSH into your Pi
ssh pi@your-pi-ip-address
```

### 2. One-Line Docker Setup

```bash
# Download and run automated setup
curl -sSL https://raw.githubusercontent.com/yourusername/voice-orchestration-agent/main/docker/pi-docker-setup.sh | bash

# Logout and login for Docker group permissions
logout
# SSH back in
ssh pi@your-pi-ip-address
```

### 3. Deploy Voice Agent

```bash
# Clone the repository
git clone https://github.com/yourusername/voice-orchestration-agent.git
cd voice-orchestration-agent

# Configure environment
cp .env.example .env
nano .env
```

**Update `.env` with your server details:**
```bash
# Core Services (Required) - Update with your server IP
OLLAMA_URL=http://100.83.40.11:11434
FASTER_WHISPER_URL=http://100.83.40.11:8003

# Optional: Home Assistant integration
HASS_URL=https://house.beachysapp.com
HASS_API=your_home_assistant_token_here

# Optional: API keys for fallback services
OPENAI_API_KEY=your_openai_key_here
GOOGLE_AI_STUDIO_KEY=your_google_ai_key_here
```

### 4. Start the Voice Agent

```bash
# Start in directory watch mode (recommended)
docker-compose up -d

# Check if it's running
docker-compose logs -f
```

## 🎤 Audio Setup

### Configure USB Microphone

```bash
# List available audio devices
docker exec voice-orchestration-agent arecord -l

# Test microphone recording
docker exec -it voice-orchestration-agent arecord -f cd -t wav -d 3 /app/recordings/test.wav

# Play back test recording
docker exec -it voice-orchestration-agent aplay /app/recordings/test.wav
```

### Fix Audio Permissions (if needed)

```bash
# Add user to audio group
sudo usermod -a -G audio $USER

# Check audio device permissions
ls -la /dev/snd/

# Restart Docker service if needed
sudo systemctl restart docker
docker-compose restart
```

## 🚀 Usage Modes

### 1. Directory Watch Mode (Default)
The agent watches the `audio_input/` directory and processes any audio files dropped there.

```bash
# Agent is already running in watch mode
# Simply copy audio files to be processed
cp your-recording.m4a audio_input/

# Check processing results in logs
docker-compose logs -f
```

### 2. Continuous Recording Mode
The agent continuously records and processes audio.

```bash
# Stop watch mode and start continuous recording
docker-compose down
docker-compose run --rm voice-agent python pi_service.py continuous

# This will record 5-second clips with 2-second pauses
# Press Ctrl+C to stop
```

### 3. Manual Recording and Processing

```bash
# Record 5 seconds and process immediately
docker-compose run --rm voice-agent python pi_service.py record 5

# Record 10 seconds
docker-compose run --rm voice-agent python pi_service.py record 10
```

### 4. Single File Processing

```bash
# Process a specific audio file
docker-compose run --rm voice-agent python pi_voice_agent.py /app/recordings/your-file.m4a
```

## 🔄 Development Commands (Using Makefile)

```bash
# Quick status check
make status

# Start the agent
make docker-run

# Test with sample audio
make docker-test

# View logs
make logs

# Stop the agent
make docker-stop

# Restart the agent
make restart

# Deploy updates to Pi (from development machine)
make pi-deploy PI_HOST=192.168.1.100
```

## 📊 Monitoring and Maintenance

### Check Service Status

```bash
# Container status
docker ps

# Service logs
docker-compose logs -f

# Resource usage
docker stats voice-orchestration-agent

# System resources
htop
```

### View Processing Results

```bash
# Check processed recordings
ls -la recordings/

# View recent logs
docker-compose logs --tail 50

# Check audio input queue
ls -la audio_input/
```

## 🔄 Updates and Maintenance

### Update to Latest Version

```bash
# Pull latest Docker image
docker-compose pull

# Restart with new version
docker-compose up -d

# Verify update
docker-compose logs -f
```

### Backup Configuration

```bash
# Backup your configuration
cp .env ~/.voice-agent-backup.env
tar -czf voice-agent-backup.tar.gz recordings/ .env docker-compose.yml
```

### Clean Up Storage

```bash
# Remove old recordings (older than 7 days)
find recordings/ -name "*.wav" -mtime +7 -delete
find recordings/ -name "*.m4a" -mtime +7 -delete

# Clean Docker cache
docker system prune -f
```

## 🌐 Network Architecture

```
┌─────────────────────┐     Network     ┌──────────────────────┐
│   Raspberry Pi 4    │    Requests     │   Your Main Server   │
│                     │    ────────►    │                      │
│ ┌─────────────────┐ │                 │ ┌──────────────────┐ │
│ │  Voice Agent    │ │                 │ │ Ollama (11434)   │ │
│ │  - Audio Record │ │ ◄─────────────► │ │ STT (8003)       │ │
│ │  - Docker       │ │    Responses    │ │ Home Assistant   │ │
│ │  - Processing   │ │                 │ └──────────────────┘ │
│ └─────────────────┘ │                 └──────────────────────┘
└─────────────────────┘
```

## 🔧 Troubleshooting

### Audio Issues

```bash
# Check if microphone is detected
lsusb | grep -i audio

# Test audio recording outside Docker
arecord -f cd -t wav -d 3 test-system.wav
aplay test-system.wav

# Check Docker audio access
docker run --rm --device /dev/snd:/dev/snd alpine arecord -l
```

### Network Connectivity Issues

```bash
# Test connectivity to your services
curl http://100.83.40.11:11434/api/tags
curl http://100.83.40.11:8003/health

# Test from inside container
docker exec voice-orchestration-agent curl http://100.83.40.11:11434/api/tags
docker exec voice-orchestration-agent curl http://100.83.40.11:8003/health
```

### Container Issues

```bash
# Check container logs for errors
docker-compose logs --tail 100

# Restart container
docker-compose restart

# Rebuild and restart (if you made code changes)
docker-compose up --build -d

# Check Docker daemon
sudo systemctl status docker
```

### Performance Issues

```bash
# Check system resources
htop
free -h
df -h

# Check container resource usage
docker stats

# Monitor temperature (Pi specific)
vcgencmd measure_temp

# Check for throttling
vcgencmd get_throttled
```

## 🔒 Security Best Practices

### Basic Security Setup

```bash
# Change default Pi password
sudo passwd pi

# Update system
sudo apt update && sudo apt upgrade -y

# Enable firewall
sudo ufw enable
sudo ufw allow ssh

# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable cups
```

### Network Security

```bash
# Use SSH keys instead of passwords
ssh-copy-id pi@your-pi-ip

# Configure fail2ban for SSH protection
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

## 🎯 Real-World Use Cases

### 1. Kitchen Voice Assistant
- Place Pi in kitchen with USB microphone
- Voice commands for lights, timers, weather
- "Turn off the kitchen lights"
- "How do you say 'delicious' in Japanese?"

### 2. Bedroom Smart Control
- Bedside voice control for home automation
- "Turn off all lights"
- "What's tomorrow's weather?"

### 3. Study Assistant
- Japanese learning companion
- "How do you say 'study' in Japanese?"
- General knowledge questions

### 4. Home Security Integration
- Voice-activated status checks
- "Are all doors locked?"
- "Turn on security mode"

## 📈 Performance Optimization

### Pi 4 Optimization

```bash
# Increase GPU memory for better performance
sudo raspi-config
# Advanced Options > Memory Split > 128

# Enable hardware acceleration
echo 'gpu_mem=128' | sudo tee -a /boot/config.txt

# Optimize SD card performance
echo 'hdparm -t /dev/mmcblk0' | sudo tee -a /etc/rc.local
```

### Docker Optimization

```bash
# Limit container memory if needed
echo 'memory: 512m' >> docker-compose.yml

# Use faster logging driver
echo 'logging: driver: "none"' >> docker-compose.yml
```

## 🚀 Advanced Features

### Running as System Service

Create a systemd service for auto-start:

```bash
sudo nano /etc/systemd/system/voice-agent.service
```

```ini
[Unit]
Description=Voice Orchestration Agent
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/pi/voice-orchestration-agent
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable voice-agent.service
sudo systemctl start voice-agent.service
```

### Multiple Pi Deployment

For multiple Raspberry Pis in different rooms:

```bash
# Each Pi can have different configuration
# Room-specific environment variables
ROOM_NAME=kitchen
DEVICE_ID=pi-kitchen-01

# Different audio input directories
mkdir -p audio_input_${ROOM_NAME}
```

## 📞 Support and Updates

### Getting Help

1. **Check logs first**: `docker-compose logs -f`
2. **Test connectivity**: Test your server connections
3. **Check audio setup**: Verify microphone is working
4. **Review configuration**: Ensure `.env` file is correct

### Staying Updated

1. **Watch the repository** for updates
2. **Pull latest images** regularly: `docker-compose pull`
3. **Backup before updates**: Save your configuration
4. **Test updates** in development before production

This deployment guide provides everything needed to run a production voice orchestration agent on Raspberry Pi 4 with Docker!