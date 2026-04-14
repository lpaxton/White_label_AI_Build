# Article Generator Setup Guide

## Quick Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install and Setup Ollama
1. Download Ollama from https://ollama.ai
2. Install and start Ollama:
   ```bash
   ollama serve
   ```
3. Pull a model (recommended):
   ```bash
   ollama pull llama3.2
   ```

### 3. Start the API Server
```bash
python api_server.py
```

### 4. Open the Web Interface
Open `article-generator.html` in your web browser.

## Easy Windows Setup
Just run `start_server.bat` - it will handle everything automatically!

## How It Works

### RAG (Retrieval-Augmented Generation) Flow:
1. **Upload Articles**: Your .txt files are uploaded and stored
2. **Text Chunking**: Articles are split into meaningful chunks
3. **Vector Storage**: Chunks are embedded and stored in ChromaDB
4. **Similarity Search**: When you enter a prompt, similar chunks are found
5. **Generation**: Ollama generates new content using similar examples as style guides

### File Structure After Setup:
```
article_getter_done/
├── article_generator.py      # Core RAG implementation
├── api_server.py            # Flask API server
├── article-generator.html   # Web interface
├── requirements.txt         # Dependencies
├── start_server.bat        # Windows startup script
├── article_generator_db/   # ChromaDB database (created automatically)
├── uploaded_articles/      # Temporary article storage (created automatically)
└── quick_example.py        # Demo script
```

## Usage Tips

### For Best Results:
- Upload 20+ articles in your writing style
- Use topics similar to your existing content
- Start with temperature 0.7 for balanced creativity
- Use 3-4 examples for good context without too much noise

### Troubleshooting:
- **"Cannot connect to Ollama"**: Make sure Ollama is running (`ollama serve`)
- **"Model not found"**: Pull the model first (`ollama pull llama3.2`)
- **"RAG setup failed"**: Check that articles were uploaded successfully
- **API errors**: Make sure the Flask server is running on port 5000

### Performance Notes:
- Initial RAG setup takes time (processes all your articles)
- Generation time depends on your hardware and chosen model
- Larger models (llama3.1) give better results but are slower
- More examples give better style matching but slower generation

## API Endpoints

The Flask server provides these REST endpoints:

- `GET /` - Health check and API documentation
- `POST /api/upload` - Upload article files
- `POST /api/setup-rag` - Initialize RAG database
- `POST /api/test-ollama` - Test Ollama connection
- `POST /api/generate` - Generate new article
- `POST /api/analyze-style` - Analyze writing style
- `GET /api/status` - Get system status

## Example API Usage

### Upload Files:
```bash
curl -X POST -F "files=@article1.txt" -F "files=@article2.txt" http://localhost:5000/api/upload
```

### Generate Article:
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"prompt": "The benefits of remote work", "num_examples": 3, "temperature": 0.7}' \
  http://localhost:5000/api/generate
```

## Security Notes

- The server runs on localhost only by default
- Uploaded files are stored temporarily and can be cleared
- No authentication is implemented (suitable for local use only)
- For production use, add proper authentication and input validation