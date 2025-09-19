from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import os
import logging

# Simple logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Bible Verse Checker API",
    description="Check if quotes come from the Bible - Lightweight Version",
    version="1.0.0"
)

# Global variables
model = None
upload_status = {"uploaded": 0, "total": 31102, "current_book": "Loading..."}

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
        "message": "Bible Verse Checker API - Lightweight",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "endpoints": {
            "check": "POST /check - Verify a Bible quote",
            "health": "GET /health - Health check",
            "status": "GET /status - Detailed status"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint - always responds quickly."""
    return {
        "status": "healthy", 
        "message": "API is responsive",
        "service": "lightweight_mode",
        "timestamp": "2025-01-19T14:30:00Z"
    }

@app.get("/status")  
def get_status():
    """Status endpoint with current information."""
    try:
        # Try to check Pinecone if API key is available
        pinecone_status = "unknown"
        verse_count = 0
        
        api_key = os.getenv("PINECONE_API_KEY")
        if api_key:
            try:
                from pinecone import Pinecone
                pc = Pinecone(api_key=api_key)
                index = pc.Index("bible-verses")
                stats = index.describe_index_stats()
                verse_count = stats.total_vector_count
                pinecone_status = "connected"
            except Exception as e:
                pinecone_status = f"error: {str(e)[:50]}"
        else:
            pinecone_status = "no_api_key"
        
        progress = (verse_count / 31102) * 100 if verse_count > 0 else 0
        
        return {
            "service_mode": "lightweight",
            "pinecone_status": pinecone_status,
            "total_verses": verse_count,
            "target_verses": 31102,
            "progress_percentage": round(progress, 1),
            "upload_active": verse_count > 0 and verse_count < 31102,
            "fully_loaded": verse_count >= 31102
        }
    except Exception as e:
        return {"error": str(e), "service_mode": "lightweight"}

@app.post("/check", response_model=VerificationResult)
def check_quote(query: Query):
    """Check if a quote comes from the Bible - Lightweight version."""
    try:
        # Check if we have Pinecone access
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            return {
                "match": False,
                "score": 0.0,
                "reference": "Service Configuration",
                "text": "API key not configured",
                "message": "Pinecone API key is not set up. Please configure the service."
            }
        
        # Try to connect to Pinecone
        try:
            from pinecone import Pinecone
            pc = Pinecone(api_key=api_key)
            index = pc.Index("bible-verses")
            stats = index.describe_index_stats()
            verse_count = stats.total_vector_count
        except Exception as e:
            return {
                "match": False,
                "score": 0.0,
                "reference": "Service Error",
                "text": f"Could not connect to database: {str(e)[:100]}",
                "message": "Database connection failed. Please try again later."
            }
        
        # Check if database has verses
        if verse_count == 0:
            return {
                "match": False,
                "score": 0.0,
                "reference": "Database Empty",
                "text": "No Bible verses loaded yet",
                "message": "The Bible verse database is empty. Upload is needed."
            }
        
        # If we have some verses but not all, warn about limited coverage
        if verse_count < 31102:
            progress = (verse_count / 31102) * 100
            coverage_msg = f"Database is {progress:.1f}% loaded ({verse_count:,}/31,102 verses). Results may be limited."
        else:
            coverage_msg = "Full Bible database available."
        
        # Load model for embedding (lightweight approach)
        global model
        if model is None:
            try:
                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("✅ Model loaded successfully")
            except Exception as e:
                return {
                    "match": False,
                    "score": 0.0,
                    "reference": "Model Error",
                    "text": f"Could not load AI model: {str(e)[:100]}",
                    "message": "AI model loading failed. Please try again later."
                }
        
        # Create query embedding
        try:
            query_embedding = model.encode(query.quote).tolist()
        except Exception as e:
            return {
                "match": False,
                "score": 0.0,
                "reference": "Processing Error",
                "text": f"Could not process quote: {str(e)[:100]}",
                "message": "Quote processing failed. Please try a different quote."
            }
        
        # Search in Pinecone
        try:
            search_results = index.query(
                vector=query_embedding,
                top_k=1,
                include_metadata=True
            )
            
            if not search_results.matches:
                return {
                    "match": False,
                    "score": 0.0,
                    "reference": "No Match",
                    "text": "No similar verse found",
                    "message": f"No matching Bible verse found. {coverage_msg}"
                }
            
            # Get best match
            best_match = search_results.matches[0]
            similarity_score = float(best_match.score)
            metadata = best_match.metadata
            
            # Determine if it's a match (threshold: 0.7)
            is_match = similarity_score >= 0.7
            
            # Format reference
            reference = f"{metadata['book']} {metadata['chapter']}:{metadata['verse']}"
            
            # Create response message
            if is_match:
                message = f"Strong match found! This appears to be from {reference}. {coverage_msg}"
            elif similarity_score >= 0.6:
                message = f"Possible match from {reference}. Similarity: {similarity_score:.3f}. {coverage_msg}"
            else:
                message = f"Low similarity score ({similarity_score:.3f}). Possibly not a Bible quote. {coverage_msg}"
            
            return {
                "match": is_match,
                "score": round(similarity_score, 4),
                "reference": reference,
                "text": metadata["text"],
                "message": message
            }
            
        except Exception as e:
            return {
                "match": False,
                "score": 0.0,
                "reference": "Search Error",
                "text": f"Search failed: {str(e)[:100]}",
                "message": "Database search failed. Please try again later."
            }
        
    except Exception as e:
        logger.error(f"Error processing quote: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error while processing quote"
        )

@app.on_event("startup")
async def startup_event():
    """Lightweight startup - no heavy operations."""
    logger.info("🚀 Starting Bible Verse Checker API - Lightweight Mode")
    logger.info("✅ Startup completed - Ready to serve requests")
    # No heavy background tasks - just start up quickly

@app.on_event("shutdown") 
def shutdown_event():
    """Log shutdown information."""
    logger.info("🛑 Shutting down Bible Verse Checker API")

# Health check for Render
@app.get("/ping")
def ping():
    """Simple ping endpoint for Render health checks."""
    return {"status": "ok", "message": "pong"}