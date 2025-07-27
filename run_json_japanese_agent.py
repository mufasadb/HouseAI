#!/usr/bin/env python3
"""
Japanese Learning Agent - JSON-Driven Implementation
Leverages ai-lego-bricks agent orchestration instead of Python code
"""

import sys
import os
import json
from pathlib import Path

# Add ai-lego-bricks to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai-lego-bricks'))

# Import from ai-lego-bricks directory
from agent_orchestration.orchestrator import AgentOrchestrator

def setup_generation_service():
    """Setup generation service for the orchestrator"""
    try:
        # Import the factory function
        from llm.llm_factory import create_ollama_generation
        from credentials.credential_manager import CredentialManager
        
        # Create credential manager
        creds = CredentialManager(load_env=True)
        
        # Create Ollama generation service
        gen_service = create_ollama_generation(
            model="gemma3:4b",
            temperature=0.3,
            max_tokens=300,
            credential_manager=creds
        )
        
        return gen_service
        
    except Exception as e:
        print(f"⚠️  Generation service initialization failed: {e}")
        return None

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Japanese Learning Agent")
    parser.add_argument("--test", help="Run test question instead of interactive mode")
    args = parser.parse_args()
    
    print("🇯🇵 Japanese Learning Agent (JSON-Driven)")
    print("=" * 50)
    
    try:
        # Load the streaming Japanese agent configuration
        agent_file = "streaming_japanese_agent.json"
        if not os.path.exists(agent_file):
            print(f"❌ Agent file not found: {agent_file}")
            return 1
        
        # Create orchestrator and load workflow
        orchestrator = AgentOrchestrator()
        
        # Setup generation service
        gen_service = setup_generation_service()
        if gen_service:
            orchestrator._services['generation'] = gen_service
            print("✅ Generation service initialized")
        else:
            print("⚠️ Generation service not available")
        
        workflow = orchestrator.load_workflow_from_file(agent_file)
        
        print("✅ Japanese learning agent ready!")
        print("\n💬 Ask me Japanese language questions! (type 'quit' to exit)")
        print("Examples:")
        print("- How do I say 'to eat' in Japanese?")
        print("- What is the て form used for?")
        print("- How do you conjugate verbs?")
        print("-" * 50)
        
        # Test mode - run single question and exit
        if args.test:
            try:
                inputs = {"user_question": args.test}
                result = orchestrator.execute_workflow(workflow, inputs)
                
                if result.success:
                    print(result.final_output)
                    return 0
                else:
                    print(f"❌ Error: {result.error}")
                    return 1
            except Exception as e:
                print(f"❌ Test failed: {e}")
                return 1
        
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                    print("👋 Goodbye! 頑張って！(Good luck!)")
                    break
                
                if not user_input:
                    continue
                
                print("🤔 Thinking...")
                
                # Execute the workflow with user input
                inputs = {"user_question": user_input}
                result = orchestrator.execute_workflow(workflow, inputs)
                
                if result.success:
                    # Display the response
                    print(result.final_output)
                else:
                    print(f"❌ Error: {result.error}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye! 頑張って！(Good luck!)")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())