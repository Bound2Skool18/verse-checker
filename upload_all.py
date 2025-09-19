#!/usr/bin/env python3
"""
Complete Bible Uploader to Pinecone
Uploads all 31,102 verses to Pinecone from scratch or resumes from last position
"""

import os
import json
import time
import sys
import asyncio
from pathlib import Path

# Use color terminal output
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RED = "\033[91m"
CYAN = "\033[96m"

def print_colored(text, color=RESET, bold=False):
    """Print colored text to terminal"""
    prefix = BOLD + color if bold else color
    print(f"{prefix}{text}{RESET}")

def load_env():
    """Load environment variables from .env file if available"""
    env_file = Path(".env")
    if env_file.exists():
        print_colored("📄 Loading environment from .env file...", BLUE)
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"\'')
        print_colored("✅ Environment loaded", GREEN)

def verify_pinecone_api_key():
    """Check if Pinecone API key is set"""
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print_colored("❌ PINECONE_API_KEY not found in environment", RED, bold=True)
        print_colored("Please set it with: export PINECONE_API_KEY='your_key_here'", YELLOW)
        return False
    return True

def load_verse_data():
    """Load Bible verses from JSON file"""
    bible_file = Path("data/bible_complete.json")
    if not bible_file.exists():
        print_colored(f"❌ Bible data not found at {bible_file}", RED, bold=True)
        return None
    
    print_colored("📖 Loading Bible data...", BLUE)
    with open(bible_file, 'r', encoding='utf-8') as f:
        verses = json.load(f)
    
    print_colored(f"✅ Loaded {len(verses):,} verses from {bible_file}", GREEN)
    return verses

