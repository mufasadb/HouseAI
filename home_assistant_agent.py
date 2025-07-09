#!/usr/bin/env python3
"""
Home Assistant Agent with LLM Integration
Uses AI Lego Bricks to create an agent that can interact with Home Assistant using tools
"""

import sys
import os
import asyncio
from pathlib import Path
from typing import Dict, Any

# Add the ai-lego-bricks directory to the path
ai_lego_path = Path(__file__).parent / "ai-lego-bricks"
sys.path.insert(0, str(ai_lego_path))

from credentials import CredentialManager
from tools.home_assistant_tool import create_home_assistant_tool
from tools.tool_registry import register_tool_globally
from tools.tool_service import ToolService
from llm.llm_factory import create_text_client
from llm.generation_service import GenerationService, LLMProvider

class HomeAssistantAgent:
    """Agent that can control Home Assistant using natural language"""
    
    def __init__(self):
        # Initialize credential manager
        from dotenv import load_dotenv
        load_dotenv()  # Explicitly load .env first
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
        
        # Register Home Assistant tool
        self.ha_tool = None
        
    async def initialize(self):
        """Initialize the agent and register tools"""
        print("🤖 Initializing Home Assistant Agent...")
        
        # Create and register Home Assistant tool
        self.ha_tool = create_home_assistant_tool(self.cred_manager)
        await register_tool_globally(self.ha_tool, "home_automation")
        
        # Verify tool registration
        tool_service = ToolService()
        available_tools = await tool_service.get_available_tools()
        if "home_assistant" in [tool.name for tool in available_tools]:
            print("✅ Home Assistant tool registered successfully")
        else:
            raise RuntimeError("Failed to register Home Assistant tool")
        
        print(f"🏠 Connected to Home Assistant at: {self.hass_url}")
        print("🔧 Agent ready to process commands")
    
    async def execute_command(self, user_command: str) -> Dict[str, Any]:
        """Execute a natural language command using the Home Assistant tool"""
        
        # Create a prompt that instructs the LLM to use the Home Assistant tool
        system_prompt = f"""You are a Home Assistant control agent. You have access to a home_assistant tool that can:

1. get_states - Get all entities or filter by domain (e.g., domain: "light")
2. get_state - Get state of specific entity (e.g., entity_id: "light.living_room")
3. turn_on - Turn on an entity (e.g., entity_id: "light.bedroom")
4. turn_off - Turn off an entity (e.g., entity_id: "light.kitchen")
5. call_service - Call any Home Assistant service

IMPORTANT INSTRUCTIONS:
- When asked about lights, ALWAYS use the get_states operation with domain: "light" first
- When looking for specific entities (like "Beachy" lights), get all entities first then filter
- If asked to check which lights are on, get the light states and analyze them
- For any Beachy-related requests, look for entity names containing "beachy" (case insensitive)
- Always provide clear, helpful responses about what you found

Current user command: {user_command}

Respond with the appropriate tool call(s) to fulfill this request, then provide a helpful summary of the results."""

        try:
            # Get response from LLM
            response = self.llm_client.chat(system_prompt)
            
            # Parse response to see if it contains tool usage instructions
            # For this demo, we'll manually execute the most common operations
            
            command_lower = user_command.lower()
            
            if "list" in command_lower and "light" in command_lower:
                return await self._get_all_lights()
            elif "beachy" in command_lower and ("on" in command_lower or "status" in command_lower):
                return await self._check_beachy_lights()
            elif "turn on" in command_lower:
                return await self._handle_turn_on_command(user_command)
            elif "turn off" in command_lower:
                return await self._handle_turn_off_command(user_command)
            else:
                return {
                    "action": "llm_response",
                    "response": response,
                    "suggestion": "Try commands like: 'list all lights', 'check if any Beachy lights are on', 'turn on bedroom light'"
                }
                
        except Exception as e:
            return {
                "action": "error",
                "error": str(e),
                "command": user_command
            }
    
    async def _get_all_lights(self) -> Dict[str, Any]:
        """Get all light entities"""
        from tools.tool_types import ToolCall
        
        call = ToolCall(
            id="get_lights",
            name="home_assistant",
            parameters={
                "operation": "get_states",
                "domain": "light"
            }
        )
        
        result = await self.ha_tool.executor.execute(call)
        
        if result.error:
            return {"action": "error", "error": result.error}
        
        lights = result.result
        return {
            "action": "list_lights",
            "count": lights["count"],
            "lights": lights["entities"],
            "summary": f"Found {lights['count']} light entities"
        }
    
    async def _check_beachy_lights(self) -> Dict[str, Any]:
        """Check status of Beachy lights"""
        # First get all lights
        lights_result = await self._get_all_lights()
        
        if lights_result.get("action") == "error":
            return lights_result
        
        # Filter for Beachy lights
        all_lights = lights_result["lights"]
        beachy_lights = []
        beachy_lights_on = []
        
        for light in all_lights:
            entity_id = light['entity_id']
            friendly_name = light['friendly_name'] or entity_id
            
            if "beachy" in friendly_name.lower() or "beachy" in entity_id.lower():
                beachy_lights.append(light)
                if light['state'] == 'on':
                    beachy_lights_on.append(light)
        
        return {
            "action": "beachy_status",
            "beachy_lights_total": len(beachy_lights),
            "beachy_lights_on": len(beachy_lights_on),
            "lights_on": beachy_lights_on,
            "all_beachy_lights": beachy_lights,
            "summary": f"Found {len(beachy_lights)} Beachy lights, {len(beachy_lights_on)} are currently on"
        }
    
    async def _handle_turn_on_command(self, command: str) -> Dict[str, Any]:
        """Handle turn on commands"""
        # This is a simplified implementation - in practice you'd parse entity names from the command
        return {
            "action": "need_entity",
            "message": "Please specify which light to turn on (e.g., 'turn on light.bedroom')",
            "command": command
        }
    
    async def _handle_turn_off_command(self, command: str) -> Dict[str, Any]:
        """Handle turn off commands"""
        # This is a simplified implementation - in practice you'd parse entity names from the command
        return {
            "action": "need_entity", 
            "message": "Please specify which light to turn off (e.g., 'turn off light.kitchen')",
            "command": command
        }

