# Quick Start Guide

## Installation (2 minutes)

```bash
# 1. Clone the repository
git clone https://github.com/lpaxton/White_label_AI_Build.git
cd White_label_AI_Build

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up API key (choose one)
export OPENAI_API_KEY="your-key-here"
# OR
export ANTHROPIC_API_KEY="your-key-here"
# OR install Ollama locally (no key needed)
```

## Run Your First Query (30 seconds)

### Using OpenAI
```bash
python main.py --provider openai \
  --persona "Junior developer learning cloud computing" \
  --xml-file sample_content.xml
```

### Using Anthropic Claude
```bash
python main.py --provider anthropic \
  --persona "Marketing manager wanting data skills" \
  --xml-file sample_content.xml
```

### Using Ollama (Local)
```bash
# First, install and run Ollama from https://ollama.ai
ollama pull llama2

python main.py --provider ollama \
  --persona "New manager needing leadership skills" \
  --xml-file sample_content.xml
```

## Interactive Mode

For exploring multiple personas:

```bash
python main.py --provider openai --xml-file sample_content.xml
```

Then enter personas one at a time:
```
> Senior software engineer transitioning to DevOps
> Customer service rep wanting technical skills
> exit
```

## What You Get

Each query returns:
1. **Selected Content** - Personalized recommendations
2. **AI Reasoning** - Why each item was selected
3. **Full Details** - Title, category, difficulty, duration, tags

## Next Steps

1. **Customize Content**: Edit `sample_content.xml` with your content
2. **Try Different Personas**: Experiment with various user descriptions
3. **Adjust Settings**: Use `--max-items` to control result count
4. **Read Docs**: See `README.md` and `USAGE.md` for more details

## Example Output

```
======================================================================
SELECTED CONTENT (3 items):
======================================================================

1. Leadership Essentials
   Category: Management | Difficulty: Intermediate
   Duration: 1 hour
   Description: Develop key leadership skills...
   Tags: leadership, management, soft-skills

[... more items ...]

AI REASONING:
Leadership Essentials is perfect for someone stepping into management...
```

## Troubleshooting

**API Key Error**: Make sure your API key is set correctly
```bash
echo $OPENAI_API_KEY  # Should show your key
```

**Module Not Found**: Install dependencies
```bash
pip install -r requirements.txt
```

**Ollama Connection**: Verify Ollama is running
```bash
ollama list  # Should show installed models
```

## Support

- 📖 Full docs: `README.md`
- 📝 Usage examples: `USAGE.md`
- 📊 Project details: `PROJECT_SUMMARY.md`
- 🧪 Run tests: `python test_basic.py`
- 🎬 Run demo: `python demo.py`
