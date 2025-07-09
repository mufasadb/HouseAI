#!/bin/bash

# Test script for HouseAI Query Routing Agent
# Usage: ./test_routing.sh [interactive|demo|streaming|streaming-interactive]

set -e

echo "🤖 HouseAI Query Routing Agent Test Script"
echo "==========================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required but not installed"
    exit 1
fi

# Check if the working agent exists
if [ ! -f "working_routing_agent.py" ]; then
    echo "❌ working_routing_agent.py not found"
    exit 1
fi

# Check if ai-lego-bricks directory exists
if [ ! -d "ai-lego-bricks" ]; then
    echo "❌ ai-lego-bricks directory not found"
    exit 1
fi

# Test Ollama connection
echo "🔍 Testing Ollama connection..."
if curl -s -f "http://100.83.40.11:11434/api/tags" > /dev/null 2>&1; then
    echo "✅ Ollama server is reachable"
else
    echo "❌ Cannot reach Ollama server at http://100.83.40.11:11434"
    echo "   Make sure the server is running and accessible"
    exit 1
fi

# Check if qwen2.5:7b model is available
echo "🔍 Checking for qwen2.5:7b model..."
if curl -s "http://100.83.40.11:11434/api/tags" | grep -q "qwen2.5:7b"; then
    echo "✅ qwen2.5:7b model is available"
else
    echo "⚠️  qwen2.5:7b model not found, but continuing anyway..."
fi

# Determine mode
MODE=${1:-demo}

echo ""
echo "🚀 Starting Query Routing Agent in $MODE mode..."
echo "   Press Ctrl+C to exit"
echo ""

# Run the agent
case "$MODE" in
    "interactive")
        echo "💬 Interactive mode - type your queries below"
        python3 working_routing_agent.py interactive
        ;;
    "streaming")
        echo "🌊 Streaming demo mode - running test queries with real-time streaming"
        python3 streaming_routing_agent.py
        ;;
    "streaming-interactive")
        echo "🌊 Streaming interactive mode - type your queries and see real-time streaming"
        python3 streaming_routing_agent.py interactive
        ;;
    *)
        echo "🧪 Demo mode - running test queries"
        python3 working_routing_agent.py
        ;;
esac

echo ""
echo "✅ Test completed!"