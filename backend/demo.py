"""Career-planning templates used with each signed-in user's own profile."""

JOURNEYS = {
    "career_switcher": {
        "title": "Software Engineer → AI Engineer",
        "description": "Build on your software engineering experience. Demonstrate Python fundamentals, then add LLM applications, retrieval, and evaluation.",
        "portfolio_project": "Extend a backend service with a grounded document assistant: retrieve passages, cite sources, validate tool inputs, and evaluate answers.",
        "suggested_prompt": "I am a software engineer transitioning to AI engineering. Build my learning roadmap.",
        "target_levels": ["mid", "unspecified"],
    },
    "student": {
        "title": "Student → First AI Engineering Role",
        "description": "Start with Python and SQL, build an explainable AI project, and explore internships and graduate roles while strengthening your evidence.",
        "portfolio_project": "Build a campus study assistant with Python, a small document collection, source citations, and a test set of ten questions. Publish a README explaining what works and what fails.",
        "suggested_prompt": "I am a computer science student seeking my first AI engineering role. Build my learning roadmap.",
        "target_levels": ["internship", "entry"],
    },
    "experienced": {
        "title": "Demonstrate Applied AI Skills",
        "description": "Connect demonstrated fundamentals with applied AI opportunities and identify remaining requirements.",
        "portfolio_project": "Build and evaluate an AI feature with cited evidence, clear failure handling, and documented tradeoffs.",
        "suggested_prompt": "Find jobs that match my demonstrated skills.",
        "target_levels": ["mid", "senior", "unspecified"],
    },
}
