# Article Brand Neutralization Prompt

## Objective
Process HTML articles to replace brand-specific content with generic, neutral alternatives while maintaining the exact HTML structure.

## CRITICAL RULES - READ FIRST

### 1. TEXT PRESERVATION
**DO NOT change ANY text outside of `data-ai-rewrite="true"` spans.**
- Do NOT fix grammar errors
- Do NOT fix typos or spelling mistakes
- Do NOT remove redundancy
- Do NOT improve sentence structure
- Do NOT add or remove punctuation
- ONLY modify text within marked spans

### 2. IMAGE PRESERVATION
**Keep ALL images with their FULL paths exactly as they appear.**
- Do NOT modify image src attributes
- Do NOT convert relative paths to absolute paths
- Do NOT change image URLs
- Do NOT remove or alter image tags

### 3. HYPERLINK EVALUATION
**Check ALL hyperlinks for Fidelity product/tool references.**
- If a link text mentions a Fidelity product or internal tool, mark it for rewriting
- Examples: "Fidelity Go®", "our planning tools", "Fidelity's calculator"
- Even if the link isn't in a data-ai-rewrite span, flag it for the user to review
- Do NOT change the href URL itself, only the link text if appropriate

## Task Instructions

1. **Load the configuration**: Read the `rewrite-config.json` file to get:
   - List of input articles to process
   - Brand replacement rules
   - Output directory

2. **For each article**:
   - Locate ALL HTML elements with the attribute `data-ai-rewrite="true"`
   - These spans contain brand-specific content that needs to be neutralized
   - Rewrite ONLY the text content within these spans

3. **Rewriting Rules**:
   - Replace brand-specific references with generic alternatives
   - Maintain the same meaning and context
   - Keep all HTML structure, attributes, and styling exactly as is
   - Preserve all other content in the document unchanged
   - Follow the brand replacement mappings provided in the config

4. **Brand Replacement Strategy**:
   - Company-specific product names → Generic product categories
   - "Company X offers Y" → "Many providers offer Y" or "Financial institutions offer Y"
   - "Company X suggests" → "Financial experts recommend" or "Industry experts suggest"
   - Specific company references → "reputable firms" or "major brokerages"
   - **ALWAYS remove trademark symbols**: Remove ®, ™, and ℠ symbols and their superscript tags
   - **ALWAYS remove parenthetical content**: Remove text in parentheses including the parentheses
   - **ALWAYS remove footnotes**: Remove <sup>1</sup>, <sup>2</sup>, etc. and standalone footnote numbers
   - **ALWAYS flag company-specific tools**: "account selector", "planning tool", "retirement calculator"

5. **Quality Checks**:
   - Verify all `data-ai-rewrite="true"` spans have been processed
   - Ensure no brand references remain in rewritten spans
   - Confirm all other HTML remains unchanged
   - Validate HTML structure is intact
   - Check for hyperlinks that reference Fidelity products/tools but aren't marked

6. **Hyperlink Handling**:
   - Scan all `<a>` tags for link text mentioning Fidelity products or tools
   - Flag any unmarked links that should be rewritten
   - If link text is within a data-ai-rewrite span, rewrite it normally
   - If link text mentions a product but isn't marked, report it to the user
   - NEVER modify href URLs - only the visible link text
   - Examples to flag:
     * "Learn more about Fidelity Go®"
     * "Use our planning calculator"
     * "Try Fidelity's retirement planner"

7. **Possessive Reference Checking**:
   - Scan the ENTIRE article for possessive references that imply Fidelity authorship
   - Flag phrases like "our glossary", "we offer", "we recommend", "check with us"
   - These need to be marked and rewritten to be brand-neutral
   - Examples to flag:
     * "check out our comprehensive glossary"
     * "we offer many investment options"
     * "we can help you with planning"
     * "contact us for more information"
     * "our website has additional resources"
   - Flag these even if they're not in hyperlinks
   - Report ALL possessive references found

8. **Output**:
   - Save rewritten files to the specified output directory
   - Use clear naming convention: `{original-name}-rewritten.html`
   - Generate a summary report of changes made

## Example Transformations

### Input
```html
<span data-ai-rewrite="true">Fidelity charges $0 account fees</span>
```

### Output
```html
<span data-ai-rewrite="true">Many major brokerages charge $0 account fees</span>
```

### Input
```html
<span data-ai-rewrite="true">Fidelity Go® offers automated management</span>
```

### Output
```html
<span data-ai-rewrite="true">Automated robo advisors offer automated management</span>
```

### Input (with HTML superscript tags)
```html
<span data-ai-rewrite="true">Try our Product Name<sup>®</sup> today</span>
```

### Output
```html
<span data-ai-rewrite="true">Try our automated service today</span>
```

### Input (possessive reference - needs marking)
```html
<p>(for help understanding them, check out our comprehensive glossary)</p>
```

### Should be marked as:
```html
<p>(for help understanding them, <span data-ai-rewrite="true">check out our comprehensive glossary</span>)</p>
```

### Then rewritten to:
```html
<p>(for help understanding them, <span data-ai-rewrite="true">check out available financial glossaries</span>)</p>
```

### Input (possessive "we" statement - needs marking)
```html
<p>We offer a wide range of investment products to meet your needs.</p>
```

### Should be marked as:
```html
<p><span data-ai-rewrite="true">We offer a wide range of investment products to meet your needs.</span></p>
```

### Then rewritten to:
```html
<p><span data-ai-rewrite="true">Financial institutions offer a wide range of investment products to meet your needs.</span></p>
```

### Input (with parenthetical content - will be removed)
```html
<p><span data-ai-rewrite="true">(Here's how to open an account if you choose to go with Fidelity.)</span></p>
```

### After rewriting (parentheses and content removed):
```html
<p><span data-ai-rewrite="true"></span></p>
```
Note: The entire parenthetical statement is removed, leaving an empty span that can be deleted.

### Input (with footnote - will be removed)
```html
<p><span data-ai-rewrite="true">Fidelity charges $0 account fees and has no minimums for opening or maintaining a brokerage account.<sup>1</sup></span></p>
```

### After rewriting (footnote removed):
```html
<p><span data-ai-rewrite="true">Many major brokerages charge $0 account fees and have no minimums for opening or maintaining a brokerage account.</span></p>
```

### Input (company-specific tool reference - needs flagging)
```html
<p>We can help you determine which type of IRA would be a good fit for you in the account selector.</p>
```

### Should be marked as:
```html
<p><span data-ai-rewrite="true">We can help you determine which type of IRA would be a good fit for you in the account selector.</span></p>
```

### After rewriting (tool reference removed):
```html
<p><span data-ai-rewrite="true">Financial professionals can help you determine which type of IRA would be a good fit for you.</span></p>
```

## Important Notes
- Only modify content within `data-ai-rewrite="true"` spans
- Do NOT alter any other part of the HTML document
- Preserve all whitespace, formatting, and inline styles
- Keep the `data-ai-rewrite="true"` attribute intact
- Maintain natural, fluent language in rewrites
- **CRITICAL: Do NOT fix grammar, spelling, or style issues outside of marked spans**
- **CRITICAL: Keep all image src paths exactly as they appear**
- **CRITICAL: Review all hyperlinks for unmarked Fidelity product references**
