#!/usr/bin/env python3
"""
Financial Jargon Detector for the Adaptive-Explainer skill.
Provides tier-based vocabulary lists and detection logic to flag terms
that should be defined or simplified based on a user's comfort level.
"""

import re

# ── Tier-based financial vocabulary ─────────────────────────────────────────

FINANCIAL_JARGON_TIERS = {
    "basic": [
        "savings account", "checking account", "credit card", "debit card",
        "interest", "loan", "budget", "debt", "income", "expenses",
        "bank account", "paycheck", "bills", "mortgage", "rent",
        "credit", "balance", "deposit", "withdrawal", "payment",
    ],
    "intermediate": [
        "401(k)", "roth ira", "traditional ira", "compound interest",
        "index fund", "etf", "diversification", "asset allocation",
        "emergency fund", "credit score", "mutual fund", "stock",
        "bond", "portfolio", "dividend", "inflation", "net worth",
        "apr", "apy", "principal", "amortization", "refinance",
        "withholding", "w-4", "w-2", "1099", "standard deduction",
        "contribution limit", "employer match", "vesting",
    ],
    "advanced": [
        "expense ratio", "tax-loss harvesting", "dollar-cost averaging",
        "rebalancing", "risk-adjusted return", "bond ladder",
        "marginal tax rate", "qualified dividends", "capital gains distribution",
        "basis points", "alpha", "beta", "sharpe ratio",
        "roth conversion", "backdoor roth", "mega backdoor roth",
        "tax-deferred", "tax-exempt", "tax-advantaged",
        "sequence of returns risk", "safe withdrawal rate",
        "glide path", "target-date fund", "fiduciary",
        "total return", "yield curve", "duration",
        "sector rotation", "monte carlo simulation",
    ],
}

# Plain-language definitions keyed by lowercase term
JARGON_DEFINITIONS = {
    # Basic
    "interest": "the cost of borrowing money, or the reward you earn for saving it",
    "budget": "a plan for how you'll spend and save your money",
    "debt": "money you owe to someone else",
    "mortgage": "a loan specifically for buying a home",
    "credit": "your ability to borrow money based on your history of paying it back",
    # Intermediate
    "401(k)": "a retirement savings account offered through your employer, often with tax benefits",
    "roth ira": "a retirement account where you pay taxes now but withdrawals in retirement are tax-free",
    "traditional ira": "a retirement account where contributions may be tax-deductible now, but you pay taxes on withdrawals later",
    "compound interest": "earning interest on your interest \u2014 your money grows faster over time",
    "index fund": "a basket of stocks that follows a market index, like the S&P 500, giving you broad diversification in one purchase",
    "etf": "exchange-traded fund \u2014 similar to an index fund but trades on the stock market like a single stock",
    "diversification": "spreading your money across different investments so you're not putting all your eggs in one basket",
    "asset allocation": "how you divide your money among different types of investments like stocks, bonds, and cash",
    "emergency fund": "money set aside for unexpected expenses, usually 3-6 months of living costs",
    "credit score": "a number (usually 300\u2013850) that tells lenders how reliable you are at repaying debt",
    "mutual fund": "a pool of money from many investors that a professional manager invests in stocks, bonds, or other assets",
    "portfolio": "the collection of all your investments",
    "dividend": "a share of a company's profits paid out to stockholders",
    "inflation": "when prices go up over time, so your money buys less",
    "net worth": "what you own minus what you owe",
    "apr": "annual percentage rate \u2014 the yearly cost of borrowing money, including fees",
    "apy": "annual percentage yield \u2014 the actual rate of return on savings, including compound interest",
    "principal": "the original amount of money you invested or borrowed, before interest",
    "contribution limit": "the maximum amount you're allowed to put into a retirement account each year",
    "employer match": "free money your employer adds to your retirement account based on how much you contribute",
    "vesting": "how long you need to work at a company before you fully own your employer's retirement contributions",
    # Advanced
    "expense ratio": "the annual fee an investment fund charges, expressed as a percentage of your investment",
    "tax-loss harvesting": "selling investments at a loss to offset gains and reduce your tax bill",
    "dollar-cost averaging": "investing a fixed amount on a regular schedule regardless of market prices",
    "rebalancing": "adjusting your portfolio back to your target mix of investments",
    "risk-adjusted return": "how much return an investment earns relative to the risk you took",
    "bond ladder": "buying bonds that mature at different times to manage risk and maintain cash flow",
    "marginal tax rate": "the tax rate on your last dollar of income \u2014 not your whole income",
    "qualified dividends": "dividends taxed at lower capital gains rates instead of regular income rates",
    "capital gains distribution": "when a fund passes along profits from selling investments inside the fund",
    "basis points": "one hundredth of a percentage point (100 basis points = 1%)",
    "roth conversion": "moving money from a traditional IRA to a Roth IRA, paying taxes now for tax-free growth later",
    "backdoor roth": "a strategy for high earners to get money into a Roth IRA by first contributing to a traditional IRA",
    "fiduciary": "someone legally required to act in your best financial interest",
    "safe withdrawal rate": "the percentage of your retirement savings you can spend each year without running out",
    "target-date fund": "a fund that automatically adjusts its investment mix as you get closer to retirement",
}

