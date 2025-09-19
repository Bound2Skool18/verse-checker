#!/usr/bin/env python3
"""
Simple local Bible upload script
Completes the upload of all 31,102 verses to Pinecone
"""

import os
import json
import time
from pathlib import Path

# Terminal colors
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def print_status(msg, color=Colors.RESET, bold=False):
    """Print colored status message"""
    prefix = Colors.BOLD + color if bold else color
    print(f"{prefix}{msg}{Colors.RESET}")

def load_env_vars():
    """Load environment variables from .env file"""
    env_file = Path(".env")
    if env_file.exists():
        print_status("📄 Loading .env file...", Colors.BLUE)
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"\'')

def get_progress():
    """Get current upload progress from Pinecone"""
    try:
        # Use pip installed pinecone package
        import subprocess
        import sys
        
        # Try to get the correct import
        result = subprocess.run([sys.executable, "-c", 
                               "from pinecone.grpc import PineconeGRPC as Pinecone; "
                               "import os; "
                               "pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY')); "
                               "idx = pc.Index('bible-verses'); "
                               "stats = idx.describe_index_stats(); "
                               "print(f'{stats.total_vector_count},{stats.dimension}')"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            count_str, dim_str = result.stdout.strip().split(',')
            current_count = int(count_str)
            print_status(f"📊 Current verses in Pinecone: {current_count:,}/31,102", Colors.CYAN, bold=True)
            return current_count
        else:
            print_status(f"❌ Error checking progress: {result.stderr}", Colors.RED)
            return None
            
    except Exception as e:
        print_status(f"❌ Error getting progress: {e}", Colors.RED)
        return None

def upload_via_render():
    """Try to trigger upload via your existing Render service"""
    try:
        import subprocess
        
        print_status("🚀 Attempting to trigger upload via Render API...", Colors.BLUE)
        
        # Try to hit the main endpoint which should trigger background upload
        result = subprocess.run([
            'curl', '-X', 'POST', 
            'https://verse-checker.onrender.com/check',
            '-H', 'Content-Type: application/json',
            '-d', '{"quote": "trigger upload"}',
            '--max-time', '10'
        ], capture_output=True, text=True)
        
        if "loading" in result.stdout.lower() or "initializing" in result.stdout.lower():
            print_status("✅ Successfully triggered background upload on Render!", Colors.GREEN, bold=True)
            return True
        else:
            print_status(f"⚠️ Render response: {result.stdout[:100]}...", Colors.YELLOW)
            return False
            
    except Exception as e:
        print_status(f"❌ Error triggering Render upload: {e}", Colors.RED)
        return False

def monitor_upload_progress():
    """Monitor upload progress until complete"""
    print_status("\n🔍 Starting upload monitoring...", Colors.CYAN, bold=True)
    print_status("Press Ctrl+C to stop monitoring\n", Colors.BLUE)
    
    start_time = time.time()
    last_count = 0
    
    try:
        while True:
            current_count = get_progress()
            
            if current_count is None:
                print_status("❌ Could not check progress, retrying in 60 seconds...", Colors.RED)
                time.sleep(60)
                continue
            
            if current_count >= 31102:
                print_status("🎉 ✅ UPLOAD COMPLETE! All 31,102 verses uploaded!", Colors.GREEN, bold=True)
                print_status("🚀 Your Bible API is now fully functional!", Colors.GREEN, bold=True)
                break
            
            # Calculate progress metrics
            progress = (current_count / 31102) * 100
            
            if current_count > last_count:
                new_verses = current_count - last_count
                elapsed = time.time() - start_time
                rate = new_verses / (elapsed / 60) if elapsed > 0 else 0
                
                if rate > 0:
                    remaining = 31102 - current_count
                    eta_minutes = remaining / rate
                    eta_text = f"ETA: {eta_minutes:.0f} minutes" if eta_minutes < 60 else f"ETA: {eta_minutes/60:.1f} hours"
                else:
                    eta_text = "ETA: calculating..."
                
                print_status(f"📈 Progress: {progress:.1f}% ({current_count:,}/31,102) - {eta_text}", Colors.CYAN)
                print_status(f"🔄 Upload rate: {rate:.0f} verses/minute", Colors.BLUE)
            else:
                print_status(f"⏸️ Progress: {progress:.1f}% ({current_count:,}/31,102) - Upload may be paused", Colors.YELLOW)
            
            # Show estimated book progress
            if current_count < 5000:
                book_status = "Early Old Testament (Genesis → Numbers)"
            elif current_count < 15000:
                book_status = "Major Old Testament books"
            elif current_count < 23000:
                book_status = "Old Testament complete, New Testament starting"
            elif current_count < 30000:
                book_status = "Most of Bible complete"
            else:
                book_status = "Nearly complete!"
                
            print_status(f"📚 Likely available: {book_status}", Colors.CYAN)
            print_status("-" * 60, Colors.RESET)
            
            last_count = current_count
            start_time = time.time()  # Reset timer for rate calculation
            
            # Wait 2 minutes before next check
            time.sleep(120)
            
    except KeyboardInterrupt:
        print_status("\n⚠️ Monitoring stopped by user", Colors.YELLOW, bold=True)
        print_status("💡 Run this script again to continue monitoring", Colors.BLUE)

def main():
    """Main function"""
    print_status("\n🚀 Bible Upload Manager", Colors.CYAN, bold=True)
    print_status("=" * 50, Colors.RESET)
    
    # Load environment
    load_env_vars()
    
    # Check API key
    if not os.getenv("PINECONE_API_KEY"):
        print_status("❌ PINECONE_API_KEY not found in environment", Colors.RED, bold=True)
        print_status("Please set it in your .env file or environment", Colors.YELLOW)
        return
    
    # Check current progress
    print_status("🔍 Checking current upload progress...", Colors.BLUE)
    current_count = get_progress()
    
    if current_count is None:
        print_status("❌ Could not connect to Pinecone. Check your API key and connection.", Colors.RED)
        return
    
    if current_count >= 31102:
        print_status("🎉 Upload already complete! All Bible verses are available.", Colors.GREEN, bold=True)
        return
    
    print_status(f"📊 Found {current_count:,} verses in Pinecone", Colors.CYAN)
    print_status(f"📈 {31102 - current_count:,} verses remaining to upload", Colors.YELLOW)
    
    # Try to trigger upload via Render
    print_status("\n🎯 Attempting to resume upload...", Colors.BLUE, bold=True)
    
    success = upload_via_render()
    
    if success:
        print_status("✅ Upload triggered successfully!", Colors.GREEN)
        print_status("📊 Starting progress monitoring...", Colors.BLUE)
        monitor_upload_progress()
    else:
        print_status("⚠️ Could not trigger upload via Render", Colors.YELLOW)
        print_status("💡 Your Render service may still be deploying", Colors.BLUE)
        print_status("🔄 Starting monitoring anyway - upload may resume automatically", Colors.CYAN)
        monitor_upload_progress()

if __name__ == "__main__":
    main()