from collections import Counter
import re

SKILLS = {"python": "Python", "sql": "SQL", "llm": "LLM applications", "rag": "RAG",
          "pytorch": "PyTorch", "aws": "AWS", "evaluation": "AI evaluation",
          "javascript": "JavaScript", "typescript": "TypeScript", "react": "React", "fastapi": "FastAPI",
          "docker": "Docker", "git": "Git", "machine_learning": "Machine learning", "statistics": "Statistics",
          "tensorflow": "TensorFlow", "data_engineering": "Data engineering", "nlp": "Natural language processing",
          "kubernetes": "Kubernetes", "java": "Java", "cpp": "C++", "postgresql": "PostgreSQL",
          "prompt_engineering": "Prompt engineering", "embeddings": "Embeddings", "linux": "Linux",
          # Broader computer-science coverage: web, mobile, backend, data, infrastructure, quality.
          "golang": "Go", "rust": "Rust", "kotlin": "Kotlin", "swift": "Swift", "ruby": "Ruby", "scala": "Scala",
          "csharp": "C#", "node_js": "Node.js", "graphql": "GraphQL", "html": "HTML", "css": "CSS", "nextjs": "Next.js",
          "vue": "Vue", "angular": "Angular", "ios": "iOS", "android": "Android", "gcp": "Google Cloud", "azure": "Azure",
          "terraform": "Terraform", "ci_cd": "CI/CD", "spark": "Apache Spark", "airflow": "Airflow", "kafka": "Kafka",
          "redis": "Redis", "mongodb": "MongoDB", "distributed_systems": "Distributed systems", "system_design": "System design",
          "microservices": "Microservices", "rest_api": "REST APIs", "accessibility": "Accessibility",
          "performance_optimization": "Performance optimization", "playwright": "Playwright", "jest": "Jest",
          "application_security": "Application security", "data_analysis": "Data analysis"}
ALIASES = {"python3": "python", "python 3": "python", "torch": "pytorch", "bedrock": "aws",
           "amazon bedrock": "aws", "amazon web services": "aws", "llms": "llm",
           "large language models": "llm", "retrieval augmented generation": "rag",
           "retrieval-augmented generation": "rag", "evals": "evaluation", "c++": "cpp", "c#": "csharp",
           "ml": "machine_learning", "machine learning": "machine_learning", "postgres": "postgresql",
           "go lang": "golang", "node.js": "node_js", "nodejs": "node_js", "next.js": "nextjs", "vue.js": "vue",
           "google cloud": "gcp", "ci/cd": "ci_cd", "apache spark": "spark", "pyspark": "spark",
           "distributed systems": "distributed_systems", "system design": "system_design", "rest api": "rest_api",
           "restful": "rest_api", "appsec": "application_security", "application security": "application_security",
           "data analysis": "data_analysis", "swiftui": "swift", "wcag": "accessibility"}
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
    # Count canonical IDs so naming variants of one skill aggregate into one demand signal.
    skills_by_job = {job["id"]: {canonical_skill(s) for s in job["required_skills"]} for job in jobs}
    counts = Counter(skill for skills in skills_by_job.values() for skill in skills)
    return [{"skill": skill, "label": skill_label(skill), "job_count": count,
             "sources": [{"job_id": j["id"], "url": j["source_url"], "synthetic": j["synthetic"],
                          "retrieved_at": j["retrieved_at"]} for j in jobs if skill in skills_by_job[j["id"]]]}
            for skill, count in counts.most_common()]


# Ordered: the first matching family wins ("Software Engineer, Frontend" is frontend).
ROLE_FAMILIES = [
    ("security", r"security|appsec|threat|detection engineer|\bsecops\b"),
    ("ml_ai", r"machine learning|\bml\b|\bai\b|\bllm\b|applied scientist|research (engineer|scientist)|inference|deep learning|\bnlp\b|computer vision|ml ?ops|post-training"),
    ("data_science", r"data scien|data analyst|business analyst|analytics|quantitative|statistician"),
    ("data_engineering", r"data engineer|data platform|data infrastructure|\betl\b|data pipeline"),
    ("mobile", r"\bios\b|android|mobile|swift|kotlin"),
    ("frontend", r"front[- ]?end|\bui\b|\bweb (engineer|developer)|design engineer|react developer"),
    ("fullstack", r"full[- ]?stack"),
    ("devops_sre", r"site reliability|\bsre\b|devops|infrastructure|platform engineer|cloud engineer|reliability|production engineer|developer productivity|build engineer|systems engineer"),
    ("qa", r"\bqa\b|quality assurance|^(senior |staff )?(software )?quality engineer|test engineer|\bsdet\b|test automation|engineer in test"),
    ("backend", r"back[- ]?end|\bapi\b|distributed systems|server|payments engineer"),
    ("software", r"software (engineer|developer)|\bdeveloper\b|member of technical staff|\bswe\b|engineer"),
]
ROLE_FAMILY_LABELS = {"security": "Security", "ml_ai": "AI / ML", "data_science": "Data science & analytics",
                      "data_engineering": "Data engineering", "mobile": "Mobile", "frontend": "Frontend",
                      "fullstack": "Full stack", "devops_sre": "DevOps / SRE / Infrastructure", "qa": "Quality / testing",
                      "backend": "Backend", "software": "General software"}
# Which job families serve a target-role family (a generalist SWE fits many teams).
RELATED_FAMILIES = {"frontend": {"frontend", "fullstack"}, "backend": {"backend", "fullstack", "software"},
                    "fullstack": {"fullstack", "frontend", "backend"},
                    "software": {"software", "backend", "fullstack", "frontend", "mobile"}}
NON_ENGINEERING = (r"manager|director|head of|\bvp\b|vice president|recruit|account executive|sales|marketing|counsel|attorney|accountant"
                   r"|designer(?! engineer)|support|solutions? (engineer|architect|consultant)|customer|partner|business development"
                   r"|operations|demand planning|hardware|manufacturing|data center|\bav engineer|industrialization|business systems"
                   r"|\bit systems|fellows|annotation|adoption specialist|policy|\blead, ")


def role_family(title):
    """Classify a job title (or a target role) into a computer-science role family."""
    text = (title or "").casefold()
    if not text.strip() or re.search(NON_ENGINEERING, text):
        return None
    for family, pattern in ROLE_FAMILIES:
        if re.search(pattern, text):
            return family
    return None


def jobs_for_role(jobs, target_role):
    """Jobs that serve the target role: same CS role family, else exact title phrase."""
    family = role_family(target_role)
    if family:
        wanted = RELATED_FAMILIES.get(family, {family})
        return [job for job in jobs if (job.get("role_family") or role_family(job["title"])) in wanted]

    def words(value):
        return ' '.join(re.findall(r'[a-z0-9]+',value.casefold()))
    role=words(target_role)
    return [job for job in jobs if role and f' {role} ' in f" {words(job['title'])} "]
