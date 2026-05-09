"""
Test script to debug chatbot issues
"""

import sys
import os

# Add the antigena_defense directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'antigena_defense'))

try:
    print("Testing chatbot import...")
    from chatbot.chatbot_service import AntigenaChatbot
    print("✅ Chatbot service imported successfully")
    
    print("Testing chatbot initialization...")
    chatbot = AntigenaChatbot()
    print("✅ Chatbot initialized successfully")
    
    print("Testing simple message processing...")
    import asyncio
    
    async def test_message():
        response = await chatbot.process_message("hello")
        print(f"✅ Response: {response.response[:100]}...")
        return response
    
    result = asyncio.run(test_message())
    print("✅ Chatbot working correctly!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
