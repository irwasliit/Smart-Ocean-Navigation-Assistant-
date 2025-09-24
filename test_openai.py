#!/usr/bin/env python3
"""
Quick test script for OpenAI API connectivity
"""
import os
import openai
from dotenv import load_dotenv

def test_openai_api():
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OPENAI_API_KEY found in .env file")
        return False
    
    print(f"🔑 API Key: {api_key[:20]}...{api_key[-10:]}")
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        print("🧪 Testing API connection...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello! Just testing the connection."}],
            max_tokens=50
        )
        
        print("✅ OpenAI API is working!")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API Error: {e}")
        if "quota" in str(e).lower():
            print("💡 Solution: Add credits to your OpenAI account or get a new API key")
        elif "authentication" in str(e).lower():
            print("💡 Solution: Check if your API key is valid")
        return False

if __name__ == "__main__":
    test_openai_api()