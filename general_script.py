#!/usr/bin/env python3
"""
General Script - Simple CLI for House Assistant with Tool Usage
Accepts text input and passes to the house assistant for processing
"""

import sys
import asyncio
import argparse
from pathlib import Path

# Add the ai-lego-bricks directory to the path
ai_lego_path = Path(__file__).parent / "ai-lego-bricks"
sys.path.insert(0, str(ai_lego_path))

from general_house_agent import GeneralHouseAgent

async def process_single_command(command: str):
    """Process a single command and return the result"""
    try:
        agent = GeneralHouseAgent()
        await agent.initialize()
        
        result = await agent.process_command(command)
        
        # Format output based on result type
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
            
    except Exception as e:
        print(f"❌ Failed to process command: {e}")

async def interactive_mode():
    """Run in interactive mode"""
    print("🤖 General House Assistant - Interactive Mode")
    print("Type your commands in natural language")
    print("Type 'quit' to exit")
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
                
                if not command:
                    continue
                
                result = await agent.process_command(command)
                
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
                print(f"\n❌ Error: {e}")
                
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="General House Assistant CLI")
    parser.add_argument("command", nargs="*", help="Command to process (if not provided, runs in interactive mode)")
    parser.add_argument("-i", "--interactive", action="store_true", help="Run in interactive mode")
    
    args = parser.parse_args()
    
    if args.interactive or not args.command:
        asyncio.run(interactive_mode())
    else:
        command = " ".join(args.command)
        asyncio.run(process_single_command(command))

if __name__ == "__main__":
    main()