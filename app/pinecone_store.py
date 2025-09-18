"""
Pinecone vector store integration for Bible verse search.
This replaces local Qdrant with cloud-based Pinecone for memory efficiency.
"""

import os
from typing import Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
import numpy as np
from app.config import logger

# Pinecone configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "bible-verses")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east-1-aws")

def get_pinecone_client():
    """Get Pinecone client instance."""
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY environment variable is required")
    
    return Pinecone(api_key=PINECONE_API_KEY)

def create_index_if_not_exists():
    """Create Pinecone index if it doesn't exist."""
    try:
        pc = get_pinecone_client()
        
        # Check if index exists
        existing_indexes = pc.list_indexes()
        index_names = [idx.name for idx in existing_indexes]
        
        if PINECONE_INDEX_NAME not in index_names:
            logger.info(f"Creating Pinecone index: {PINECONE_INDEX_NAME}")
            pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=384,  # all-MiniLM-L6-v2 embedding dimension
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=PINECONE_ENVIRONMENT
                )
            )
            logger.info(f"Index {PINECONE_INDEX_NAME} created successfully")
        else:
            logger.info(f"Index {PINECONE_INDEX_NAME} already exists")
            
        return pc.Index(PINECONE_INDEX_NAME)
        
    except Exception as e:
        logger.error(f"Failed to create/connect to Pinecone index: {str(e)}")
        raise

def upload_verses_to_pinecone(verses_data, model):
    """Upload Bible verses to Pinecone."""
    try:
        index = create_index_if_not_exists()
        
        logger.info(f"Uploading {len(verses_data)} verses to Pinecone...")
        
        # Prepare vectors for upsert
        vectors_to_upsert = []
        batch_size = 100  # Pinecone batch limit
        
        for i, verse in enumerate(verses_data):
            # Create embedding
            embedding = model.encode(verse["text"]).tolist()
            
            # Create metadata
            metadata = {
                "book": verse["book"],
                "chapter": verse["chapter"],
                "verse": verse["verse"],
                "text": verse["text"]
            }
            
            # Create vector record
            vector_record = {
                "id": f"{verse['book']}_{verse['chapter']}_{verse['verse']}",
                "values": embedding,
                "metadata": metadata
            }
            
            vectors_to_upsert.append(vector_record)
            
            # Upsert in batches
            if len(vectors_to_upsert) >= batch_size or i == len(verses_data) - 1:
                index.upsert(vectors=vectors_to_upsert)
                logger.info(f"Uploaded batch ending at verse {i+1}/{len(verses_data)}")
                vectors_to_upsert = []
        
        logger.info(f"Successfully uploaded all {len(verses_data)} verses to Pinecone")
        return True
        
    except Exception as e:
        logger.error(f"Failed to upload verses to Pinecone: {str(e)}")
        return False

def search_verse_pinecone(query_text: str, model, top_k: int = 1) -> Dict[str, Any]:
    """
    Search for Bible verse using Pinecone.
    
    Args:
        query_text: The text to search for
        model: The embedding model
        top_k: Number of results to return
        
    Returns:
        Dictionary containing search results
    """
    try:
        # Get Pinecone index
        pc = get_pinecone_client()
        index = pc.Index(PINECONE_INDEX_NAME)
        
        # Create query embedding
        query_embedding = model.encode(query_text).tolist()
        
        # Search in Pinecone
        search_results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        if not search_results.matches:
            return {
                "match": False,
                "score": 0.0,
                "reference": "Unknown",
                "text": "No matching verse found",
                "message": "No similar Bible verse found."
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
            message = f"Strong match found! This appears to be from {reference}."
        elif similarity_score >= 0.6:
            message = f"Possible match from {reference}. Similarity: {similarity_score:.3f}"
        else:
            message = f"Low similarity score ({similarity_score:.3f}). Possibly not a Bible quote."
        
        return {
            "match": is_match,
            "score": round(similarity_score, 4),
            "reference": reference,
            "text": metadata["text"],
            "message": message
        }
        
    except Exception as e:
        logger.error(f"Error searching verse in Pinecone: {str(e)}")
        raise Exception(f"Search failed: {str(e)}")

def get_index_stats() -> Dict[str, Any]:
    """Get statistics about the Pinecone index."""
    try:
        pc = get_pinecone_client()
        index = pc.Index(PINECONE_INDEX_NAME)
        
        stats = index.describe_index_stats()
        
        return {
            "total_vectors": stats.total_vector_count,
            "index_fullness": stats.index_fullness,
            "dimension": stats.dimension
        }
        
    except Exception as e:
        logger.error(f"Failed to get index stats: {str(e)}")
        return {}