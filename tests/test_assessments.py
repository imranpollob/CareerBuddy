import pytest
from backend.tools.assessments import grade, BANK


@pytest.mark.parametrize("skill", BANK)
def test_grading_each_topic(skill):
    answers = {f"q{i+1}": q[2] for i,q in enumerate(BANK[skill])}
    assert grade(skill, answers)["score"] == 100
    answers["q1"] = (answers["q1"] + 1) % 4
    assert grade(skill, answers)["score"] == 75
    answers["q2"] = (answers["q2"] + 1) % 4
    assert grade(skill, answers)["passed"] is False


@pytest.mark.parametrize("answers", [{}, {"q1":0}, {"q1":0,"q2":2,"q3":1,"q4":True}, {"q1":9,"q2":2,"q3":1,"q4":3}])
def test_invalid_answers_rejected(answers):
    with pytest.raises(ValueError):
        grade("python",answers)


def test_no_answer_keys_in_pending_attempt(candidate):
    data=candidate.post("/api/assessments",json={"skill":"python"}).json()
    assert data["status"] == "pending"
    assert all(set(q)=={"id","prompt","choices"} for q in data["questions"])
    assert "result" not in data


def test_grade_cannot_be_supplied_or_replayed(candidate):
    data=candidate.post("/api/assessments",json={"skill":"python"}).json()
    url=f"/api/assessments/{data['id']}/submit"
    answers={"q1":0,"q2":2,"q3":1,"q4":3}
    assert candidate.post(url,json={"answers":answers,"score":100}).status_code==422
    assert candidate.post(url,json={"answers":{**answers,"q1":True}}).status_code==422
    assert candidate.post(url,json={"answers":answers}).json()["result"]["score"]==100
    assert candidate.post(url,json={"answers":answers}).status_code==409


def test_invalid_submission_does_not_change_evidence(candidate):
    data=candidate.post("/api/assessments",json={"skill":"python"}).json()
    assert candidate.post(f"/api/assessments/{data['id']}/submit",json={"answers":{"q1":0}}).status_code==400
    assert candidate.get("/api/dashboard").json()["skills"]==[]