async def demo_agent():
    """Demo the Home Assistant agent"""
    print("🏠 Home Assistant Agent Demo")
    print("=" * 50)
    
    try:
        # Initialize agent
        agent = HomeAssistantAgent()
        await agent.initialize()
        
        # Test commands
        test_commands = [
            "List all lights",
            "Check if any Beachy lights are on",
            "What's the status of my lights?"
        ]
        
        for i, command in enumerate(test_commands, 1):
            print(f"\n{'='*50}")
            print(f"🧪 Test {i}: {command}")
            print("="*50)
            
            result = await agent.execute_command(command)
            
            # Display results based on action type
            if result["action"] == "list_lights":
                print(f"✅ {result['summary']}")
                print("\n📋 Light Details:")
                for light in result["lights"]:
                    state_emoji = "🔆" if light["state"] == "on" else "💤"
                    name = light["friendly_name"] or light["entity_id"]
                    print(f"  {state_emoji} {name} ({light['entity_id']}) - {light['state']}")
                    
            elif result["action"] == "beachy_status":
                print(f"✅ {result['summary']}")
                if result["lights_on"]:
                    print("\n🔆 Beachy lights that are ON:")
                    for light in result["lights_on"]:
                        name = light["friendly_name"] or light["entity_id"]
                        print(f"  - {name} ({light['entity_id']})")
                else:
                    print("\n💤 No Beachy lights are currently on")
                    
                if result["all_beachy_lights"]:
                    print(f"\n📋 All Beachy lights found:")
                    for light in result["all_beachy_lights"]:
                        name = light["friendly_name"] or light["entity_id"]
                        state_emoji = "🔆" if light["state"] == "on" else "💤"
                        print(f"  {state_emoji} {name} ({light['entity_id']}) - {light['state']}")
                        
            elif result["action"] == "error":
                print(f"❌ Error: {result['error']}")
                
            else:
                print(f"🤖 Response: {result.get('response', 'Unknown action')}")
        
        print(f"\n{'='*50}")
        print("✅ Demo completed!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

async def interactive_mode():
    """Interactive mode for testing the agent"""
    print("🏠 Interactive Home Assistant Agent")
    print("Type 'quit' to exit")
    print("=" * 50)
    
    try:
        agent = HomeAssistantAgent() 
        await agent.initialize()
        
        while True:
            try:
                command = input("\n💬 Your command: ").strip()
                
                if command.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not command:
                    continue
                
                result = await agent.execute_command(command)
                
                # Display result
                if result["action"] == "beachy_status":
                    print(f"\n🔍 {result['summary']}")
                    if result["lights_on"]:
                        for light in result["lights_on"]:
                            name = light["friendly_name"] or light["entity_id"]
                            print(f"  🔆 {name} is ON")
                elif result["action"] == "list_lights":
                    print(f"\n📋 {result['summary']}")
                elif result["action"] == "error":
                    print(f"\n❌ Error: {result['error']}")
                else:
                    print(f"\n🤖 {result.get('response', 'Action completed')}")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        asyncio.run(interactive_mode())
    else:
        asyncio.run(demo_agent())