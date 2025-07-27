#!/usr/bin/env python3
"""
Test if the Home Assistant tool is actually available to the AI agent
"""

import sys
import os
import asyncio

# Add ai-lego-bricks to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai-lego-bricks'))

from tools.home_assistant_tool import register_home_assistant_tool
from tools.tool_registry import get_global_registry
from tools.tool_types import ToolCall

async def test_tool_availability():
    """Test if the Home Assistant tool is properly registered and accessible"""
    
    print("🔧 Testing Home Assistant tool availability...")
    
    # Step 1: Register the tool
    print("\nStep 1: Registering Home Assistant tool...")
    tool = await register_home_assistant_tool()
    print(f"Registration result: {tool}")
    
    # Step 2: Check tool registry
    print("\nStep 2: Checking tool registry...")
    registry = await get_global_registry()
    available_tools = await registry.list_tools()
    print(f"Available tools: {available_tools}")
    
    # Step 3: Get the tool instance
    print("\nStep 3: Getting tool instance...")
    ha_tool = await registry.get_tool("home_assistant")
    print(f"Tool instance: {ha_tool}")
    
    # Step 4: Test the tool directly
    if ha_tool:
        print("\nStep 4: Testing tool directly...")
        print(f"Tool attributes: {dir(ha_tool)}")
        try:
            # Test using executor with proper ToolCall interface
            find_call = ToolCall(
                id="test_find",
                name="home_assistant",
                parameters={
                    "operation": "find_entity",
                    "search_term": "beachy",
                    "entity_type": "light"
                }
            )
            result = await ha_tool.executor.execute(find_call)
            print(f"Direct tool call result: {result}")
            
            if result and result.result and "matches" in result.result and result.result["matches"]:
                entity_id = result.result["matches"][0]["entity_id"]
                print(f"Found entity: {entity_id}")
                
                # Test turn_off_light operation
                print("\nTesting turn_off_light operation...")
                turn_off_call = ToolCall(
                    id="test_turn_off",
                    name="home_assistant", 
                    parameters={
                        "operation": "turn_off_light",
                        "entity_id": entity_id
                    }
                )
                turn_off_result = await ha_tool.executor.execute(turn_off_call)
                print(f"Turn off result: {turn_off_result}")
                
                return True
            else:
                print("❌ No entities found")
                return False
                
        except Exception as e:
            print(f"❌ Direct tool call failed: {e}")
            return False
    else:
        print("❌ Tool not available")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_tool_availability())
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Tool availability test")