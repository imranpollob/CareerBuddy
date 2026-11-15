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
# Model-generated IDs drift ("web_performance_optimization" vs "performance_optimization").
# Matching compares canonical IDs so assessment evidence lines up with job requirements.
CANONICAL_ALIASES = {"web_performance": "performance_optimization", "frontend_performance": "performance_optimization",
                     "performance_tuning": "performance_optimization", "web_performance_optimization": "performance_optimization",
                     "a11y": "accessibility", "wcag": "accessibility", "web_accessibility": "accessibility",
                     "playwright_testing": "playwright", "playwright_e2e": "playwright", "playwright_e2e_testing": "playwright",
                     "end_to_end_testing": "e2e_testing", "e2e_tests": "e2e_testing", "jest_testing": "jest",
                     "reactjs": "react", "react_js": "react", "react.js": "react", "nodejs": "node_js", "node.js": "node_js",
                     "node": "node_js", "ts": "typescript", "js": "javascript", "large_language_models": "llm",
                     "retrieval_augmented_generation": "rag", "amazon_bedrock": "aws", "amazon_web_services": "aws"}
QUALIFIER_PREFIXES = ("web_", "frontend_", "front_end_", "backend_", "modern_", "advanced_", "basic_", "core_")
QUALIFIER_SUFFIXES = ("_framework", "_library", "_programming", "_language", "_fundamentals", "_basics", "_concepts", "_skills")


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


def canonical_skill(skill):
    """Collapse qualifier/alias variants of a skill ID onto one canonical ID."""
    key = normalize_skills([skill])[0]
    key = CANONICAL_ALIASES.get(key, key)
    known = set(SKILLS) | set(ALIASES.values()) | set(CANONICAL_ALIASES.values())
    if key in known:
        return key
    for prefix in QUALIFIER_PREFIXES:
        stem = CANONICAL_ALIASES.get(key[len(prefix):], key[len(prefix):])
        if key.startswith(prefix) and stem in known:
            return stem
    for suffix in QUALIFIER_SUFFIXES:
        stem = CANONICAL_ALIASES.get(key[:-len(suffix)], key[:-len(suffix)])
        if key.endswith(suffix) and stem in known:
            return stem
    return key


def canonical_skills(values):
    return list(dict.fromkeys(canonical_skill(v) for v in values))


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


def jobs_for_role(jobs, target_role):
    """Conservative title coverage; never treat a different role's sample as demand."""
    def words(value):
        return ' '.join(re.findall(r'[a-z0-9]+',value.casefold()))
    role=words(target_role)
    return [job for job in jobs if role and f' {role} ' in f" {words(job['title'])} "]
