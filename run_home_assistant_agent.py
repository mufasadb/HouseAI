#!/usr/bin/env python3
"""
Home Assistant Agent Runner using AI Lego Bricks Orchestrator
Uses the tool_call step type with the Home Assistant tool
"""

import sys
import asyncio
import argparse
from pathlib import Path

# Add the ai-lego-bricks directory to the path
ai_lego_path = Path(__file__).parent / "ai-lego-bricks"
sys.path.insert(0, str(ai_lego_path))

from agent_orchestration.orchestrator import AgentOrchestrator
from tools.home_assistant_tool import create_home_assistant_tool
from tools.tool_registry import register_tool_globally
from credentials import CredentialManager


async def main():
    parser = argparse.ArgumentParser(description="Run Home Assistant Agent")
    parser.add_argument("--test", type=str, help="Test command to run non-interactively")
    args = parser.parse_args()

    print("🏠 Starting Home Assistant Control Agent...")
    
    try:
        # Load .env explicitly
        from dotenv import load_dotenv
        load_dotenv()
        
        # Initialize credential manager
        cred_manager = CredentialManager(load_env=True)
        
        # Create and register Home Assistant tool
        print("🔧 Registering Home Assistant tool...")
        ha_tool = create_home_assistant_tool(cred_manager)
        await register_tool_globally(ha_tool, "smart_home")
        print("✅ Home Assistant tool registered")
        
        # Load the agent configuration
        agent_config_path = Path(__file__).parent / "home_assistant_agent.json"
        orchestrator = AgentOrchestrator(credential_manager=cred_manager)
        workflow = orchestrator.load_workflow_from_file(str(agent_config_path))
        
        if args.test:
            # Non-interactive test mode
            print(f"🧪 Testing with command: {args.test}")
            print("--" * 25)
            
            # Provide the test input
            inputs = {"user_request": args.test}
            result = orchestrator.execute_workflow(workflow, inputs)
            
            if result.success:
                print(f"Response: {result.final_output}")
            else:
                print(f"Error: {result.error}")
            
        else:
            # Interactive mode
            print("Available commands:")
            print("  - 'turn on table light'")
            print("  - 'turn off [light name]'")
            print("  - 'list all lights'")
            print("  - 'show me all switches'")
            print("  - Type 'quit' to exit")
            print("--" * 25)
            
            while True:
                try:
                    user_input = input("\n💬 Your command: ").strip()
                    
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        print("👋 Goodbye!")
                        break
                    
                    if not user_input:
                        continue
                    
                    # Run the orchestrator with user input
                    inputs = {"user_request": user_input}
                    result = orchestrator.execute_workflow(workflow, inputs)
                    
                    if result.success:
                        print(f"\n{result.final_output}")
                    else:
                        print(f"\nError: {result.error}")
                    
                except KeyboardInterrupt:
                    print("\n👋 Goodbye!")
                    break
                except Exception as e:
                    print(f"\n❌ Error: {e}")
                    
    except Exception as e:
        print(f"❌ Failed to start agent: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())