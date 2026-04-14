#!/usr/bin/env python3
"""
Military-Specific Calibration for the Adaptive-Explainer skill.
Provides military-aware financial terminology, analogies, and prompt
augmentation for aRCHi's military audience (active duty, veterans,
military spouses, and first-generation investors).
"""

# ── Military financial terms and their plain-language expansions ────────────

MILITARY_FINANCIAL_TERMS = {
    "TSP": "Thrift Savings Plan \u2014 the federal government's retirement savings plan for service members and federal employees, similar to a civilian 401(k)",
    "BRS": "Blended Retirement System \u2014 combines a traditional pension (reduced from 50% to 40% of base pay at 20 years) with TSP matching contributions",
    "BAH": "Basic Allowance for Housing \u2014 a monthly payment to help cover housing costs, which varies by location and rank",
    "BAS": "Basic Allowance for Subsistence \u2014 a monthly payment to offset the cost of food",
    "PCS": "Permanent Change of Station \u2014 an official relocation to a new duty station",
    "VA loan": "a mortgage backed by the Department of Veterans Affairs with benefits like no down payment and no private mortgage insurance",
    "GI Bill": "education benefits that help cover tuition, housing, and other costs for service members and veterans",
    "SGLI": "Servicemembers' Group Life Insurance \u2014 low-cost group life insurance for active duty members",
    "VGLI": "Veterans' Group Life Insurance \u2014 the post-service continuation of SGLI coverage",
    "SBP": "Survivor Benefit Plan \u2014 provides ongoing income to your beneficiaries if you pass away after retirement",
    "TRICARE": "the health care program for uniformed service members, retirees, and their families",
    "SCRA": "Servicemembers Civil Relief Act \u2014 provides financial protections like interest rate caps on pre-service debts",
    "MHA": "Monthly Housing Allowance \u2014 the housing stipend paid under the GI Bill based on your school's location",
    "ETS": "Expiration Term of Service \u2014 the date your current enlistment or service obligation ends",
    "LES": "Leave and Earnings Statement \u2014 your military pay stub showing all pay, allowances, deductions, and leave balances",
}

# ── Military-flavored analogies for common financial concepts ───────────────

MILITARY_ANALOGIES = {
    "diversification": (
        "Like having multiple supply lines \u2014 if one gets cut off, "
        "you're still operational."
    ),
    "emergency fund": (
        "Your financial reserve unit \u2014 always ready when you need backup, "
        "ideally covering 3\u20136 months of expenses."
    ),
    "compound interest": (
        "Rank progression for your money \u2014 the longer it serves, "
        "the more it earns."
    ),
    "budget": (
        "Like an operations order for your finances \u2014 a clear plan "
        "so every dollar has a mission."
    ),
    "asset allocation": (
        "Deploying your resources across different sectors \u2014 some on "
        "offense (stocks), some on defense (bonds), some in reserve (cash)."
    ),
    "dollar-cost averaging": (
        "Steady resupply \u2014 investing the same amount every paycheck "
        "regardless of market conditions, so you average out the highs and lows."
    ),
    "rebalancing": (
        "Adjusting your formation \u2014 when one flank advances too far, "
        "you pull it back into alignment with the rest of your line."
    ),
    "index fund": (
        "The whole battalion in one package \u2014 instead of picking "
        "individual soldiers (stocks), you get the full unit and share "
        "in the overall performance."
    ),
    "credit score": (
        "Your financial readiness rating \u2014 a number that tells lenders "
        "how mission-ready you are for borrowing."
    ),
    "net worth": (
        "Your total combat power \u2014 everything you own minus everything "
        "you owe."
    ),
    "401(k)": (
        "The civilian version of the TSP \u2014 a retirement savings account "
        "offered by private-sector employers."
    ),
}

# ── TSP fund descriptions (most common military investment question) ────────

TSP_FUNDS = {
    "G Fund": "Government Securities \u2014 the safest option, backed by the U.S. government, but lowest growth potential",
    "F Fund": "Fixed Income (Bond) Index \u2014 tracks the U.S. bond market, moderate risk and return",
    "C Fund": "Common Stock Index \u2014 tracks the S&P 500 (large U.S. companies), higher growth potential",
    "S Fund": "Small Cap Stock Index \u2014 tracks small and mid-size U.S. companies, higher risk/reward than C Fund",
    "I Fund": "International Stock Index \u2014 tracks stocks in developed countries outside the U.S.",
    "L Funds": "Lifecycle Funds \u2014 automatically adjust your mix of G, F, C, S, and I Funds based on your target retirement date",
}

