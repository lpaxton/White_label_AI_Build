# Fidelity Learning Center Article Scraper & Persona Finder

A comprehensive toolkit for scraping Fidelity Learning Center articles and finding the most relevant content for specific user personas using AI.

## 🎯 What It Does

This toolkit includes:

### 📊 Article Scraper
- ✅ Visits all 51 Fidelity Learning Center category pages
- ✅ Extracts article cards from each page including:
  - Title
  - URL
  - Description
  - Article type (Article/Video/Podcast)
  - Reading time
  - Images
- ✅ Exports results in multiple formats (JSON, CSV)
- ✅ Provides detailed progress logging
- ✅ Respects rate limits (2-second delay between requests)

### 🎯 Persona-Based Article Finder (NEW!)
- ✅ AI-powered article matching using Ollama
- ✅ Detailed persona descriptions supported
- ✅ Relevance scoring (1-100) with explanations
- ✅ Both web interface and command-line tools
- ✅ Multiple LLM models supported

## 📦 Installation

python -m venv venv

venv\Scripts\activate

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Install and setup Ollama (for Persona Finder):**
```bash
# Visit https://ollama.ai for installation instructions
ollama pull llama3.2  # or your preferred model
ollama serve
```

## 🚀 Quick Start

### Step 1: Scrape Articles
```bash
python fidelity_scraper.py
```

### Step 2: Find Articles for Your Persona

**Web Interface:**
1. Open `persona-article-finder.html` in your browser
2. Upload the generated JSON file
3. Describe your persona
4. Get AI-powered recommendations

**Command Line:**
```bash
python persona_finder.py fidelity_articles_flat_20251106_154850.json "25-year-old recent college graduate, starting first job, wants to learn about budgeting and saving for the future"
```

## 🎯 Persona Finder Features

### Supported Persona Examples
- **New Graduate**: Recent college grad with student loans, needs budgeting basics
- **Mid-Career Professional**: Stable income, wants investment advice, planning major purchases
- **Pre-Retiree**: High earner focused on retirement planning and wealth preservation
- **Small Business Owner**: Irregular income, needs business and personal finance strategies

### AI Models Supported
- llama3.2 (recommended)
- llama3.1
- mistral
- phi3
- Any Ollama-compatible model

### Output Formats
- Interactive web interface with clickable results
- Formatted command-line output
- JSON export for integration with other tools

## 📦 Installation

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install requests beautifulsoup4 lxml
```

## 🚀 Usage

### Basic Usage

Simply run the script:
```bash
python fidelity_scraper.py
```

### What You'll Get

The script creates 3 files:

1. **`fidelity_articles_[timestamp].json`** - Full results with all metadata
2. **`fidelity_articles_flat_[timestamp].json`** - Flat list of all articles
3. **`fidelity_articles_[timestamp].csv`** - CSV export for easy viewing

## 📊 Output Format

### JSON Structure (Full Results)
```json
[
  {
    "url": "https://www.fidelity.com/learning-center/personal-finance/saving-and-budgeting-money",
    "success": true,
    "articles": [
      {
        "title": "What is financial literacy?",
        "url": "https://www.fidelity.com/learning-center/smart-money/financial-literacy",
        "description": "And why is financial literacy important?",
        "image": "https://www.fidelity.com/bin-public/...",
        "metadata": {
          "type": "Article",
          "duration": "8 min"
        }
      }
    ],
    "total_articles": 15,
    "all_links_found": 45,
    "scraped_at": "2024-01-15T10:30:00"
  }
]
```

### CSV Columns
- `title` - Article title
- `url` - Direct link to article
- `description` - Article description
- `type` - Content type (Article/Video/Podcast)
- `duration` - Reading/viewing time
- `source_page` - Category page where found

## 🔧 Advanced Usage

### Modify URLs to Scrape

Edit the `FIDELITY_URLS` list in the script to add/remove pages:

```python
FIDELITY_URLS = [
    "https://www.fidelity.com/learning-center/personal-finance/saving-and-budgeting-money",
    # Add more URLs here...
]
```

### Adjust Rate Limiting

Change the delay between requests (line ~220):

```python
time.sleep(2)  # Change to desired seconds
```

### Custom Headers

Modify the `get_headers()` function to change User-Agent or other headers.

## 📝 Example Output

```
================================================================================
FIDELITY LEARNING CENTER ARTICLE SCRAPER
================================================================================
Total URLs to scrape: 51
Started at: 2024-01-15 10:30:00
================================================================================

Progress: 1/51

================================================================================
Scraping: https://www.fidelity.com/learning-center/personal-finance/saving-and-budgeting-money
================================================================================
  Found 15 article cards
    ✓ What is financial literacy?
    ✓ How to create a budget
    ✓ Emergency fund: How much to save
    ...

================================================================================
SCRAPING COMPLETE
================================================================================
Total URLs processed: 51
Successful: 50
Failed: 1
Total articles found: 450
Results saved to: fidelity_articles_20240115_103045.json
Flat article list saved to: fidelity_articles_flat_20240115_103045.json
CSV export saved to: fidelity_articles_20240115_103045.csv
================================================================================
```

## 🔍 Troubleshooting

### No articles found
- Check if Fidelity's HTML structure has changed
- Verify the URL is accessible
- Check for bot detection (add delays between requests)

### Connection errors
- Check your internet connection
- Verify the URLs are correct
- Try adding a longer delay between requests

### Import errors
- Make sure all dependencies are installed: `pip install -r requirements.txt`

## 🤖 Using with Ollama

### Persona-Based Article Finding
Use the new persona finder to get personalized article recommendations:

```bash
# Find articles for a new graduate
python persona_finder.py articles.json "Recent college graduate with student loans, new to budgeting" --max-results 10

# Save results to file
python persona_finder.py articles.json "Mid-career professional planning retirement" --output recommendations.json
```

### Custom Analysis
For custom analysis of scraped articles:

```python
import json
import requests

# Load scraped articles
with open('fidelity_articles_flat_20240115_103045.json') as f:
    articles = json.load(f)

# Analyze with Ollama
for article in articles[:5]:  # First 5 articles
    prompt = f"Analyze this article: {article['title']}\nDescription: {article['description']}"
    
    response = requests.post('http://localhost:11434/api/generate', json={
        'model': 'llama2',
        'prompt': prompt,
        'stream': False
    })
    
    print(f"\n{article['title']}")
    print(response.json()['response'])
```

## 📚 Categories Covered

The scraper covers these main categories:
- Financial Essentials (10 pages)
- Life Events (14 pages)
- Investing and Trading (8 pages)
- Investment Products (6 pages)
- Advanced Trading (7 pages)
- Content Hubs (6 pages)

## ⚠️ Important Notes

- **Be Respectful**: The script includes delays to avoid overwhelming the server
- **Terms of Service**: Make sure your use complies with Fidelity's terms of service
- **Rate Limiting**: If you get blocked, increase the delay between requests
- **Dynamic Content**: Some content may be loaded via JavaScript and not captured

## 📄 License

This is a utility script for educational purposes. Please respect Fidelity's terms of service and robots.txt when using this tool.

## 🤝 Contributing

Feel free to improve the script:
- Better error handling
- Support for JavaScript-rendered content
- Additional export formats
- Enhanced article metadata extraction

## 💡 Tips

1. **Run during off-peak hours** to be more respectful of server resources
2. **Save results regularly** - the script creates timestamped files
3. **Check CSV output first** for a quick overview before diving into JSON
4. **Combine with web_fetch** if you need full article content
