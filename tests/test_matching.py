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
