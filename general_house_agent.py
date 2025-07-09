#!/usr/bin/env python3
"""
General House Agent - Natural Language Home Assistant Controller
Allows you to input text commands that are processed by an LLM and executed via Home Assistant
"""

import sys
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List

# Add the ai-lego-bricks directory to the path
ai_lego_path = Path(__file__).parent / "ai-lego-bricks"
sys.path.insert(0, str(ai_lego_path))

from credentials import CredentialManager
from tools.home_assistant_tool import create_home_assistant_tool
from tools.tool_types import ToolCall
from llm.llm_factory import create_text_client
from llm.generation_service import GenerationService, LLMProvider

class GeneralHouseAgent:
    """General agent that processes natural language commands for Home Assistant"""
    
    def __init__(self):
        # Initialize credential manager
        from dotenv import load_dotenv
        load_dotenv()
        
        # Also try loading from the project root
        project_root = Path(__file__).parent
        dotenv_path = project_root / '.env'
        if dotenv_path.exists():
            load_dotenv(dotenv_path)
        
        self.cred_manager = CredentialManager(load_env=True)
        
        # Verify Home Assistant credentials
        self.hass_url = self.cred_manager.get_credential("HASS_URL")
        self.hass_api = self.cred_manager.get_credential("HASS_API")
        
        if not self.hass_url or not self.hass_api:
            raise ValueError("Missing Home Assistant credentials in .env (HASS_URL, HASS_API)")
        
        # Initialize LLM client
        self.llm_client = create_text_client(
            "ollama",
            model="qwen2.5:7b",
            temperature=0.1,
            credential_manager=self.cred_manager
        )
        
        # Initialize Home Assistant tool
        self.ha_tool = None
        self.available_lights = []
        
    async def initialize(self):
        """Initialize the agent and get available devices"""
        print("🤖 Initializing General House Agent...")
        print(f"🏠 Connected to Home Assistant at: {self.hass_url}")
        
        # Create Home Assistant tool
        self.ha_tool = create_home_assistant_tool(self.cred_manager)
        
        # Get available lights for context
        await self._refresh_device_list()
        
        print("✅ Agent ready to process natural language commands!")
        print("🎯 Available device types: lights, switches, fans, sensors")
        print("📝 Example commands:")
        print("   - 'Turn on the kitchen light'")
        print("   - 'Turn off all bedroom lights'")
        print("   - 'Show me all lights that are on'")
        print("   - 'Turn off beachy's light'")
        
    async def _refresh_device_list(self):
        """Refresh the list of available devices"""
        try:
            # Get all lights
            lights_call = ToolCall(
                id="get_lights",
                name="home_assistant",
                parameters={
                    "operation": "get_states",
                    "domain": "light"
                }
            )
            
            result = await self.ha_tool.executor.execute(lights_call)
            if not result.error:
                self.available_lights = result.result.get('entities', [])
                print(f"📋 Found {len(self.available_lights)} available lights")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not refresh device list: {e}")
    
    async def process_command(self, user_input: str) -> Dict[str, Any]:
        """Process a natural language command"""
        print(f"\n🎤 Processing: '{user_input}'")
        
        # Create context about available devices
        lights_context = []
        for light in self.available_lights[:10]:  # Limit to first 10 for context
            lights_context.append({
                "entity_id": light['entity_id'],
                "friendly_name": light.get('friendly_name', light['entity_id']),
                "state": light['state']
            })
        
        # Create system prompt with device context
        system_prompt = f"""You are a Home Assistant controller. You can control smart home devices using these operations:

AVAILABLE OPERATIONS:
1. get_states - Get all entities or filter by domain (e.g., domain: "light")
2. get_state - Get state of specific entity (e.g., entity_id: "light.living_room")
3. turn_on - Turn on an entity (e.g., entity_id: "light.bedroom")
4. turn_off - Turn off an entity (e.g., entity_id: "light.kitchen")
5. call_service - Call any Home Assistant service

AVAILABLE LIGHTS (first 10):
{json.dumps(lights_context, indent=2)}

INSTRUCTIONS:
- Analyze the user's request and determine the best operation to use
- For lighting requests, match friendly names or entity IDs from the available lights
- For "beachy" requests, look for lights with "beachy" in the name
- If you need to see all lights first, use get_states with domain: "light"
- Respond with JSON containing the operation and parameters

USER REQUEST: {user_input}

Respond with a JSON object containing:
- "operation": the operation to perform
- "parameters": the parameters for the operation
- "reasoning": brief explanation of your choice

Example responses:
{{"operation": "turn_off", "parameters": {{"entity_id": "light.beachyswitch"}}, "reasoning": "Turning off beachy's light"}}
{{"operation": "get_states", "parameters": {{"domain": "light"}}, "reasoning": "Getting all lights to show status"}}
"""
        
        try:
            # Get response from LLM
            response = self.llm_client.chat(system_prompt)
            
            # Try to parse JSON response
            try:
                # Clean up the response - remove markdown code blocks if present
                clean_response = response.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]
                clean_response = clean_response.strip()
                
                command_data = json.loads(clean_response)
                
                # Execute the command
                return await self._execute_command(command_data, user_input)
                
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract command from text
                return await self._parse_text_response(response, user_input)
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "user_input": user_input
            }
    
    async def _execute_command(self, command_data: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """Execute a parsed command"""
        try:
            operation = command_data.get("operation")
            parameters = command_data.get("parameters", {})
            reasoning = command_data.get("reasoning", "")
            
            print(f"🔧 Executing: {operation} with parameters: {parameters}")
            print(f"💭 Reasoning: {reasoning}")
            
            # Create tool call
            tool_call = ToolCall(
                id=f"cmd_{operation}",
                name="home_assistant",
                parameters={
                    "operation": operation,
                    **parameters
                }
            )
            
            # Execute the command
            result = await self.ha_tool.executor.execute(tool_call)
            
            if result.error:
                return {
                    "success": False,
                    "error": result.error,
                    "operation": operation,
                    "parameters": parameters,
                    "user_input": user_input
                }
            
            # Format the response based on operation type
            return self._format_response(result.result, operation, user_input)
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "user_input": user_input
            }
    
    def _format_response(self, result: Dict[str, Any], operation: str, user_input: str) -> Dict[str, Any]:
        """Format the response based on operation type"""
        
        if operation == "get_states":
            entities = result.get("entities", [])
            domain = result.get("domain", "all")
            
            if domain == "light":
                lights_on = [e for e in entities if e["state"] == "on"]
                lights_off = [e for e in entities if e["state"] == "off"]
                
                return {
                    "success": True,
                    "operation": operation,
                    "summary": f"Found {len(entities)} lights: {len(lights_on)} on, {len(lights_off)} off",
                    "lights_on": lights_on,
                    "lights_off": lights_off,
                    "user_input": user_input
                }
            else:
                return {
                    "success": True,
                    "operation": operation,
                    "summary": f"Found {result.get('count', 0)} entities",
                    "entities": entities,
                    "user_input": user_input
                }
        
        elif operation in ["turn_on", "turn_off"]:
            entity_id = result.get("entity_id")
            return {
                "success": True,
                "operation": operation,
                "summary": f"Successfully {operation.replace('_', ' ')} {entity_id}",
                "entity_id": entity_id,
                "timestamp": result.get("timestamp"),
                "user_input": user_input
            }
        
        elif operation == "get_state":
            entity_id = result.get("entity_id")
            state = result.get("state")
            return {
                "success": True,
                "operation": operation,
                "summary": f"{entity_id} is {state}",
                "entity_id": entity_id,
                "state": state,
                "attributes": result.get("attributes", {}),
                "user_input": user_input
            }
        
        else:
            return {
                "success": True,
                "operation": operation,
                "result": result,
                "user_input": user_input
            }
    
    async def _parse_text_response(self, response: str, user_input: str) -> Dict[str, Any]:
        """Parse text response when JSON parsing fails"""
        # Simple text parsing fallback
        response_lower = response.lower()
        user_lower = user_input.lower()
        
        # Look for common patterns
        if "turn off" in user_lower:
            # Try to find entity in response or user input
            for light in self.available_lights:
                entity_id = light['entity_id']
                friendly_name = light.get('friendly_name', '').lower()
                
                if any(name in user_lower for name in [friendly_name, entity_id.split('.')[-1]]):
                    return await self._execute_command({
                        "operation": "turn_off",
                        "parameters": {"entity_id": entity_id},
                        "reasoning": f"Parsed from text: turn off {entity_id}"
                    }, user_input)
        
        elif "turn on" in user_lower:
            # Similar logic for turn on
            for light in self.available_lights:
                entity_id = light['entity_id']
                friendly_name = light.get('friendly_name', '').lower()
                
                if any(name in user_lower for name in [friendly_name, entity_id.split('.')[-1]]):
                    return await self._execute_command({
                        "operation": "turn_on",
                        "parameters": {"entity_id": entity_id},
                        "reasoning": f"Parsed from text: turn on {entity_id}"
                    }, user_input)
        
        elif any(word in user_lower for word in ["list", "show", "status"]):
            return await self._execute_command({
                "operation": "get_states",
                "parameters": {"domain": "light"},
                "reasoning": "Showing light status"
            }, user_input)
        
        return {
            "success": False,
            "error": "Could not parse command",
            "raw_response": response,
            "user_input": user_input
        }

