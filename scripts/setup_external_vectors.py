#!/usr/bin/env python3
"""
Setup external vector database to store Bible embeddings.
This keeps your Render app lightweight while accessing all verses.
"""

def setup_pinecone_free():
    """Setup instructions for Pinecone free tier."""
    
    print("🎯 OPTION 1: Pinecone (Recommended)")
    print("=" * 50)
    print("✅ FREE: 1 million vectors (enough for entire Bible)")
    print("✅ FAST: Sub-100ms search times")
    print("✅ MANAGED: No memory issues on your app")
    print()
    print("📋 Setup steps:")
    print("1. Go to https://www.pinecone.io/")
    print("2. Sign up for free account")
    print("3. Create a new index:")
    print("   - Name: bible-verses")
    print("   - Dimensions: 384 (for all-MiniLM-L6-v2)")
    print("   - Metric: cosine")
    print("4. Get your API key from dashboard")
    print("5. Add to Render environment variables:")
    print("   PINECONE_API_KEY=your_api_key_here")
    print("   PINECONE_INDEX_NAME=bible-verses")
    print()

def setup_qdrant_cloud():
    """Setup instructions for Qdrant Cloud free tier."""
    
    print("🎯 OPTION 2: Qdrant Cloud")
    print("=" * 50)
    print("✅ FREE: 1GB storage")
    print("✅ COMPATIBLE: Same as your current Qdrant code")
    print("✅ EASY: Minimal code changes")
    print()
    print("📋 Setup steps:")
    print("1. Go to https://cloud.qdrant.io/")
    print("2. Sign up for free account")
    print("3. Create a cluster (free tier)")
    print("4. Get your cluster URL and API key")
    print("5. Add to Render environment variables:")
    print("   QDRANT_URL=https://your-cluster.qdrant.io")
    print("   QDRANT_API_KEY=your_api_key")
    print()

def setup_chroma_hosted():
    """Setup for hosted Chroma (alternative)."""
    
    print("🎯 OPTION 3: Hosted Vector Databases")
    print("=" * 50)
    print("• Supabase Vector (Postgres + pgvector)")
    print("• Neon with pgvector extension")
    print("• Upstash Vector (Redis-based)")
    print()

def show_lazy_loading_strategy():
    """Show how to implement lazy loading to reduce memory."""
    
    print("🎯 OPTION 4: Lazy Loading Strategy (No External Service)")
    print("=" * 50)
    print("✅ FREE: No external dependencies")
    print("✅ SMART: Load verses on-demand")
    print("✅ EFFICIENT: Cache most-used verses")
    print()
    print("📋 How it works:")
    print("1. Start with popular verses in memory (~2000)")
    print("2. Keep full dataset on disk")
    print("3. Search popular first, then search disk if needed")
    print("4. Cache recently searched verses")
    print()

def main():
    """Show all free options for handling large Bible dataset."""
    
    print("🚀 FREE Ways to Use All 31,102 Bible Verses")
    print("=" * 60)
    print()
    
    setup_pinecone_free()
    print()
    setup_qdrant_cloud()
    print()
    show_lazy_loading_strategy()
    print()
    
    print("🏆 RECOMMENDATION:")
    print("Use PINECONE (Option 1) - it's the easiest and most reliable")
    print("Your Render app becomes lightweight, just makes API calls to Pinecone")
    print()
    print("📊 Memory usage with external vectors:")
    print("• Current: 512MB+ (loading all embeddings)")
    print("• With Pinecone: ~100MB (just your API code)")
    print()
    print("Would you like me to help you set up Pinecone integration?")

if __name__ == "__main__":
    main()