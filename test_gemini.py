#!/usr/bin/env python3
"""
Test Gemini API connection
"""
import os
import google.generativeai as genai

# Load API key
GEMINI_API_KEY = "AIzaSyCVFV1O16B-ByDargD7LzLt2Y6LLpDqqeQ"  # From .env

print(f"🔑 Testing Gemini API Key: {GEMINI_API_KEY[:20]}...")

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    print("✅ Gemini configured successfully")
    print("🧪 Testing simple generation...")
    
    response = model.generate_content("Say hello in Persian")
    
    print(f"✅ Response received: {response.text}")
    print("\n🎉 Gemini API is working!")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    print("\n💡 Try fallback model...")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say hello")
        print(f"✅ Fallback model works: {response.text}")
    except Exception as e2:
        print(f"❌ Fallback also failed: {e2}")
