#!/usr/bin/env python3
"""
Profiling Service for the Adaptive-Explainer skill.

Continuously profiles each user's financial literacy level, vocabulary
comfort, and learning preferences, then calibrates every Money Buddy
response to their level.

Part of the aRCHi (Life on Easy) platform.
"""

import re
from datetime import datetime, timezone

from jargon_detector import (
    detect_jargon_in_text,
    classify_vocabulary_level,
    FINANCIAL_JARGON_TIERS,
)
from military_context import apply_military_context

# ── Constants ───────────────────────────────────────────────────────────────

VALID_LEVELS = {"Low", "Medium", "High"}
VALID_PACES = {"Short", "Medium", "Thorough"}

# Explicit recalibration phrases from the user
_SIMPLIFY_SIGNALS = [
    "explain more simply", "explain that more simply",
    "too complicated", "too complex", "i don't understand",
    "i dont understand", "what does that mean", "can you dumb it down",
    "say that again", "in simple terms", "in plain english",
    "eli5", "explain like i'm 5", "simpler please",
    "that's confusing", "i'm confused", "i am confused",
    "what do you mean", "huh?", "lost me",
]

_ADVANCE_SIGNALS = [
    "i know the basics", "i already know",
    "skip the basics", "get to the point",
    "more detail", "go deeper", "more advanced",
    "tell me more", "what about the specifics",
    "i'm familiar with", "i am familiar with",
]

_CLARITY_SIGNALS = [
    "that makes sense", "makes sense", "got it", "i see",
    "oh i understand", "thanks that helps", "that's clear",
    "perfect", "great explanation", "ah ok", "ah okay",
    "now i get it",
]

_CONFUSION_SIGNALS = [
    "i don't get it", "i dont get it", "still confused",
    "what?", "huh?", "i'm lost", "i am lost",
    "can you repeat", "say again", "not following",
]


# ── Profile initialisation ─────────────────────────────────────────────────

def _default_profile(user_id: str, session_id: str,
                     persona_tags: list[str] | None = None) -> dict:
    """Return a fresh profile dict with Medium defaults."""
    now = datetime.now(timezone.utc)
    return {
        "user_id": user_id,
        "session_id": session_id,
        "created_at": now,
        "updated_at": now,
        # Profile dimensions
        "financial_literacy": "Medium",
        "vocabulary_comfort": "Medium",
        "abstraction_tolerance": "Medium",
        "pace_preference": "Medium",
        # Signals & evidence
        "vocabulary_used": [],
        "questions_asked": [],
        "confusion_signals": 0,
        "engagement_signals": 0,
        # Persona
        "persona_tags": persona_tags or [],
        # History
        "interaction_count": 0,
        "last_topics": [],
    }


def initialize_user_profile(user_id: str, session_id: str,
                            persona_tags: list[str] | None = None) -> dict:
    """
    Create a new user profile with Medium defaults for all dimensions.
    Include persona tags if provided (military, first-gen, etc.).

    This returns the dict; the caller is responsible for persisting it
    via ``fcat_db.upsert_user_profile``.
    """
    return _default_profile(user_id, session_id, persona_tags)


# ── Vocabulary / question analysis ─────────────────────────────────────────

def extract_vocabulary_signals(message: str) -> dict:
    """
    Analyse a message for financial vocabulary usage.

    Returns::

        {
            "level_estimate": "Low" | "Medium" | "High",
            "terms_used": [str],
            "jargon_count": int,
        }
    """
    hits = detect_jargon_in_text(message)
    terms = [h["term"] for h in hits]
    level = classify_vocabulary_level(terms)
    return {
        "level_estimate": level,
        "terms_used": terms,
        "jargon_count": len(terms),
    }


