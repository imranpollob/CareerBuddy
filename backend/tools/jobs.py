from collections import Counter
import re

SKILLS = {"python": "Python", "sql": "SQL", "llm": "LLM applications", "rag": "RAG",
          "pytorch": "PyTorch", "aws": "AWS / Bedrock", "evaluation": "AI evaluation",
          "javascript": "JavaScript", "typescript": "TypeScript", "react": "React", "fastapi": "FastAPI",
          "docker": "Docker", "git": "Git", "machine_learning": "Machine learning", "statistics": "Statistics",
          "tensorflow": "TensorFlow", "data_engineering": "Data engineering", "nlp": "Natural language processing",
          "kubernetes": "Kubernetes", "java": "Java", "cpp": "C++", "postgresql": "PostgreSQL",
          "prompt_engineering": "Prompt engineering", "embeddings": "Embeddings", "linux": "Linux"}
ALIASES = {"python3": "python", "python 3": "python", "torch": "pytorch", "bedrock": "aws",
           "amazon bedrock": "aws", "amazon web services": "aws", "llms": "llm",
           "large language models": "llm", "retrieval augmented generation": "rag",
           "retrieval-augmented generation": "rag", "evals": "evaluation", "c++": "cpp", "c#": "csharp",
           "ml": "machine_learning", "machine learning": "machine_learning", "postgres": "postgresql"}


def normalize_skills(values):
    result = []
    for value in values:
        key = ALIASES.get(value.strip().lower(), value.strip().lower())
        key = re.sub(r"[\s/-]+", "_", key)
        if not re.fullmatch(r"[a-z][a-z0-9_+.]{1,63}", key):
            raise ValueError("Use a short skill name containing letters, numbers, spaces or underscores")
        if key not in result:
            result.append(key)
    return result


def skill_label(skill):
    return SKILLS.get(skill, skill.replace("_", " ").title())


def extract_skills(text):
    terms = {**{k: k for k in SKILLS}, **ALIASES}
    return sorted({target for term, target in terms.items()
                   if re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text.lower())})


def requirements(jobs):
    counts = Counter(skill for job in jobs for skill in set(job["required_skills"]))
    return [{"skill": skill, "label": skill_label(skill), "job_count": count,
             "sources": [{"job_id": j["id"], "url": j["source_url"], "synthetic": j["synthetic"],
                          "retrieved_at": j["retrieved_at"]} for j in jobs if skill in j["required_skills"]]}
            for skill, count in counts.most_common()]
