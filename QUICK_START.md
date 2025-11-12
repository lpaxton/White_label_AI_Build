# 🚀 Quick Start Guide - Fidelity Article Scraper & Persona Finder

## What You Have

You now have **4 different tools** to extract and analyze articles from Fidelity's Learning Center:

### 1. 🐍 Python Scraper (RECOMMENDED)
**File:** `fidelity_scraper.py`

**Best for:**
- ✅ Actual article extraction from live pages
- ✅ No CORS issues
- ✅ Structured data (JSON + CSV)
- ✅ Handles 51 category pages automatically

**How to use:**
```bash
# Install dependencies
pip install requests beautifulsoup4 lxml

# Run the scraper
python fidelity_scraper.py
```

**Output:**
- Full JSON with all metadata
- Flat JSON list of articles
- CSV file for Excel/Sheets

---

### 2. � Persona-Based Article Finder (NEW!)
**Files:** `persona-article-finder.html` & `persona_finder.py`

**Best for:**
- ✅ Finding articles for specific user personas
- ✅ AI-powered relevance matching
- ✅ Both web interface and command-line
- ✅ Detailed explanations for recommendations

**How to use:**

**Web Interface:**
1. Setup Ollama: `ollama serve`
2. Open `persona-article-finder.html`
3. Upload your scraped JSON file
4. Describe your persona
5. Get AI recommendations

**Command Line:**
```bash
# Setup Ollama first
ollama pull llama3.2
ollama serve

# Find articles for a persona
python persona_finder.py articles.json "25-year-old recent graduate with student loans, new to budgeting"
```

**Output:**
- Relevance-scored article recommendations
- Detailed explanations for each match
- Optional JSON export

---

### 3. �🌐 Web Scraper (Browser-based)
**File:** `fidelity-article-scraper.html`

**Best for:**
- Users who prefer browser tools
- Visual progress monitoring
- Ollama integration for AI analysis

**How to use:**
1. Open HTML file in browser
2. Configure Ollama URL
3. Click "Start Scraping"

**Limitations:**
- CORS issues may occur
- Requires CORS proxy

---

### 4. 🤖 Simple AI Analyzer
**File:** `fidelity-article-scraper-simple.html`

**Best for:**
- Quick analysis without scraping
- No CORS issues
- AI-powered content prediction

**How to use:**
1. Start Ollama: `ollama serve`
2. Open HTML file in browser
3. Click "Start Analysis"

**Note:** Predicts content based on URL structure, doesn't fetch actual pages

---

## 📊 Expected Results

The Python scraper should find approximately:
- **450-600 total articles** across all 51 pages
- Categories: Personal Finance, Life Events, Investing, Trading, etc.
- Content types: Articles, Videos, Podcasts
- Reading times: 3-15 minutes typically

---

## 🎯 Recommended Workflow

**For Complete Article List + Persona Matching:**
```bash
# Step 1: Scrape all articles
python fidelity_scraper.py

# Step 2: Find relevant articles for your persona
python persona_finder.py fidelity_articles_flat_*.json "Your persona description here"

# Step 3: Review results and click through to articles
```

**For Quick Web-Based Analysis:**
```bash
# Step 1: Setup Ollama
ollama serve

# Step 2: Open persona-article-finder.html in browser
# Step 3: Upload JSON file and enter persona
```

---

## 📁 Files Included

```
fidelity_scraper.py               - Main Python scraper
persona_finder.py                 - AI-powered persona matcher (CLI)
persona-article-finder.html       - Persona finder web interface
requirements.txt                  - Python dependencies
README.md                         - Full documentation
PERSONA_FINDER_GUIDE.md          - Detailed persona finder guide
fidelity-article-scraper.html     - Web tool (advanced)
fidelity-article-scraper-simple.html - Web tool (simple)
fidelity_learning_center_urls.txt - List of all URLs
```

---

## 💡 Pro Tips

1. **Python scraper is most reliable** - use this for production
2. **Run during off-peak hours** to be respectful
3. **Save results immediately** - files are timestamped
4. **Check CSV first** for quick overview
5. **Use Ollama separately** to analyze results after scraping

---

## 🆘 Need Help?

**Python Scraper Issues:**
- Ensure `requests` and `beautifulsoup4` are installed
- Check your internet connection
- Verify URLs are still valid

**Browser Tool Issues:**
- CORS errors: Try the simple version
- Ollama not connecting: Check `http://localhost:11434`

**Questions about output:**
- See README.md for detailed format documentation
- CSV files can be opened in Excel/Google Sheets

---

## ⚡ Quick Test

Test the Python scraper on just one URL:

```python
python3 -c "
from fidelity_scraper import scrape_url
import requests

session = requests.Session()
result = scrape_url('https://www.fidelity.com/learning-center/smart-money', session)
print(f'Found {result.get(\"total_articles\", 0)} articles')
"
```

---

Happy scraping! 🎉
