## Project Documentation

HouseAI is a clean, focused voice orchestration system with specialized agents for Japanese language learning and smart home control. The repository has been cleaned up to contain only essential agents and runners.

## 🧹 Clean Repository Structure

The repository now contains only essential components:

### Core Agent Configurations
- `home_assistant_agent.json` - Smart home device control
- `streaming_japanese_agent.json` - Japanese language learning  
- `routing_agent.json` - Query routing without TTS
- `routing_agent_with_tts.json` - Query routing with Sonnet 29 voice output

### Core Runners (All Support Non-Interactive Testing)
- `run_home_assistant_agent.py` - Home Assistant agent (use `--test "command"`)
- `run_json_japanese_agent.py` - Japanese learning agent (use `--test "question"`)
- `run_routing_agent.py` - Multi-agent router (use `--test-mode "query"`)

### Audio Pipeline Components  
- `custom_tts.py` - Fish Speech TTS with trained Sonnet 29 voice
- `custom_stt.py` - Custom transcription for speech-to-text

### Testing
- `experimental/test_all_agents.py` - Comprehensive agent testing suite
- All test files moved to `experimental/` folder

## ✅ Verified Working Features

1. **Routing Agent**: Successfully routes queries to appropriate specialized agents
2. **Japanese Agent**: Provides Japanese language learning responses via routing
3. **Home Assistant Integration**: ✅ **FULLY WORKING** - Multi-step workflow with dynamic light control
4. **Non-Interactive Testing**: All agents support command-line testing without input loops
5. **TTS Pipeline**: Sonnet 29 trained voice ready for audio output

- The PRD is our project requirements doc that we can lean on to guide our overall goal

## ⚠️ CRITICAL REMINDER: Interactive Input Loops

**ALWAYS CHECK FOR INTERACTIVE INPUT LOOPS BEFORE RUNNING SCRIPTS**

Many scripts in this project use `input()` calls that create infinite waiting loops when run from command line tools like Claude Code. This includes:
- `run_home_assistant_agent.py` - has interactive input loop
- Any script with `input()` or similar blocking calls

**SOLUTION**: 
1. Create dedicated test scripts with non-interactive modes
2. Modify scripts to accept command-line arguments instead of interactive input
3. Use non-blocking execution methods for testing

**Before running ANY script, check for:**
- `input()` calls
- `while True:` loops waiting for user input  
- Interactive prompts that will hang the terminal

## Project Structure

- Main scripts should have non-interactive modes for automation
- Test scripts should accept command-line arguments to avoid interactive loops
- Keep testing focused on the same agents used in production

## ⚠️ CRITICAL ARCHITECTURE PRINCIPLE: Single Source of Truth

**ONE AGENT, MULTIPLE PATHWAYS**: 
Never maintain multiple versions of the same agent. All pathways must use the same agent definition:

- ✅ `home_assistant_agent.json` - SINGLE home assistant agent used by ALL systems
- ✅ `run_routing_agent.py` routes HOME_ASSISTANT requests to `home_assistant_agent.json`
- ✅ `test_agents.sh` option 2 uses `home_assistant_agent.json`
- ✅ All testing now validates the SAME agent that production uses

**Why This Matters:**
- Testing fractured parts must apply to the whole system
- Agent improvements benefit all usage pathways immediately
- No confusion between "test" vs "production" agent behavior
- Consistent user experience across all interaction methods

## Home Assistant Integration Status

**✅ FULLY WORKING**: Clean, single-source Home Assistant integration
- **Multi-step workflow**: 4-step process (find → control → verify → format) ✅
- **Dynamic light control**: Extracts actual light names from user requests ✅
- **Real device control**: Actually turns lights on/off via Home Assistant API ✅
- **Repository cleaned**: All duplicate/experimental approaches removed ✅

**Architecture:**
```
User Input → [4-Step Home Assistant Agent] → [AI Lego Bricks Tool] → [Home Assistant API]
```

**Supported Commands:**
- `"turn on the table light"` → Controls table light
- `"turn off the garage light"` → Controls garage light  
- `"turn on beachy's light"` → Controls beachyswitch light
- `"turn on the kitchen light"` → Controls kitchen lights
- Dynamic extraction works with any light name

**Testing:**
```bash
python run_home_assistant_agent.py --test "turn on the table light"
```

**Key Components:**
- Home Assistant tool integration via AI Lego Bricks ✅
- Credential management with .env file ✅  
- Multi-step workflows (find → control → verify → format) ✅
- Dynamic light name extraction from user requests ✅
- AI Lego Bricks properly installed as package ✅

**Clean File Structure:**
- `home_assistant_agent.json` - Main 4-step workflow configuration
- `run_home_assistant_agent.py` - Main runner with `--test` support
- `ai-lego-bricks/tools/home_assistant_tool.py` - Tool implementation

## Text-to-Speech (TTS) Configuration

**✅ SONNET 29 TRAINED VOICE**: All TTS operations use the custom-trained Sonnet 29 voice model

**Configuration:**
- **Default Voice**: `sonnet29` (trained on Shakespeare's Sonnet 29)
- **Reference Audio**: `/experimental/fish_speech_tests/sonnet29_reference_optimized.wav`
- **Training Data**: 25 audio segments in `/experimental/fish_speech_tests/fish_speech_training/sonnet29/`
- **Provider**: Fish Speech S1 with custom voice cloning

**Implementation:**
- `custom_tts.py`: Fish Speech TTS client configured for Sonnet 29 voice
- `routing_agent_with_tts.json`: Routing agent with TTS using trained voice
- All agents with TTS steps automatically use the trained Sonnet 29 voice

**Training Materials (Preserved):**
- Training audio segments: `/experimental/fish_speech_tests/fish_speech_training/sonnet29/audio/`
- Training configuration: `/experimental/fish_speech_tests/fish_speech_training/sonnet29/training_config.json`
- Manifest file: `/experimental/fish_speech_tests/fish_speech_training/sonnet29/manifest.jsonl`

**Usage:**
All TTS-enabled agents will automatically use the Sonnet 29 trained voice without requiring additional configuration.