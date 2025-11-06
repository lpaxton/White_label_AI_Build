# White Label AI Build - Persona-Based Content Selector

An AI-powered content curation system that selects personalized content from XML files based on user personas. Supports multiple LLM providers: OpenAI, Anthropic Claude, and Ollama (local).

## Features

- 🎯 **Persona-Based Selection**: Describe a user type or persona in free text, and the AI will recommend relevant content
- 🤖 **Multiple LLM Support**: Choose from OpenAI, Anthropic Claude, or run locally with Ollama
- 📄 **XML Content Library**: Easy-to-manage content in structured XML format
- 💬 **Interactive Mode**: Enter multiple personas and get instant recommendations
- ⚡ **Single Query Mode**: Get quick results for a single persona description

## Installation

1. Clone the repository:
```bash
git clone https://github.com/lpaxton/White_label_AI_Build.git
cd White_label_AI_Build
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your API keys (for OpenAI or Anthropic):
```bash
cp .env.example .env
# Edit .env and add your API keys
```

## Quick Start

### Using OpenAI

```bash
# Interactive mode
python main.py --provider openai --xml-file sample_content.xml

# Single query
python main.py --provider openai --persona "A new manager wanting to learn leadership skills" --xml-file sample_content.xml
```

### Using Anthropic Claude

```bash
# Interactive mode
python main.py --provider anthropic --xml-file sample_content.xml

# Single query with custom model
python main.py --provider anthropic --model claude-3-opus-20240229 --persona "Data scientist learning advanced ML" --xml-file sample_content.xml
```

### Using Ollama (Local)

First, make sure Ollama is installed and running on your local machine:
```bash
# Install Ollama from https://ollama.ai
# Pull a model (e.g., llama2)
ollama pull llama2

# Run the content selector
python main.py --provider ollama --model llama2 --xml-file sample_content.xml
```

## Usage Examples

### Example 1: Tech Professional
```bash
python main.py --provider openai --persona "Senior software engineer transitioning into DevOps role" --xml-file sample_content.xml
```

### Example 2: Business Leader
```bash
python main.py --provider anthropic --persona "VP of Sales wanting to understand data-driven decision making" --xml-file sample_content.xml
```

### Example 3: Career Starter
```bash
python main.py --provider ollama --persona "Recent college graduate starting career in customer service" --xml-file sample_content.xml
```

## XML Content Format

The content XML file should follow this structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<content_library>
    <content id="1">
        <title>Content Title</title>
        <description>Detailed description of the content</description>
        <category>Category Name</category>
        <difficulty>Beginner|Intermediate|Advanced</difficulty>
        <tags>tag1, tag2, tag3</tags>
        <duration>Time required</duration>
    </content>
    <!-- More content items -->
</content_library>
```

A sample XML file (`sample_content.xml`) is included with 12 diverse content items.

## Command-Line Options

```
--provider          LLM provider: openai, anthropic, or ollama (required)
--xml-file          Path to XML content file (default: sample_content.xml)
--persona           Persona description for single query mode
--max-items         Maximum content items to select (default: 5)
--api-key           API key for OpenAI/Anthropic (or use env vars)
--model             Specific model name to use
--ollama-host       Ollama server host (default: http://localhost:11434)
```

## How It Works

1. **XML Parsing**: The system parses your XML content library
2. **Persona Analysis**: Your persona description is analyzed by the selected LLM
3. **Content Matching**: The AI matches content based on:
   - Role and responsibilities
   - Experience level
   - Learning goals
   - Skills and interests
4. **Recommendations**: Returns top matching content with reasoning

## Architecture

```
main.py              - CLI application entry point
content_selector.py  - Core logic for persona-based selection
llm_providers.py     - LLM provider abstractions (OpenAI, Anthropic, Ollama)
xml_parser.py        - XML content parsing
sample_content.xml   - Sample content library
```

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key
- `ANTHROPIC_API_KEY`: Your Anthropic API key

## Requirements

- Python 3.7+
- openai >= 1.0.0
- anthropic >= 0.25.0
- ollama >= 0.1.0
- python-dotenv >= 1.0.0

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

## License

This project is open source and available under the MIT License.

## Use Cases

- **Corporate Training**: Personalize learning paths for different roles
- **Educational Platforms**: Match courses to student profiles
- **Content Platforms**: Recommend articles/videos based on user type
- **Onboarding**: Tailor resources for new employees by department/role

## Troubleshooting

### OpenAI/Anthropic API Errors
- Ensure your API key is correctly set in `.env` or passed via `--api-key`
- Check your API quota and billing status

### Ollama Connection Issues
- Verify Ollama is running: `ollama list`
- Check the host/port settings with `--ollama-host`
- Ensure the model is downloaded: `ollama pull <model-name>`

## Future Enhancements

- Web UI interface
- Support for additional LLM providers
- Content rating and feedback system
- Multiple XML file support
- Export recommendations to various formats