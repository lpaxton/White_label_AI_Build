# aRCHi — Content and Learning System

A web-based toolkit for extracting, neutralizing, reviewing, and managing financial articles, backed by MongoDB Atlas and powered by Claude (Anthropic) and OpenAI.

---

## Exact Environment Requirements

| Requirement | Version | Notes |
|---|---|---|
| **Python** | **3.11.8** | Must be 3.11.x — ChromaDB has known issues on 3.12+ |
| **pip** | 26.0.1 | Bundled with Python 3.11.8 installer |
| **OS** | Windows 10/11 or Ubuntu 22.04 | Tested on both |
| **Ollama** | Latest | Only needed for Article Generator / Persona Finder |

> **Critical:** Do not use Python 3.12 or 3.13. ChromaDB's native bindings are not compatible. Install Python 3.11.8 exactly from [python.org/downloads](https://www.python.org/downloads/release/python-3118/).

---

## Tools

| Tool | File | Description |
|---|---|---|
| **Dashboard** | `index.html` | Main navigation hub |
| **Article Extractor** | `article-extractor.html` | Step 1 — Fetch & clean articles from URLs |
| **Brand Neutralizer** | `article-rewriter.html` | Step 2 — AI rewrite using Claude |
| **Content Diff Tool** | `article-diff.html` | Step 3 — Side-by-side diff of original vs. neutralized |
| **Word Editor** | `article-editor.html` | Step 4 — Rich-text edit & export |
| **Money Buddy Chat** | `chat.html` | DB-grounded Q&A (answers only from FCAT articles) |
| **Article Search** | `article-search.html` | Search FCAT DB by eReview #, tags, title, or semantic meaning |
| **Article Generator** | `article-generator.html` | RAG-based generation via Ollama (optional) |

---

## Installation

### 1. Install Python 3.11.8

Download from: https://www.python.org/downloads/release/python-3118/

- On Windows: run the installer, check **"Add Python to PATH"**
- Verify: `python --version` → should print `Python 3.11.8`

### 2. Clone the repository

```bash
git clone https://github.com/lpaxton/White_label_AI_Build.git
cd White_label_AI_Build
```

### 3. Create a virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / Mac
python3.11 -m venv .venv
source .venv/bin/activate
```

### 4. Install pinned dependencies

Use the pinned file for a guaranteed-working install:

```bash
pip install -r requirements-pinned.txt
```

If you prefer unpinned (may produce different versions):

```bash
pip install -r Requirements.txt
```

### 5. Create the `.env` file

Create a file named `.env` in the project root:

```env
# MongoDB Atlas connection string
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?appName=<AppName>

# OpenAI API key (used for text-embedding-3-small embeddings)
OPENAI_API_KEY=sk-...

# Anthropic API key (used for Claude brand neutralizer and Money Buddy chat)
ANTHROPIC_API_KEY=sk-ant-...
```

> **Never commit `.env` to version control.** It is already in `.gitignore`.

### 6. (Optional) Install and start Ollama

Only required for the **Article Generator** and **Persona Finder** tools.

```bash
# Install from https://ollama.ai, then:
ollama serve

# In a second terminal, pull the model:
ollama pull llama3.2
```

---

## Starting the Application

Two servers must run simultaneously:

### Server 1 — Flask API (port 5000)

Handles all backend logic: article extraction, rewriting, MongoDB, embeddings, chat, search.

```bash
# Windows
.venv\Scripts\python api_server.py

# Linux / Mac
.venv/bin/python api_server.py
```

### Server 2 — Static file server (port 8080)

Serves the HTML frontend files.

```bash
# Windows
.venv\Scripts\python -m http.server 8080

