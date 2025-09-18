from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from app.config import (
    QDRANT_DATA_DIR, COLLECTION_NAME, VECTOR_SIZE, 
    SIMILARITY_THRESHOLD, MAX_SEARCH_RESULTS, logger
)

def get_client():
    """Initialize and return Qdrant client with proper collection setup."""
    try:
        logger.info(f"Connecting to Qdrant at {QDRANT_DATA_DIR}")
        client = QdrantClient(path=str(QDRANT_DATA_DIR))
        
        # Create collection if it doesn't exist
        if not client.collection_exists(COLLECTION_NAME):
            logger.info(f"Creating collection '{COLLECTION_NAME}' with {VECTOR_SIZE} dimensions")
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
            )
        else:
            logger.info(f"Using existing collection '{COLLECTION_NAME}'")
        
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant client: {str(e)}")
        raise

def search_verse(client, model, quote):
    """Search for the most similar Bible verse to the given quote."""
    if not quote or not quote.strip():
        return {
            "match": False, 
            "score": 0.0,
            "reference": "",
            "text": "",
            "message": "Empty quote provided"
        }
    
    try:
        # Encode the quote into a vector
        vector = model.encode(quote.strip()).tolist()
        logger.debug(f"Generated vector with {len(vector)} dimensions")
        
        # Search for similar verses
        search_results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            limit=MAX_SEARCH_RESULTS
        )
        
        if search_results:
            best_match = search_results[0]
            is_match = best_match.score >= SIMILARITY_THRESHOLD
            
            logger.debug(f"Best match score: {best_match.score:.3f} (threshold: {SIMILARITY_THRESHOLD})")
            
            return {
                "match": is_match,
                "score": round(best_match.score, 4),
                "reference": f"{best_match.payload['book']} {best_match.payload['chapter']}:{best_match.payload['verse']}",
                "text": best_match.payload["text"],
                "message": None if is_match else f"Low similarity score ({best_match.score:.3f}). Possibly not a Bible quote."
            }
        else:
            logger.warning("No search results returned from Qdrant")
            return {
                "match": False, 
                "score": 0.0,
                "reference": "",
                "text": "",
                "message": "No verses found in database"
            }
            
    except Exception as e:
        logger.error(f"Error during verse search: {str(e)}")
        raise
