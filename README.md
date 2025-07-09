# Query Routing Agent

A sophisticated AI agent that routes user queries to specialized assistants based on content analysis, built using the AI Lego Bricks orchestration framework.

## Overview

This project demonstrates how to create an intelligent query routing system that:

1. **Analyzes incoming queries** using structured LLM responses
2. **Routes to specialized assistants** based on content classification
3. **Provides expert responses** from domain-specific AI assistants

## Architecture

The system uses AI Lego Bricks' JSON-driven orchestration to create a workflow with these components:

### Query Classification
- Uses `llm_structured` step type for reliable JSON responses
- Classifies queries into three categories:
  - **Home Assistant**: Smart home, IoT, automation, security systems
  - **Japanese Assistant**: Language, culture, travel, anime, customs  
  - **General Assistant**: Science, programming, general knowledge

### Conditional Routing
- Uses `condition` step type to route based on classification
- Each route leads to a specialized assistant with domain expertise

### Specialized Responses
- Each assistant has custom system prompts and knowledge areas
- Responses include classification metadata for transparency

## Files

- `query_routing_agent.json` - AI Lego Bricks orchestration workflow (requires framework setup)
- `simple_routing_workflow.json` - Simplified version for learning
- `working_routing_agent.py` - **🚀 READY TO RUN** - Direct implementation using AI Lego Bricks LLM services

## Features

### Structured Classification
```json
{
  "category": "home|japanese|general",
  "confidence": 0.95,
  "reasoning": "Query mentions smart thermostats and Home Assistant platform"
}
```

### Domain Expertise
- **Home Assistant**: Home automation, IoT devices, smart home setups
- **Japanese Assistant**: Language translation, cultural insights, anime recommendations
- **General Assistant**: Programming, science, mathematics, general knowledge

### Transparency
- Shows which assistant handled the query
- Displays classification confidence and reasoning
- Helps users understand the routing decision

## Setup

### ⚡ Quick Start (Works Now!)
The `working_routing_agent.py` is ready to run with the existing Ollama setup:

```bash
python working_routing_agent.py
```

This connects to the Ollama instance at `100.83.40.11:11434` and demonstrates real LLM-powered query routing.

### 🎮 Interactive Mode
For testing custom queries:

```bash  
python working_routing_agent.py interactive
```

### 🔧 Full AI Lego Bricks Setup (Optional)
For the complete orchestration framework experience:

1. **Install dependencies**:
   ```bash
   cd ai-lego-bricks
   pip install -r requirements.txt
   ```

2. **Configure .env**:
   ```bash
   # The .env is already configured for the existing Ollama instance
   # OLLAMA_URL=http://100.83.40.11:11434
   # OLLAMA_DEFAULT_MODEL=qwen2.5:7b
   ```

## Usage Examples

### Working Agent (Real LLM)
```python
from working_routing_agent import QueryRoutingAgent

# Initialize agent (connects to Ollama)
agent = QueryRoutingAgent()

# Route a query
result = agent.route_query("How do I set up a smart thermostat?")

print(f"Category: {result['classification'].category}")
print(f"Confidence: {result['classification'].confidence}")
print(f"Response: {result['response']}")
```

### AI Lego Bricks Orchestrator (Advanced)
```python
from agent_orchestration import AgentOrchestrator

orchestrator = AgentOrchestrator()
workflow = orchestrator.load_workflow_from_file("query_routing_agent.json")

result = orchestrator.execute_workflow(workflow, {
    "user_query": "How do I set up a smart thermostat?"
})

print(result.final_output)
```

### Sample Queries and Expected Routing

**Home Assistant queries**:
- "How do I set up a smart thermostat with Home Assistant?"
- "How to automate my lights to turn on at sunset?"
- "Configure motion sensor automations"

**Japanese Assistant queries**:
- "What does 'arigatou gozaimasu' mean?"
- "Tell me about Japanese tea ceremony"
- "What are some popular anime series?"

**General Assistant queries**:
- "Explain quantum computing"
- "What is the time complexity of quicksort?"
- "How do I implement a binary search tree?"

## Technical Details

### Step Types Used
- `input` - Collect user queries
- `llm_structured` - Reliable JSON classification
- `condition` - Route based on classification
- `llm_chat` - Generate specialized responses
- `output` - Format final results

### Benefits of AI Lego Bricks
- **Configuration over Code**: Define complex agents through JSON
- **Modular Design**: Reusable components and step types
- **Structured Responses**: Type-safe LLM outputs
- **Conditional Logic**: Smart routing and branching
- **Easy Testing**: Simple workflow execution

### Extensibility
The system can easily be extended to:
- Add new assistant categories
- Include memory for conversation context
- Add human-in-the-loop approval steps
- Integrate with external APIs
- Support multi-modal inputs (images, audio)

## Learning Objectives

This project demonstrates:
1. **JSON-driven AI workflows** using orchestration systems
2. **Structured LLM responses** for reliable classification
3. **Conditional routing** for intelligent query handling
4. **Domain-specific AI assistants** with specialized knowledge
5. **Transparent AI decision-making** with confidence scoring

## Next Steps

Potential enhancements:
- Add conversation memory for context-aware routing
- Implement confidence-based fallback routing
- Add support for multi-language queries
- Include voice input/output capabilities
- Create a web interface for easier interaction