def extract_question_type(message: str) -> str:
    """
    Classify a user question's complexity.

    Returns ``"beginner"``, ``"intermediate"``, or ``"advanced"``.
    """
    msg = message.lower().strip()

    # Advanced patterns: multi-concept, conditional, comparative
    advanced_patterns = [
        r"how does .+ interact with .+",
        r"how does .+ affect .+",
        r"what('s| is) the (relationship|difference|trade-?off) between .+ and .+",
        r"under what (conditions|circumstances)",
        r"compare .+ (to|with|vs|versus) .+",
        r"what are the tax implications",
        r"how (should|would|could) i optimiz",
        r"what('s| is) the impact of .+ on .+",
        r"if .+ then .+",
    ]
    for pat in advanced_patterns:
        if re.search(pat, msg):
            return "advanced"

    # Intermediate patterns: reasoning, strategy
    intermediate_patterns = [
        r"why (should|would|do|does|is|are|isn't|aren't)",
        r"when (is it|should i|would it|does it) (better|best|worth)",
        r"how much (should|do|does|would)",
        r"what('s| is) the best (way|strategy|approach|time)",
        r"should i .+ or .+",
        r"(pro|con)s? (of|and)",
        r"is it (worth|better|smart|wise)",
    ]
    for pat in intermediate_patterns:
        if re.search(pat, msg):
            return "intermediate"

    # Default: beginner patterns (What is, How do I, Where can I)
    return "beginner"


# ── Profile update logic ───────────────────────────────────────────────────

def _shift_level(current: str, direction: str) -> str:
    """Shift a Low/Medium/High level up or down by one step."""
    order = ["Low", "Medium", "High"]
    idx = order.index(current) if current in order else 1
    if direction == "up":
        return order[min(idx + 1, 2)]
    elif direction == "down":
        return order[max(idx - 1, 0)]
    return current


def _detect_explicit_signals(message: str) -> str | None:
    """
    Check for explicit recalibration phrases.
    Returns ``"simplify"``, ``"advance"``, ``"clarity"``, ``"confusion"``,
    or ``None``.
    """
    msg = message.lower()
    for phrase in _SIMPLIFY_SIGNALS:
        if phrase in msg:
            return "simplify"
    for phrase in _ADVANCE_SIGNALS:
        if phrase in msg:
            return "advance"
    for phrase in _CLARITY_SIGNALS:
        if phrase in msg:
            return "clarity"
    for phrase in _CONFUSION_SIGNALS:
        if phrase in msg:
            return "confusion"
    return None


def update_profile_from_message(profile: dict, message: str,
                                message_type: str = "user_query") -> dict:
    """
    Analyse a user message and update their profile based on signals.

    * Vocabulary analysis (jargon vs. everyday terms)
    * Question type (basic vs. advanced)
    * Explicit signals ("explain more simply", "I know the basics")

    ``message_type``: ``"user_query"`` or ``"user_response"``

    Returns the *mutated* profile dict (caller should persist).
    """
    profile["interaction_count"] = profile.get("interaction_count", 0) + 1
    profile["updated_at"] = datetime.now(timezone.utc)

    # 1. Check explicit recalibration signals
    signal = _detect_explicit_signals(message)
    if signal == "simplify":
        profile["financial_literacy"] = _shift_level(
            profile["financial_literacy"], "down")
        profile["vocabulary_comfort"] = _shift_level(
            profile["vocabulary_comfort"], "down")
        profile["abstraction_tolerance"] = _shift_level(
            profile["abstraction_tolerance"], "down")
        profile["pace_preference"] = "Thorough"
        profile["confusion_signals"] = profile.get("confusion_signals", 0) + 1
        return profile
    elif signal == "advance":
        profile["financial_literacy"] = _shift_level(
            profile["financial_literacy"], "up")
        profile["vocabulary_comfort"] = _shift_level(
            profile["vocabulary_comfort"], "up")
        profile["pace_preference"] = "Short"
        profile["engagement_signals"] = profile.get("engagement_signals", 0) + 1
        return profile
    elif signal == "clarity":
        profile["engagement_signals"] = profile.get("engagement_signals", 0) + 1
        return profile
    elif signal == "confusion":
        profile["confusion_signals"] = profile.get("confusion_signals", 0) + 1
        profile["financial_literacy"] = _shift_level(
            profile["financial_literacy"], "down")
        profile["vocabulary_comfort"] = _shift_level(
            profile["vocabulary_comfort"], "down")
        profile["pace_preference"] = "Thorough"
        return profile

    # 2. Vocabulary analysis
    vocab_signals = extract_vocabulary_signals(message)
    if vocab_signals["terms_used"]:
        existing = set(profile.get("vocabulary_used", []))
        existing.update(vocab_signals["terms_used"])
        profile["vocabulary_used"] = list(existing)

        # Adjust vocabulary comfort based on terms the user *actively uses*
        all_terms = list(existing)
        estimated_level = classify_vocabulary_level(all_terms)
        profile["vocabulary_comfort"] = estimated_level

    # 3. Question type analysis (for queries only)
    if message_type == "user_query":
        q_type = extract_question_type(message)
        questions = profile.get("questions_asked", [])
        questions.append(q_type)
        # Keep last 20
        profile["questions_asked"] = questions[-20:]

        # Adjust literacy based on recent question pattern
        recent = questions[-5:]
        if recent.count("advanced") >= 2:
            profile["financial_literacy"] = _shift_level(
                profile["financial_literacy"], "up")
            profile["abstraction_tolerance"] = _shift_level(
                profile["abstraction_tolerance"], "up")
        elif recent.count("beginner") >= 3:
            profile["financial_literacy"] = _shift_level(
                profile["financial_literacy"], "down")
            profile["abstraction_tolerance"] = _shift_level(
                profile["abstraction_tolerance"], "down")
            profile["pace_preference"] = "Thorough"

    return profile


