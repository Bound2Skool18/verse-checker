from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional
import os
import asyncio
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

async def populate_pinecone_background():
    """Populate Pinecone in background to avoid startup timeout."""
    global pinecone_ready, population_in_progress, model
    
    try:
        population_in_progress = True
        logger.info("Starting background Pinecone population...")
        
        # Load model if not already loaded
        if model is None:
            logger.info("Loading embedding model...")
            model = get_model()
        
        # Check if we should use Pinecone
        if os.getenv("PINECONE_API_KEY"):
            from app.pinecone_store import create_index_if_not_exists, get_index_stats, upload_verses_to_pinecone
            
            # Create/connect to index
            index = create_index_if_not_exists()
            stats = get_index_stats()
            
            if stats.get('total_vectors', 0) == 0:
                logger.info("Empty Pinecone index detected, populating with Bible verses...")
                
                # Load Bible data
                import json
                from pathlib import Path
                
                bible_file = Path(__file__).parent.parent / "data" / "bible_complete.json"
                if bible_file.exists():
                    with open(bible_file, 'r', encoding='utf-8') as f:
                        verses_data = json.load(f)
                    
                    logger.info(f"Background upload: {len(verses_data)} verses to Pinecone...")
                    success = upload_verses_to_pinecone(verses_data, model)
                    
                    if success:
                        logger.info("Background: Bible verses successfully uploaded to Pinecone!")
                        pinecone_ready = True
                    else:
                        logger.error("Background: Failed to upload verses to Pinecone")
                else:
                    logger.error("Background: Bible data file not found")
            else:
                logger.info(f"Pinecone index already populated with {stats.get('total_vectors', 0)} verses")
                pinecone_ready = True
        
        population_in_progress = False
        logger.info("Background Pinecone population completed!")
        
    except Exception as e:
        logger.error(f"Background population failed: {str(e)}")
        population_in_progress = False

def initialize_components_fast():
    """Quick initialization that doesn't block startup."""
    global model
    
    if model is None:
        logger.info("Fast init: Loading embedding model...")
        model = get_model()
        logger.info("Fast init: Model loaded")

@app.get("/")
def root():
    """Root endpoint with basic API information."""
    status = "ready" if pinecone_ready else ("populating" if population_in_progress else "initializing")
    
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
        # Don't wait for full initialization, just check if app is responsive
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
    """Detailed status endpoint."""
    try:
        if os.getenv("PINECONE_API_KEY") and pinecone_ready:
            from app.pinecone_store import get_index_stats
            stats = get_index_stats()
            total_verses = stats.get('total_vectors', 0)
        else:
            total_verses = "initializing"
            
        return {
            "pinecone_ready": pinecone_ready,
            "population_in_progress": population_in_progress,
            "total_verses": total_verses,
            "model_loaded": model is not None
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/check", response_model=VerificationResult)
def check_quote(query: Query):
    """
    Check if a quote comes from the Bible.
    """
    try:
        # Quick check if system is ready
        if not pinecone_ready and not population_in_progress:
            # Start background population if not started
            asyncio.create_task(populate_pinecone_background())
            
        # If Pinecone isn't ready, return a helpful message
        if not pinecone_ready:
            return {
                "match": False,
                "score": 0.0,
                "reference": "System Initializing",
                "text": "Bible verse database is still loading. Please try again in a few minutes.",
                "message": "System is populating the Bible verse database. This takes about 10-15 minutes on first startup."
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
            asyncio.create_task(populate_pinecone_background())
            
        logger.info("Application startup completed successfully - Pinecone population running in background")
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")

@app.on_event("shutdown")
def shutdown_event():
    """Log shutdown information."""
    logger.info("Shutting down Bible Verse Checker API")