from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional
import os
import asyncio
import time
from app.config import (
    API_TITLE, API_DESCRIPTION, API_VERSION, logger
)
from app.embedding import get_model
import traceback

# Initialize FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION + " - Powered by Pinecone",
    version=API_VERSION
)

# Global variables for lazy initialization
model = None
pinecone_ready = False
population_in_progress = False
upload_status = {"uploaded": 0, "total": 0, "current_book": ""}

class Query(BaseModel):
    quote: str = Field(
        ..., 
        min_length=0, 
        max_length=1000,
        description="The quote to check against Bible verses",
        json_schema_extra={"example": "For God so loved the world"}
    )

class VerificationResult(BaseModel):
    match: bool = Field(description="Whether the quote likely comes from the Bible")
    score: float = Field(description="Similarity score (0.0 to 1.0)")
    reference: str = Field(description="Bible reference (book, chapter:verse)")
    text: str = Field(description="The actual Bible verse text")
    message: Optional[str] = Field(None, description="Additional message or explanation")

async def populate_pinecone_robust():
    """Robust Pinecone population with progress tracking and retry logic."""
    global pinecone_ready, population_in_progress, model, upload_status
    
    try:
        population_in_progress = True
        logger.info("Starting ROBUST Pinecone population with retry logic...")
        
        # Load model if not already loaded
        if model is None:
            logger.info("Loading embedding model...")
            model = get_model()
            logger.info("✅ Embedding model loaded successfully")
        
        # Check if we should use Pinecone
        if not os.getenv("PINECONE_API_KEY"):
            logger.warning("No Pinecone API key found")
            population_in_progress = False
            return
            
        from app.pinecone_store import create_index_if_not_exists, get_index_stats
        
        # Create/connect to index
        logger.info("Connecting to Pinecone index...")
        index = create_index_if_not_exists()
        stats = get_index_stats()
        
        current_vectors = stats.get('total_vectors', 0)
        logger.info(f"Current Pinecone vectors: {current_vectors}")
        
        # Check if we need to upload
        if current_vectors >= 31000:  # Allow for some variance
            logger.info(f"✅ Pinecone already has {current_vectors} verses - skipping upload")
            pinecone_ready = True
            population_in_progress = False
            return
            
        # Load Bible data
        import json
        from pathlib import Path
        
        bible_file = Path(__file__).parent.parent / "data" / "bible_complete.json"
        if not bible_file.exists():
            logger.error("❌ Bible data file not found")
            population_in_progress = False
            return
            
        logger.info("📖 Loading complete Bible dataset...")
        with open(bible_file, 'r', encoding='utf-8') as f:
            verses_data = json.load(f)
        
        total_verses = len(verses_data)
        upload_status["total"] = total_verses
        logger.info(f"✅ Loaded {total_verses} Bible verses from file")
        
        # Upload with robust batching and progress tracking
        success = await upload_verses_robust(verses_data, model, index)
        
        if success:
            # Verify final count
            final_stats = get_index_stats()
            final_count = final_stats.get('total_vectors', 0)
            logger.info(f"🎉 Upload complete! Final verse count: {final_count}")
            
            if final_count >= total_verses * 0.95:  # Allow 5% tolerance
                pinecone_ready = True
                logger.info("✅ Bible verse database is now ready!")
            else:
                logger.warning(f"⚠️ Upload incomplete: {final_count}/{total_verses}")
        else:
            logger.error("❌ Upload failed")
            
        population_in_progress = False
        
    except Exception as e:
        logger.error(f"❌ Background population failed: {str(e)}")
        logger.debug(f"Full error: {traceback.format_exc()}")
        population_in_progress = False

async def upload_verses_robust(verses_data, model, index):
    """Upload verses with robust batching and error handling."""
    global upload_status
    
    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index("bible-verses")
        
        batch_size = 50  # Smaller batches for reliability
        total_verses = len(verses_data)
        uploaded_count = 0
        
        logger.info(f"🚀 Starting upload of {total_verses} verses in batches of {batch_size}")
        
        for i in range(0, total_verses, batch_size):
            batch = verses_data[i:i + batch_size]
            batch_start = time.time()
            
            # Track current book for status
            if batch:
                current_book = batch[0].get('book', 'Unknown')
                upload_status["current_book"] = current_book
            
            # Prepare batch for upload
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
                    logger.error(f"Error processing verse {i+j}: {e}")
                    continue
            
            # Upload batch with retry logic
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries:
                try:
                    index.upsert(vectors=vectors_to_upsert)
                    uploaded_count += len(vectors_to_upsert)
                    upload_status["uploaded"] = uploaded_count
                    
                    batch_time = time.time() - batch_start
                    progress = (uploaded_count / total_verses) * 100
                    
                    logger.info(f"✅ Batch {i//batch_size + 1}: {len(vectors_to_upsert)} verses uploaded "
                              f"({uploaded_count}/{total_verses}, {progress:.1f}%) "
                              f"[{batch_time:.1f}s] - {current_book}")
                    break
                    
                except Exception as e:
                    retry_count += 1
                    logger.warning(f"⚠️ Batch upload failed (attempt {retry_count}/{max_retries}): {e}")
                    if retry_count < max_retries:
                        await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                    else:
                        logger.error(f"❌ Failed to upload batch after {max_retries} attempts")
                        return False
            
            # Small delay between batches to avoid rate limits
            await asyncio.sleep(0.5)
        
        logger.info(f"🎉 Successfully uploaded {uploaded_count}/{total_verses} verses")
        return uploaded_count >= total_verses * 0.95  # 95% success rate acceptable
        
    except Exception as e:
        logger.error(f"❌ Robust upload failed: {e}")
        return False