async def upload_bible_to_pinecone():
    """Upload all Bible verses to Pinecone"""
    # Verify necessary imports
    try:
        from pinecone import Pinecone
        print_colored("✅ Pinecone SDK imported successfully", GREEN)
    except ImportError as e:
        print_colored(f"❌ Failed to import Pinecone: {e}", RED, bold=True)
        print_colored("Make sure you have the correct Pinecone SDK installed:", YELLOW)
        print_colored("pip install pinecone", CYAN)
        return False
    
    try:
        from sentence_transformers import SentenceTransformer
        print_colored("✅ SentenceTransformer imported successfully", GREEN)
    except ImportError as e:
        print_colored(f"❌ Failed to import SentenceTransformer: {e}", RED, bold=True)
        print_colored("Install with: pip install sentence-transformers", YELLOW)
        return False
    
    # Load environment variables
    load_env()
    
    # Check for API key
    if not verify_pinecone_api_key():
        return False
    
    # Load verse data
    verses_data = load_verse_data()
    if not verses_data:
        return False
    
    # Initialize Pinecone
    print_colored("🔌 Connecting to Pinecone...", BLUE)
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    
    # Check if index exists
    index_name = "bible-verses"
    index_exists = False
    
    try:
        indices = pc.list_indexes()
        index_names = [idx.name for idx in indices]
        
        if index_name in index_names:
            print_colored(f"✅ Found existing index: {index_name}", GREEN)
            index_exists = True
        else:
            print_colored(f"⚠️ Index {index_name} not found, creating...", YELLOW)
            from pinecone import ServerlessSpec
            
            pc.create_index(
                name=index_name,
                dimension=384,  # for all-MiniLM-L6-v2
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1-aws"
                )
            )
            print_colored(f"✅ Created new index: {index_name}", GREEN)
            index_exists = True
            
    except Exception as e:
        print_colored(f"❌ Error checking/creating index: {e}", RED, bold=True)
        return False
    
    if not index_exists:
        print_colored("❌ Failed to find or create index", RED, bold=True)
        return False
    
    # Connect to index
    index = pc.Index(index_name)
    
    # Check current progress
    try:
        stats = index.describe_index_stats()
        current_count = stats.total_vector_count
        target_count = len(verses_data)
        
        print_colored(f"📊 Current progress: {current_count:,}/{target_count:,} verses ({current_count/target_count*100:.1f}%)", CYAN, bold=True)
        
        if current_count >= target_count:
            print_colored("🎉 Upload already complete! All Bible verses are in Pinecone.", GREEN, bold=True)
            return True
            
    except Exception as e:
        print_colored(f"❌ Error checking index stats: {e}", RED)
        current_count = 0
    
    # Load embedding model
    print_colored("🧠 Loading embedding model...", BLUE)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print_colored("✅ Model loaded successfully", GREEN)
    
    # Calculate resume point (with safety buffer)
    buffer = max(0, min(100, current_count // 10))  # 10% buffer, max 100 verses
    resume_from = max(0, current_count - buffer)
    
    print_colored(f"🔄 Resuming upload from verse #{resume_from:,} (with {buffer} verse buffer)", CYAN)
    
    # Upload verses in batches
    batch_size = 50
    start_time = time.time()
    successful = 0
    failed = 0
    
    print_colored(f"🚀 Starting upload of ~{len(verses_data) - resume_from:,} verses in batches of {batch_size}", BLUE, bold=True)
    
    try:
        for i in range(resume_from, len(verses_data), batch_size):
            batch = verses_data[i:i + batch_size]
            if not batch:
                continue
                
            batch_num = (i // batch_size) + 1
            batch_start = time.time()
            
            # Get current book for tracking
            current_book = batch[0].get('book', 'Unknown')
            
            print_colored(f"⏳ Processing batch {batch_num}: {len(batch)} verses... ({current_book})", BLUE)
            
            # Create embeddings and prepare vectors
            vectors = []
            for verse in batch:
                try:
                    # Create embedding
                    embedding = model.encode(verse["text"]).tolist()
                    
                    # Create vector record
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
                    print_colored(f"⚠️ Error processing verse: {e}", YELLOW)
                    failed += 1
                    continue
            
            # Upload batch with retries
            success = False
            for attempt in range(3):
                try:
                    index.upsert(vectors=vectors)
                    success = True
                    break
                except Exception as e:
                    print_colored(f"⚠️ Upload attempt {attempt+1}/3 failed: {e}", YELLOW)
                    if attempt < 2:
                        print_colored(f"Retrying in {2**attempt} seconds...", YELLOW)
                        await asyncio.sleep(2**attempt)
            
            if success:
                successful += len(vectors)
                batch_time = time.time() - batch_start
                progress = (i + len(batch)) / len(verses_data) * 100
                
                # Calculate ETA
                elapsed = time.time() - start_time
                items_per_second = successful / elapsed if elapsed > 0 else 0
                remaining_items = len(verses_data) - (i + len(batch))
                eta_seconds = remaining_items / items_per_second if items_per_second > 0 else 0
                
                print_colored(f"✅ Batch {batch_num}: {len(vectors)} verses uploaded in {batch_time:.1f}s", GREEN)
                print_colored(f"📈 Progress: {progress:.1f}% ({i + len(batch):,}/{len(verses_data):,})", CYAN)
                print_colored(f"📚 Current book: {current_book}", CYAN)
                
                if eta_seconds > 0:
                    eta_minutes = eta_seconds / 60
                    if eta_minutes < 60:
                        print_colored(f"⏱️ ETA: ~{eta_minutes:.0f} minutes", CYAN)
                    else:
                        eta_hours = eta_minutes / 60
                        print_colored(f"⏱️ ETA: ~{eta_hours:.1f} hours", CYAN)
            else:
                print_colored(f"❌ Failed to upload batch {batch_num} after 3 attempts", RED)
                failed += len(vectors)
            
            # Brief pause to avoid rate limits
            await asyncio.sleep(0.5)
    
    except KeyboardInterrupt:
        print_colored("\n⚠️ Upload interrupted by user", YELLOW, bold=True)
        interrupted = True
    except Exception as e:
        print_colored(f"\n❌ Upload error: {e}", RED, bold=True)
        import traceback
        traceback.print_exc()
        interrupted = True
    
    # Final stats
    total_time = time.time() - start_time
    print_colored("\n" + "="*60, RESET, bold=True)
    print_colored("📊 UPLOAD SUMMARY", CYAN, bold=True)
    print_colored("="*60, RESET, bold=True)
    
    try:
        stats = index.describe_index_stats()
        final_count = stats.total_vector_count
        print_colored(f"📈 Verses in Pinecone: {final_count:,}/{len(verses_data):,} ({final_count/len(verses_data)*100:.1f}%)", CYAN)
    except Exception as e:
        print_colored(f"❌ Error checking final count: {e}", RED)
        final_count = 0
    
    print_colored(f"✅ Successfully uploaded: {successful:,} verses", GREEN)
    if failed > 0:
        print_colored(f"❌ Failed uploads: {failed:,} verses", RED)
    
    print_colored(f"⏱️ Total time: {total_time/60:.1f} minutes", BLUE)
    print_colored(f"📊 Upload rate: {successful/(total_time/60):.0f} verses/minute", BLUE)
    
    if final_count >= len(verses_data) * 0.95:  # 95% success
        print_colored("\n🎉 UPLOAD COMPLETE! Your Bible verse database is ready.", GREEN, bold=True)
        print_colored("🚀 You can now search for verses from Genesis to Revelation!", GREEN, bold=True)
        return True
    else:
        print_colored("\n⚠️ Upload incomplete. Run this script again to continue.", YELLOW, bold=True)
        return False

if __name__ == "__main__":
    print_colored("\n🚀 Complete Bible Verse Uploader", CYAN, bold=True)
    print_colored("="*60, RESET)
    
    success = asyncio.run(upload_bible_to_pinecone())
    
    if success:
        print_colored("\n🎉 SUCCESS! Your Bible verse database is complete and ready to use.", GREEN, bold=True)
    else:
        print_colored("\n⚠️ Upload incomplete. Run this script again to continue.", YELLOW, bold=True)
    
    print_colored("\n💡 To check progress anytime, run:", BLUE)
    print_colored("python3 check_progress.py", CYAN)
    print_colored("="*60, RESET)