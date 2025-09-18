# Bible Verse Checker API

A FastAPI-based service that uses semantic search to verify and find Bible verses using vector embeddings and similarity matching.

## 🚀 Features

- **Semantic Search**: Uses sentence transformers to find verses by meaning, not just exact text matches
- **Fast API**: RESTful API with automatic documentation
- **Vector Storage**: Efficient similarity search using Qdrant vector database
- **Bible Verification**: Check if a quote is actually from the Bible and get the reference

## 📋 Requirements

- Python 3.8+
- 2GB+ RAM (for loading the sentence transformer model)
- 1GB+ storage (for Bible data and vector embeddings)

## 🛠 Installation

1. **Clone or download the project**:
   ```bash
   cd verse-checker
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Load Bible data** (first time only):
   ```bash
   python3 -m app.bible_loader
   ```

5. **Start the API server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## 📚 API Usage

### Interactive Documentation
Visit `http://localhost:8000/docs` for interactive API documentation.

### Check a Quote
**POST** `/check`

```bash
curl -X POST "http://localhost:8000/check" \
     -H "Content-Type: application/json" \
     -d '{"quote": "For God so loved the world"}'
```

**Response**:
```json
{
  "match": true,
  "score": 0.89,
  "reference": "John 3:16",
  "text": "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life."
}
```

### Response Fields

- `match` (boolean): Whether the quote likely comes from the Bible (score > 0.7)
- `score` (float): Similarity score (0.0 to 1.0, higher is more similar)
- `reference` (string): Book, chapter, and verse reference
- `text` (string): The actual Bible verse text

## 🔧 Configuration

Key settings can be modified in the code:

- **Similarity Threshold**: Currently set to 0.7 (70% similarity required for a match)
- **Search Results**: Returns top 1 match (can be increased for multiple suggestions)
- **Model**: Uses `all-MiniLM-L6-v2` for good speed/accuracy balance

## 📊 Examples

### Exact Match
```bash
curl -X POST "http://localhost:8000/check" \
     -H "Content-Type: application/json" \
     -d '{"quote": "In the beginning God created the heaven and the earth"}'
```

### Paraphrase
```bash
curl -X POST "http://localhost:8000/check" \
     -H "Content-Type: application/json" \
     -d '{"quote": "God created everything at the start"}'
```

### Non-Biblical Quote
```bash
curl -X POST "http://localhost:8000/check" \
     -H "Content-Type: application/json" \
     -d '{"quote": "To be or not to be, that is the question"}'
```

## 📁 Project Structure

```
verse-checker/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── bible_loader.py      # Data loading and embedding
│   ├── embedding.py         # Sentence transformer model
│   ├── vector_store.py      # Qdrant vector database operations
│   └── config.py            # Configuration settings
├── data/
│   └── bible.json           # Bible verses in JSON format
├── tests/
│   └── test_api.py          # Unit tests
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## 🧪 Testing

Run tests with:
```bash
python3 -m pytest tests/ -v
```

## 🔍 How It Works

1. **Data Loading**: Bible verses are loaded from JSON and converted to vector embeddings
2. **Vector Storage**: Embeddings are stored in Qdrant for fast similarity search
3. **Query Processing**: Input quotes are converted to embeddings using the same model
4. **Similarity Search**: Cosine similarity finds the most similar verses
5. **Threshold Filtering**: Only matches above 70% similarity are considered valid

## 🚧 Current Limitations

- **Dataset Size**: Currently includes only 2 sample verses (needs full Bible)
- **Single Translation**: Only supports KJV translation
- **Language**: English only
- **Context**: Doesn't consider surrounding verses or context

## 🛣 Roadmap

- [ ] Complete Bible dataset (all 31,000+ verses)
- [ ] Multiple Bible translations (NIV, ESV, etc.)
- [ ] Batch processing endpoint
- [ ] Confidence levels and multiple suggestions
- [ ] Web interface
- [ ] Docker deployment
- [ ] Multi-language support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📝 License

This project is open source. Please respect copyright for Bible translations.

## 🆘 Troubleshooting

### Common Issues

**"ModuleNotFoundError: No module named 'app'"**
- Make sure you're running commands from the project root directory
- Ensure you've installed all dependencies: `pip install -r requirements.txt`

**"Collection 'bible' does not exist"**
- Run the data loader first: `python3 -m app.bible_loader`

**API responds with low scores for known verses**
- The similarity threshold might be too high
- Check if the verse text matches the version in the database (KJV)

**High memory usage**
- The sentence transformer model requires ~1-2GB RAM
- Consider using a smaller model for resource-constrained environments

### Getting Help

For issues and questions:
1. Check this README
2. Look at the API documentation at `http://localhost:8000/docs`
3. Review the code - it's designed to be readable and well-commented