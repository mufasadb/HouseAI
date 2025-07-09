#!/usr/bin/env python3
"""
Working Query Routing Agent using direct LLM services
"""

import sys
import os
from pathlib import Path

# Add the ai-lego-bricks directory to the path
ai_lego_path = Path(__file__).parent / "ai-lego-bricks"
sys.path.insert(0, str(ai_lego_path))

# Set environment variables for Ollama
os.environ['OLLAMA_URL'] = 'http://100.83.40.11:11434'
os.environ['OLLAMA_DEFAULT_MODEL'] = 'qwen2.5:7b'

from llm.llm_factory import create_text_client, create_structured_client
from credentials import CredentialManager
from pydantic import BaseModel

class QueryClassification(BaseModel):
    category: str
    confidence: float
    reasoning: str

class QueryRoutingAgent:
    """Query routing agent using direct LLM services"""
    
    def __init__(self):
        # Create credential manager
        self.creds = CredentialManager({
            "OLLAMA_URL": "http://100.83.40.11:11434"
        }, load_env=False)
        
        # Create classifier
        self.classifier = create_structured_client(
            "ollama",
            QueryClassification,
            model="qwen2.5:7b",
            temperature=0.1,
            credential_manager=self.creds
        )
        
        # Create assistants
        self.home_assistant = create_text_client(
            "ollama",
            model="qwen2.5:7b",
            temperature=0.7,
            credential_manager=self.creds
        )
        
        self.japanese_assistant = create_text_client(
            "ollama", 
            model="qwen2.5:7b",
            temperature=0.7,
            credential_manager=self.creds
        )
        
        self.general_assistant = create_text_client(
            "ollama",
            model="qwen2.5:7b", 
            temperature=0.7,
            credential_manager=self.creds
        )
    
    def classify_query(self, query: str) -> QueryClassification:
        """Classify a query using the LLM"""
        classification_prompt = f"""You are a query classifier that determines which specialized assistant should handle a user's question. 

Classify queries into these categories:
- 'home': Smart home automation, IoT devices, home security, lighting, thermostats, appliances, Home Assistant platform
- 'japanese': Japanese language, culture, anime, manga, travel to Japan, Japanese food, customs, traditions  
- 'general': Everything else including science, programming, general knowledge, math, history, etc.

Provide a confidence score (0.0 to 1.0) and brief reasoning for your classification.

Query: {query}

Respond with JSON containing category, confidence, and reasoning."""
        
        return self.classifier.chat(classification_prompt)
    
    def get_response(self, query: str, category: str) -> str:
        """Get response from the appropriate assistant"""
        if category == "home":
            prompt = f"""You are a Home Assistant expert specializing in smart home automation, IoT devices, and home management systems. You have deep knowledge of:
- Home Assistant platform and integrations
- Smart lighting, thermostats, and climate control
- Security systems and cameras
- Automation scripts and scenes
- Device troubleshooting and setup
- Energy monitoring and management

Provide helpful, practical advice with specific examples and configuration details when appropriate.

Query: {query}"""
            return self.home_assistant.chat(prompt)
            
        elif category == "japanese":
            prompt = f"""You are a Japanese culture and language expert with comprehensive knowledge of:
- Japanese language (grammar, vocabulary, kanji, hiragana, katakana)
- Japanese culture, customs, and traditions
- Anime, manga, and Japanese entertainment
- Japanese food, cooking, and dining etiquette
- Travel in Japan (transportation, accommodations, attractions)
- Japanese business culture and social norms
- Japanese history and regional differences

Provide accurate, culturally sensitive information with practical examples. When discussing language, include romanization and explain cultural context.

Query: {query}"""
            return self.japanese_assistant.chat(prompt)
            
        else:  # general
            prompt = f"""You are a knowledgeable general assistant with expertise across many domains including:
- Programming and software development
- Science, mathematics, and technology
- History, geography, and social sciences
- Arts, literature, and philosophy
- Problem-solving and analysis
- Research and fact-checking

Provide accurate, well-reasoned responses with clear explanations. When appropriate, include examples, step-by-step guidance, or references to help users understand complex topics.

Query: {query}"""
            return self.general_assistant.chat(prompt)
    
    def route_query(self, query: str) -> dict:
        """Route a query to the appropriate assistant and return response"""
        print(f"📋 Query: {query}")
        print("-" * 50)
        
        # Classify the query
        print("🔍 Classifying query...")
        classification = self.classify_query(query)
        
        print(f"🤖 Assistant: {classification.category}")
        print(f"📊 Confidence: {classification.confidence:.2f}")
        print(f"💭 Reasoning: {classification.reasoning}")
        
        # Get response from appropriate assistant
        print(f"\n💬 Getting response from {classification.category} assistant...")
        response = self.get_response(query, classification.category)
        
        return {
            "query": query,
            "classification": classification,
            "response": response
        }

def demo_routing():
    """Demo the query routing with sample queries"""
    print("🤖 AI Lego Bricks Query Routing Agent")
    print("Testing with real Ollama LLM at: http://100.83.40.11:11434")
    print("=" * 60)
    
    # Create agent
    try:
        agent = QueryRoutingAgent()
        print("✅ Agent initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return
    
    # Test queries
    test_queries = [
        "How do I set up a smart thermostat with Home Assistant?",
        "What does 'konnichiwa' mean in Japanese?",
        "Explain the concept of machine learning algorithms"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"🧪 Test {i}/3")
        print("="*60)
        
        try:
            result = agent.route_query(query)
            
            print(f"\n📝 Response:")
            print("-" * 50)
            print(result["response"])
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("✅ Demo completed!")

def interactive_mode():
    """Interactive mode for testing custom queries"""
    print("🤖 Interactive Query Routing Agent")
    print("Type 'quit' to exit")
    print("=" * 50)
    
    try:
        agent = QueryRoutingAgent()
        print("✅ Agent ready!")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return
    
    while True:
        try:
            query = input("\n💬 Your query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            if not query:
                continue
            
            result = agent.route_query(query)
            
            print(f"\n📝 Response:")
            print("-" * 50)
            print(result["response"])
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_mode()
    else:
        demo_routing()