async def interactive_mode():
    """Run the agent in interactive mode"""
    print("🏠 General House Agent - Interactive Mode")
    print("Type 'quit' to exit, 'refresh' to update device list")
    print("=" * 60)
    
    try:
        agent = GeneralHouseAgent()
        await agent.initialize()
        
        while True:
            try:
                print("\n" + "─" * 60)
                command = input("💬 Enter your command: ").strip()
                
                if command.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if command.lower() == 'refresh':
                    await agent._refresh_device_list()
                    continue
                
                if not command:
                    continue
                
                # Process the command
                result = await agent.process_command(command)
                
                # Display results
                print("─" * 60)
                if result["success"]:
                    print(f"✅ {result['summary']}")
                    
                    if result.get("lights_on"):
                        print(f"\n🔆 Lights ON ({len(result['lights_on'])}):")
                        for light in result["lights_on"]:
                            name = light.get("friendly_name", light["entity_id"])
                            print(f"  - {name}")
                    
                    if result.get("lights_off") and len(result["lights_off"]) <= 10:
                        print(f"\n💤 Lights OFF ({len(result['lights_off'])}):")
                        for light in result["lights_off"]:
                            name = light.get("friendly_name", light["entity_id"])
                            print(f"  - {name}")
                    elif result.get("lights_off"):
                        print(f"\n💤 {len(result['lights_off'])} lights are off")
                    
                    if result.get("timestamp"):
                        print(f"\n🕐 Completed at: {result['timestamp']}")
                        
                else:
                    print(f"❌ Error: {result['error']}")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(interactive_mode())