def update_profile_from_engagement(profile: dict,
                                   engagement_type: str) -> dict:
    """
    Update profile based on explicit engagement signals.

    ``engagement_type``:
        * ``"confusion_signal"`` — user expressed confusion
        * ``"clarity_signal"`` — user indicated understanding
        * ``"advanced_followup"`` — user asked a sophisticated follow-up

    Returns the mutated profile dict.
    """
    profile["updated_at"] = datetime.now(timezone.utc)

    if engagement_type == "confusion_signal":
        profile["confusion_signals"] = profile.get("confusion_signals", 0) + 1
        profile["financial_literacy"] = _shift_level(
            profile["financial_literacy"], "down")
        profile["vocabulary_comfort"] = _shift_level(
            profile["vocabulary_comfort"], "down")
        profile["pace_preference"] = "Thorough"

    elif engagement_type == "clarity_signal":
        profile["engagement_signals"] = profile.get("engagement_signals", 0) + 1
        # Don't shift up on a single clarity signal — just note it

    elif engagement_type == "advanced_followup":
        profile["engagement_signals"] = profile.get("engagement_signals", 0) + 1
        profile["financial_literacy"] = _shift_level(
            profile["financial_literacy"], "up")
        profile["abstraction_tolerance"] = _shift_level(
            profile["abstraction_tolerance"], "up")

    return profile


def update_profile_from_feedback(profile: dict,
                                 feedback_type: str) -> dict:
    """
    Update profile based on explicit UI feedback buttons.

    ``feedback_type``:
        * ``"confused"`` — response was too complex
        * ``"clear"`` — response was just right
        * ``"too_simple"`` — user wants more depth
        * ``"too_complex"`` — user wants simpler language

    Returns the mutated profile dict.
    """
    profile["updated_at"] = datetime.now(timezone.utc)

    if feedback_type in ("confused", "too_complex"):
        profile["confusion_signals"] = profile.get("confusion_signals", 0) + 1
        profile["financial_literacy"] = _shift_level(
            profile["financial_literacy"], "down")
        profile["vocabulary_comfort"] = _shift_level(
            profile["vocabulary_comfort"], "down")
        profile["abstraction_tolerance"] = _shift_level(
            profile["abstraction_tolerance"], "down")
        profile["pace_preference"] = "Thorough"

    elif feedback_type == "too_simple":
        profile["engagement_signals"] = profile.get("engagement_signals", 0) + 1
        profile["financial_literacy"] = _shift_level(
            profile["financial_literacy"], "up")
        profile["vocabulary_comfort"] = _shift_level(
            profile["vocabulary_comfort"], "up")
        profile["abstraction_tolerance"] = _shift_level(
            profile["abstraction_tolerance"], "up")
        profile["pace_preference"] = "Short"

    elif feedback_type == "clear":
        profile["engagement_signals"] = profile.get("engagement_signals", 0) + 1
        # Current calibration is working — don't change

    return profile


