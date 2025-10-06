#!/usr/bin/env python3
"""
Example: Basic RelayShell usage
"""

import asyncio
from relayshell import RelayShell

async def main():
    """Demonstrate basic RelayShell functionality."""
    print("🚀 RelayShell Example - Basic Usage")
    
    # Create RelayShell instance
    relay = RelayShell()
    
    try:
        # Start RelayShell
        print("Starting RelayShell...")
        await relay.start()
        
        # Demo query
        print("\n📝 Querying LLMs with sample problem...")
        response = await relay.llm_manager.get_best_response(
            "How do I fix a Python import error?",
            "I'm getting 'ModuleNotFoundError: No module named requests'"
        )
        
        if response:
            print(f"\n✅ Best response from {response.provider}:")
            print(f"Confidence: {response.confidence_score:.2f}")
            print(f"Response: {response.response_text[:200]}...")
        else:
            print("❌ No response received")
        
        # Show status
        print("\n📊 System Status:")
        status = relay.get_status()
        print(f"- Running: {status['running']}")
        print(f"- LLM Backends: {len(status['llm'])}")
        print(f"- Speech Language: {status['speech']['current_language']}")
        
        # Wait a moment
        print("\n⏱️ RelayShell is running... Press Ctrl+C to stop")
        await asyncio.sleep(5)
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await relay.stop()
        print("👋 RelayShell stopped")

if __name__ == "__main__":
    asyncio.run(main())