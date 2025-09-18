from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.config import (
    API_TITLE, API_DESCRIPTION, API_VERSION, logger
)
from app.embedding import get_model
from app.vector_store import get_client, search_verse
import traceback

# Initialize FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION
)

# Initialize components
try:
    logger.info("Initializing embedding model...")
    model = get_model()
    logger.info("Initializing vector store client...")
    client = get_client()
    logger.info("Application startup completed successfully")
except Exception as e:
    logger.error(f"Failed to initialize application: {str(e)}")
    raise

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

@app.get("/")
def root():
    """Root endpoint with basic API information."""
    return {
        "message": "Bible Verse Checker API",
        "version": API_VERSION,
        "docs": "/docs",
        "endpoints": {
            "check": "POST /check - Verify a Bible quote"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint."""
    try:
        # Test if vector store is accessible
        client.get_collections()
        return {"status": "healthy", "message": "All systems operational"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.post("/check", response_model=VerificationResult)
def check_quote(query: Query):
    """
    Check if a quote comes from the Bible.
    
    Returns the most similar Bible verse with a similarity score.
    Quotes with similarity > 0.7 are considered matches.
    """
    try:
        logger.info(f"Processing quote: {query.quote[:50]}...")
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
def startup_event():
    """Log startup information."""
    logger.info(f"Starting {API_TITLE} v{API_VERSION}")

@app.on_event("shutdown")
def shutdown_event():
    """Log shutdown information."""
    logger.info("Shutting down Bible Verse Checker API")
