#!/usr/bin/env python3
"""
Example: Tamil/English speech interaction
"""

import asyncio
from relayshell import RelayShell

async def main():
    """Demonstrate Tamil/English speech capabilities."""
    print("🗣️ RelayShell Example - Tamil/English Speech")
    
    relay = RelayShell()
    
    try:
        await relay.start()
        
        # Test English speech
        print("\n🇺🇸 Testing English TTS...")
        await relay.speak("Hello! RelayShell is ready to assist you.", "en-US")
        
        # Test Tamil speech (if available)
        print("\n🇮🇳 Testing Tamil TTS...")
        await relay.speak("வணக்கம்! RelayShell உங்களுக்கு உதவ தயாராக உள்ளது.", "ta-IN")
        
        # Switch language
        print("\n🔄 Switching to Tamil...")
        relay.switch_language("ta-IN")
        
        print("\n👂 Say something in Tamil or English...")
        print("RelayShell will detect the language automatically")
        
        # Listen for 10 seconds
        await asyncio.sleep(10)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await relay.stop()

if __name__ == "__main__":
    asyncio.run(main())