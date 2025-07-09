# Docker Deployment for Voice Orchestration Agent

This directory contains Docker configuration for deploying the voice orchestration agent on Raspberry Pi 4 and other platforms.

## 🚀 Quick Start (Raspberry Pi)

### 1. Install Docker on Pi

```bash
# Download and run the setup script
curl -sSL https://raw.githubusercontent.com/yourusername/voice-orchestration-agent/main/docker/pi-docker-setup.sh | bash

# Logout and login for group permissions
logout
```

### 2. Clone Repository

```bash
git clone https://github.com/yourusername/voice-orchestration-agent.git
cd voice-orchestration-agent
```

### 3. Configure Environment

```bash
# Copy and edit environment file
cp .env.example .env
nano .env

# Update with your server addresses:
OLLAMA_URL=http://YOUR_SERVER_IP:11434
FASTER_WHISPER_URL=http://YOUR_SERVER_IP:8003
```

### 4. Run Voice Agent

```bash
# Start in directory watch mode (default)
docker-compose up -d

# Or run in continuous recording mode
docker-compose run --rm voice-agent python pi_service.py continuous

# View logs
docker-compose logs -f
```

## 📋 Available Services

### Production Service
```bash
# Default: Directory watching mode
docker-compose up -d

# Alternative modes:
docker-compose run --rm voice-agent python pi_service.py record 5
docker-compose run --rm voice-agent python pi_voice_agent.py /app/recordings/test.m4a
```

### Development Service
```bash
# Development mode with live code reloading
docker-compose --profile dev up voice-agent-dev
```

## 🎤 Audio Setup

### USB Microphone Setup

```bash
# Check audio devices
docker exec voice-orchestration-agent arecord -l

# Test recording (if in continuous mode)
docker exec -it voice-orchestration-agent bash
arecord -f cd -t wav -d 3 /app/recordings/test.wav
```

### Audio Device Permissions

If you have audio permission issues:

```bash
# Add your user to audio group
sudo usermod -a -G audio $USER

# Check device permissions
ls -la /dev/snd/

# Run with additional privileges if needed
docker run --privileged --device /dev/snd:/dev/snd ...
```

## 🔄 Usage Modes

### 1. Directory Watch Mode (Default)
```bash
docker-compose up -d

# Drop audio files here for processing:
cp your-audio.m4a audio_input/
```

### 2. Continuous Recording Mode
```bash
docker-compose run --rm voice-agent python pi_service.py continuous
```

### 3. Single File Processing
```bash
# Process a specific file
docker-compose run --rm voice-agent python pi_voice_agent.py /app/recordings/your-file.m4a
```

### 4. Record and Process
```bash
# Record 5 seconds and process
docker-compose run --rm voice-agent python pi_service.py record 5
```

## 📊 Monitoring

### View Logs
```bash
# All logs
docker-compose logs -f

# Specific service logs
docker logs voice-orchestration-agent -f
```

### Check Health
```bash
# Container status
docker ps

# Health check
docker inspect voice-orchestration-agent | grep Health -A 10
```

### Resource Usage
```bash
# Container stats
docker stats voice-orchestration-agent

# System resources
htop
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_URL` | Ollama server URL | `http://host.docker.internal:11434` |
| `FASTER_WHISPER_URL` | STT service URL | `http://host.docker.internal:8003` |
| `OPENAI_API_KEY` | OpenAI API key (optional) | - |
| `GOOGLE_AI_STUDIO_KEY` | Google AI key (optional) | - |
| `HASS_URL` | Home Assistant URL | - |
| `HASS_API` | Home Assistant token | - |

### Volume Mounts

| Host Path | Container Path | Description |
|-----------|----------------|-------------|
| `./recordings` | `/app/recordings` | Processed audio files |
| `./audio_input` | `/app/audio_input` | Input directory for watch mode |
| `./logs` | `/app/logs` | Application logs |

## 🔄 Updates

### Pull Latest Image
```bash
# Pull updates
docker-compose pull

# Restart with new image
docker-compose up -d
```

### Development Updates
```bash
# Rebuild local image
docker-compose build

# Restart services
docker-compose up -d
```

## 🐛 Troubleshooting

### Audio Issues
```bash
# Check audio devices inside container
docker exec voice-orchestration-agent arecord -l

# Test audio permissions
docker run --rm --device /dev/snd:/dev/snd alpine arecord -l
```

### Network Issues
```bash
# Test connectivity to services
docker exec voice-orchestration-agent curl http://YOUR_SERVER_IP:11434/api/tags
docker exec voice-orchestration-agent curl http://YOUR_SERVER_IP:8003/health
```

### Container Issues
```bash
# Restart container
docker-compose restart

# Rebuild and restart
docker-compose up --build -d

# Check container logs
docker logs voice-orchestration-agent --tail 50
```

## 🏗️ Multi-Architecture Support

The Docker image supports both:
- **linux/amd64** (x86_64 development machines)
- **linux/arm64** (Raspberry Pi 4, Apple Silicon)

Images are automatically built and published via GitHub Actions.

## 🔒 Security

- Runs as non-root user inside container
- No privileged access required (unless audio recording fails)
- Environment variables for sensitive data
- Network isolation by default

This Docker setup provides a clean, isolated environment for the voice agent that's easy to deploy and update!