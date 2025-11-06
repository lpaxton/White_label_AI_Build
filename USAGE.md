# Usage Examples

This document provides detailed examples of using the Persona-Based Content Selector.

## Basic Usage

### Interactive Mode (Recommended for exploration)

Start the application in interactive mode where you can enter multiple persona descriptions:

```bash
# Using OpenAI
python main.py --provider openai --xml-file sample_content.xml

# Using Anthropic Claude
python main.py --provider anthropic --xml-file sample_content.xml

# Using Ollama (local)
python main.py --provider ollama --model llama2 --xml-file sample_content.xml
```

Once running, you can enter persona descriptions like:
- "Junior developer wanting to learn cloud computing"
- "Marketing manager needing data analysis skills"
- "Technical support specialist transitioning to DevOps"

### Single Query Mode

For one-off queries, provide the persona directly:

```bash
python main.py --provider openai \
  --persona "Senior software engineer transitioning into DevOps role" \
  --xml-file sample_content.xml
```

## Persona Examples by Role

### Software Developers

```bash
# Beginner Developer
python main.py --provider openai \
  --persona "Recent bootcamp graduate learning their first programming language. Needs hands-on practice and foundational concepts." \
  --max-items 3

# Mid-Level Developer
python main.py --provider anthropic \
  --persona "Software engineer with 3 years experience in web development. Want to learn advanced patterns and best practices." \
  --max-items 5

# Senior Developer
python main.py --provider ollama \
  --persona "Senior developer with 10+ years experience looking to learn machine learning and AI technologies" \
  --max-items 4
```

### Business Professionals

```bash
# New Manager
python main.py --provider openai \
  --persona "First-time manager promoted from individual contributor. Needs leadership and people management skills." \
  --max-items 5

# Executive
python main.py --provider anthropic \
  --persona "C-level executive wanting to understand data science and analytics to make data-driven decisions" \
  --max-items 3

# Marketing Professional
python main.py --provider ollama \
  --persona "Digital marketing specialist wanting to understand technical concepts to better work with engineering teams" \
  --max-items 4
```

### Career Changers

```bash
# Career Transition
python main.py --provider openai \
  --persona "Former teacher transitioning into tech. Completely new to programming but strong analytical skills." \
  --max-items 5

# Role Expansion
python main.py --provider anthropic \
  --persona "Customer support representative wanting to move into technical support and learn system administration" \
  --max-items 4
```

### Specialized Roles

```bash
# Data Professional
python main.py --provider openai \
  --persona "Data analyst proficient in SQL and Excel, wanting to expand into Python and machine learning" \
  --max-items 5

# Security Specialist
python main.py --provider anthropic \
  --persona "System administrator wanting to specialize in cybersecurity and secure infrastructure" \
  --max-items 4

# DevOps Engineer
python main.py --provider ollama \
  --persona "Backend developer wanting to learn DevOps practices, CI/CD, and cloud infrastructure" \
  --max-items 5
```

## Advanced Usage

### Custom Model Selection

```bash
# Use GPT-4 with OpenAI
python main.py --provider openai \
  --model gpt-4 \
  --persona "Advanced AI researcher" \
  --xml-file sample_content.xml

# Use Claude 3 Opus with Anthropic
python main.py --provider anthropic \
  --model claude-3-opus-20240229 \
  --persona "Senior data scientist" \
  --xml-file sample_content.xml

# Use specific Ollama model
python main.py --provider ollama \
  --model mistral \
  --persona "Software architect" \
  --xml-file sample_content.xml
```

### API Key Management

```bash
# Using environment variables (recommended)
export OPENAI_API_KEY="your-key-here"
python main.py --provider openai --persona "Your persona"

# Using command-line argument
python main.py --provider openai \
  --api-key "your-key-here" \
  --persona "Your persona"

# Using .env file
# Create .env file with: OPENAI_API_KEY=your-key-here
python main.py --provider openai --persona "Your persona"
```

### Custom Ollama Host

If Ollama is running on a different host or port:

```bash
python main.py --provider ollama \
  --ollama-host "http://192.168.1.100:11434" \
  --model llama2 \
  --persona "Your persona"
```

### Adjusting Number of Results

```bash
# Get only top 3 recommendations
python main.py --provider openai \
  --persona "Your persona" \
  --max-items 3

# Get up to 10 recommendations
python main.py --provider openai \
  --persona "Your persona" \
  --max-items 10
```

## Output Interpretation

The application provides:

1. **Selected Content**: A list of recommended content items with:
   - Title
   - Category and Difficulty level
   - Duration
   - Description
   - Tags

2. **AI Reasoning**: Explanation of why each item was selected for the persona

Example output:
```
======================================================================
PERSONA DESCRIPTION:
======================================================================
Junior developer wanting to learn cloud computing

======================================================================
SELECTED CONTENT (3 items):
======================================================================

1. Introduction to Cloud Computing
   Category: Technology | Difficulty: Beginner
   Duration: 30 minutes
   Description: Learn the fundamentals of cloud computing...
   Tags: cloud, infrastructure, basics

[... more items ...]

======================================================================
AI REASONING:
======================================================================
The selected content is appropriate for a junior developer because:
1. Introduction to Cloud Computing (ID: 1) - Perfect starting point...
[... detailed reasoning ...]
```

## Tips for Writing Effective Personas

1. **Be Specific**: Include role, experience level, and learning goals
   - Good: "Mid-level developer with 3 years JavaScript experience wanting to learn Python"
   - Less effective: "Developer who wants to learn"

2. **Mention Context**: Add why they need the content
   - "Marketing manager preparing for cross-functional project with data team"
   - "Support engineer promoted to technical lead role"

3. **Include Constraints**: Mention time, skill level, or priorities
   - "Busy executive needing high-level overview in under 1 hour"
   - "Complete beginner with no technical background"

4. **Describe Background**: Previous experience helps AI make better matches
   - "Former teacher with strong communication skills, new to tech"
   - "Sales professional wanting to understand technical products"

## Custom Content XML Files

To use your own content, create an XML file following this structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<content_library>
    <content id="unique_id">
        <title>Your Content Title</title>
        <description>Detailed description</description>
        <category>Category Name</category>
        <difficulty>Beginner/Intermediate/Advanced</difficulty>
        <tags>comma, separated, tags</tags>
        <duration>Estimated time</duration>
    </content>
    <!-- Add more content items -->
</content_library>
```

Then use it:
```bash
python main.py --provider openai \
  --xml-file /path/to/your/content.xml \
  --persona "Your persona"
```

## Troubleshooting

### No results returned
- Check that your XML file has content items
- Try being more specific in your persona description
- Increase --max-items

### API errors
- Verify your API key is correct
- Check your API quota/billing
- Ensure you have internet connection

### Ollama connection issues
- Verify Ollama is running: `ollama list`
- Check the model is downloaded: `ollama pull llama2`
- Verify host/port with --ollama-host
