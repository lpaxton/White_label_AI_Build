# Quick Start Guide - aRCHi Content & Learning Tools

This guide walks you through the 4-step workflow for extracting, neutralizing, reviewing, and editing brand-specific article content.

---

## Overview

```
[ Step 01 ]       [ Step 02 ]          [ Step 03 ]       [ Step 04 ]
Article      ->   Brand          ->   Content Diff  ->   Word
Extractor         Neutralizer         Tool               Editor
```

---

## Step 01 - Article Extractor

**File:** `article-extractor.html`

Extract and clean article content from any URL. This is the starting point - it pulls the raw article HTML and prepares it for brand neutralization.

**What it does:**
- Extracts `<article>` content from a given URL
- Removes unwanted elements (nav links, call-outs, disclaimers)
- Outputs clean, readable HTML
- Provides a real-time content preview before sending to Step 02

**How to use:**
1. Open `article-extractor.html` in your browser
2. Paste the article URL into the input field
3. Click **Extract Article**
4. Review the extracted content in the preview panel
5. Click **Send to Brand Neutralizer** to proceed to Step 02

> **Note:** The extracted content is passed to Step 02 via session storage. Do not refresh the page before proceeding or you will need to re-extract.

---

## Step 02 - Brand Neutralizer

**File:** `article-rewriter.html`

Transform brand-specific content into generic, white-label alternatives using Claude AI.

**What it does:**
- AI-powered brand neutralization (removes or replaces brand references)
- Automatically removes trademark symbols (R, TM, SM)
- Removes specific product names cleanly without inventing new ones
- Flags unmarked product hyperlinks and possessive references (our/we/us)
- Preserves all HTML structure throughout the rewrite

**How to use:**
1. Content loaded from Step 01 will appear automatically with a confirmation message
2. If no content is loaded, click **Back to Article Extractor** to restart from Step 01
3. Expand **Rewrite Options** to configure:
   - Processing options (trademarks, footnotes, hyperlink/possessive flagging)
   - Brand to neutralize (Fidelity or custom)
   - Your Claude AI API key (`sk-ant-api...`)
4. Click **Rewrite with AI**
5. Review the neutralized output on the right panel
6. When satisfied, click **Article Diff View** to proceed to Step 03

> **API Key:** Your key is stored locally in your browser and never sent to any server other than Anthropic's API directly.

---

## Step 03 - Content Diff Tool

**File:** `article-diff.html`

Compare the original extracted article against the brand-neutralized output side by side to verify every change the AI made.

**What it does:**
- Side-by-side rendered view of original vs. rewritten content
- Word-level diff highlighting so no change goes unnoticed
- Clear original vs. rewritten markers
- Synchronized scrolling between both panels
- Change count statistics at a glance

**How to use:**
1. Arriving from Step 02 via **Article Diff View** automatically loads both versions
2. Scroll through both panels - changes are highlighted inline
3. Use the statistics bar to see a summary of total changes
4. If you need to re-run the rewrite, go back to Step 02
5. When the diff looks good, proceed to Step 04 for final editing

---

## Step 04 - Word Editor

**File:** `article-editor.html`

Review and refine the brand-neutralized article in a word-processor-style editor before final export.

**What it does:**
- Rich text editing: bold, italic, underline, lists, and more
- Heading & paragraph formatting controls
- One-click removal of AI highlight markers left from the rewrite
- Live word and character count
- Download as HTML or plain text

**How to use:**
1. Content arrives from the workflow automatically, or paste HTML manually
2. Use the toolbar to make any final edits or formatting adjustments
3. Click **Remove AI Highlights** to clean up any rewrite markers
4. When ready, click **Download as HTML** or **Download as Text** to export

---

## Full Workflow at a Glance

| Step | Tool | Action |
|------|------|--------|
| 01 | Article Extractor | Paste URL -> Extract -> Send to Neutralizer |
| 02 | Brand Neutralizer | Review options -> Add API key -> Rewrite with AI -> Diff View |
| 03 | Content Diff Tool | Review all changes -> Confirm accuracy |
| 04 | Word Editor | Final edits -> Remove highlights -> Download |

---

## Requirements

To run the AI rewrite in Step 02 you need:

- A **Claude API key** from https://console.anthropic.com
- An internet connection (the API call goes directly from your browser to Anthropic)

To run the local API server (optional, for server-side processing):

```bash
pip install -r requirements.txt
python api_server.py
```

---

## Troubleshooting

**"Back to Article Extractor" button is showing in Step 02**
Content was not passed from Step 01. Go back to `article-extractor.html` and re-extract.

**Rewrite fails or returns an error**
Check that your Claude API key is correct and has available credits.

**Content looks wrong after extraction**
Some pages block automated access. Try copying the article HTML manually and pasting it into the textarea in Step 02.

**Diff tool shows nothing**
Both original and rewritten content must be present. Make sure you clicked **Article Diff View** from Step 02 after a successful rewrite.