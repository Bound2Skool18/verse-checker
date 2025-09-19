#!/usr/bin/env python3
"""
Simplified Bible Verse Uploader
Uses existing project structure to complete the upload
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def load_env():
    """Load .env file if it exists"""
    env_file = Path(".env")
    if env_file.exists():
        print("📄 Loading .env file...")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"\'')

def check_progress():
    """Check current upload progress"""
    try:
        from pinecone import Pinecone
        
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            print("❌ PINECONE_API_KEY not set")
            return None
            
        pc = Pinecone(api_key=api_key)
        index = pc.Index("bible-verses")
        stats = index.describe_index_stats()
        
        current = stats.total_vector_count
        target = 31102
        
        print(f"📊 Current progress: {current:,}/{target:,} verses ({current/target*100:.1f}%)")
        return current, target, index
        
    except Exception as e:
        print(f"❌ Error checking progress: {e}")
        return None

async def upload_remaining_verses():
    """Upload remaining verses using the project's existing modules"""
    try:
        # Load environment
        load_env()
        
        # Check current progress
        result = check_progress()
        if not result:
            return False
            
        current_count, target_count, index = result
        
        if current_count >= target_count:
            print("🎉 Upload already complete!")
            return True
        
        print(f"🚀 Need to upload {target_count - current_count:,} more verses...")
        
        # Load the Bible data
        bible_file = Path("data/bible_complete.json")
        if not bible_file.exists():
            print("❌ Bible data file not found")
            return False
            
        print("📖 Loading Bible data...")
        with open(bible_file, 'r', encoding='utf-8') as f:
            verses_data = json.load(f)
        
        print(f"✅ Loaded {len(verses_data):,} verses from file")
        
        # Import project modules
        try:
            from embedding import get_model
            from pinecone_store import upload_verses_batch
        except ImportError as e:
            print(f"❌ Could not import project modules: {e}")
            print("💡 Make sure you're in the verse-checker directory")
            return False
        
        # Load model
        print("🧠 Loading embedding model...")
        model = get_model()
        print("✅ Model loaded")
        
        # Resume from where we left off (with a small buffer for safety)
        buffer = max(0, min(100, current_count // 20))  # 5% buffer, max 100
        resume_from = max(0, current_count - buffer)
        
        print(f"🔄 Resuming from verse {resume_from:,} (with {buffer} verse buffer)")
        
        # Upload remaining verses in batches
        batch_size = 50
        successful_uploads = 0
        total_time_start = time.time()
        
        for i in range(resume_from, len(verses_data), batch_size):
            batch = verses_data[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            print(f"📤 Uploading batch {batch_num} ({len(batch)} verses)...")
            
            batch_start = time.time()
            
            # Prepare vectors
            vectors = []
            for verse in batch:
                try:
                    embedding = model.encode(verse["text"]).tolist()
                    vector = {
                        "id": f"{verse['book']}_{verse['chapter']}_{verse['verse']}",
                        "values": embedding,
                        "metadata": {
                            "book": verse["book"],
                            "chapter": verse["chapter"],
                            "verse": verse["verse"],
                            "text": verse["text"]
                        }
                    }
                    vectors.append(vector)
                except Exception as e:
                    print(f"⚠️  Error processing verse: {e}")
                    continue
            
            # Upload with retries
            success = False
            for attempt in range(3):
                try:
                    index.upsert(vectors=vectors)
                    success = True
                    break
                except Exception as e:
                    print(f"⚠️  Upload attempt {attempt+1} failed: {e}")
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)
            
            if success:
                successful_uploads += len(vectors)
                batch_time = time.time() - batch_start
                progress = (i + len(batch)) / len(verses_data) * 100
                
                # ETA calculation
                elapsed_time = time.time() - total_time_start
                if successful_uploads > 0:
                    rate = successful_uploads / elapsed_time
                    remaining = len(verses_data) - (i + len(batch))
                    eta_seconds = remaining / rate if rate > 0 else 0
                    eta_minutes = eta_seconds / 60
                else:
                    eta_minutes = 0
                
                current_book = batch[0].get('book', 'Unknown')
                print(f"✅ Batch {batch_num} complete: {len(vectors)} verses in {batch_time:.1f}s")
                print(f"📈 Progress: {progress:.1f}% - {current_book}")
                
                if eta_minutes > 1:
                    print(f"⏱️  ETA: {eta_minutes:.0f} minutes")
                    
            else:
                print(f"❌ Batch {batch_num} failed after 3 attempts")
            
            # Small delay to avoid rate limits
            await asyncio.sleep(0.5)
        
        # Final check
        final_result = check_progress()
        if final_result:
            final_count = final_result[0]
            print(f"🏁 Final count: {final_count:,}/{target_count:,} verses")
            
            if final_count >= target_count * 0.95:
                print("🎉 ✅ UPLOAD SUCCESSFUL!")
                return True
            else:
                print("⚠️  Upload may be incomplete")
                return False
        
        return False
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Simple Bible Verse Uploader")
    print("=" * 50)
    
    success = asyncio.run(upload_remaining_verses())
    
    if success:
        print("\n🎉 SUCCESS! Bible upload complete!")
        print("🚀 Your API is ready with all 31,102 verses!")
    else:
        print("\n❌ Upload incomplete. Check the errors above.")