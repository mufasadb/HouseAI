#!/usr/bin/env python3
"""
Demo script for the Query Routing Agent

This script demonstrates how to use the AI Lego Bricks orchestration system
to route queries to specialized assistants based on content analysis.
"""

import sys
from pathlib import Path

# Add the ai-lego-bricks directory to the path
ai_lego_path = Path(__file__).parent / "ai-lego-bricks"
sys.path.insert(0, str(ai_lego_path))

from agent_orchestration import AgentOrchestrator

def demo_query_routing():
    """Demonstrate the query routing agent with sample queries."""
    
    # Initialize the orchestrator
    orchestrator = AgentOrchestrator()
    
    # Load the routing workflow
    workflow_path = Path(__file__).parent / "query_routing_agent.json"
    workflow = orchestrator.load_workflow_from_file(workflow_path)
    
    # Sample queries to test different routing paths
    test_queries = [
        "How do I set up a smart thermostat with Home Assistant?",
        "What does 'arigatou gozaimasu' mean in Japanese?",
        "Can you explain quantum computing?",
        "How to automate my lights to turn on at sunset?",
        "What are some popular anime series to watch?",
        "What is the time complexity of quicksort?",
        "How do I configure motion sensor automations?",
        "Tell me about Japanese tea ceremony",
        "How do I implement a binary search tree?"
    ]
    
    print("🤖 Query Routing Agent Demo")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📋 Test Query {i}: {query}")
        print("-" * 50)
        
        try:
            # Execute the workflow with the test query
            result = orchestrator.execute_workflow(workflow, {
                "user_query": query
            })
            
            print(result.final_output)
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
        
        if i < len(test_queries):
            print("\n" + "="*30)
    
    print("\n✅ Demo completed!")

def interactive_mode():
    """Run the agent in interactive mode for custom queries."""
    
    orchestrator = AgentOrchestrator()
    workflow_path = Path(__file__).parent / "query_routing_agent.json"
    workflow = orchestrator.load_workflow_from_file(workflow_path)
    
    print("🤖 Interactive Query Routing Agent")
    print("Type 'quit' to exit")
    print("=" * 50)
    
    while True:
        query = input("\n💬 Your query: ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
            
        if not query:
            continue
            
        try:
            result = orchestrator.execute_workflow(workflow, {
                "user_query": query
            })
            
            print("\n" + result.final_output)
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Run demo mode by default
    demo_query_routing()