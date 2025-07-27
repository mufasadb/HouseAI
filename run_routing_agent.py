#!/usr/bin/env python3
"""
Multi-Agent Router with Streaming Support
Routes queries to Japanese, Home Assistant, or General agents and streams responses back
"""

import sys
import os
import asyncio

# Add ai-lego-bricks to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai-lego-bricks'))

# Import from ai-lego-bricks directory
from credentials.credential_manager import CredentialManager
from agent_orchestration.orchestrator import AgentOrchestrator


class MultiAgentRouter:
    """Routes queries to appropriate specialized agents with streaming support"""
    
    def __init__(self, quiet=False):
        # Load .env explicitly like the direct Home Assistant agent does
        from dotenv import load_dotenv
        load_dotenv()
        self.creds = CredentialManager(load_env=True)
        self.quiet = quiet
        self.orchestrator = AgentOrchestrator(credential_manager=self.creds)
        
        # Agent configuration mapping
        self.agent_configs = {
            "JAPANESE": "streaming_japanese_agent.json",
            "HOME_ASSISTANT": "home_assistant_agent.json",  # Use the working home assistant agent
            "GENERAL": None  # No general agent configured
        }
        
        # Initialize services
        self._setup_services()
        
        if not self.quiet:
            print("🤖 Multi-Agent Router initialized")
    
    async def _setup_tools_async(self):
        """Setup Home Assistant tools for smart home integration (async)"""
        try:
            from tools.home_assistant_tool import create_home_assistant_tool
            from tools import register_tool_globally
            
            # Create and register the Home Assistant tool globally
            tool = create_home_assistant_tool(self.creds)
            await register_tool_globally(tool, category="smart_home")
            
            if not self.quiet:
                print("✅ Home Assistant tools initialized successfully")
        except Exception as e:
            if not self.quiet:
                print(f"⚠️  Home Assistant tools initialization failed: {e}")
    
    def _setup_services(self):
        """Setup LLM and TTS services for the orchestrator"""
        try:
            # Import the factory function
            from llm.llm_factory import create_ollama_generation
            
            # Create Ollama generation service
            gen_service = create_ollama_generation(
                model="gemma3:4b",
                temperature=0.1,
                max_tokens=10,
                credential_manager=self.creds
            )
            
            # Inject into orchestrator
            self.orchestrator._services['generation'] = gen_service
            
            if not self.quiet:
                print("✅ Ollama generation service initialized")
                
        except Exception as e:
            if not self.quiet:
                print(f"⚠️  Generation service initialization failed: {e}")
        
        # Setup TTS service for TTS routing workflows
        try:
            # For now, just print a note about TTS
            if not self.quiet:
                print("⚠️  TTS service not configured for routing (TTS workflows will fail at TTS step)")
                
        except Exception as e:
            if not self.quiet:
                print(f"⚠️  TTS service initialization failed: {e}")
    
    
    def route_query(self, user_query, use_tts=False):
        """Determine which agent should handle the query"""
        
        # Choose routing workflow based on TTS preference
        routing_file = "routing_agent_with_tts.json" if use_tts else "routing_agent.json"
        
        # Load routing workflow
        routing_workflow = self.orchestrator.load_workflow_from_file(routing_file)
        
        # Execute routing decision
        routing_result = self.orchestrator.execute_workflow(
            routing_workflow, 
            {"user_query": user_query}
        )
        
        if not routing_result.success:
            if not self.quiet:
                print(f"❌ Routing failed: {routing_result.error}")
            return "GENERAL"  # Fallback to general agent
        
        # Extract the routing decision from the response
        routing_decision = routing_result.final_output
        
        # Debug output
        if not self.quiet:
            print(f"🔍 Raw routing result: {routing_decision}")
            if hasattr(routing_result, 'step_outputs'):
                print(f"🔍 Step outputs: {routing_result.step_outputs}")
        
        # Handle case where final_output is a formatted string from workflow
        if isinstance(routing_decision, str) and "🤖 Router: Routing to " in routing_decision:
            # Extract just the agent name from formatted output
            parts = routing_decision.split("🤖 Router: Routing to ")
            if len(parts) > 1:
                agent_part = parts[1].replace(" agent", "").strip()
                return agent_part if agent_part in ["JAPANESE", "HOME_ASSISTANT", "GENERAL"] else "GENERAL"
        
        # For TTS routing, look for different output format
        if use_tts and "📍 Routing to:" in routing_decision:
            parts = routing_decision.split("📍 Routing to:")
            if len(parts) > 1:
                agent_part = parts[1].split(" agent")[0].strip()
                return agent_part if agent_part in ["JAPANESE", "HOME_ASSISTANT", "GENERAL"] else "GENERAL"
        
        # Improved routing decision extraction to avoid false positives
        return self._extract_agent_from_response(routing_decision)
    
    def _extract_agent_from_response(self, response: str) -> str:
        """Extract agent decision from LLM response with improved logic"""
        
        if not response:
            return "GENERAL"
        
        response_upper = response.upper().strip()
        agents = ["JAPANESE", "HOME_ASSISTANT", "GENERAL"]
        
        # Method 1: Exact match (ideal case - LLM follows instructions)
        if response_upper in agents:
            return response_upper
        
        # Method 2: Look for agents as whole words at start of response
        # This handles cases like "JAPANESE for language questions"
        for agent in agents:
            if response_upper.startswith(agent):
                return agent
        
        # Method 3: Look for agents as whole words at end of response  
        # This handles cases like "This should go to JAPANESE"
        for agent in agents:
            if response_upper.endswith(agent):
                return agent
        
        # Method 4: Look for "-> AGENT" pattern (common in explanatory responses)
        import re
        for agent in agents:
            pattern = r'->\s*' + re.escape(agent) + r'\b'
            if re.search(pattern, response_upper):
                return agent
        
        # Method 5: Count agent mentions and use the last one mentioned
        # This handles cases where multiple agents are mentioned
        last_positions = {}
        for agent in agents:
            # Find the last occurrence of each agent
            pos = response_upper.rfind(agent)
            if pos != -1:
                last_positions[agent] = pos
        
        if last_positions:
            # Return the agent that appears last (most likely the final decision)
            latest_agent = max(last_positions.items(), key=lambda x: x[1])
            return latest_agent[0]
        
        # Method 6: Fallback - look for any occurrence, but prefer order: GENERAL, HOME_ASSISTANT, JAPANESE
        # Reverse order to prefer more specific agents when all are mentioned
        for agent in ["GENERAL", "HOME_ASSISTANT", "JAPANESE"]:
            if agent in response_upper:
                return agent
        
        # Default fallback
        return "GENERAL"
    
    def execute_with_agent(self, agent_type, user_query):
        """Execute the query with the specified agent"""
        
        if agent_type not in self.agent_configs:
            if not self.quiet:
                print(f"❌ Unknown agent type: {agent_type}")
            return f"Sorry, I don't have an agent configured to handle that type of request."
        
        config_file = self.agent_configs[agent_type]
        
        # Handle GENERAL queries with a simple response since we don't have a general agent
        if agent_type == "GENERAL" or config_file is None:
            return f"I'm a specialized routing system. I can help with Japanese language learning or smart home control, but I don't have a general chat agent configured for '{user_query}'. Please ask about Japanese language or smart home devices."
        
        if not os.path.exists(config_file):
            if not self.quiet:
                print(f"❌ Config file not found: {config_file}")
            return f"Error: Agent configuration {config_file} not found"
        
        try:
            # Load and execute the appropriate agent workflow
            workflow = self.orchestrator.load_workflow_from_file(config_file)
            
            # Prepare inputs for the agent
            inputs = {
                "user_input": user_query,
                "user_query": user_query,
                "user_request": user_query,
                "user_question": user_query,
                "user_command": user_query,
                "message": user_query
            }
            
            # Execute the workflow
            result = self.orchestrator.execute_workflow(workflow, inputs)
            
            if result.success:
                return result.final_output
            else:
                return f"❌ Agent execution failed: {result.error}"
                
        except Exception as e:
            return f"❌ Error executing {agent_type} agent: {e}"
    
    def process_query(self, user_query, use_tts=False):
        """Full pipeline: route query and execute with appropriate agent"""
        
        if not self.quiet:
            print(f"\n🔍 Analyzing query: '{user_query}'")
        
        # Step 1: Route the query
        agent_type = self.route_query(user_query, use_tts=use_tts)
        
        if not self.quiet:
            print(f"🎯 Routing to: {agent_type} agent")
        
        # Step 2: Execute with the chosen agent
        response = self.execute_with_agent(agent_type, user_query)
        
        # Step 3: Clean up the response for better user experience
        cleaned_response = self._clean_agent_response(response, agent_type)
        
        return agent_type, cleaned_response
    
    def _clean_agent_response(self, response: str, agent_type: str) -> str:
        """Clean up agent responses for better user presentation"""
        
        if not response:
            return "Sorry, I couldn't process your request."
        
        # Handle Home Assistant responses with complex data structures
        if agent_type == "HOME_ASSISTANT":
            return self._extract_natural_language_from_ha_response(response)
        
        # Handle other agent responses
        return self._clean_generic_response(response)
    
    def _extract_natural_language_from_ha_response(self, response: str) -> str:
        """Extract natural language from Home Assistant tool responses"""
        
        try:
            # First, clean up any prefixes
            content = response
            if content.startswith("response: "):
                content = content[10:].strip()
            
            # Check for HTML error responses (common with network issues)
            if content.strip().startswith("<!DOCTYPE html>") or "<html" in content[:100]:
                # This is likely an HTML error page - extract useful info
                if "Cloudflare Tunnel error" in content:
                    return "🏠 Smart Home Assistant: Sorry, I can't connect to your home automation system right now. The connection appears to be down. Please try again later."
                elif "Error 503" in content or "Error 502" in content or "Error 530" in content:
                    return "🏠 Smart Home Assistant: Sorry, your home automation system is currently unavailable. Please try again in a few minutes."
                else:
                    return "🏠 Smart Home Assistant: Sorry, I'm having trouble connecting to your home automation system right now."
            
            # Check for API error patterns
            if "Home Assistant API error:" in content:
                # Extract just the error code and provide user-friendly message
                if "530" in content:
                    return "🏠 Smart Home Assistant: Your home automation system is currently offline or unreachable. Please check your Home Assistant connection."
                elif "502" in content:
                    return "🏠 Smart Home Assistant: Your Home Assistant server appears to be down. Please check if your Home Assistant instance is running."
                elif "503" in content:
                    return "🏠 Smart Home Assistant: Your Home Assistant server is temporarily unavailable. Please try again in a moment."
                elif "403" in content:
                    return "🏠 Smart Home Assistant: I don't have permission to access your home automation system. Please check the API credentials."
                elif "404" in content:
                    return "🏠 Smart Home Assistant: The requested device or service wasn't found in your home automation system."
                else:
                    return "🏠 Smart Home Assistant: There was an error communicating with your home automation system. Please try again."
            
            # Now look for data structure patterns
            if content.startswith("{'success'") or content.startswith('{"success"'):
                import ast
                try:
                    # Use ast.literal_eval for safer evaluation
                    if content.startswith("{'"):
                        data = ast.literal_eval(content)
                    else:
                        import json
                        data = json.loads(content)
                    
                    # Extract natural language response
                    if isinstance(data, dict):
                        # Try different fields
                        for field in ['final_response', 'response', 'content']:
                            if field in data and data[field]:
                                return f"🏠 Smart Home Assistant: {data[field]}"
                        
                        # Try conversation history
                        if 'conversation_history' in data and data['conversation_history']:
                            last_msg = data['conversation_history'][-1]
                            if last_msg.get('role') == 'assistant' and last_msg.get('content'):
                                return f"🏠 Smart Home Assistant: {last_msg['content']}"
                except Exception as parse_error:
                    if not self.quiet:
                        print(f"Could not parse HA response: {parse_error}")
            
            # Look for existing Smart Home Assistant prefix
            if "🏠 Smart Home Assistant:" in content:
                return content
            
            # Check for common error patterns before treating as plain text
            if "encountered an error:" in content.lower():
                # Keep the error message but make it more user-friendly
                error_part = content[content.lower().find("encountered an error:"):].strip()
                return f"🏠 Smart Home Assistant: Sorry, I {error_part}"
            
            # If we get here, treat as plain text and add prefix
            return f"🏠 Smart Home Assistant: {content}"
            
        except Exception as e:
            if not self.quiet:
                print(f"Error processing HA response: {e}")
            return "🏠 Smart Home Assistant: Sorry, I encountered an unexpected error while processing your request."
    
    def _clean_generic_response(self, response: str) -> str:
        """Clean up generic agent responses"""
        
        # Remove response prefixes if they exist
        prefixes_to_clean = [
            "response: ",
            "routing_decision: ",
            "final_output: "
        ]
        
        cleaned = response
        for prefix in prefixes_to_clean:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        
        return cleaned


