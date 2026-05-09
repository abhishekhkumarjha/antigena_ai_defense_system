"""
Test frontend API connection
"""

import requests
import json

def test_frontend_api():
    # Test direct backend
    print("Testing direct backend...")
    try:
        response = requests.post(
            "http://localhost:8000/chatbot/chat",
            json={"message": "hello", "user_context": {}},
            timeout=5
        )
        print(f"Backend response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response data: {json.dumps(data, indent=2)[:200]}...")
        else:
            print(f"Backend error: {response.text}")
    except Exception as e:
        print(f"Backend error: {e}")
    
    # Test through frontend proxy
    print("\nTesting frontend proxy...")
    try:
        response = requests.post(
            "http://localhost:3002/api/chatbot/chat",
            json={"message": "hello", "user_context": {}},
            timeout=5
        )
        print(f"Frontend response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response data: {json.dumps(data, indent=2)[:200]}...")
        else:
            print(f"Frontend error: {response.text}")
    except Exception as e:
        print(f"Frontend error: {e}")

if __name__ == "__main__":
    test_frontend_api()
