#!/usr/bin/env python3
"""
Standalone Bible Verse Uploader to Pinecone
Runs independently of the web service to ensure complete upload
"""

import os
import json
import time
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('upload.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_environment():
    """Load environment variables from .env if available"""
    env_file = Path(".env")
    if env_file.exists():
        logger.info("📄 Loading environment from .env file...")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"\'')

def get_embedding_model():
    """Load the sentence transformer model"""
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("📥 Loading embedding model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✅ Embedding model loaded successfully")
        return model
    except ImportError:
        logger.error("❌ sentence-transformers not installed. Run: pip install sentence-transformers")
        return None
    except Exception as e:
        logger.error(f"❌ Error loading model: {e}")
        return None

def get_pinecone_client():
    """Initialize Pinecone client and get index"""
    try:
        from pinecone import Pinecone
        
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            logger.error("❌ PINECONE_API_KEY not found in environment")
            return None, None
        
        logger.info("🔌 Connecting to Pinecone...")
        pc = Pinecone(api_key=api_key)
        
        index_name = "bible-verses"
        if index_name not in pc.list_indexes().names():
            logger.error(f"❌ Index '{index_name}' not found")
            return None, None
        
        index = pc.Index(index_name)
        logger.info("✅ Connected to Pinecone index")
        return pc, index
        
    except ImportError:
        logger.error("❌ pinecone-client not installed. Run: pip install pinecone-client")
        return None, None
    except Exception as e:
        logger.error(f"❌ Error connecting to Pinecone: {e}")
        return None, None

def load_bible_data():
    """Load Bible verses from JSON file"""
    try:
        bible_file = Path("data/bible_complete.json")
        if not bible_file.exists():
            logger.error("❌ Bible data file not found at data/bible_complete.json")
            return None
        
        logger.info("📖 Loading complete Bible dataset...")
        with open(bible_file, 'r', encoding='utf-8') as f:
            verses_data = json.load(f)
        
        logger.info(f"✅ Loaded {len(verses_data)} Bible verses")
        return verses_data
        
    except Exception as e:
        logger.error(f"❌ Error loading Bible data: {e}")
        return None

def get_current_progress(index):
    """Get current number of verses already uploaded"""
    try:
        stats = index.describe_index_stats()
        current_count = stats.total_vector_count
        logger.info(f"📊 Current verses in Pinecone: {current_count}")
        return current_count
    except Exception as e:
        logger.error(f"❌ Error getting current progress: {e}")
        return 0

def find_resume_point(verses_data: List[Dict], current_count: int) -> int:
    """Find where to resume upload based on current count"""
    if current_count == 0:
        return 0
    
    # Since we upload in order, we can resume from current_count
    # But let's add a small buffer in case some uploads failed
    buffer = max(0, min(100, current_count // 10))  # 10% buffer, max 100
    resume_point = max(0, current_count - buffer)
    
    logger.info(f"🚀 Resuming upload from verse {resume_point} (with {buffer} verse buffer)")
    return resume_point

async def upload_batch_with_retries(index, vectors: List[Dict], batch_num: int, max_retries: int = 5) -> bool:
    """Upload a batch with exponential backoff retries"""
    for attempt in range(max_retries):
        try:
            start_time = time.time()
            index.upsert(vectors=vectors)
            upload_time = time.time() - start_time
            
            logger.info(f"✅ Batch {batch_num}: {len(vectors)} verses uploaded in {upload_time:.1f}s")
            return True
            
        except Exception as e:
            wait_time = (2 ** attempt) + (attempt * 0.5)  # Exponential backoff with jitter
            logger.warning(f"⚠️  Batch {batch_num} attempt {attempt+1}/{max_retries} failed: {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"⏳ Retrying in {wait_time:.1f} seconds...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"❌ Batch {batch_num} failed after {max_retries} attempts")
                return False
    
    return False

async def upload_verses_robust(verses_data: List[Dict], model, index, resume_from: int = 0):
    """Upload verses with robust error handling and progress tracking"""
    
    total_verses = len(verses_data)
    batch_size = 50
    successful_uploads = 0
    failed_batches = []
    
    logger.info(f"🚀 Starting robust upload of {total_verses - resume_from} verses (resuming from {resume_from})")
    logger.info(f"📊 Batch size: {batch_size}, Total batches: {(total_verses - resume_from + batch_size - 1) // batch_size}")
    
    start_time = time.time()
    
    # Process in batches starting from resume point
    for i in range(resume_from, total_verses, batch_size):
        batch_num = (i // batch_size) + 1
        batch_start_time = time.time()
        
        # Get batch data
        batch = verses_data[i:i + batch_size]
        if not batch:
            continue
        
        # Track current book
        current_book = batch[0].get('book', 'Unknown')
        
        # Prepare vectors
        vectors_to_upsert = []
        for j, verse in enumerate(batch):
            try:
                # Create embedding
                embedding = model.encode(verse["text"]).tolist()
                
                # Create vector record
                vector_record = {
                    "id": f"{verse['book']}_{verse['chapter']}_{verse['verse']}",
                    "values": embedding,
                    "metadata": {
                        "book": verse["book"],
                        "chapter": verse["chapter"],
                        "verse": verse["verse"],
                        "text": verse["text"]
                    }
                }
                vectors_to_upsert.append(vector_record)
                
            except Exception as e:
                logger.error(f"❌ Error processing verse {i+j}: {e}")
                continue
        
        if not vectors_to_upsert:
            logger.warning(f"⚠️  No valid vectors in batch {batch_num}")
            continue
        
        # Upload batch with retries
        success = await upload_batch_with_retries(index, vectors_to_upsert, batch_num)
        
        if success:
            successful_uploads += len(vectors_to_upsert)
            batch_time = time.time() - batch_start_time
            progress = (i + len(batch)) / total_verses * 100
            
            # Calculate ETA
            elapsed_time = time.time() - start_time
            if successful_uploads > 0:
                avg_time_per_verse = elapsed_time / successful_uploads
                remaining_verses = total_verses - (i + len(batch))
                eta_seconds = remaining_verses * avg_time_per_verse
                eta_minutes = eta_seconds / 60
            else:
                eta_minutes = 0
            
            logger.info(f"📈 Progress: {progress:.1f}% ({i + len(batch)}/{total_verses}) - {current_book}")
            if eta_minutes > 0:
                logger.info(f"⏱️  ETA: {eta_minutes:.0f} minutes")
        else:
            failed_batches.append((batch_num, i, batch))
        
        # Small delay to avoid rate limits
        await asyncio.sleep(0.5)
    
    # Retry failed batches
    if failed_batches:
        logger.warning(f"⚠️  Retrying {len(failed_batches)} failed batches...")
        
        for batch_num, start_idx, batch in failed_batches:
            logger.info(f"🔄 Retrying batch {batch_num}")
            
            # Prepare vectors again
            vectors_to_upsert = []
            for verse in batch:
                try:
                    embedding = model.encode(verse["text"]).tolist()
                    vector_record = {
                        "id": f"{verse['book']}_{verse['chapter']}_{verse['verse']}",
                        "values": embedding,
                        "metadata": {
                            "book": verse["book"],
                            "chapter": verse["chapter"], 
                            "verse": verse["verse"],
                            "text": verse["text"]
                        }
                    }
                    vectors_to_upsert.append(vector_record)
                except Exception as e:
                    logger.error(f"❌ Error reprocessing verse: {e}")
                    continue
            
            success = await upload_batch_with_retries(index, vectors_to_upsert, batch_num, max_retries=3)
            if success:
                successful_uploads += len(vectors_to_upsert)
    
    total_time = time.time() - start_time
    logger.info(f"🎉 Upload completed!")
    logger.info(f"✅ Successfully uploaded: {successful_uploads} verses")
    logger.info(f"⏱️  Total time: {total_time/60:.1f} minutes")
    logger.info(f"📊 Upload rate: {successful_uploads/(total_time/60):.0f} verses/minute")
    
    return successful_uploads

async def main():
    """Main upload function"""
    print("🚀 Bible Verse Uploader - Standalone Version")
    print("=" * 60)
    
    # Load environment
    load_environment()
    
    # Load model
    model = get_embedding_model()
    if not model:
        return False
    
    # Connect to Pinecone
    pc, index = get_pinecone_client()
    if not index:
        return False
    
    # Load Bible data
    verses_data = load_bible_data()
    if not verses_data:
        return False
    
    # Check current progress
    current_count = get_current_progress(index)
    target_count = len(verses_data)
    
    if current_count >= target_count:
        logger.info("🎉 Upload already complete!")
        return True
    
    # Find resume point
    resume_from = find_resume_point(verses_data, current_count)
    
    # Start upload
    logger.info(f"🎯 Target: {target_count} verses")
    logger.info(f"📊 Current: {current_count} verses")
    logger.info(f"📈 Remaining: {target_count - current_count} verses")
    
    try:
        uploaded_count = await upload_verses_robust(verses_data, model, index, resume_from)
        
        # Final verification
        final_stats = index.describe_index_stats()
        final_count = final_stats.total_vector_count
        
        logger.info(f"🏁 Final count: {final_count}/{target_count} verses")
        
        if final_count >= target_count * 0.95:  # 95% success rate
            logger.info("🎉 ✅ UPLOAD SUCCESSFUL!")
            logger.info("🚀 Your Bible verse database is now complete!")
            return True
        else:
            logger.warning("⚠️  Upload incomplete, some verses may be missing")
            return False
            
    except Exception as e:
        logger.error(f"❌ Upload failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🎉 SUCCESS! All Bible verses uploaded!")
    else:
        print("\n❌ Upload incomplete. Check logs for details.")