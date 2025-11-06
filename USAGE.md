# Usage Guide

This document expands on the quick-start material in the README by detailing configuration, persona design strategies, and advanced workflows for the Persona-Based Content Selector.

## Table of Contents

1. [Overview](#overview)
2. [Persona Design Tips](#persona-design-tips)
3. [Command-Line Options](#command-line-options)
4. [Web Service & API](#web-service--api)
5. [Environment Configuration](#environment-configuration)
6. [Using Custom XML Libraries](#using-custom-xml-libraries)
7. [Working with Different Providers](#working-with-different-providers)
8. [Advanced Prompt Customization](#advanced-prompt-customization)
9. [Interpreting Results](#interpreting-results)
10. [Example Scenarios](#example-scenarios)
11. [Troubleshooting](#troubleshooting)
12. [FAQ](#faq)
13. [Changelog](#changelog)

---

## Overview

The Persona-Based Content Selector ingests an XML content library, prompts a large language model with persona descriptions, and returns the most relevant learning items. Its architecture separates concerns into modular components:

- **XML Parser** – Responsible for loading and validating XML content.
- **Content Selector** – Builds prompts, communicates with the LLM, and parses responses.
- **LLM Providers** – Adapter implementations for OpenAI, Anthropic, and Ollama services.
- **CLI Interface** – Exposes the functionality in both single-shot and interactive modes.
- **Web Service** – Delivers a JSON API and browser UI for organizational consumption.

The system is designed for easy extension: add new providers by implementing the `LLMProvider` protocol, integrate additional metadata by extending the `ContentItem` dataclass, or build a web UI that leverages the existing selection logic.

## Persona Design Tips

Well-crafted personas lead to higher-quality recommendations. Consider the following guidelines:

1. **Contextualize the Role** – Mention the persona’s job title, industry, and responsibilities.
2. **Highlight Goals** – Specify learning outcomes or challenges the persona is trying to address.
3. **Describe Experience Level** – Indicate whether the persona is a beginner, intermediate, or advanced learner.
4. **Capture Preferences** – Share stylistic preferences such as “prefers hands-on labs” or “needs executive summaries”.
5. **Include Constraints** – Add time availability, required certifications, or technology stacks when relevant.

### Persona Template

```
{Name} is a {role} working in {industry}. They have {experience level} experience with {topic}. Their goal is to {objective}. They prefer {content format} and want to avoid {avoidance}. They can dedicate {time commitment} per week to learning.
```

### Example Persona

```
Jordan is a community lending manager working at a nonprofit credit union. They have foundational experience with cash-flow analysis and want to strengthen their ability to coach clients on debt reduction and savings strategies. They prefer workshops with actionable worksheets and want to avoid abstract theory. They can dedicate three hours per week to professional development.
```

## Command-Line Options

The CLI exposes several flags to tailor the selection process:

| Flag | Description | Default |
| ---- | ----------- | ------- |
| `--provider` | Provider name (`openai`, `anthropic`, `ollama`) | Required |
| `--model` | Specific model identifier for the provider | Provider default |
| `--xml-file` | Path to the XML content file | `sample_content.xml` |
| `--persona` | Persona description for single-run mode | None |
| `--top-n` | Number of recommendations to request | `3` |
| `--temperature` | Sampling temperature passed to the provider | `0.2` |
| `--max-tokens` | Maximum tokens for model responses | `1024` |
| `--interactive` | Start interactive prompt mode | `False` |
| `--system-prompt` | Override the default system prompt | See README |

### Examples

Retrieve five items with a warmer temperature:

```bash
python main.py --provider openai --model gpt-4 --top-n 5 --temperature 0.6 --persona "Customer success manager scaling onboarding" --xml-file sample_content.xml
```

Run interactively with Anthropic Claude:

```bash
python main.py --provider anthropic --interactive --xml-file sample_content.xml
```

Use a local Ollama model with a custom system prompt:

```bash
python main.py --provider ollama --model mistral --system-prompt "You are a pragmatic financial literacy coach." --persona "Operations director improving cash-flow visibility" --xml-file sample_content.xml
```

## Web Service & API

In addition to the CLI, the project provides a lightweight WSGI application (`web_service.py`) that powers a JSON API and browser interface.

### Starting the Server

```bash
python web_service.py
```

The command starts a development server on `http://127.0.0.1:8000`. Use `python -m web_service` or call `web_service.serve(host, port)` within your own runner to customise deployment settings.

### Endpoints

| Method & Path | Description | Sample Use |
| ------------- | ----------- | ----------- |
| `GET /` | Serves a lightweight UI for entering personas and viewing results. | Visit in a browser for manual exploration. |
| `POST /api/recommendations` | Returns financial literacy recommendations in JSON. | `curl -X POST http://127.0.0.1:8000/api/recommendations -d '{"persona":"HR director launching an employee money program"}' -H 'Content-Type: application/json'` |
| `GET /api/content` | Lists the parsed XML content items for auditing or caching. | `curl http://127.0.0.1:8000/api/content` |

### Configuration

Environment variables influence runtime behavior:

- `LLM_PROVIDER`, `LLM_MODEL`, `API_KEY` – Provider selection and credentials. Fall back to the CLI defaults when unset.
- `CONTENT_XML_FILE` – Path to an alternate XML library; defaults to `sample_content.xml`.
- `DEFAULT_TOP_N` – Default number of items returned when the request omits `top_n`.
- `DEFAULT_SYSTEM_PROMPT` – Financial literacy framing passed to the LLM when no override is provided.

### Embedding the API

To integrate with existing platforms, call the `POST /api/recommendations` endpoint from your application server and surface the returned `recommendations` array in your UI. Pair the response with the `GET /api/content` output to display supporting details or to pre-cache catalog entries for search.

## Environment Configuration

Credentials are loaded through environment variables. Two common workflows include:

1. **Direct Export**

   ```bash
   export OPENAI_API_KEY=sk-...
   export ANTHROPIC_API_KEY=anthropic-...
   python main.py --provider openai --persona "Finance manager learning automation" --xml-file sample_content.xml
   ```

2. **`.env` File with `python-dotenv`**

   ```bash
   cp .env.example .env
   # edit the file to include real keys
   python -m dotenv run -- python main.py --provider anthropic --persona "People leader improving inclusion" --xml-file sample_content.xml
   ```

When working in continuous integration or containerized environments, inject the secrets using secure secret management solutions provided by your infrastructure.

## Using Custom XML Libraries

To load custom content, supply the path via `--xml-file`. Ensure the XML conforms to the supported schema:

```xml
<content>
  <item>
    <title>Required</title>
    <description>Required</description>
    <category>Optional</category>
    <difficulty>Optional</difficulty>
    <duration>Optional</duration>
    <tags>
      <tag>Optional</tag>
    </tags>
    <metadata>
      <author>Optional</author>
      <url>Optional</url>
    </metadata>
  </item>
</content>
```

### Validation Tips

- Use `xmllint` or VS Code extensions to validate XML syntax.
- Ensure that every `<item>` has both `<title>` and `<description>` elements.
- Tags may be omitted entirely; the parser safely handles missing optional fields.
- Additional metadata is stored as free-form key/value pairs in the `metadata` dictionary of each `ContentItem`.

## Working with Different Providers

### OpenAI

- Default model: `gpt-3.5-turbo`
- Environment variable: `OPENAI_API_KEY`
- Supports chat completions; the provider class automatically constructs system and user messages.
- Consider enabling [response JSON mode](https://platform.openai.com/docs/guides/text-generation/json-mode) via the `extra` keyword in future enhancements.

### Anthropic Claude

- Default model: `claude-3-sonnet-20240229`
- Environment variable: `ANTHROPIC_API_KEY`
- Uses the Messages API to supply both system and user content.
- Adjust `max_tokens` and `temperature` to manage response length and creativity.

### Ollama

- Default model: `llama2`
- Runs locally; install via [Ollama documentation](https://github.com/jmorganca/ollama).
- Supports offline deployments where data privacy is critical.
- For custom options (such as `top_k` or `repeat_penalty`), pass an `options` dictionary to `create_provider` when extending the CLI.

## Advanced Prompt Customization

The default system prompt positions the LLM as an experienced learning consultant. To tailor outputs:

1. **Override the System Prompt**

   ```bash
   python main.py --provider openai --system-prompt "You are a cybersecurity advisor who prioritizes compliance." --persona "IT manager securing remote teams" --xml-file sample_content.xml
   ```

2. **Modify Prompt Template**

   Edit `content_selector.py` and adjust `PROMPT_TEMPLATE`. Examples include:

   - Requesting structured JSON with additional fields (e.g., difficulty alignment).
   - Asking for relevance scores on a 0–100 scale.
   - Instructing the LLM to reference specific metadata fields.

3. **Inject Persona Metadata**

   Combine the CLI with templated persona files stored as YAML or JSON. Load them externally and pass the formatted string via `--persona`.

## Interpreting Results

Each selection includes a title, reason, and optional score. Scores are returned when the provider follows the JSON format. When scores are absent, treat the order as the implicit ranking.

### Recommendation Output Anatomy

```
Persona: Data analyst transitioning to machine learning
Recommendations:
  1. Advanced Data Visualization in Python (score: 0.78)
     Reason: Builds upon existing analytics skills with ML-ready visualization practices.
  2. Introduction to Generative AI
     Reason: Provides foundational understanding of generative modeling techniques.
  3. Agile Fundamentals Bootcamp
     Reason: Supports cross-functional collaboration with product teams.
```

Use these insights to craft follow-up learning plans, schedule workshops, or create curated digests for stakeholders.

## Example Scenarios

### 1. Community Financial Educator

**Persona**

```
Community center instructor designing workshops for first-time budgeters and credit rebuilders.
```

**Command**

```bash
python main.py --provider openai --persona "Community instructor supporting first-time budgeters" --xml-file sample_content.xml
```

**Interpretation**

Expect budgeting foundations, credit literacy explainers, and facilitator guides tailored to group sessions.

### 2. HR Benefits Manager

**Persona**

```
HR benefits manager launching an employee financial wellness program focused on emergency savings.
```

**Command**

```bash
python main.py --provider anthropic --persona "HR benefits manager launching a financial wellness program" --xml-file sample_content.xml
```

**Interpretation**

Look for recommendations that blend employee-focused workshops with policy toolkits and communication aids.

### 3. Small Business Owner Scaling Operations

**Persona**

```
Entrepreneur preparing for growth who needs help with cash-flow planning and access to capital.
```

**Command**

```bash
python main.py --provider ollama --model mistral --persona "Entrepreneur preparing for growth with cash-flow pressures" --xml-file sample_content.xml
```

**Interpretation**

Likely to receive cash-flow planners, debt restructuring playbooks, and investment policy guidance.

### 4. Grant Compliance Officer

**Persona**

```
Nonprofit grant manager ensuring restricted funds follow donor reporting requirements.
```

**Command**

```bash
python main.py --provider openai --persona "Grant manager ensuring financial compliance" --xml-file sample_content.xml
```

**Interpretation**

Recommendations will emphasize compliance checklists, financial statement refreshers, and reporting templates.

## Troubleshooting

| Issue | Possible Cause | Resolution |
| ----- | -------------- | ---------- |
| `XMLContentError: ...` | Missing `<title>` or `<description>` | Validate the XML structure and ensure all required elements are present. |
| `ValueError: OpenAI API key is required` | API key not set | Export `OPENAI_API_KEY` or pass `api_key` when constructing the provider. |
| Empty recommendation list | LLM returned unparseable text | Inspect the raw response printed by the CLI and adjust prompts accordingly. |
| Slow responses | Provider latency | Reduce `max_tokens`, use smaller models, or cache results for repeated personas. |
| Ollama connection refused | Local server not running | Start Ollama (`ollama serve`) and confirm the model is installed. |

### Debugging Techniques

- Set the environment variable `PYTHONWARNINGS=default` to reveal additional warnings.
- Enable logging in `content_selector.py` by configuring Python’s logging module:

  ```python
  import logging
  logging.basicConfig(level=logging.DEBUG)
  ```

- Capture raw responses by running the CLI with a persona, then review the fallback output when parsing fails.

## FAQ

**Q: Can the tool prioritize specific categories?**

A: Yes. Extend `ContentSelector` to incorporate rule-based filters before invoking the LLM, or include explicit instructions in the persona description.

**Q: How do I integrate additional metadata like URLs or authors?**

A: Add new XML elements under `<metadata>`; they will populate the `metadata` dictionary. Adjust prompt templates to highlight these details.

**Q: Is there a way to avoid calling external APIs during testing?**

A: Use the included `demo.py` script or inject a mock provider when instantiating `ContentSelector` in your own scripts.

**Q: Can I deploy this as a web service?**

A: Absolutely. Use the bundled `web_service.py` WSGI app or embed `SelectorService` in your own framework to reuse providers and the parsed catalog.

**Q: How does the tool handle multiple personas at once?**

A: In interactive mode, you can submit personas sequentially. For batch processing, wrap `ContentSelector` in your own loop and feed each persona individually.

## Changelog

| Version | Date | Notes |
| ------- | ---- | ----- |
| 0.1.0 | 2024-04-01 | Initial release with OpenAI, Anthropic, and Ollama support, XML parser, CLI, demo script, and documentation. |
| 0.1.1 | 2024-04-05 | Added advanced usage guide, improved response parsing, and expanded test coverage. |
| 0.1.2 | 2024-04-10 | Introduced mock provider demo and refined CLI output formatting. |
| 0.1.3 | 2024-04-15 | Updated documentation with troubleshooting and persona templates. |
| 0.1.4 | 2024-04-20 | Security hardening and improved environment configuration examples. |
| 0.1.5 | 2024-04-25 | Added additional scenario walkthroughs and FAQ entries. |
| 0.1.6 | 2024-04-30 | Clarified provider defaults and advanced prompt customization techniques. |
| 0.1.7 | 2024-05-05 | Expanded XML metadata guidance and debugging recommendations. |
| 0.1.8 | 2024-05-10 | Current version shipped with this repository snapshot. |

---

For further assistance, contact the maintainers or open an issue in the project repository.
