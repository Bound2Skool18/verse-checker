"""
Configuration settings for the Bible Verse Checker API.
"""

import logging
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
QDRANT_DATA_DIR = PROJECT_ROOT / "qdrant_data"

# Bible data
BIBLE_JSON_PATH = DATA_DIR / "bible.json"

# Model settings
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
VECTOR_SIZE = 384  # Dimension of the all-MiniLM-L6-v2 model

# Search settings
SIMILARITY_THRESHOLD = 0.7  # Minimum similarity score for a match
MAX_SEARCH_RESULTS = 1  # Number of top results to return
COLLECTION_NAME = "bible"

# API settings
API_TITLE = "Bible Verse Checker API"
API_DESCRIPTION = "Semantic search and verification of Bible verses"
API_VERSION = "1.0.0"
API_HOST = "0.0.0.0"
API_PORT = 8000

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Create logger for the app
    logger = logging.getLogger("verse_checker")
    return logger

# Create default logger
logger = setup_logging()