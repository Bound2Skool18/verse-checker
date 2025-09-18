#!/usr/bin/env python3
"""
Demo script for the Bible Verse Checker API.

This script demonstrates how to use the verse checker both programmatically
and via the REST API.
"""

import json
import time
from fastapi.testclient import TestClient
from app.main import app

def demo_verse_checker():
    """Demonstrate the Bible Verse Checker functionality."""
    print("🙏 Bible Verse Checker Demo")
    print("=" * 50)
    
    # Initialize test client
    client = TestClient(app)
    
    # Test cases
    test_cases = [
        {
            "name": "Exact Bible Verse",
            "quote": "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.",
            "expected": "Should be a perfect match (John 3:16)"
        },
        {
            "name": "Partial Bible Quote",
            "quote": "For God so loved the world",
            "expected": "Should match John 3:16 with lower similarity"
        },
        {
            "name": "Another Famous Verse",
            "quote": "The LORD is my shepherd; I shall not want.",
            "expected": "Should match Psalm 23:1"
        },
        {
            "name": "Paraphrased Quote",
            "quote": "I can do all things through Christ",
            "expected": "Should match Philippians 4:13"
        },
        {
            "name": "Non-Biblical Quote",
            "quote": "To be or not to be, that is the question",
            "expected": "Should not match (Shakespeare, not Bible)"
        },
        {
            "name": "Modern Paraphrase",
            "quote": "Trust in God with all your heart",
            "expected": "Should match Proverbs 3:5"
        },
        {
            "name": "Empty Quote",
            "quote": "",
            "expected": "Should handle gracefully"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"Quote: \"{test_case['quote']}\"")
        print(f"Expected: {test_case['expected']}")
        
        try:
            response = client.post("/check", json={"quote": test_case['quote']})
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Match: {result['match']}")
                print(f"   Score: {result['score']:.3f}")
                print(f"   Reference: {result['reference']}")
                if result['message']:
                    print(f"   Message: {result['message']}")
                if result['match']:
                    print(f"   Text: {result['text'][:60]}{'...' if len(result['text']) > 60 else ''}")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"   Details: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
        
        # Small delay for readability
        time.sleep(0.5)
    
    print("\n" + "=" * 50)
    print("🎉 Demo completed!")
    print(f"\nTo start the API server, run:")
    print(f"  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print(f"\nThen visit http://localhost:8000/docs for interactive API documentation")

if __name__ == "__main__":
    demo_verse_checker()