# ── System prompt calibration ───────────────────────────────────────────────

_LEVEL_INSTRUCTIONS = {
    "Low": {
        "vocabulary": (
            "- Use plain, everyday language \u2014 avoid financial jargon entirely\n"
            "- When technical terms are unavoidable, define them immediately inline\n"
            '  Example: "an index fund \u2014 basically a basket of stocks that follows the market"'
        ),
        "abstraction": (
            "- Lead with concrete examples BEFORE stating principles\n"
            "- Use real-world analogies (grocery shopping, saving for a vacation, piggy banks)\n"
            "- Short sentences. One concept at a time."
        ),
        "pace": (
            "- Build step-by-step, use numbered lists\n"
            "- Always offer to elaborate or go deeper\n"
            "- Check in: 'Does that make sense so far?'"
        ),
    },
    "Medium": {
        "vocabulary": (
            "- Use common financial terms but define advanced ones on first use\n"
            '  Example: "Your 401(k) contributions benefit from compound interest \u2014 '
            'you earn returns on your returns."'
        ),
        "abstraction": (
            "- Balance principles with examples\n"
            "- Analogies are helpful but not required for every concept"
        ),
        "pace": (
            "- Moderate detail \u2014 answer the question fully without over-explaining\n"
            "- Offer to go deeper on specific sub-topics"
        ),
    },
    "High": {
        "vocabulary": (
            "- Use precise financial vocabulary without hedging\n"
            "- Skip definitional scaffolding \u2014 respect their time\n"
            "- You can reference advanced concepts like tax-advantaged strategies, "
            "asset allocation models, and risk-adjusted returns without explanation"
        ),
        "abstraction": (
            "- State principles first, examples are optional\n"
            "- Comfortable with abstract reasoning about trade-offs"
        ),
        "pace": (
            "- Crisp answers, trust the user to ask for more\n"
            "- Focus on insight and nuance rather than foundations"
        ),
    },
}


