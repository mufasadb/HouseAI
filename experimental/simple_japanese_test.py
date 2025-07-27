#!/usr/bin/env python3
"""
Simple Japanese Question Test - Direct Ollama
Test Japanese learning without ai-lego-bricks to bypass import issues
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def ask_japanese_question(question):
    """Ask a Japanese learning question directly to Ollama"""
    
    ollama_url = os.getenv('OLLAMA_URL', 'http://100.83.40.11:11434')
    model = os.getenv('OLLAMA_DEFAULT_MODEL', 'gemma3:4b')
    
    system_prompt = """You are a Japanese language tutor. Provide brief, clear answers to Japanese language questions.

Guidelines:
- Keep responses under 100 words
- Include Japanese text with romaji (romanization) when relevant  
- Be educational but concise
- Focus on practical usage
- Use simple explanations"""

    full_prompt = f"{system_prompt}\n\nUser question: {question}"

    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": False
    }
    
    try:
        response = requests.post(f"{ollama_url}/api/generate", json=payload)
        response.raise_for_status()
        
        result = response.json()
        return result['response']
        
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    question = "How do you say 'its better to practice japanese in japan' in Japanese?"
    
    print("🇯🇵 Simple Japanese Learning Test")
    print("=" * 50)
    print(f"Question: {question}")
    print("-" * 50)
    
    answer = ask_japanese_question(question)
    print(f"Answer: {answer}")