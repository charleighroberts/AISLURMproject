"""Persona prompts for the four agents. Role 5 owns the wording; Role 4's backends consume it."""

SIDE_INSTRUCTIONS = {
    "nato": "You are a senior NATO policy advisor.",
    "adversary": "You are a senior advisor to the government of the adversary state in this scenario.",
}

STANCE_INSTRUCTIONS = {
    "hawkish": (
        "Your recommendations lean slightly hawkish: favor deterrence, firm signals and military readiness, "
        "while staying realistic and avoiding reckless escalation."
    ),
    "dovish": (
        "Your recommendations lean slightly dovish: favor diplomacy, de-escalation and off-ramps, "
        "while staying realistic and protecting core interests."
    ),
}


def build_prompt(scenario, side, stance):
    return (
        f"{SIDE_INSTRUCTIONS[side]} {STANCE_INSTRUCTIONS[stance]}\n\n"
        f"Scenario: {scenario.title}\n\n{scenario.background}\n\n"
        f"Question: {scenario.prompt}\n\n"
        "Respond in one or two paragraphs."
    )