# ── Military-specific financial tips by life stage ──────────────────────────

MILITARY_LIFE_STAGE_TIPS = {
    "active_duty": [
        "Maximize your TSP contributions, especially the Roth TSP option while in a lower tax bracket or a combat zone (tax-free contributions).",
        "BAH and BAS are not taxable \u2014 this effectively lowers your tax bracket, making Roth contributions especially powerful.",
        "Check your SGLI coverage and make sure your beneficiaries are up to date.",
    ],
    "pcs_transition": [
        "A PCS is a good time to review your budget \u2014 BAH rates change by location.",
        "Consider whether to buy or rent at your new duty station based on how long you expect to be there.",
        "VA loans have no down payment requirement and can be reused at each new station.",
    ],
    "separating": [
        "Understand your BRS pension calculation and whether you've reached the vesting threshold.",
        "Your TSP stays with you after separation \u2014 don't cash it out (you'll pay taxes and penalties).",
        "Use your GI Bill benefits strategically; they can also transfer to dependents if you've served long enough.",
        "TRICARE coverage ends, so plan for health insurance through a new employer or the VA.",
    ],
    "veteran": [
        "Check your VA loan eligibility \u2014 it's one of the strongest mortgage benefits available.",
        "Look into VA disability compensation; it's tax-free and doesn't affect your retirement pay under concurrent receipt.",
        "Your TSP can be rolled into an IRA for more investment options, or you can keep it for the low fees.",
    ],
    "military_spouse": [
        "The Military Spouse Career Advancement Account (MyCAA) offers up to $4,000 for education and training.",
        "During PCS moves, you may face gaps in employment \u2014 build an emergency fund to bridge those periods.",
        "You may be eligible for spousal benefits under the GI Bill if your service member transfers them.",
    ],
}


def get_military_terms_for_prompt() -> str:
    """
    Return a formatted block of military financial terms suitable for
    injecting into an LLM system prompt.
    """
    lines = []
    for abbrev, description in MILITARY_FINANCIAL_TERMS.items():
        lines.append(f"- {abbrev}: {description}")
    return "\n".join(lines)


def get_analogy(concept: str) -> str | None:
    """
    Return a military-flavored analogy for a financial concept, or None.
    """
    return MILITARY_ANALOGIES.get(concept.lower())


def apply_military_context(base_prompt: str, persona_tags: list[str]) -> str:
    """
    If the user has a military-related persona tag, augment *base_prompt*
    with military-aware context, terminology, and analogy instructions.

    Returns the augmented prompt (or the original if no military tags).
    """
    military_tags = {"military", "veteran", "active_duty", "military_spouse",
                     "national_guard", "reservist", "first_gen_investor"}
    matched = set(t.lower() for t in persona_tags) & military_tags

    if not matched:
        return base_prompt

    # Build the military context block
    sections = []

    sections.append(
        "MILITARY-AWARE CALIBRATION:\n"
        "This user has a military background. Keep the following in mind:"
    )

    # Core terms
    sections.append(
        "Military Financial Terms You Should Know:\n" +
        get_military_terms_for_prompt()
    )

    # TSP awareness
    sections.append(
        "TSP Fund Overview (commonly asked by military users):\n" +
        "\n".join(f"- {fund}: {desc}" for fund, desc in TSP_FUNDS.items())
    )

    # Analogies
    sections.append(
        "When explaining financial concepts, prefer military-friendly analogies:\n" +
        "\n".join(
            f'- {concept}: "{analogy}"'
            for concept, analogy in MILITARY_ANALOGIES.items()
        )
    )

    # Life-stage tips
    stage_keys = []
    if "active_duty" in matched:
        stage_keys.append("active_duty")
    if "veteran" in matched:
        stage_keys.append("veteran")
    if "military_spouse" in matched:
        stage_keys.append("military_spouse")
    if not stage_keys:
        # Default to general active duty tips
        stage_keys.append("active_duty")

    for key in stage_keys:
        tips = MILITARY_LIFE_STAGE_TIPS.get(key, [])
        if tips:
            label = key.replace("_", " ").title()
            sections.append(
                f"Relevant Tips ({label}):\n" +
                "\n".join(f"- {tip}" for tip in tips)
            )

    # Append to base prompt
    military_block = "\n\n".join(sections)
    return f"{base_prompt}\n\n{military_block}"
