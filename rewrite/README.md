# Article Brand Neutralization System

Automated system for rewriting HTML articles to replace brand-specific content with generic, neutral alternatives.

## Overview

This system processes HTML articles that have been pre-marked with `data-ai-rewrite="true"` attributes on spans containing brand-specific content. It replaces company names, product names, and branded statements with generic alternatives while preserving the exact HTML structure.

### Critical Preservation Rules

1. **Text Preservation**: The system does NOT fix grammar, spelling, redundancy, or style issues. It ONLY changes text within marked spans.

2. **Image Preservation**: All image paths remain exactly as they appear in the original HTML. No modifications to src attributes.

3. **Hyperlink Checking**: The system scans all hyperlinks and flags any that reference Fidelity products or tools but aren't marked for rewriting.

## Files

1. **rewrite-prompt.md** - Human-readable instructions for manual processing
2. **rewrite-config.json** - Configuration file defining articles and replacement rules
3. **rewrite_articles.py** - Python automation script for batch processing
4. **README.md** - This file

## Quick Start

### Method 1: Automated Processing (Python)

```bash
# 1. Install Python 3.7+ (if not already installed)

# 2. Update the configuration file with your articles
nano rewrite-config.json

# 3. Run the script
python3 rewrite_articles.py
```

### Method 2: Manual Processing with Claude

```
1. Upload your HTML article(s) to Claude
2. Share the rewrite-prompt.md instructions
3. Ask Claude to process the article(s) following the prompt
```

## Configuration File Structure

### Articles Section
Add your articles to the `articles` array:

```json
{
  "id": 1,
  "name": "Article Title",
  "input_file": "/path/to/input/article.html",
  "output_file": "output-filename.html",
  "status": "pending",
  "notes": "Optional notes"
}
```

### Brand Replacements Section
Define how brand references should be replaced:

```json
"brand_replacements": {
  "BrandName": {
    "company_name": ["generic alternative 1", "generic alternative 2"],
    "products": {
      "Product Name®": "generic product type"
    },
    "statements": {
      "Brand says": "Experts recommend",
      "Brand offers": "Many providers offer"
    }
  }
}
```

## Replacement Strategy

### Company Names
- **Fidelity** → "many major brokerages", "reputable financial firms"
- **Company X** → "leading providers", "major institutions"

### Product Names
- **Branded Product®** → "generic product category"
- **Fidelity Go®** → "automated robo advisors"
- **Fidelity Youth®** → "custodial accounts for minors"
- **Note:** All trademark symbols (®, ™, ℠) and their HTML tags are automatically removed

### Statements
- **"Company suggests"** → "Financial experts recommend"
- **"Company offers"** → "Many providers offer"
- **"with Company"** → "with your chosen provider"

## Output

### File Output
- Rewritten articles saved to: `/mnt/user-data/outputs/rewritten-articles/`
- Original HTML structure preserved completely
- Only `data-ai-rewrite="true"` spans modified

### Report Output
JSON report generated with:
- Total articles processed
- Success/failure counts
- Detailed replacement information
- Processing times

Example report:
```json
{
  "generated_at": "2026-02-03T10:30:00",
  "total_articles": 3,
  "successful": 3,
  "failed": 0,
  "results": [...]
}
```

## Workflow

### Pre-Processing (Done by Content Team)
1. Review article HTML
2. Identify brand-specific content that needs to be neutralized
3. Wrap identified content in spans: `<span data-ai-rewrite="true">Brand content</span>`

### Processing (Automated or Manual)
1. Load configuration file
2. For each article:
   - Find all `data-ai-rewrite="true"` spans
   - Replace brand references per configuration
   - Save rewritten file
3. Generate summary report

### Post-Processing (Quality Check)
1. Review rewritten articles
2. Verify brand neutralization
3. Confirm HTML integrity
4. Approve for publication

## Validation Checks

The system performs automatic validation:
- ✓ All `data-ai-rewrite` spans processed
- ✓ No brand references remain in rewritten spans
- ✓ All trademark symbols removed (®, ™, ℠)
- ✓ HTML structure preserved
- ✓ All other content unchanged
- ✓ Image paths preserved exactly
- ✓ Hyperlinks checked for unmarked product references
- ✓ Possessive references checked (our/we/us)
- ⚠️ Unmarked product links flagged for review
- ⚠️ Possessive references flagged for review

## Trademark Symbol Removal

The system automatically removes:
- **Registration marks**: ® (and `<sup>®</sup>`)
- **Trademark symbols**: ™ (and `<sup>™</sup>`)
- **Service marks**: ℠ (and `<sup>℠</sup>`, `<sup>SM</sup>`)

This happens automatically when brand names are replaced. You can configure which symbols to remove in the `processing_options` section of the config file.

## Hyperlink Handling

The system checks all hyperlinks in the article for unmarked Fidelity product references.

### What Gets Flagged:
- Link text mentioning Fidelity products: "Try Fidelity Go®"
- References to company tools: "Use our planning calculator"
- Product calls-to-action: "Open a Fidelity Youth Account"

### What Happens:
1. System scans all `<a>` tags
2. Checks link text against product keywords
3. Flags unmarked links in the report
4. Alerts you to review these links manually

### Important:
- The system NEVER modifies href URLs
- Only the visible link text should be rewritten
- Links inside data-ai-rewrite spans are handled automatically
- Unmarked links are reported for manual review

