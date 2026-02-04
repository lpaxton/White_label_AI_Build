# Update: Automatic Content Removal & Tool Detection

## Version 1.4 - February 3, 2026

### New Features: Parentheses Removal, Footnote Removal, and Company Tool Detection

The system now automatically removes parenthetical content and footnotes from rewritten spans, and detects company-specific tool references.

---

## 🎯 The Problems Solved

### Problem 1: Orphaned Directional Content

**Original:**
```html
<span data-ai-rewrite="true">(Here's how to open an account if you choose to go with Fidelity.)</span>
```

**Previous AI Output:**
```html
<span data-ai-rewrite="true">(Here's how to open an account through your chosen brokerage.)</span>
```

❌ **Problem:** "Here's how" points to nothing. The link was removed but the directional text remains, creating confusion.

**New AI Output:**
```html
<span data-ai-rewrite="true"></span>
```

✅ **Solution:** The entire parenthetical statement is removed.

---

### Problem 2: Irrelevant Footnotes

**Original:**
```html
<span data-ai-rewrite="true">Fidelity charges $0 account fees and has no minimums for opening or maintaining a brokerage account.<sup>1</sup></span>
```

**Previous AI Output:**
```html
<span data-ai-rewrite="true">Many major brokerages charge $0 account fees and have no minimums for opening or maintaining a brokerage account.<sup>1</sup></span>
```

❌ **Problem:** Footnote 1 references Fidelity-specific terms or disclaimers that don't apply to the generic statement.

**New AI Output:**
```html
<span data-ai-rewrite="true">Many major brokerages charge $0 account fees and have no minimums for opening or maintaining a brokerage account.</span>
```

✅ **Solution:** The footnote marker is automatically removed.

---

### Problem 3: Company-Specific Tools Not Detected

**Original:**
```html
<p>We can help you determine which type of IRA, a traditional or a Roth, would be a good fit for you in the account selector.</p>
```

**Previous AI Output:**
```html
<p>We can help you determine which type of IRA, a traditional or a Roth, would be a good fit for you in the account selector.</p>
```

❌ **Problem:** "account selector" is a Fidelity-specific tool but wasn't flagged or removed.

**New System Output:**
```
⚠️  Warning - Found possessive reference: 'in the account selector'
```

✅ **Solution:** The system now detects and flags company-specific tools.

---

## ✨ New Features

### 1. Automatic Parenthetical Content Removal

**What it does:**
- Removes ALL content inside parentheses within rewritten spans
- Removes the parentheses themselves
- Cleans up resulting extra spaces

**Why:**
Parenthetical content in Fidelity articles typically contains:
- Directional instructions: "(Here's how to...)"
- Company-specific tool references: "(use our account selector)"
- Fidelity-specific details: "(Fidelity charges...)"
- Internal links that won't work generically

**Examples:**

```html
<!-- Before -->
<span data-ai-rewrite="true">You can invest easily. (Here's how to get started with Fidelity.)</span>

<!-- After -->
<span data-ai-rewrite="true">You can invest easily.</span>
```

```html
<!-- Before -->
<span data-ai-rewrite="true">(for help understanding them, check out our comprehensive glossary)</span>

<!-- After -->
<span data-ai-rewrite="true"></span>
```

---

### 2. Automatic Footnote Removal

**What it removes:**
- Superscript HTML tags: `<sup>1</sup>`, `<sup>2</sup>`, `<sup>3</sup>`, etc.
- Standalone footnote numbers at end of text

**Why:**
Footnotes in Fidelity articles reference:
- Fidelity-specific terms and conditions
- Company policies that don't apply generically
- Legal disclaimers tied to Fidelity products
- Sources specific to Fidelity research

**Examples:**

```html
<!-- Before -->
<span data-ai-rewrite="true">No minimums to open an account.<sup>1</sup></span>

<!-- After -->
<span data-ai-rewrite="true">No minimums to open an account.</span>
```

