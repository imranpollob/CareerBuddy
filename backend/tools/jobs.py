from collections import Counter
import re

SKILLS = {"python": "Python", "sql": "SQL", "llm": "LLM applications", "rag": "RAG",
          "pytorch": "PyTorch", "aws": "AWS / Bedrock", "evaluation": "AI evaluation"}
ALIASES = {"python3": "python", "python 3": "python", "torch": "pytorch", "bedrock": "aws",
           "amazon bedrock": "aws", "amazon web services": "aws", "llms": "llm",
           "large language models": "llm", "retrieval augmented generation": "rag",
           "retrieval-augmented generation": "rag", "evals": "evaluation"}


def normalize_skills(values):
    result = []
    for value in values:
        key = ALIASES.get(value.strip().lower(), value.strip().lower())
        if key not in SKILLS:
            raise ValueError(f"Unsupported skill: {value}. Choose from {', '.join(SKILLS)}")
        if key not in result:
            result.append(key)
    return result


def extract_skills(text):
    terms = {**{k: k for k in SKILLS}, **ALIASES}
    return sorted({target for term, target in terms.items()
                   if re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text.lower())})


def requirements(jobs):
    counts = Counter(skill for job in jobs for skill in set(job["required_skills"]))
    return [{"skill": skill, "label": SKILLS[skill], "job_count": count,
             "sources": [{"job_id": j["id"], "url": j["source_url"], "synthetic": j["synthetic"],
                          "retrieved_at": j["retrieved_at"]} for j in jobs if skill in j["required_skills"]]}
            for skill, count in counts.most_common()]
