# 🏠 HouseAI Raspberry Pi Quick Start

## Fresh RPi OS 64-bit Setup

### One-Command Setup
```bash
# On your Raspberry Pi (fresh install):
curl -sSL https://raw.githubusercontent.com/mufasadb/HouseAI/main/deploy/rpi_setup_complete.sh | bash
```

### Manual Setup Steps

1. **Clone Repository**
   ```bash
   cd /home/pi
   git clone https://github.com/mufasadb/HouseAI.git
   cd HouseAI
   ```

2. **Configure Settings**
   ```bash
   cp deploy/pi_config.env .env
   nano .env  # Edit your server URLs and wake word
   ```

3. **Run Setup**
   ```bash
   chmod +x deploy/rpi_setup_complete.sh
   ./deploy/rpi_setup_complete.sh
   ```

4. **Reboot and Start**
   ```bash
   sudo reboot
   # After reboot:
   sudo systemctl start houseai
   sudo systemctl enable houseai
   ```

## Configuration

Edit `.env` file:
```bash
# Your main server with Ollama
OLLAMA_URL=http://192.168.1.100:11434

# Your STT server
FASTER_WHISPER_URL=http://192.168.1.100:8003

# Wake word (porcupine, alexa, computer, hey google)
WAKE_WORD=porcupine

# Sensitivity (0.0-1.0, lower = fewer false positives)
WAKE_WORD_SENSITIVITY=0.5
```

## Usage

Once running, simply say your wake word ("porcupine" by default) and ask your question!

Example:
```
"Porcupine... What's the weather like today?"
"Porcupine... Turn on the living room lights"
"Porcupine... What does 'arigatou' mean in Japanese?"
```

## Troubleshooting

**Check Status:**
```bash
sudo systemctl status houseai
docker logs houseai-wake-word
```

**Test Microphone:**
```bash
arecord -f cd -t wav test.wav
# Ctrl+C to stop, then:
aplay test.wav
```

**Manual Run:**
```bash
cd /home/pi/HouseAI
docker-compose -f docker-compose.rpi.yml up
```

## Available Wake Words

- **porcupine** (default)
- **alexa**
- **computer** 
- **hey google**
- **americano**
- **blueberry**
- **bumblebee**

Change in `.env` file and restart service.