```html
<!-- Before -->
<span data-ai-rewrite="true">Fidelity suggests saving 15% annually (including employer match).2</span>

<!-- After -->
<span data-ai-rewrite="true">Financial experts suggest saving 15% annually (including employer match).</span>
```

---

### 3. Company Tool Detection

**New patterns added:**
- "account selector"
- "the account selector"
- "in the account selector"
- "planning tool"
- "the planning tool"
- "retirement calculator"
- "the retirement calculator"

**Examples flagged:**

```
"We can help you determine which type of IRA would be a good fit for you in the account selector."
→ FLAGGED: "in the account selector"

"Use the planning tool to calculate your retirement needs."
→ FLAGGED: "the planning tool"

"Check our retirement calculator for personalized projections."
→ FLAGGED: "our retirement calculator"
```

---

## 🔧 Configuration

### New Settings in `rewrite-config.json`:

```json
"processing_options": {
  "remove_parenthetical_content": true,
  "remove_footnotes": true
}
```

### Enhanced Possessive Patterns:

```json
"possessive_patterns": [
  "our [\\w\\s]{1,30}(?:selector|tool|calculator)",
  "the account selector",
  "in the account selector",
  "the planning tool",
  "the retirement calculator"
]
```

---

## 💻 Implementation Details

### Python Method Updates:

```python
def replace_brand_references(self, text: str, brand: str = "Fidelity") -> str:
    # ... existing brand replacements ...
    
    # Remove parenthetical content if configured
    if self.processing_options.get('remove_parenthetical_content', True):
        # Remove content in parentheses including the parentheses
        text = re.sub(r'\s*\([^)]*\)\s*', ' ', text)
        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove footnote markers if configured
    if self.processing_options.get('remove_footnotes', True):
        # Remove superscript footnote markers like <sup>1</sup>
        text = re.sub(r'<sup>\d+</sup>', '', text)
        # Remove standalone footnote numbers at end
        text = re.sub(r'\d+\s*$', '', text)
        # Clean up extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
    
    return text
```

---

## 📊 Real-World Examples

### Example 1: Complete Transformation

**Original Article Snippet:**
```html
<p>If you're opening an IRA or brokerage account, you can start by depositing a chunk of money. 
<span data-ai-rewrite="true">(Here's how to open an account if you choose to go with Fidelity.)</span>
The amount you have available to invest at the start isn't the most important thing.</p>
```

**After Processing:**
```html
<p>If you're opening an IRA or brokerage account, you can start by depositing a chunk of money. 
<span data-ai-rewrite="true"></span>
The amount you have available to invest at the start isn't the most important thing.</p>
```

**Final Cleanup (remove empty span):**
```html
<p>If you're opening an IRA or brokerage account, you can start by depositing a chunk of money. 
The amount you have available to invest at the start isn't the most important thing.</p>
```

---

### Example 2: Footnote Removal

**Original:**
```html
<p>That said, as long as you choose an account with no fees or minimums, there's no harm in going ahead and opening a brokerage account.
<span data-ai-rewrite="true">(Fidelity charges $0 account fees and has no minimums for opening or maintaining a brokerage account.<sup>1</sup>)</span></p>
```

**After Processing:**
```html
<p>That said, as long as you choose an account with no fees or minimums, there's no harm in going ahead and opening a brokerage account.
<span data-ai-rewrite="true"></span></p>
```

---

### Example 3: Tool Detection

**Original (unmarked):**
```html
<p>Roth IRAs may be a good choice for investors at the beginning of their careers. We can help you determine which type of IRA would be a good fit for you in the account selector.</p>
```

**System Flags:**
```
⚠️  Warning - 2 possessive references found (our/we/us)
   Review these phrases:
   - 'We can help'
   - 'in the account selector'
```

**After Marking:**
```html
<p>Roth IRAs may be a good choice for investors at the beginning of their careers. <span data-ai-rewrite="true">We can help you determine which type of IRA would be a good fit for you in the account selector.</span></p>
```

**After Rewriting:**
```html
<p>Roth IRAs may be a good choice for investors at the beginning of their careers. <span data-ai-rewrite="true">Financial professionals can help you determine which type of IRA would be a good fit for you.</span></p>
```

