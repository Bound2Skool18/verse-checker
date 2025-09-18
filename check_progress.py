#!/usr/bin/env python3
"""
Direct Pinecone Progress Checker
Check how many Bible verses are uploaded without running the full web service
"""

import os
import sys
from pathlib import Path

def check_pinecone_progress():
    """Check current progress of Bible verse upload to Pinecone"""
    
    # Check if API key is available
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("❌ No PINECONE_API_KEY found in environment")
        print("   Set it with: export PINECONE_API_KEY='your_key_here'")
        return False
    
    try:
        from pinecone import Pinecone
        
        # Initialize Pinecone
        print("🔌 Connecting to Pinecone...")
        pc = Pinecone(api_key=api_key)
        
        # Get index
        index_name = "bible-verses"
        if index_name not in pc.list_indexes().names():
            print(f"❌ Index '{index_name}' not found")
            return False
            
        index = pc.Index(index_name)
        
        # Get index statistics
        print("📊 Fetching index statistics...")
        stats = index.describe_index_stats()
        
        # Extract data
        current_vectors = stats.total_vector_count
        target_verses = 31102  # Total Bible verses
        
        # Calculate progress
        progress_percent = (current_vectors / target_verses) * 100
        
        # Display results
        print("\n" + "="*60)
        print("📖 BIBLE VERSE UPLOAD PROGRESS")
        print("="*60)
        print(f"📊 Current verses in database: {current_vectors:,}")
        print(f"🎯 Target verses (complete Bible): {target_verses:,}")
        print(f"📈 Progress: {progress_percent:.1f}% complete")
        print(f"📉 Remaining: {target_verses - current_vectors:,} verses")
        
        if current_vectors >= target_verses:
            print("🎉 ✅ UPLOAD COMPLETE! All Bible verses are loaded!")
            print("   Your API can now find verses from Genesis to Revelation")
        elif current_vectors >= target_verses * 0.95:  # 95% complete
            print("🚀 ⏰ NEARLY COMPLETE! Upload is almost finished")
            print("   Your API should be working well for most searches")
        elif current_vectors >= 15000:  # About halfway
            print("⏳ 🔄 GOOD PROGRESS! About halfway through the Bible")
            print("   Many Old Testament and some New Testament books available")
        elif current_vectors >= 5000:  # Some progress
            print("🌱 📚 MAKING PROGRESS! Several Bible books loaded")
            print("   Early Old Testament books should be searchable")
        else:
            print("🚀 🔄 UPLOAD IN PROGRESS! Still early in the process")
            print("   Upload is running - check again in 30 minutes")
        
        # Estimate time to completion
        if current_vectors > 0 and current_vectors < target_verses:
            # Rough estimate based on ~2 seconds per batch of 50 verses
            remaining_verses = target_verses - current_vectors
            remaining_batches = remaining_verses / 50
            estimated_minutes = (remaining_batches * 2) / 60  # 2 seconds per batch
            
            if estimated_minutes < 60:
                print(f"⏱️  Estimated time to completion: ~{estimated_minutes:.0f} minutes")
            else:
                hours = estimated_minutes / 60
                print(f"⏱️  Estimated time to completion: ~{hours:.1f} hours")
        
        print("="*60)
        
        # Show which books are likely available
        if current_vectors > 0:
            estimated_book_progress = get_estimated_book_progress(current_vectors)
            print(f"📚 Likely available books: {estimated_book_progress}")
        
        print("\n💡 TIP: Run this script again anytime to check progress!")
        return current_vectors >= target_verses
        
    except ImportError:
        print("❌ Pinecone library not installed. Run: pip install pinecone-client")
        return False
    except Exception as e:
        print(f"❌ Error checking Pinecone: {str(e)}")
        return False

def get_estimated_book_progress(verse_count):
    """Estimate which Bible books are likely loaded based on verse count"""
    
    # Approximate verse counts for major Bible sections
    if verse_count >= 31000:
        return "Complete Bible (Genesis → Revelation)"
    elif verse_count >= 23000:
        return "Old Testament complete, most New Testament"
    elif verse_count >= 20000:
        return "Old Testament complete, some New Testament (Matthew, Mark, Luke...)"
    elif verse_count >= 15000:
        return "Most Old Testament (Genesis → Malachi)"
    elif verse_count >= 10000:
        return "Major Old Testament books (Genesis → Kings, Psalms, Proverbs...)"
    elif verse_count >= 5000:
        return "Early Old Testament (Genesis → Judges, some Psalms)"
    elif verse_count >= 1000:
        return "Genesis, Exodus, Leviticus, Numbers..."
    elif verse_count >= 500:
        return "Genesis, Exodus, some Leviticus"
    else:
        return "Early Genesis chapters"

if __name__ == "__main__":
    print("🔍 Bible Verse Upload Progress Checker")
    print("="*40)
    
    # Check if we can load environment from .env file
    env_file = Path(".env")
    if env_file.exists():
        print("📄 Loading environment from .env file...")
        # Simple .env loading
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"\'')
    
    success = check_pinecone_progress()
    
    if success:
        print("\n🎉 Your Bible verse database is complete!")
        print("🚀 Your API is ready to search all Bible verses!")
    else:
        print("\n⏳ Upload still in progress. Check again later!")
        
    print("\n" + "="*60)
    print("📱 When complete, test with queries like:")
    print("   • 'love your neighbor' (New Testament)")
    print("   • 'valley of dry bones' (Old Testament)")
    print("   • 'faith hope love' (Paul's letters)")
    print("="*60)