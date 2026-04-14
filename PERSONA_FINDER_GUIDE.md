# Persona-Based Article Finder

## Overview

The Persona-Based Article Finder helps you discover the most relevant Fidelity Learning Center articles for specific user personas using AI analysis. This tool analyzes article content and matches it to detailed persona descriptions, providing relevance scores and explanations.

## Features

- **AI-Powered Matching**: Uses Ollama LLMs to analyze article relevance
- **Flexible Persona Input**: Supports detailed persona descriptions
- **Relevance Scoring**: Each recommendation includes a 1-100 relevance score
- **Multiple Interfaces**: Both web UI and command-line versions available
- **Detailed Explanations**: AI provides reasoning for each recommendation

## Getting Started

### Prerequisites

1. **Ollama Installation**: Install and run Ollama locally
   ```bash
   # Install Ollama (visit https://ollama.ai for instructions)
   ollama pull llama3.2  # or your preferred model
   ollama serve
   ```

2. **Articles Data**: You need a JSON file with scraped Fidelity articles
   - Use `fidelity_scraper.py` to generate this file
   - Or use the existing `fidelity_articles_flat_*.json` file

### Web Interface

1. Open `persona-article-finder.html` in your browser
2. Upload your JSON articles file
3. Configure Ollama settings (URL and model)
4. Describe your target persona
5. Click "Find Best Articles"

### Command Line Interface

```bash
python persona_finder.py <json_file> "<persona_description>" [options]
```

#### Examples

```bash
# Basic usage
python persona_finder.py fidelity_articles_flat_20251106_154850.json "25-year-old recent college graduate, starting first job, wants to learn about budgeting and saving for the future, has student loans, tech-savvy but financially inexperienced"

# With custom settings
python persona_finder.py articles.json "Mid-career professional planning for retirement" --max-results 15 --model llama3.1 --output results.json

# Using different Ollama server
python persona_finder.py articles.json "Small business owner with irregular income" --ollama-url http://192.168.1.100:11434
```

#### Command Line Options

- `--max-results`: Number of articles to return (default: 10)
- `--ollama-url`: Ollama server URL (default: http://localhost:11434)
- `--model`: Ollama model to use (default: llama3.2)
- `--output`: Save results to JSON file

## Persona Examples

### New Graduate
```
25-year-old recent college graduate, starting first job at a tech company, 
$50k salary, has $30k in student loans, wants to learn about budgeting, 
building credit, and saving for the future. Tech-savvy but financially 
inexperienced. Lives in a high-cost city, rents an apartment.
```

### Mid-Career Professional
```
35-year-old marketing manager, married with one child, household income 
$120k, owns a home, wants to optimize investments for retirement and 
college savings. Some investment experience but wants to learn more 
about advanced strategies and tax optimization.
```

### Pre-Retiree
```
55-year-old senior executive, high earner ($200k+), 10 years from 
retirement, substantial 401k but concerned about healthcare costs 
and wealth preservation. Wants strategies for retirement income 
planning and estate planning.
```

### Small Business Owner
```
42-year-old restaurant owner, irregular income, needs both business 
and personal finance strategies. Concerns include cash flow management, 
business insurance, and retirement planning for self-employed individuals.
```

## How It Works

1. **Article Analysis**: The AI analyzes each article's title and description
2. **Persona Matching**: Compares article content against the provided persona
3. **Relevance Scoring**: Assigns scores based on how well articles match persona needs
4. **Ranking**: Returns the highest-scoring articles with explanations

## Supported Models

The tool works with any Ollama model, but these are recommended:

- **llama3.2**: Good balance of speed and accuracy (default)
- **llama3.1**: More detailed analysis, slightly slower
- **mistral**: Fast and efficient
- **phi3**: Lightweight option for lower-end hardware

## Output Format

### Web Interface
- Interactive cards with article titles, descriptions, and relevance scores
- Click-through links to original articles
- Visual relevance indicators

### Command Line
- Formatted text output with all article details
- Optional JSON export for further processing

### JSON Output Structure
```json
{
  "persona": "Persona description",
  "timestamp": "2024-11-06 15:48:50",
  "total_recommendations": 10,
  "recommendations": [
    {
      "title": "Article Title",
      "url": "https://...",
      "description": "Article description",
      "relevance_score": 95,
      "explanation": "Why this article is relevant"
    }
  ]
}
```

## Tips for Better Results

1. **Detailed Personas**: Include age, income, financial goals, experience level, and specific concerns
2. **Model Selection**: Use larger models (llama3.1) for more nuanced analysis
3. **Article Quality**: Ensure your JSON file has good article descriptions
4. **Ollama Performance**: Use models that fit your hardware capabilities

## Troubleshooting

### Ollama Connection Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve
```

### Model Not Found
```bash
# Pull the required model
ollama pull llama3.2
```

### JSON File Issues
- Ensure the JSON file is valid
- Check that articles have 'title' and 'url' fields
- Descriptions are helpful but optional

### AI Response Issues
- Try a different model if getting parsing errors
- Reduce the number of articles being analyzed
- Check Ollama logs for errors

## Integration Examples

### Use in Workflows
```bash
# Generate recommendations for multiple personas
for persona in "new_graduate" "mid_career" "pre_retiree"; do
    python persona_finder.py articles.json "$persona" --output "${persona}_recommendations.json"
done
```

### API Integration
The Python script can be imported and used programmatically:

```python
from persona_finder import PersonaArticleFinder

finder = PersonaArticleFinder()
articles = finder.load_articles('articles.json')
recommendations = finder.analyze_articles_with_ai('your persona', articles)
```

## Performance Notes

- **Token Limits**: Large article sets are automatically truncated to fit model context windows
- **Processing Time**: Depends on model size and article count (typically 30-60 seconds)
- **Memory Usage**: Ensure sufficient RAM for your chosen model

## Future Enhancements

- Support for multiple persona analysis in one run
- Integration with article content scraping for deeper analysis
- Batch processing capabilities
- Performance optimizations for large datasets