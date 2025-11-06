# Persona-Based Content Selector

Persona-Based Content Selector is a financial-literacy-focused application that uses large language models (LLMs) to recommend education experiences from XML libraries based on persona descriptions. The project supports OpenAI, Anthropic Claude, and locally hosted Ollama models, and now includes a lightweight web service with a browser-based interface so organizations can integrate or explore recommendations without touching the command line.

## Key Features

- **XML Content Management** – Parse structured XML files that contain titles, descriptions, categories, difficulty, tags, and durations.
- **Multi-Provider LLM Support** – Integrations for OpenAI, Anthropic Claude, and Ollama providers through a clean provider abstraction layer.
- **Persona-Based Selection** – Free-text persona descriptions are analyzed by the LLM to return the most relevant content items with reasoning.
- **Flexible User Experience** – Choose between interactive multi-persona conversations, single-query CLI execution, or the hosted browser UI.
- **JSON API Delivery** – Serve recommendations and content catalogs through REST endpoints suitable for organizational integration.
- **Robust Tooling** – Rich error handling, comprehensive documentation, unit tests (including REST coverage), and a demo script with a mock LLM provider.

## Project Layout

```
├── .env.example            # Environment variable template
├── content_selector.py     # Core persona-to-content matching logic
├── demo.py                 # Mock-driven interactive demonstration
├── llm_providers.py        # Provider abstraction and integrations
├── main.py                 # CLI entry point
├── requirements.txt        # Python dependencies
├── web_service.py          # Lightweight web app and browser UI
├── sample_content.xml      # Example XML content library
├── test_basic.py           # Unit tests and CLI validation
├── test_api.py             # API and web UI tests
├── USAGE.md                # Deep-dive usage guide
├── xml_parser.py           # XML parsing utilities
└── README.md               # Project overview
```

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/persona-content-selector.git
cd persona-content-selector
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Keys

Copy `.env.example` to `.env` and populate the necessary API keys. Supported environment variables include:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `API_KEY` (optional convenience variable used by the CLI)

Use `python-dotenv` or your preferred secrets manager to load credentials before executing the CLI.

### 5. Load Sample Content

The repository ships with `sample_content.xml`, containing 12 sample learning items across diverse categories. You can replace this file with your own content library by following the same XML structure.

## Running the CLI

### Single Query Mode

Pass the persona directly as an argument:

```bash
python main.py --provider openai \
  --model gpt-3.5-turbo \
  --persona "Program director launching a financial empowerment initiative" \
  --xml-file sample_content.xml
```

### Interactive Mode

Launch an interactive shell for multiple personas:

```bash
python main.py --provider anthropic --xml-file sample_content.xml --interactive
```

Sample session:

```
Interactive persona mode. Type 'exit' to quit.

> Marketing manager needing data skills
Persona: Marketing manager needing data skills
Recommendations:
  1. Marketing Analytics with SQL (score: 0.85)
     Reason: Aligns with data-driven marketing objectives.
```

### Ollama Local Usage

If you have [Ollama](https://ollama.com/) running locally:

```bash
python main.py --provider ollama \
  --model llama2 \
  --persona "Community educator teaching first-time homebuyers" \
  --xml-file sample_content.xml
```

## Serving the API and Web UI

Run the bundled web server to access both JSON endpoints and a browser-based interface:

```bash
python web_service.py
```

The command starts a WSGI server on `http://127.0.0.1:8000`. Use `python -m web_service` or call `web_service.serve(host, port)` from your own launcher to customise deployment.

Key routes:

- `GET /` – Minimal UI for entering persona descriptions and reviewing responses.
- `POST /api/recommendations` – Returns structured JSON recommendations. Example payload: `{ "persona": "Budget owner", "top_n": 3 }`.
- `GET /api/content` – Lists all parsed financial literacy resources from the XML library.

Environment variables tune the deployment:

- `LLM_PROVIDER`, `LLM_MODEL`, `API_KEY` – Choose provider credentials.
- `CONTENT_XML_FILE` – Replace the default XML library.
- `DEFAULT_TOP_N`, `DEFAULT_SYSTEM_PROMPT` – Adjust the default recommendation count and financial literacy framing.

## XML Content Format

Each `<item>` entry requires at least a `<title>` and `<description>`. Optional elements include `<category>`, `<difficulty>`, `<duration>`, and `<tags>` with nested `<tag>` values. Additional metadata blocks may be added under a `<metadata>` element if needed.

```xml
<content>
  <item>
    <title>Budget Foundations Workshop</title>
    <description>Interactive session covering zero-based budgeting, expense tracking, and communicating budget variances.</description>
    <category>Budgeting</category>
    <difficulty>Beginner</difficulty>
    <duration>2 hours</duration>
    <tags>
      <tag>cash flow</tag>
      <tag>expense management</tag>
    </tags>
  </item>
</content>
```

## Testing

Run the unit tests using `pytest`:

```bash
pytest
```

The suite validates XML parsing, content selection logic, REST API responses, and a CLI smoke test using a mock LLM provider.

## Demo Script

For quick experimentation without calling external APIs, run the demo script:

```bash
python demo.py
```

The demo uses a mock provider that scores content items based on keyword overlap with persona descriptions, showcasing the selection pipeline end-to-end.

## Extending the Project

- **Additional Providers:** Implement new provider classes by following the `LLMProvider` protocol in `llm_providers.py`.
- **Custom Output Formats:** Modify `ContentSelector` to produce alternative representations (JSON, CSV, or HTML reports).
- **Persona Templates:** Integrate persona templates or import/export capabilities to streamline organizational usage.
- **Feedback Loop:** Capture user feedback on recommendations to fine-tune scoring or prompt strategies over time.

## Troubleshooting

- **Missing Dependencies:** Ensure all libraries in `requirements.txt` are installed in your environment.
- **Authentication Errors:** Double-check that API keys are loaded into the environment before running the CLI.
- **Invalid XML:** Use the `xml_parser.XMLContentError` messages to debug malformed XML structures.
- **Empty Responses:** The CLI surfaces the raw provider response when parsing fails, enabling manual inspection of output.

## License

This project is provided as-is for demonstration purposes. Integrate into your own organization’s workflows and adjust licensing accordingly.

## Acknowledgements

- OpenAI, Anthropic, and Ollama teams for providing powerful LLM APIs
- Early reviewers for feedback on prompt engineering and API ergonomics
- Community testers who validated persona scenarios and documentation clarity
