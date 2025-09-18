from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import os
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

def initialize_components():
    """Initialize model and Pinecone components."""
    global model, pinecone_ready
    
    if model is None:
        logger.info("Initializing embedding model...")
        model = get_model()
        logger.info("Embedding model initialized")
    
    if not pinecone_ready:
        try:
            # Check if we should use Pinecone
            if os.getenv("PINECONE_API_KEY"):
                logger.info("Pinecone API key found, initializing Pinecone integration...")
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
                        
                        logger.info(f"Uploading {len(verses_data)} verses to Pinecone...")
                        success = upload_verses_to_pinecone(verses_data, model)
                        
                        if success:
                            logger.info("Bible verses successfully uploaded to Pinecone!")
                            pinecone_ready = True
                        else:
                            logger.error("Failed to upload verses to Pinecone")
                            raise Exception("Pinecone population failed")
                    else:
                        logger.error("Bible data file not found")
                        raise Exception("Bible data file missing")
                else:
                    logger.info(f"Pinecone index already populated with {stats.get('total_vectors', 0)} verses")
                    pinecone_ready = True
                    
            else:
                logger.warning("No Pinecone API key found, falling back to local Qdrant")
                from app.vector_store import get_client
                client = get_client()
                pinecone_ready = True
                
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}")
            raise

@app.get("/")
def root():
    """Root endpoint with basic API information."""
    return {
        "message": "Bible Verse Checker API",
        "version": API_VERSION,
        "vector_store": "Pinecone" if os.getenv("PINECONE_API_KEY") else "Local Qdrant",
        "docs": "/docs",
        "endpoints": {
            "check": "POST /check - Verify a Bible quote"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint."""
    try:
        initialize_components()
        
        if os.getenv("PINECONE_API_KEY"):
            from app.pinecone_store import get_index_stats
            stats = get_index_stats()
            total_verses = stats.get('total_vectors', 0)
        else:
            from app.vector_store import get_client
            client = get_client()
            try:
                client.get_collections()
                total_verses = "unknown"
            except:
                total_verses = 0
                
        return {
            "status": "healthy", 
            "message": "All systems operational",
            "vector_store": "Pinecone" if os.getenv("PINECONE_API_KEY") else "Local Qdrant",
            "total_verses": total_verses
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

@app.post("/check", response_model=VerificationResult)
def check_quote(query: Query):
    """
    Check if a quote comes from the Bible.
    
    Returns the most similar Bible verse with a similarity score.
    Quotes with similarity > 0.7 are considered matches.
    """
    try:
        initialize_components()
        
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
    """Initialize on startup."""
    logger.info(f"Starting {API_TITLE} v{API_VERSION}")
    try:
        initialize_components()
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        # Don't raise here, let individual endpoints handle initialization

@app.on_event("shutdown")
def shutdown_event():
    """Log shutdown information."""
    logger.info("Shutting down Bible Verse Checker API")