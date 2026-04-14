# Quick Reference: Article Rewriting System

## For Claude: How to Use This System

When a user asks you to rewrite articles using this system:

### Step 1: Load Configuration
```
Read rewrite-config.json to get:
- List of articles to process
- Brand replacement rules
- Output settings
```

### Step 2: Identify What to Change
```
Find all HTML elements with: data-ai-rewrite="true"
Example: <span data-ai-rewrite="true">Fidelity offers...</span>
```

### Step 3: Apply Replacements
Use the brand_replacements rules from config:

**Company Names:**
- Fidelity → "many major brokerages"
- Company X → "leading providers"

**Products:**
- Fidelity Go® → "automated robo advisors"  
- Fidelity Youth® → "custodial accounts for minors"

**Statements:**
- "Fidelity suggests" → "Financial experts recommend"
- "Fidelity charges" → "Many major brokerages charge"
- "with Fidelity" → "with your chosen brokerage"

**Automatic Removals:**
- Remove all parenthetical content: (including the parentheses)
- Remove all footnotes: <sup>1</sup>, <sup>2</sup>, etc.
- Remove trademark symbols: ®, ™, ℠

### Step 4: Critical Rules
✓ ONLY modify text inside data-ai-rewrite spans
✓ Keep ALL other HTML exactly the same
✓ DO NOT fix grammar, spelling, or redundancy
✓ DO NOT modify image src paths
✓ Preserve all attributes, styles, and structure
✓ Remove ® ™ ℠ symbols and their <sup> tags
✓ Remove trademark symbols from ALL rewritten content
✓ Check hyperlinks for unmarked Fidelity product references
✓ Flag unmarked product links for manual review

### Step 5: Process Each Article
```python
For each article in config:
  1. Read input file
  2. Find all data-ai-rewrite spans
  3. Replace brand references in those spans only
  4. Save to output directory
  5. Generate report
```

### Example Transformation

**Input:**
```html
<span data-ai-rewrite="true">Fidelity offers commission-free trading</span>
```

**Output:**
```html
<span data-ai-rewrite="true">Many major brokerages offer commission-free trading</span>
```

**Input with Trademark:**
```html
<span data-ai-rewrite="true">Try Fidelity Go<sup>®</sup> today</span>
```

**Output:**
```html
<span data-ai-rewrite="true">Try automated robo advisors today</span>
```

### User Request Patterns

If user says:
- "Rewrite this article" → Follow rewrite-prompt.md
- "Process multiple articles" → Use rewrite-config.json
- "Use the rewrite system" → Load config and process all articles
- "Neutralize this content" → Apply brand replacements

### Quality Checks Before Delivering

□ All data-ai-rewrite spans processed
□ No brand names remain in rewritten spans
□ All other HTML unchanged
□ HTML structure valid
□ Image paths unchanged
□ Output files in correct directory
□ Hyperlinks checked for product references
□ Possessive references checked (our/we/us)
□ Report any unmarked product links to user
□ Report any possessive references to user

### Report What You Did

Always tell the user:
- How many articles processed
- How many spans found and rewritten  
- Where output files are saved
- Any errors encountered

---

## File Locations

- **Config:** rewrite-config.json
- **Prompt:** rewrite-prompt.md
- **Script:** rewrite_articles.py
- **Template:** article-template.html
- **Docs:** README.md
- **This file:** QUICK-REFERENCE.md
