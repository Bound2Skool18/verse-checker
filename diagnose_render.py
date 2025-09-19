#!/usr/bin/env python3
"""
Diagnostic script to check Render service status and troubleshoot issues
"""

import subprocess
import time
import json
from datetime import datetime

def test_endpoint(url, name="endpoint"):
    """Test an endpoint and return status"""
    try:
        result = subprocess.run([
            'curl', '-s', '-w', '%{http_code}', url,
            '--max-time', '10',
            '--connect-timeout', '5'
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            # Extract HTTP code (last 3 characters)
            http_code = result.stdout[-3:]
            response_body = result.stdout[:-3]
            
            status = "🟢 Online" if http_code.startswith('2') else f"🔴 HTTP {http_code}"
            
            return {
                "status": status,
                "http_code": http_code,
                "response": response_body[:200] + "..." if len(response_body) > 200 else response_body,
                "success": http_code.startswith('2')
            }
        else:
            return {
                "status": "🔴 Connection Failed",
                "http_code": "000",
                "response": result.stderr,
                "success": False
            }
    except Exception as e:
        return {
            "status": "🔴 Error",
            "http_code": "000", 
            "response": str(e),
            "success": False
        }

def diagnose_service():
    """Run comprehensive diagnostics on the Render service"""
    
    print("🔍 Bible Verse Checker - Render Service Diagnostics")
    print("=" * 60)
    print(f"⏰ Check time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    base_url = "https://verse-checker.onrender.com"
    
    # Test various endpoints
    endpoints = [
        ("/", "Root endpoint"),
        ("/health", "Health check"),
        ("/status", "Status endpoint"),
        ("/docs", "API documentation"),
        ("/ping", "Ping endpoint")
    ]
    
    print("🌐 Testing Endpoints:")
    print("-" * 30)
    
    working_endpoints = 0
    
    for path, description in endpoints:
        url = base_url + path
        result = test_endpoint(url, description)
        
        print(f"{result['status']} {description}")
        print(f"   📍 {url}")
        print(f"   📊 HTTP {result['http_code']}")
        
        if result['success']:
            working_endpoints += 1
            if result['response']:
                # Try to parse as JSON for prettier output
                try:
                    parsed = json.loads(result['response'])
                    if isinstance(parsed, dict):
                        key_info = []
                        for key in ['message', 'status', 'service_mode', 'version']:
                            if key in parsed:
                                key_info.append(f"{key}: {parsed[key]}")
                        if key_info:
                            print(f"   📋 {', '.join(key_info)}")
                except:
                    print(f"   📝 {result['response'][:100]}")
        else:
            if result['response'] and 'Not Found' not in result['response']:
                print(f"   ❌ {result['response'][:100]}")
        
        print()
    
    print("=" * 60)
    print(f"📊 Summary: {working_endpoints}/{len(endpoints)} endpoints working")
    
    if working_endpoints == 0:
        print("\n🚨 SERVICE APPEARS TO BE DOWN")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check your Render dashboard for deployment status")
        print("2. Look at Render build and runtime logs")
        print("3. Verify the service name matches your URL")
        print("4. Check if the service is still deploying")
        
        # Try to identify the issue type
        root_test = test_endpoint(base_url)
        if "Connection" in root_test['status']:
            print("\n💡 Likely issue: Service is not responding (down or deploying)")
        elif "404" in root_test['http_code']:
            print("\n💡 Likely issue: Service running but routes not found (app error)")
        elif "500" in root_test['http_code']:
            print("\n💡 Likely issue: Server error (check logs)")
        else:
            print(f"\n💡 Unexpected status: {root_test['status']}")
    
    elif working_endpoints < len(endpoints):
        print("\n⚠️  SERVICE PARTIALLY WORKING")
        print("Some endpoints are responding, but not all")
    
    else:
        print("\n🎉 SERVICE FULLY OPERATIONAL")
        print("All endpoints are responding correctly!")
    
    # Test a Bible verse search if service is working
    if working_endpoints > 0:
        print("\n🧪 Testing Bible Verse Search:")
        print("-" * 30)
        
        test_quote = "In the beginning God created"
        search_result = test_bible_search(base_url, test_quote)
        
        if search_result['success']:
            print("✅ Bible search is working!")
            print(f"   📖 Test quote: \"{test_quote}\"")
            print(f"   📊 Response received: {len(search_result['response'])} characters")
        else:
            print("❌ Bible search failed")
            print(f"   📝 Error: {search_result['response'][:200]}")
    
    print("\n" + "=" * 60)

def test_bible_search(base_url, quote):
    """Test the Bible verse search functionality"""
    try:
        # Create JSON payload
        payload = json.dumps({"quote": quote})
        
        result = subprocess.run([
            'curl', '-s', '-X', 'POST',
            f'{base_url}/check',
            '-H', 'Content-Type: application/json',
            '-d', payload,
            '--max-time', '30'
        ], capture_output=True, text=True, timeout=35)
        
        if result.returncode == 0 and result.stdout:
            return {
                "success": True,
                "response": result.stdout
            }
        else:
            return {
                "success": False,
                "response": result.stderr or "No response"
            }
    except Exception as e:
        return {
            "success": False,
            "response": str(e)
        }

if __name__ == "__main__":
    diagnose_service()