### Example:
```html
<!-- This will be flagged -->
<a href="/tools">Try our Fidelity Go® robo advisor</a>

<!-- This should be marked -->
<a href="/tools"><span data-ai-rewrite="true">Try Fidelity Go®</span></a>
```

## Possessive Reference Checking

The system scans the ENTIRE article for possessive references (our/we/us) that imply Fidelity wrote the article.

### What Gets Flagged:

**Possessive Pronouns:**
- "our glossary", "our tools", "our calculator"
- "our website", "our platform", "our company"

**Company-Specific Tools:**
- "the account selector", "in the account selector"
- "the planning tool", "the retirement calculator"

**First-Person Statements:**
- "we offer", "we provide", "we recommend"
- "we can help", "we suggest"

**Direct References:**
- "contact us", "check with us"
- "at Fidelity"

### Examples:

**Unmarked possessive reference:**
```html
<p>(for help understanding them, check out our comprehensive glossary)</p>
```

**Should be marked:**
```html
<p>(for help understanding them, <span data-ai-rewrite="true">check out our comprehensive glossary</span>)</p>
```

**After rewriting:**
```html
<p>(for help understanding them, <span data-ai-rewrite="true">check out available financial glossaries</span>)</p>
```

### Why This Matters:
These articles were written BY Fidelity FOR Fidelity's website. When you remove the branding, you also need to remove the first-person voice that implies Fidelity authorship. Otherwise, the generic article still sounds like it was written by a specific company.

### What Happens:
1. System scans entire article with regex patterns
2. Flags all possessive references not already in rewrite spans
3. Reports them for manual review
4. You mark them and reprocess

## Automatic Content Removal

The system automatically removes certain types of content from rewritten spans to ensure clean, brand-neutral output.

### Parenthetical Content Removal

**ALL content in parentheses is removed from rewritten spans**, including the parentheses themselves.

**Why:** Parenthetical content often contains:
- Company-specific instructions: "(Here's how to open an account with Fidelity)"
- Internal tool references: "(use our account selector)"
- Fidelity-specific details that don't translate to generic content

**Example:**
```html
<!-- Original -->
<span data-ai-rewrite="true">(Here's how to open an account if you choose to go with Fidelity.)</span>

<!-- After rewriting -->
<span data-ai-rewrite="true"></span>
```

The entire parenthetical statement is removed because directional content like "Here's how" doesn't make sense without the actual link or resource.

### Footnote Removal

**ALL footnotes and footnote markers are removed** from rewritten spans.

**Formats removed:**
- Superscript footnotes: `<sup>1</sup>`, `<sup>2</sup>`, etc.
- Standalone numbers at end of sentences

**Why:** Footnotes typically reference:
- Fidelity-specific disclaimers
- Company policies that don't apply generically
- Legal disclosures tied to Fidelity
- Sources that aren't relevant in generic context

**Example:**
```html
<!-- Original -->
<span data-ai-rewrite="true">Fidelity charges $0 account fees.<sup>1</sup></span>

<!-- After rewriting -->
<span data-ai-rewrite="true">Many major brokerages charge $0 account fees.</span>
```

**Note:** Legal/compliance teams should review if any footnotes need to be retained for regulatory reasons.

### Configuration

Both features can be toggled in `rewrite-config.json`:

```json
"processing_options": {
  "remove_parenthetical_content": true,
  "remove_footnotes": true
}
```

## Example Transformation

### Before
```html
<p>Start investing today.<span data-ai-rewrite="true"> Fidelity offers 
zero-fee accounts and the Fidelity Go® robo advisor.</span> Learn more.</p>
```

### After
```html
<p>Start investing today.<span data-ai-rewrite="true"> Many major brokerages 
offer zero-fee accounts and automated robo advisors.</span> Learn more.</p>
```

## Troubleshooting

### Articles not processing
- Check file paths in config are correct
- Ensure input files exist and are readable
- Verify JSON syntax in config file

### Brand references not replaced
- Confirm replacement rules are defined in config
- Check case sensitivity settings
- Verify span has `data-ai-rewrite="true"` attribute

### HTML structure changed
- This should never happen - report as bug
- Verify you're using the correct version of the script
- Check for manual edits outside of rewrite spans

## Adding New Brand Replacements

Edit `rewrite-config.json`:

```json
"brand_replacements": {
  "NewBrand": {
    "company_name": ["generic alternative"],
    "products": {
      "NewBrand Product": "generic product"
    },
    "statements": {
      "NewBrand recommends": "Industry experts recommend"
    }
  }
}
```

## Best Practices

1. **Pre-mark content carefully** - Only mark truly brand-specific content
2. **Test on one article first** - Verify replacements before batch processing
3. **Review outputs** - Always QA rewritten articles before publishing
4. **Keep config updated** - Add new patterns as you encounter them
5. **Version control** - Track changes to replacement rules
6. **Backup originals** - Keep original files before rewriting

## Support

For issues or questions:
1. Review this README
2. Check the rewrite-prompt.md for detailed instructions
3. Verify configuration file syntax
4. Test with a single article first

## Version History

- **v1.0** (2026-02-03) - Initial release
  - Basic brand replacement functionality
  - JSON configuration support
  - Automated batch processing
  - Summary reporting
