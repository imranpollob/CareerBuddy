from backend.tools.matching import match
from backend.tools.jobs import normalize_skills, extract_skills, requirements


def test_only_passing_assessment_evidence_counts():
    job={"required_skills":["python","rag","sql"]}
    result=match(job,[{"skill":"python","passed":True},{"skill":"rag","passed":False}])
    assert result["supported"]==["python"]
    assert result["missing"]==["rag","sql"]
    assert result["supported_count"]==1
    assert "1 of 3" in result["explanation"]


def test_normalization_and_sample_counts():
    assert normalize_skills(["Python 3","python","Bedrock"])==["python","aws"]
    assert extract_skills("Python, PyTorch and retrieval-augmented generation") == ["python","pytorch","rag"]
    jobs=[{"id":"1","required_skills":["python","python"],"source_url":"https://example.org","synthetic":True,"retrieved_at":"2026-11-14"}]
    assert requirements(jobs)[0]["job_count"]==1


def test_role_families_cover_computer_science_roles():
    from backend.tools.jobs import role_family, jobs_for_role
    assert role_family("Software Engineer, Frontend") == role_family("Frontend Developer") == "frontend"
    assert role_family("Senior Backend Engineer") == "backend"
    assert role_family("Machine Learning Engineer") == role_family("AI Engineer") == "ml_ai"
    assert role_family("Data Analyst") == "data_science" and role_family("Data Engineer Intern") == "data_engineering"
    assert role_family("Senior Site Reliability Engineer") == "devops_sre" and role_family("Android Engineer") == "mobile"
    assert role_family("Application Security Engineer") == "security"
    for title in ("Engineering Manager", "Solutions Engineer", "Manufacturing Quality Engineer", "Writer"):
        assert role_family(title) is None
    jobs = [{"title": "Software Engineer, Frontend"}, {"title": "Full Stack Engineer"}, {"title": "Data Scientist"}]
    assert [j["title"] for j in jobs_for_role(jobs, "Frontend Developer")] == ["Software Engineer, Frontend", "Full Stack Engineer"]
    assert jobs_for_role(jobs, "Writer") == []


def test_marketplace_ranking_fits_role_and_career_stage():
    from backend.agents.marketplace import rank_for_candidate
    jobs = [{"id": "intern", "title": "Software Engineer Intern, Fullstack", "career_level": "internship"},
            {"id": "senior", "title": "Senior Full Stack Engineer", "career_level": "senior"},
            {"id": "data", "title": "Analytics Engineer Intern", "career_level": "internship"}]
    matches = [{"job": j, "supported_count": 1 if j["id"] == "data" else 0, "required_count": 2} for j in jobs]
    student = rank_for_candidate(matches, {"target_role": "Full Stack Developer", "candidate_track": "student", "years_experience": 0}, jobs)
    assert [m["job"]["id"] for m in student] == ["intern", "senior", "data"]
    veteran = rank_for_candidate(matches, {"target_role": "Full Stack Developer", "candidate_track": "unspecified", "years_experience": 6}, jobs)
    assert [m["job"]["id"] for m in veteran][:2] == ["senior", "intern"]
