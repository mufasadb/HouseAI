# Multi-stage Dockerfile for Voice Orchestration Agent
# Supports both x86_64 and ARM64 (Raspberry Pi 4)

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including audio tools
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    alsa-utils \
    portaudio19-dev \
    pulseaudio \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 voiceagent && \
    chown -R voiceagent:voiceagent /app

# Copy requirements first for better caching
COPY requirements-docker.txt /app/
RUN pip install --no-cache-dir -r requirements-docker.txt

# Copy application code
COPY voice_orchestration_agent.py /app/
COPY process_audio.py /app/
COPY deploy/pi_voice_agent.py /app/
COPY deploy/pi_service.py /app/

# Create directories for audio processing
RUN mkdir -p /app/recordings /app/audio_input /app/logs && \
    chown -R voiceagent:voiceagent /app

# Switch to non-root user
USER voiceagent

# Environment variables with defaults
ENV OLLAMA_URL=http://host.docker.internal:11434
ENV FASTER_WHISPER_URL=http://host.docker.internal:8003
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('${FASTER_WHISPER_URL}/health', timeout=5)"

# Default command
CMD ["python", "pi_service.py", "watch", "/app/audio_input"]