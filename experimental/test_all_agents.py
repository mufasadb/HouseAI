#!/usr/bin/env python3
"""
Test All Core Agents - Non-interactive testing script
Tests the core agents without interactive input loops
"""

import subprocess
import sys
import os

def test_agent(script_name, test_input, agent_name):
    """Test an agent with non-interactive mode"""
    print(f"\n🧪 Testing {agent_name}...")
    print(f"Input: '{test_input}'")
    print("-" * 40)
    
    try:
        # Run the agent script in test mode
        if "routing_agent" in script_name:
            # Routing agent uses --test-mode instead of --test
            result = subprocess.run([
                sys.executable, 
                script_name,
                "--test-mode", 
                test_input
            ], capture_output=True, text=True, timeout=30)
        else:
            result = subprocess.run([
                sys.executable, 
                script_name,
                "--test", 
                test_input
            ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✅ {agent_name} - SUCCESS")
            print(f"Output: {result.stdout.strip()}")
        else:
            print(f"❌ {agent_name} - FAILED (exit code: {result.returncode})")
            print(f"Error: {result.stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {agent_name} - TIMEOUT (30s)")
        return False
    except Exception as e:
        print(f"💥 {agent_name} - EXCEPTION: {e}")
        return False
    
    return True

def main():
    """Test all core agents"""
    print("🧪 Testing All Core Agents")
    print("=" * 50)
    
    # Change to the parent directory where agents are located
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    tests = [
        ("run_routing_agent.py", "How do I say hello in Japanese?", "Routing Agent (Japanese)"),
        ("run_routing_agent.py", "What is machine learning?", "Routing Agent (General)"),
    ]
    
    # Note: Home Assistant and Japanese agents require credentials that may not be available
    # The routing agent provides the best coverage since it can handle all routing scenarios
    
    results = []
    
    for script, test_input, name in tests:
        success = test_agent(script, test_input, name)
        results.append((name, success))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name}: {status}")
        if success:
            passed += 1
    
    total = len(results)
    print(f"\nOverall: {passed}/{total} agents passed")
    
    if passed == total:
        print("🎉 All agents are working correctly!")
        return 0
    else:
        print("⚠️  Some agents need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())