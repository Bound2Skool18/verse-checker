#!/usr/bin/env python3
"""
Upload all Bible verses to Pinecone cloud vector database.
Run this once to populate Pinecone with your complete Bible dataset.
"""

import os
import sys
import json
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from sentence_transformers import SentenceTransformer
from app.config import EMBEDDING_MODEL, logger
from app.pinecone_store import upload_verses_to_pinecone, get_index_stats

def main():
    """Upload Bible verses to Pinecone."""
    
    # Check for API key
    if not os.getenv("PINECONE_API_KEY"):
        print("❌ PINECONE_API_KEY environment variable not set!")
        print()
        print("Please set your Pinecone API key first:")
        print("export PINECONE_API_KEY='your_api_key_here'")
        print()
        print("Or add it to your shell profile (~/.zshrc or ~/.bashrc):")
        print("echo 'export PINECONE_API_KEY=\"your_api_key_here\"' >> ~/.zshrc")
        return
    
    # Load Bible data
    bible_file = Path(__file__).parent.parent / "data" / "bible_complete.json"
    
    if not bible_file.exists():
        print(f"❌ Bible data file not found: {bible_file}")
        print("Make sure you have the complete Bible dataset.")
        return
    
    print("📖 Loading Bible verses...")
    with open(bible_file, 'r', encoding='utf-8') as f:
        verses_data = json.load(f)
    
    print(f"✅ Loaded {len(verses_data)} Bible verses")
    
    # Initialize embedding model
    print("🤖 Loading embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("✅ Model loaded")
    
    # Upload to Pinecone
    print("☁️  Uploading to Pinecone (this may take several minutes)...")
    success = upload_verses_to_pinecone(verses_data, model)
    
    if success:
        print("🎉 Upload successful!")
        
        # Get stats
        print("\n📊 Pinecone Index Stats:")
        stats = get_index_stats()
        if stats:
            print(f"   Total vectors: {stats.get('total_vectors', 'Unknown')}")
            print(f"   Index fullness: {stats.get('index_fullness', 'Unknown')}")
            print(f"   Dimension: {stats.get('dimension', 'Unknown')}")
        
        print("\n✅ Your Bible verse API is now ready!")
        print("🚀 You can deploy your lightweight app to Render!")
        
    else:
        print("❌ Upload failed. Check the logs above for errors.")

if __name__ == "__main__":
    main()