# Linux / Mac
.venv/bin/python -m http.server 8080
```

Open the dashboard at: **http://localhost:8080/index.html**

---

## MongoDB Atlas Setup

### Connection

1. Log in to [cloud.mongodb.com](https://cloud.mongodb.com)
2. Go to **Database > Connect > Drivers** and copy your connection string
3. Paste it as `MONGODB_URI` in `.env`
4. **Whitelist your server's IP** under **Security > Network Access** (or allow `0.0.0.0/0` for dev)

Database: `fcat` | Collection: `articles`

### Vector Search Index (required for Semantic Search and Money Buddy chat)

In the MongoDB Atlas UI:
1. Go to your cluster → **Atlas Search** tab → **Create Search Index**
2. Choose **JSON Editor** and select the `fcat.articles` collection
3. Use this definition:

```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding.vector",
      "numDimensions": 1536,
      "similarity": "cosine"
    }
  ]
}
```

4. Name the index `vector_index` and click **Create**

> Without this index, Semantic Search and Money Buddy automatically fall back to keyword search. Everything still works — just less accurate.

---

## Pinned Package Versions

The following are the exact versions running in the working environment. If you hit install errors on another machine, pin to these versions.

```
Flask==3.1.3
Werkzeug==3.1.6
Jinja2==3.1.6
anthropic==0.84.0
openai==2.30.0
pymongo==4.16.0
python-dotenv==1.2.2
flask-cors==6.0.2
beautifulsoup4==4.14.3
lxml==6.0.2
requests==2.32.5
chromadb==1.5.2
numpy==2.4.2
pydantic==2.12.5
pydantic_core==2.41.5
httpx==0.28.1
anyio==4.12.1
certifi==2026.2.25
charset-normalizer==3.4.4
click==8.3.1
dnspython==2.8.0
huggingface_hub==1.5.0
onnxruntime==1.24.2
tokenizers==0.22.2
uvicorn==0.41.0
grpcio==1.78.0
protobuf==6.33.5
opentelemetry-api==1.40.0
opentelemetry-sdk==1.40.0
typing_extensions==4.15.0
```

---

## Common Installation Problems

| Problem | Cause | Fix |
|---|---|---|
| `chromadb` install fails | Wrong Python version | Use exactly Python **3.11.8** |
| `onnxruntime` not found | ARM / Apple Silicon | Install `onnxruntime-silicon` instead |
| `pip install` hangs on `grpcio` | C compiler missing | Install Visual Studio Build Tools (Windows) or `build-essential` (Linux) |
| `MONGODB_URI not set` | Missing `.env` file | Create `.env` in project root with correct values |
| `ANTHROPIC_API_KEY not set` | Missing `.env` key | Add `ANTHROPIC_API_KEY=sk-ant-...` to `.env` |
| `OPENAI_API_KEY not set` | Missing `.env` key | Add `OPENAI_API_KEY=sk-...` to `.env` |
| Port 5000 already in use | Another process | `netstat -ano \| findstr :5000` (Windows) to find and kill it |
| Port 8080 already in use | Another process | Change port: `python -m http.server 8081` |
| API calls return 501 | Calling API on wrong port | All `/api/` calls must go to port **5000**, not 8080 |
| `Cannot connect to Ollama` | Ollama not running | Run `ollama serve` and confirm it's on port 11434 |
| Chat says no articles found | Vector index missing | Create the Atlas Vector Search index (see above) |
| Network Access denied (Atlas) | IP not whitelisted | Add your server IP in Atlas → Security → Network Access |
| `ModuleNotFoundError` on start | venv not activated | Run `.venv\Scripts\activate` before starting servers |

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `MONGODB_URI` | Yes | MongoDB Atlas connection string |
| `ANTHROPIC_API_KEY` | Yes | Claude API key — [console.anthropic.com](https://console.anthropic.com) |
| `OPENAI_API_KEY` | Yes | OpenAI key for embeddings — [platform.openai.com](https://platform.openai.com) |

---

## Project Structure

```
article_getter_done/
├── api_server.py               # Flask API server (port 5000) — all backend logic
├── fcat_db.py                  # MongoDB Atlas client & search functions
├── claude_rewriter.py          # Claude brand neutralization
├── embedding_service.py        # OpenAI text-embedding-3-small
├── article_generator.py        # RAG pipeline (ChromaDB + Ollama)
├── profiling_service.py        # Adaptive user profiling (Money Buddy)
├── jargon_detector.py          # Financial jargon tier detection
├── military_context.py         # Military persona context
├── Requirements.txt            # Unpinned direct dependencies
├── requirements-pinned.txt     # Exact pinned versions (use this for fresh installs)
├── .env                        # API keys — create this, never commit it
├── index.html                  # Dashboard / hub
├── article-extractor.html      # Step 1 — Extract from URL
├── article-rewriter.html       # Step 2 — Brand neutralize
├── article-diff.html           # Step 3 — Diff viewer
├── article-editor.html         # Step 4 — Word editor
├── chat.html                   # Money Buddy DB-grounded chat
├── article-search.html         # FCAT article search tool
├── article-generator.html      # RAG article generator (Ollama)
├── enhanced-persona-finder.html
├── shared.css                  # Design system (neumorphic theme)
├── article_generator_db/       # ChromaDB store (auto-created)
└── uploaded_articles/          # Temp uploads (auto-created)
```

---

## Created by

Jim Janeteas, Luke Paxton & Matt Ledoux — Started November 2025