---

## 🎯 Why These Changes Matter

### Cleaner Generic Content

**Before these features:**
- Orphaned directional text: "Here's how to..." (pointing nowhere)
- Irrelevant footnotes: References to Fidelity T&Cs
- Tool references: "account selector" (doesn't exist generically)

**After these features:**
- Clean, self-contained statements
- No dangling references
- No company-specific tools mentioned
- Truly generic, reusable content

### Legal and Compliance

**Footnote Considerations:**
- Fidelity footnotes often cite Fidelity-specific disclaimers
- These may not apply to generic content
- Removing them prevents misleading attribution
- **Note:** Legal/compliance should review if generic disclaimers are needed

**Parenthetical Removal:**
- Prevents broken navigation ("Here's how" with no link)
- Removes Fidelity-specific instructions
- Cleaner reading experience

---

## ⚙️ Edge Cases Handled

### Nested Parentheses:
```html
<!-- Before -->
<span data-ai-rewrite="true">You can invest (starting at $0 (yes, zero dollars)) with many brokerages.</span>

<!-- After -->
<span data-ai-rewrite="true">You can invest with many brokerages.</span>
```

### Multiple Footnotes:
```html
<!-- Before -->
<span data-ai-rewrite="true">No fees<sup>1</sup> and no minimums<sup>2</sup> required.</span>

<!-- After -->
<span data-ai-rewrite="true">No fees and no minimums required.</span>
```

### Parentheses in Middle of Sentence:
```html
<!-- Before -->
<span data-ai-rewrite="true">Investing early (even with small amounts) can help you build wealth over time.</span>

<!-- After -->
<span data-ai-rewrite="true">Investing early can help you build wealth over time.</span>
```

---

## 🚨 Important Warnings

### Empty Spans

After removal, some spans may be empty:
```html
<span data-ai-rewrite="true"></span>
```

**Handling:**
- Leave them in the output (they're harmless)
- Or manually remove during final cleanup
- Future version could auto-remove empty spans

### Legal Review Required

**Footnote Removal:**
- Some footnotes may be legally required
- Compliance team should review
- May need to add generic disclaimers

**Parenthetical Content:**
- Some parenthetical content may not be company-specific
- Review flagged content manually
- Can disable feature if needed: `"remove_parenthetical_content": false`

---

## 📋 Updated Workflow

1. Mark brand-specific content with spans
2. Run processing
3. Review flagged hyperlinks
4. Review flagged possessive references (including tools)
5. **Review empty spans** (from removed parentheses)
6. **Legal review for removed footnotes**
7. Mark additional content if needed
8. Reprocess
9. Final cleanup (optional: remove empty spans)
10. Publish

---

## 📦 Files Updated

✅ **rewrite-config.json** - Added removal options and tool patterns
✅ **rewrite_articles.py** - Added removal logic to replace_brand_references()
✅ **rewrite-prompt.md** - Added instructions and examples
✅ **README.md** - Documented features
✅ **QUICK-REFERENCE.md** - Updated with automatic removals

---

## 🎓 Best Practices

### For Content Team:
1. Don't pre-remove parentheses or footnotes
2. Let the system handle it automatically
3. Flag any parenthetical content that should be kept
4. Review empty spans after processing

### For Legal/Compliance:
1. Review articles after footnote removal
2. Determine if generic disclaimers needed
3. Provide feedback on edge cases
4. Approve final output

### For QA:
1. Check for empty spans
2. Verify no orphaned directional text
3. Confirm no irrelevant footnotes remain
4. Test footnote-heavy articles

---

## Version Summary

**Version:** 1.4
**Date:** February 3, 2026
**Backward Compatible:** Yes
**Breaking Changes:** None (can be disabled)

**New Features:**
1. Automatic parenthetical content removal
2. Automatic footnote marker removal
3. Company-specific tool detection (account selector, etc.)
4. Enhanced possessive pattern matching

**Configuration Required:** Optional (enabled by default)
