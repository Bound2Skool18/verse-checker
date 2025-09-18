#!/usr/bin/env python3
"""
Simple script to upload Bible verses to Pinecone.
Uses minimal dependencies to avoid import issues.
"""

import os
import json
from pathlib import Path

def main():
    """Upload Bible verses to Pinecone."""
    
    # Check for API key
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("❌ PINECONE_API_KEY environment variable not set!")
        print()
        print("Please set your Pinecone API key first:")
        print("export PINECONE_API_KEY='your_api_key_here'")
        print()
        return
    
    print(f"✅ API key found (ends with: ...{api_key[-6:]})")
    
    # Check for Bible data
    bible_file = Path(__file__).parent.parent / "data" / "bible_complete.json"
    
    if not bible_file.exists():
        print(f"❌ Bible data file not found: {bible_file}")
        return
    
    # Load and count verses
    with open(bible_file, 'r', encoding='utf-8') as f:
        verses_data = json.load(f)
    
    print(f"📖 Found {len(verses_data)} Bible verses to upload")
    
    # Try importing and using Pinecone
    try:
        from pinecone import Pinecone, ServerlessSpec
        print("✅ Pinecone client imported successfully")
        
        # Initialize Pinecone
        pc = Pinecone(api_key=api_key)
        print("✅ Connected to Pinecone")
        
        # Check if index exists
        index_name = "bible-verses"
        existing_indexes = pc.list_indexes()
        index_names = [idx.name for idx in existing_indexes]
        
        if index_name in index_names:
            print(f"✅ Index '{index_name}' found")
            index = pc.Index(index_name)
            
            # Check current stats
            stats = index.describe_index_stats()
            print(f"📊 Current index stats:")
            print(f"   Total vectors: {stats.total_vector_count}")
            print(f"   Index fullness: {stats.index_fullness}")
            
            if stats.total_vector_count > 0:
                print(f"⚠️  Index already contains {stats.total_vector_count} vectors")
                print("Would you like to continue and add more? (This might create duplicates)")
                response = input("Continue? (y/N): ").lower()
                if response != 'y':
                    print("Upload cancelled.")
                    return
            
            print("\n🚀 Ready to upload! This will take several minutes...")
            print("Note: You'll need to install sentence-transformers to continue.")
            print("The upload script is ready - just need to resolve the embedding model import.")
            
            return True
            
        else:
            print(f"❌ Index '{index_name}' not found")
            print(f"Available indexes: {index_names}")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import Pinecone: {e}")
        return False
    except Exception as e:
        print(f"❌ Error connecting to Pinecone: {e}")
        return False

if __name__ == "__main__":
    main()