# All terms flattened for quick lookup: term -> tier
_TERM_TO_TIER: dict[str, str] = {}
for _tier, _terms in FINANCIAL_JARGON_TIERS.items():
    for _term in _terms:
        _TERM_TO_TIER[_term.lower()] = _tier


def _tier_rank(tier: str) -> int:
    """Return numeric rank for a tier string."""
    return {"basic": 0, "intermediate": 1, "advanced": 2}.get(tier, 0)


def _comfort_to_tier(vocabulary_comfort: str) -> str:
    """Map a vocabulary_comfort level to the highest tier the user is comfortable with."""
    return {"Low": "basic", "Medium": "intermediate", "High": "advanced"}.get(
        vocabulary_comfort, "intermediate"
    )


# ── Public API ──────────────────────────────────────────────────────────────

def detect_jargon_in_text(text: str) -> list[dict]:
    """
    Find all recognised financial jargon terms in *text*.

    Returns a list of dicts:
        [{"term": str, "tier": str, "definition": str | None}, ...]
    sorted from most advanced to least.
    """
    text_lower = text.lower()
    found = []
    seen = set()

    # Longest-match first so "compound interest" isn't shadowed by "interest"
    sorted_terms = sorted(_TERM_TO_TIER.keys(), key=len, reverse=True)

    for term in sorted_terms:
        if term in seen:
            continue
        # Word-boundary-ish match (handles parentheses in terms like "401(k)")
        escaped = re.escape(term)
        if re.search(rf"(?<![a-z]){escaped}(?![a-z])", text_lower):
            seen.add(term)
            found.append({
                "term": term,
                "tier": _TERM_TO_TIER[term],
                "definition": JARGON_DEFINITIONS.get(term),
            })

    found.sort(key=lambda d: _tier_rank(d["tier"]), reverse=True)
    return found


def detect_jargon_in_response(response: str, user_profile: dict) -> dict:
    """
    Scan an LLM response for jargon that may be above the user's comfort level.

    Args:
        response: The generated LLM response text.
        user_profile: The user's profile dict (needs ``vocabulary_comfort``).

    Returns:
        {
            "flagged_terms": [{"term", "tier", "definition"}],
            "ok_terms": [{"term", "tier"}],
            "suggestions": str,  # human-readable summary
        }
    """
    comfort = user_profile.get("vocabulary_comfort", "Medium")
    max_tier = _comfort_to_tier(comfort)
    max_rank = _tier_rank(max_tier)

    all_terms = detect_jargon_in_text(response)

    flagged = [t for t in all_terms if _tier_rank(t["tier"]) > max_rank]
    ok = [t for t in all_terms if _tier_rank(t["tier"]) <= max_rank]

    if flagged:
        names = ", ".join(f'"{t["term"]}"' for t in flagged)
        suggestions = (
            f"The response contains {len(flagged)} term(s) above the user's "
            f"comfort level ({comfort}): {names}. Consider defining them inline "
            f"or replacing with simpler alternatives."
        )
    else:
        suggestions = "All terms are within the user's comfort level."

    return {
        "flagged_terms": flagged,
        "ok_terms": [{"term": t["term"], "tier": t["tier"]} for t in ok],
        "suggestions": suggestions,
    }


def get_definition(term: str) -> str | None:
    """Return the plain-language definition for a term, or None."""
    return JARGON_DEFINITIONS.get(term.lower())


def classify_vocabulary_level(terms: list[str]) -> str:
    """
    Given a list of terms a user has used, estimate their vocabulary tier.

    Returns "Low", "Medium", or "High".
    """
    if not terms:
        return "Low"

    tier_counts = {"basic": 0, "intermediate": 0, "advanced": 0}
    for term in terms:
        tier = _TERM_TO_TIER.get(term.lower())
        if tier:
            tier_counts[tier] += 1

    if tier_counts["advanced"] >= 2:
        return "High"
    if tier_counts["intermediate"] >= 2 or tier_counts["advanced"] >= 1:
        return "Medium"
    return "Low"
