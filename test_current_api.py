#!/usr/bin/env python3
"""
Test the current Bible Verse API to see what books are available
"""

import subprocess
import json
import sys

def test_api_endpoint(url, method="GET", data=None):
    """Test an API endpoint and return the response"""
    try:
        cmd = ['curl', '-s', '-X', method, url, '--max-time', '10']
        
        if data:
            cmd.extend(['-H', 'Content-Type: application/json', '-d', json.dumps(data)])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"raw_response": result.stdout}
        else:
            return {"error": f"Request failed: {result.stderr}"}
    except Exception as e:
        return {"error": str(e)}

def test_bible_search(quote):
    """Test searching for a Bible quote"""
    print(f"🔍 Testing quote: '{quote}'")
    
    response = test_api_endpoint(
        "https://verse-checker.onrender.com/check",
        method="POST",
        data={"quote": quote}
    )
    
    if "error" in response:
        print(f"❌ Error: {response['error']}")
        return False
    
    if "match" in response:
        print(f"✅ Match: {response['match']}")
        print(f"📊 Score: {response['score']}")
        print(f"📖 Reference: {response['reference']}")
        print(f"📜 Text: {response['text'][:100]}{'...' if len(response['text']) > 100 else ''}")
        print(f"💬 Message: {response.get('message', 'No message')}")
        return True
    else:
        print(f"📄 Unexpected response: {response}")
        return False

def main():
    """Main function to test the API"""
    
    print("🔍 Bible Verse API Status Test")
    print("=" * 50)
    
    # Test basic status
    print("1️⃣ Testing API Status...")
    status = test_api_endpoint("https://verse-checker.onrender.com/")
    
    if "error" in status:
        print(f"❌ API Error: {status['error']}")
        return
    
    print(f"✅ API Response: {json.dumps(status, indent=2)}")
    
    # Extract progress info if available
    if "status" in status and "%" in str(status["status"]):
        print(f"\n📊 Upload Status: {status['status']}")
    
    print("\n" + "=" * 50)
    
    # Test with Genesis verses (should be available)
    print("2️⃣ Testing Genesis verses...")
    
    genesis_quotes = [
        "In the beginning God created the heavens and the earth",
        "Let there be light",
        "It is not good for man to be alone",
        "Am I my brother's keeper"
    ]
    
    working_quotes = 0
    
    for quote in genesis_quotes:
        print(f"\n📖 Testing: '{quote[:30]}...'")
        if test_bible_search(quote):
            working_quotes += 1
        print("-" * 30)
    
    print(f"\n📊 Results: {working_quotes}/{len(genesis_quotes)} Genesis quotes found")
    
    if working_quotes > 0:
        print("✅ Genesis verses are available in your database!")
    else:
        print("⚠️ Genesis verses not found - upload may still be in progress")
    
    print("\n" + "=" * 50)
    
    # Test what should NOT be available yet
    print("3️⃣ Testing verses that should NOT be available yet...")
    
    future_quotes = [
        "love your neighbor as yourself",  # Matthew - New Testament
        "faith hope and love",  # 1 Corinthians - New Testament  
        "valley of dry bones",  # Ezekiel - Later Old Testament
    ]
    
    unavailable_count = 0
    
    for quote in future_quotes:
        print(f"\n🔮 Testing: '{quote}'")
        response = test_api_endpoint(
            "https://verse-checker.onrender.com/check",
            method="POST", 
            data={"quote": quote}
        )
        
        if "match" in response and not response["match"]:
            print(f"✅ Correctly not found (upload hasn't reached this verse yet)")
            unavailable_count += 1
        elif "match" in response and response["match"]:
            print(f"🎉 Unexpectedly found! Upload has progressed further than expected")
            print(f"   📖 Found in: {response['reference']}")
        else:
            print(f"❓ Unclear response: {response}")
    
    print(f"\n📊 Expected unavailable: {unavailable_count}/{len(future_quotes)}")
    
    print("\n" + "=" * 50)
    print("🎯 Summary:")
    print(f"   • API is {'✅ online' if 'message' in status else '❌ offline'}")
    print(f"   • Genesis verses: {'✅ available' if working_quotes > 0 else '❌ not yet'}")
    print(f"   • Upload progress: {status.get('status', 'Unknown')}")
    
    if working_quotes > 0:
        print("\n🎉 Your API is working! You can search for:")
        print("   • Genesis creation stories")  
        print("   • Adam and Eve")
        print("   • Noah's flood") 
        print("   • Abraham stories")
        print("   • And other early Genesis content")

if __name__ == "__main__":
    main()