def initialize_components_fast():
    """Quick initialization that doesn't block startup."""
    global model
    
    if model is None:
        logger.info("Fast init: Loading embedding model...")
        model = get_model()
        logger.info("Fast init: ✅ Model loaded")

@app.get("/")
def root():
    """Root endpoint with basic API information."""
    if pinecone_ready:
        status = "ready"
    elif population_in_progress:
        progress = upload_status["uploaded"] / max(upload_status["total"], 1) * 100
        status = f"populating ({progress:.1f}% - {upload_status['current_book']})"
    else:
        status = "initializing"
    
    return {
        "message": "Bible Verse Checker API",
        "version": API_VERSION,
        "vector_store": "Pinecone" if os.getenv("PINECONE_API_KEY") else "Local Qdrant",
        "status": status,
        "docs": "/docs",
        "endpoints": {
            "check": "POST /check - Verify a Bible quote"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint - quick response to avoid timeout."""
    try:
        return {
            "status": "healthy", 
            "message": "API is responsive",
            "vector_store": "Pinecone" if os.getenv("PINECONE_API_KEY") else "Local Qdrant",
            "pinecone_ready": pinecone_ready,
            "population_in_progress": population_in_progress
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

@app.get("/status")
def get_status():
    """Detailed status endpoint with upload progress."""
    try:
        if os.getenv("PINECONE_API_KEY") and pinecone_ready:
            from app.pinecone_store import get_index_stats
            stats = get_index_stats()
            total_verses = stats.get('total_vectors', 0)
        else:
            total_verses = upload_status["uploaded"]
            
        return {
            "pinecone_ready": pinecone_ready,
            "population_in_progress": population_in_progress,
            "total_verses": total_verses,
            "model_loaded": model is not None,
            "upload_progress": {
                "uploaded": upload_status["uploaded"],
                "total": upload_status["total"],
                "current_book": upload_status["current_book"],
                "percentage": round(upload_status["uploaded"] / max(upload_status["total"], 1) * 100, 1)
            }
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/check", response_model=VerificationResult)
def check_quote(query: Query):
    """Check if a quote comes from the Bible."""
    try:
        # Quick check if system is ready
        if not pinecone_ready and not population_in_progress:
            # Start background population if not started
            asyncio.create_task(populate_pinecone_robust())
            
        # If Pinecone isn't ready, return a helpful message
        if not pinecone_ready:
            progress = upload_status["uploaded"] / max(upload_status["total"], 1) * 100
            return {
                "match": False,
                "score": 0.0,
                "reference": "System Initializing",
                "text": f"Bible verse database is loading ({progress:.1f}% complete - {upload_status['current_book']}). Please try again in a few minutes.",
                "message": f"System is populating the Bible verse database. Progress: {progress:.1f}% complete."
            }
        
        # Ensure model is loaded
        if model is None:
            initialize_components_fast()
        
        logger.info(f"Processing quote: {query.quote[:50]}...")
        
        if os.getenv("PINECONE_API_KEY") and pinecone_ready:
            # Use Pinecone
            from app.pinecone_store import search_verse_pinecone
            result = search_verse_pinecone(query.quote, model)
        else:
            # Fallback to local Qdrant
            from app.vector_store import get_client, search_verse
            client = get_client()
            result = search_verse(client, model, query.quote)
        
        logger.info(f"Search completed with score: {result.get('score', 0):.3f}")
        return result
    except Exception as e:
        logger.error(f"Error processing quote: {str(e)}")
        logger.debug(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error while processing quote"
        )

@app.on_event("startup")
async def startup_event():
    """Quick startup - don't wait for Pinecone population."""
    logger.info(f"Starting {API_TITLE} v{API_VERSION}")
    try:
        # Fast initialization
        initialize_components_fast()
        
        # Start background population but don't wait for it
        if os.getenv("PINECONE_API_KEY"):
            asyncio.create_task(populate_pinecone_robust())
            
        logger.info("✅ Application startup completed successfully - Robust Pinecone population starting")
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")

@app.on_event("shutdown")
def shutdown_event():
    """Log shutdown information."""
    logger.info("Shutting down Bible Verse Checker API")