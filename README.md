# aRCHi — Content and Learning System

A web-based toolkit for extracting, rewriting, and managing Fidelity Learning Center articles, backed by MongoDB Atlas and powered by Claude (Anthropic) and Ollama.

---

## What's Included

| Tool | File | Description |
|---|---|---|
| **Dashboard** | `index.html` | Main navigation hub |
| **Article Extractor** | `article-extractor.html` | Fetch & clean articles from URLs |
| **Word Editor** | `article-editor.html` | Edit articles with live formatting |
| **Article Rewriter** | `article-rewriter.html` | AI rewrite using Claude (Anthropic) |
| **Article Generator** | `article-generator.html` | RAG-based article generation via Ollama |
| **Persona Finder** | `enhanced-persona-finder.html` | Match articles to user personas via Ollama |

---

## Prerequisites

- **Python 3.9+** — [python.org](https://python.org)
- **Ollama** (for AI generation/persona features) — [ollama.ai](https://ollama.ai)
- **MongoDB Atlas account** (for article storage pipeline)
- **Anthropic API key** (for article rewriter)
- **OpenAI API key** (for text embeddings)

---

## Setup

### 1. Clone / copy the project files

Place the project folder on the server. All commands below run from that folder.

### 2. Create a Python virtual environment

```bash
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create the `.env` file

Copy the template below into a file named `.env` in the project root and fill in your credentials:

```env
# MongoDB Atlas connection string
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?appName=<AppName>

# OpenAI API key (for text-embedding-3-small embeddings)
OPENAI_API_KEY=sk-...

# Anthropic API key (for Claude rewriter)
ANTHROPIC_API_KEY=sk-ant-...
```

> **Never commit `.env` to version control.** It is already listed in `.gitignore`.

### 5. Install and start Ollama

```bash
# Install from https://ollama.ai, then:
ollama serve

# Pull the recommended model (in a second terminal)
ollama pull llama3.2
```

---

## Starting the Servers

This project uses **two** servers that must both be running:

### Server 1 — Main HTTP server (port 8000)

Serves the HTML tools and proxies requests to Ollama. Also handles article extraction (`/api/extract-article`).

```bash
python serve.py
# or on a custom port:
python serve.py 9000
```

Open the dashboard at: `http://localhost:8000`

### Server 2 — Flask API server (port 5000)

Required only for the **Article Generator** (RAG pipeline).

```bash
python api_server.py
```

### Windows shortcut

Run `start_server.bat` to install dependencies and start the Flask API server automatically.

---

## Using the Tools

### Article Extractor
1. Open `http://localhost:8000/article-extractor.html`
2. Paste a Fidelity Learning Center article URL
3. Click **Extract** — the tool fetches, cleans, and displays the article content
4. Optionally save to MongoDB Atlas

### Article Rewriter
1. Open `http://localhost:8000/article-rewriter.html`
2. Paste or load an article
3. Select a rewrite style and click **Rewrite** — uses Claude via Anthropic API

### Article Generator (RAG)
1. Make sure the Flask server (`api_server.py`) is running on port 5000
2. Open `http://localhost:8000/article-generator.html`
3. Upload `.txt` article files as style examples
4. Enter a topic prompt and generate

### Persona Finder
1. Open `http://localhost:8000/enhanced-persona-finder.html`
2. Upload the scraped articles JSON file (`fidelity_articles_flat_*.json`)
3. Describe your persona and get AI-powered article recommendations

### Scraping Articles (optional, one-time)
```bash
python fidelity_scraper.py
```
Outputs `fidelity_articles_[timestamp].json`, `fidelity_articles_flat_[timestamp].json`, and a `.csv`.

---

## MongoDB Atlas Setup

The FCAT pipeline (`fcat_db.py`) connects to an Atlas cluster. To configure:

1. Log in to [cloud.mongodb.com](https://cloud.mongodb.com)
2. Go to **Database > Connect > Drivers** and copy your connection string
3. Paste it as `MONGODB_URI` in your `.env` file
4. Ensure your server's IP is whitelisted in **Network Access**

Database: `fcat` | Collection: `articles`

---

## Project Structure

```
article_getter_done/
├── serve.py                    # Main HTTP server + Ollama proxy + article extraction API
├── api_server.py               # Flask server for RAG article generator
├── fcat_db.py                  # MongoDB Atlas client
├── claude_rewriter.py          # Claude-based article rewriter backend
├── embedding_service.py        # OpenAI embedding service
├── article_generator.py        # RAG implementation (ChromaDB)
├── fidelity_scraper.py         # Fidelity Learning Center scraper
├── persona_finder.py           # CLI persona finder
├── requirements.txt            # Python dependencies
├── .env                        # API keys and connection strings (create this)
├── start_server.bat            # Windows startup script
├── index.html                  # Dashboard
├── article-extractor.html      # Article extraction tool
├── article-editor.html         # Word editor
├── article-rewriter.html       # AI rewriter
├── article-generator.html      # RAG generator
├── enhanced-persona-finder.html
├── shared.css                  # Shared styles
├── article_generator_db/       # ChromaDB vector store (auto-created)
└── uploaded_articles/          # Temp article uploads (auto-created)
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Cannot connect to Ollama` | Run `ollama serve` and confirm it's on port 11434 |
| `Model not found` | Run `ollama pull llama3.2` |
| `MONGODB_URI not set` | Check your `.env` file is in the project root |
| `Article extraction failed` | The target page may block server-side requests; try a different article |
| Flask server errors | Check that `api_server.py` is running on port 5000 |
| Port already in use | Pass a different port: `python serve.py 8080` |

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `MONGODB_URI` | Yes (for DB features) | MongoDB Atlas connection string |
| `ANTHROPIC_API_KEY` | Yes (for rewriter) | Claude API key from [console.anthropic.com](https://console.anthropic.com) |
| `OPENAI_API_KEY` | Yes (for embeddings) | OpenAI key from [platform.openai.com](https://platform.openai.com) |