def build_calibrated_system_prompt(profile: dict,
                                   context_articles: list[dict]) -> str:
    """
    Build a full system prompt for the LLM that includes:

    1. Base Money Buddy personality and guidelines
    2. Calibration instructions based on user profile dimensions
    3. aRCHi core tenets (No Judgment But Balanced, Non-Bias, etc.)
    4. Retrieved article context from FCAT
    5. Specific vocabulary/abstraction/pace guidance for this user's level
    """
    literacy = profile.get("financial_literacy", "Medium")
    vocab = profile.get("vocabulary_comfort", "Medium")
    abstraction = profile.get("abstraction_tolerance", "Medium")
    pace = profile.get("pace_preference", "Medium")

    # Map pace display
    pace_display = {
        "Short": "Short (crisp answers, trust user to ask for more)",
        "Medium": "Medium (balanced detail)",
        "Thorough": "Thorough (build step-by-step, use numbered lists)",
    }.get(pace, pace)

    literacy_display = {
        "Low": "Low (new to financial concepts)",
        "Medium": "Medium (familiar with common terms)",
        "High": "High (experienced with financial concepts)",
    }.get(literacy, literacy)

    vocab_display = {
        "Low": "Low (avoid jargon, define all terms)",
        "Medium": "Medium (common terms ok, define advanced ones)",
        "High": "High (comfortable with technical terminology)",
    }.get(vocab, vocab)

    abstraction_display = {
        "Low": "Low (lead with concrete examples and analogies)",
        "Medium": "Medium (balance principles and examples)",
        "High": "High (can handle abstract principles)",
    }.get(abstraction, abstraction)

    # Determine instruction tier (use the lowest dimension as anchor)
    levels = [literacy, vocab, abstraction]
    if "Low" in levels:
        tier = "Low"
    elif "High" in levels and levels.count("High") >= 2:
        tier = "High"
    else:
        tier = "Medium"

    instructions = _LEVEL_INSTRUCTIONS[tier]

    # Build article context
    context_block = ""
    if context_articles:
        parts = []
        for i, article in enumerate(context_articles, 1):
            plain_text = (article.get("content") or {}).get("plain_text", "").strip()
            if not plain_text:
                continue
            if len(plain_text) > 4000:
                plain_text = plain_text[:4000] + " [...]"
            parts.append(f"=== ARTICLE {i} ===\n{plain_text}")
        if parts:
            context_block = (
                "\n\nCONTEXT FROM FCAT:\n" + "\n\n".join(parts)
            )

    # Assemble system prompt
    prompt = f"""\
You are Money Buddy, a supportive financial education companion for aRCHi (Life on Easy).

USER PROFILE:
- Financial Literacy: {literacy_display}
- Vocabulary Comfort: {vocab_display}
- Abstraction Tolerance: {abstraction_display}
- Pace Preference: {pace_display}

CALIBRATION INSTRUCTIONS:

Vocabulary & Terminology:
{instructions["vocabulary"]}

Explanations & Examples:
{instructions["abstraction"]}

Pacing & Depth:
{instructions["pace"]}

MANDATORY RULES:
1. Base every answer exclusively on the article excerpts provided in CONTEXT FROM FCAT.
   Do NOT use your training data, general knowledge, or any information
   not explicitly present in the provided articles.
2. If the provided articles do not contain sufficient information to answer
   the question, say so honestly rather than making something up.
3. Do NOT speculate, infer beyond what is written, or fill gaps with outside knowledge.
4. Do NOT introduce any facts, statistics, or guidance not found in the articles.

aRCHi CORE TENETS:
- No Judgment But Balanced \u2014 Never make users feel bad about their financial situation or knowledge gaps
- Non-Bias \u2014 Avoid product pushing or financial institution bias
- You Have Time \u2014 Don't rush; build understanding step-by-step
- It's For You \u2014 Personalize to their situation, goals, and background

ANTI-PATTERNS (never do these):
- Don't narrate the profiling ("Based on your expertise level...")
- Don't use "simply" or "just" before explaining complex topics
- Don't chain jargon without definitions for users with Low vocabulary comfort
- Don't over-explain to users who demonstrate expertise{context_block}

Remember: This user should feel "This thing gets me." No judgment. Make finance accessible."""

    # Apply military calibration if applicable
    persona_tags = profile.get("persona_tags", [])
    if persona_tags:
        prompt = apply_military_context(prompt, persona_tags)

    return prompt


def get_calibrated_prompt(profile: dict, base_prompt: str) -> str:
    """
    Lightweight variant: augment an existing base prompt with calibration
    instructions derived from the user profile.  Useful when you already
    have a system prompt and just want to layer on profiling.
    """
    literacy = profile.get("financial_literacy", "Medium")
    vocab = profile.get("vocabulary_comfort", "Medium")

    calibration = (
        f"\n\n[ADAPTIVE CALIBRATION]\n"
        f"User financial literacy: {literacy}\n"
        f"User vocabulary comfort: {vocab}\n"
    )

    if literacy == "Low" or vocab == "Low":
        calibration += (
            "Adjust your response: use plain language, define any financial "
            "terms, lead with concrete examples, and keep sentences short.\n"
        )
    elif literacy == "High" and vocab == "High":
        calibration += (
            "Adjust your response: use precise financial terminology, skip "
            "basic definitions, be concise, and focus on insight.\n"
        )

    return base_prompt + calibration


def get_calibration_level(profile: dict) -> str:
    """
    Return a single string summarising the profile's calibration level
    for analytics / debugging.
    """
    dims = [
        profile.get("financial_literacy", "Medium"),
        profile.get("vocabulary_comfort", "Medium"),
        profile.get("abstraction_tolerance", "Medium"),
    ]
    if all(d == "High" for d in dims):
        return "advanced"
    if all(d == "Low" for d in dims):
        return "beginner"
    if "Low" in dims:
        return "beginner-intermediate"
    if "High" in dims:
        return "intermediate-advanced"
    return "intermediate"
