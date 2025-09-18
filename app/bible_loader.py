import json
import sys
from pathlib import Path
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from app.config import (
    BIBLE_JSON_PATH, QDRANT_DATA_DIR, COLLECTION_NAME, 
    EMBEDDING_MODEL, VECTOR_SIZE, logger
)

def load_and_embed(force_reload=False):
    """Load Bible verses and create embeddings in Qdrant vector store.
    
    Args:
        force_reload (bool): If True, delete existing collection and reload data.
    """
    try:
        # Initialize model and client
        logger.info(f"Initializing embedding model: {EMBEDDING_MODEL}")
        model = SentenceTransformer(EMBEDDING_MODEL)
        
        logger.info(f"Connecting to Qdrant at {QDRANT_DATA_DIR}")
        client = QdrantClient(path=str(QDRANT_DATA_DIR))
        
        # Handle existing collection
        collection_exists = client.collection_exists(COLLECTION_NAME)
        
        if collection_exists and force_reload:
            logger.info(f"🗑️  Deleting existing collection '{COLLECTION_NAME}'")
            client.delete_collection(COLLECTION_NAME)
            collection_exists = False
        elif collection_exists:
            collection_info = client.get_collection(COLLECTION_NAME)
            count = collection_info.points_count
            logger.info(f"⚠️  Collection '{COLLECTION_NAME}' already exists with {count} verses")
            print(f"Collection already loaded with {count} verses. Use --force to reload.")
            return
        
        # Create collection
        logger.info(f"Creating collection '{COLLECTION_NAME}' with {VECTOR_SIZE} dimensions")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        
        # Load Bible data
        if not BIBLE_JSON_PATH.exists():
            logger.error(f"Bible data file not found: {BIBLE_JSON_PATH}")
            print(f"❌ Error: Bible data file not found at {BIBLE_JSON_PATH}")
            print("Please ensure the bible.json file exists in the data/ directory.")
            sys.exit(1)
        
        logger.info(f"Loading Bible data from {BIBLE_JSON_PATH}")
        with open(BIBLE_JSON_PATH, 'r', encoding='utf-8') as f:
            verses = json.load(f)
        
        if not verses:
            logger.error("No verses found in Bible data file")
            print("❌ Error: Bible data file is empty")
            sys.exit(1)
        
        logger.info(f"Processing {len(verses)} verses...")
        print(f"📖 Processing {len(verses)} Bible verses...")
        
        # Create embeddings and points
        points = []
        for i, verse in enumerate(verses):
            if i % 1000 == 0 and i > 0:
                print(f"  Processed {i}/{len(verses)} verses...")
            
            # Validate verse data
            required_fields = ['book', 'chapter', 'verse', 'text']
            if not all(field in verse for field in required_fields):
                logger.warning(f"Skipping verse {i}: missing required fields")
                continue
            
            try:
                embedding = model.encode(verse["text"]).tolist()
                points.append(PointStruct(id=i, vector=embedding, payload=verse))
            except Exception as e:
                logger.error(f"Error processing verse {i}: {str(e)}")
                continue
        
        if not points:
            logger.error("No valid verses to embed")
            print("❌ Error: No valid verses found to embed")
            sys.exit(1)
        
        # Upload to Qdrant
        logger.info(f"Uploading {len(points)} embeddings to Qdrant...")
        print(f"⬆️  Uploading {len(points)} embeddings to vector store...")
        
        client.upsert(COLLECTION_NAME, points=points)
        
        # Verify upload
        collection_info = client.get_collection(COLLECTION_NAME)
        final_count = collection_info.points_count
        
        logger.info(f"Successfully loaded {final_count} Bible verses")
        print(f"✅ Successfully loaded {final_count} Bible verses!")
        print(f"   Collection: {COLLECTION_NAME}")
        print(f"   Vector dimensions: {VECTOR_SIZE}")
        print(f"   Model: {EMBEDDING_MODEL}")
        
    except Exception as e:
        logger.error(f"Failed to load Bible data: {str(e)}")
        print(f"❌ Error loading Bible data: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Load Bible verses into vector store")
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force reload even if collection exists"
    )
    args = parser.parse_args()
    
    load_and_embed(force_reload=args.force)
