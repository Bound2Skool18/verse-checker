#!/usr/bin/env python3
"""
Auto-checker that monitors progress and notifies when complete
Run with: python3 auto_check.py
"""

import time
import os
import subprocess
from datetime import datetime

def check_and_notify():
    """Check progress and notify when complete"""
    
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Checking progress...")
    
    try:
        # Run the progress checker
        result = subprocess.run(['python3', 'check_progress.py'], 
                              capture_output=True, text=True, timeout=60)
        
        output = result.stdout
        print(output)
        
        # Check if complete
        if "UPLOAD COMPLETE" in output:
            print("\n🎉🎉🎉 BIBLE UPLOAD COMPLETE! 🎉🎉🎉")
            print("🚀 Your API can now search ALL Bible verses!")
            print("📱 Test it with New Testament queries!")
            
            # Try to send system notification (macOS)
            try:
                subprocess.run(['osascript', '-e', 
                              'display notification "Bible verse upload complete! 🎉" with title "Verse Checker API"'],
                              timeout=5)
            except:
                pass  # Notification failed, but that's ok
            
            return True  # Upload is complete
            
        return False  # Still in progress
        
    except Exception as e:
        print(f"❌ Error checking progress: {e}")
        return False

def main():
    """Main monitoring loop"""
    print("🚀 Starting automatic progress monitoring...")
    print("⏹️  Press Ctrl+C to stop")
    print("="*50)
    
    check_interval = 30 * 60  # Check every 30 minutes
    
    try:
        while True:
            complete = check_and_notify()
            
            if complete:
                print("\n✅ Monitoring complete - upload finished!")
                break
                
            print(f"\n⏰ Next check in {check_interval//60} minutes...")
            print("="*50)
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print("\n⏹️  Monitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Monitoring error: {e}")

if __name__ == "__main__":
    main()