def main():
    """Interactive mode for the multi-agent router"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Agent Router")
    parser.add_argument("--test-mode", help="Run in test mode with provided query")
    parser.add_argument("--tts", action="store_true", help="Use TTS routing agent with voice output")
    args = parser.parse_args()
    
    # Test mode for quick testing
    if args.test_mode:
        try:
            router = MultiAgentRouter(quiet=False)  # Enable debug output
            # Setup Home Assistant tools asynchronously
            asyncio.run(router._setup_tools_async())
            agent_type, response = router.process_query(args.test_mode, use_tts=args.tts)
            print(f"Query: '{args.test_mode}'")
            print(f"Routed to: {agent_type}")
            print(f"Response: {response}")
            return 0
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return 1
    
    # Interactive mode
    print("🤖 Multi-Agent Router with Streaming")
    print("=" * 50)
    print("I can route your queries to:")
    print("🇯🇵 Japanese Language Tutor")
    print("🏠 Smart Home Assistant") 
    print("💬 General Chat Assistant")
    print("=" * 50)
    
    try:
        router = MultiAgentRouter()
        # Setup Home Assistant tools asynchronously
        print("🔧 Setting up Home Assistant tools...")
        asyncio.run(router._setup_tools_async())
        print("✅ Router ready!")
        
        print("\n💬 Ask me anything! (type 'quit' to exit)")
        print("Examples:")
        print("- 'How do I say hello in Japanese?'")
        print("- 'Turn on beachy's light'")
        print("- 'What is machine learning?'")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Process the query through routing and execution
                agent_type, response = router.process_query(user_input)
                
                # Display the result
                print(f"\n{response}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                
    except Exception as e:
        print(f"❌ Failed to initialize router: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())