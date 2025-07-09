# Voice Orchestration Agent - Development & Deployment Makefile

.PHONY: help build run test clean docker-build docker-run docker-push pi-setup

# Default target
help:
	@echo "Voice Orchestration Agent - Available Commands"
	@echo "=============================================="
	@echo ""
	@echo "Development:"
	@echo "  test          - Test the voice agent with sample audio"
	@echo "  run           - Run the agent locally"
	@echo "  clean         - Clean up temporary files"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build  - Build Docker image for multiple architectures"
	@echo "  docker-run    - Run the agent in Docker (watch mode)"
	@echo "  docker-test   - Test Docker container with sample audio"
	@echo "  docker-push   - Push image to registry"
	@echo ""
	@echo "Raspberry Pi:"
	@echo "  pi-setup      - Generate Pi setup instructions"
	@echo "  pi-deploy     - Deploy to Raspberry Pi (requires PI_HOST)"
	@echo ""
	@echo "Examples:"
	@echo "  make test"
	@echo "  make docker-run"
	@echo "  make pi-deploy PI_HOST=192.168.1.100"

# Local development
test:
	@echo "🧪 Testing voice agent..."
	@if [ -f "recordings/20250708 063500.m4a" ]; then \
		python process_audio.py "recordings/20250708 063500.m4a"; \
	else \
		echo "❌ No test audio file found. Please add audio files to recordings/"; \
	fi

run:
	@echo "🚀 Running voice agent..."
	python process_audio.py

clean:
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf dist/
	rm -rf *.egg-info/

# Docker operations
docker-build:
	@echo "🐳 Building multi-architecture Docker image..."
	docker buildx build \
		--platform linux/amd64,linux/arm64 \
		--tag ghcr.io/callmebeachy/voice-orchestration-agent:latest \
		--tag callmebeachy/voice-orchestration-agent:latest \
		--push .

docker-build-local:
	@echo "🐳 Building local Docker image..."
	docker build -t voice-orchestration-agent:local .

docker-run:
	@echo "🐳 Running Docker container in watch mode..."
	@mkdir -p recordings audio_input logs
	docker-compose up -d
	@echo "✅ Container started. Drop audio files in audio_input/ to process them."
	@echo "📋 View logs with: docker-compose logs -f"

docker-test:
	@echo "🧪 Testing Docker container..."
	@mkdir -p recordings audio_input logs
	@if [ -f "recordings/20250708 063500.m4a" ]; then \
		cp "recordings/20250708 063500.m4a" audio_input/test.m4a; \
		docker-compose run --rm voice-agent python pi_voice_agent.py /app/audio_input/test.m4a; \
	else \
		echo "❌ No test audio file found."; \
	fi

docker-stop:
	@echo "🛑 Stopping Docker containers..."
	docker-compose down

docker-logs:
	@echo "📋 Viewing Docker logs..."
	docker-compose logs -f

docker-push:
	@echo "📤 Pushing Docker images..."
	docker push ghcr.io/callmebeachy/voice-orchestration-agent:latest
	docker push callmebeachy/voice-orchestration-agent:latest

# Raspberry Pi deployment
pi-setup:
	@echo "📋 Raspberry Pi Setup Instructions"
	@echo "=================================="
	@echo ""
	@echo "1. SSH to your Raspberry Pi:"
	@echo "   ssh pi@YOUR_PI_IP"
	@echo ""
	@echo "2. Install Docker:"
	@echo "   curl -sSL https://raw.githubusercontent.com/yourusername/voice-orchestration-agent/main/docker/pi-docker-setup.sh | bash"
	@echo ""
	@echo "3. Clone repository:"
	@echo "   git clone https://github.com/yourusername/voice-orchestration-agent.git"
	@echo "   cd voice-orchestration-agent"
	@echo ""
	@echo "4. Configure environment:"
	@echo "   cp .env.example .env"
	@echo "   nano .env  # Update with your server IPs"
	@echo ""
	@echo "5. Start the agent:"
	@echo "   docker-compose up -d"
	@echo ""
	@echo "6. Test with audio:"
	@echo "   cp your-audio.m4a audio_input/"

pi-deploy:
	@if [ -z "$(PI_HOST)" ]; then \
		echo "❌ Please specify PI_HOST. Example: make pi-deploy PI_HOST=192.168.1.100"; \
		exit 1; \
	fi
	@echo "🥧 Deploying to Raspberry Pi at $(PI_HOST)..."
	@echo "📤 Copying files..."
	scp docker-compose.yml pi@$(PI_HOST):~/voice-agent/
	scp .env.example pi@$(PI_HOST):~/voice-agent/
	scp -r docker/ pi@$(PI_HOST):~/voice-agent/
	@echo "🐳 Pulling latest image on Pi..."
	ssh pi@$(PI_HOST) "cd ~/voice-agent && docker-compose pull && docker-compose up -d"
	@echo "✅ Deployment complete!"
	@echo "📋 Check status: ssh pi@$(PI_HOST) 'cd ~/voice-agent && docker-compose logs -f'"

# Development helpers
install-dev:
	@echo "📦 Installing development dependencies..."
	pip install -r requirements-docker.txt
	pip install pytest black flake8

format:
	@echo "🎨 Formatting code..."
	black *.py deploy/*.py

lint:
	@echo "🔍 Linting code..."
	flake8 *.py deploy/*.py --max-line-length=88 --extend-ignore=E203

# Audio testing
record-test:
	@echo "🎤 Recording 5-second test audio..."
	@if command -v arecord >/dev/null 2>&1; then \
		arecord -f cd -t wav -d 5 recordings/test-recording.wav; \
		echo "✅ Test recording saved to recordings/test-recording.wav"; \
	else \
		echo "❌ arecord not found. Install with: sudo apt install alsa-utils"; \
	fi

# Show current status
status:
	@echo "📊 Voice Agent Status"
	@echo "===================="
	@echo ""
	@if docker ps | grep -q voice-orchestration-agent; then \
		echo "🐳 Docker Status: RUNNING"; \
		docker ps --filter name=voice-orchestration-agent --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"; \
	else \
		echo "🐳 Docker Status: STOPPED"; \
	fi
	@echo ""
	@echo "📁 Audio Files:"
	@ls -la recordings/ 2>/dev/null || echo "   No recordings found"
	@echo ""
	@echo "📥 Input Queue:"
	@ls -la audio_input/ 2>/dev/null || echo "   No input files"

# Quick actions
restart: docker-stop docker-run

logs: docker-logs

# Release management
tag:
	@if [ -z "$(VERSION)" ]; then \
		echo "❌ Please specify VERSION. Example: make tag VERSION=v1.0.0"; \
		exit 1; \
	fi
	@echo "🏷️ Creating tag $(VERSION)..."
	git tag $(VERSION)
	git push origin $(VERSION)
	@echo "✅ Tag $(VERSION) created and pushed"