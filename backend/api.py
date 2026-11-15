from contextlib import asynccontextmanager
from dataclasses import dataclass, field
import logging
import secrets
from threading import Lock

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from botocore.exceptions import BotoCoreError, ClientError

from backend.config import Settings
from backend.db import MemoryRepository, DynamoRepository, Conflict
from backend.models import ProfileUpdate, JobCreate, AssessmentCreate, Submission, ChatRequest, ChatResponse
from backend.models import Profile, Job, DashboardRecord, MarketRecord, AssessmentRecord, RoadmapRecord, LessonRecord, MatchRecord, CandidateMatch
from backend.orchestrator import chat
from backend.service import Service
from backend.demo import DEMO_IDENTITIES

ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000", "http://127.0.0.1:8000"]


@dataclass
class Session:
    uid: str
    role: str
    history: list = field(default_factory=list)
    lock: Lock = field(default_factory=Lock)


def create_app(repo=None, settings=None):
    load_dotenv()
    settings = settings or Settings()
    if repo is None:
        repo = MemoryRepository() if settings.repository == "memory" else DynamoRepository(
            settings.table_name, settings.dynamodb_endpoint if settings.repository == "dynamodb-local" else None)
    service = Service(repo)
    sessions = {}

    @asynccontextmanager
    async def lifespan(app):
        service.seed()
        yield

    app = FastAPI(title="SkillPilot", version="0.1.0", lifespan=lifespan)
    app.state.service = service
    app.add_middleware(CORSMiddleware, allow_origins=ORIGINS, allow_credentials=True,
                       allow_methods=["GET", "POST", "PATCH"], allow_headers=["Content-Type"])

    @app.middleware("http")
    async def reject_cross_origin_writes(request, call_next):
        if request.method in {"POST", "PATCH", "DELETE", "PUT"} and request.headers.get("origin") not in [None, *ORIGINS]:
            return JSONResponse(status_code=403, content={"detail": "Untrusted request origin"})
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.exception_handler(ValueError)
    async def bad_input(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(PermissionError)
    async def forbidden(request, exc):
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(Conflict)
    async def conflict(request, exc):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    async def storage_error(request, exc):
        logging.getLogger(__name__).warning("Storage unavailable: %s", type(exc).__name__)
        return JSONResponse(status_code=503, content={"detail": "Storage is unavailable. Check the configured repository and local service."})

    app.add_exception_handler(ClientError, storage_error)
    app.add_exception_handler(BotoCoreError, storage_error)

    def authenticated(request: Request):
        session = sessions.get(request.cookies.get("skillpilot_session"))
        if session is None:
            raise HTTPException(401, "Choose a demo session first")
        return session

    def candidate(session=Depends(authenticated)):
        if session.role != "candidate":
            raise HTTPException(403, "Candidate session required")
        return session

    def employer(session=Depends(authenticated)):
        if session.role != "employer":
            raise HTTPException(403, "Employer session required")
        return session

    def start_session(identity, request, response):
        previous = request.cookies.get("skillpilot_session")
        if previous:
            sessions.pop(previous, None)
        token = secrets.token_urlsafe(32)
        uid, role = DEMO_IDENTITIES[identity]
        sessions[token] = Session(uid=uid, role=role)
        response.set_cookie("skillpilot_session", token, httponly=True, samesite="strict", max_age=14400)
        return {"profile": service.profile(uid), "mode": settings.ai_mode}

    @app.get("/api/health")
    def health():
        return {"status": "ok", "ai_mode": settings.ai_mode, "repository": settings.repository,
                "persistence": "temporary; resets on restart" if settings.repository == "memory" else "DynamoDB",
                "model_id": settings.model_id if settings.ai_mode == "bedrock" else "offline fixture"}

    @app.post("/api/demo/candidate")
    def candidate_login(request: Request, response: Response):
        return start_session("candidate", request, response)

    @app.post("/api/demo/student")
    def student_login(request: Request, response: Response):
        return start_session("student", request, response)

    @app.post("/api/demo/employer")
    def employer_login(request: Request, response: Response):
        return start_session("employer", request, response)

    @app.get("/api/session")
    def session_info(session=Depends(authenticated)):
        return {"profile": service.profile(session.uid), "mode": settings.ai_mode}

    @app.get("/api/dashboard", response_model=DashboardRecord, response_model_exclude_none=True)
    def dashboard(session=Depends(candidate)):
        return service.dashboard(session.uid)

    @app.patch("/api/profile", response_model=Profile)
    def update_profile(body: ProfileUpdate, session=Depends(candidate)):
        return service.update_profile(session.uid, body)

    @app.get("/api/jobs", response_model=list[Job])
    def jobs(session=Depends(authenticated)):
        return service.jobs()

    @app.get("/api/market", response_model=MarketRecord)
    def market(session=Depends(authenticated)):
        return service.market()

    @app.post("/api/assessments", response_model=AssessmentRecord, response_model_exclude_none=True)
    def create_assessment(body: AssessmentCreate, session=Depends(candidate)):
        return service.create_assessment(session.uid, body.skill)

    @app.get("/api/assessments/{assessment_id}", response_model=AssessmentRecord, response_model_exclude_none=True)
    def assessment(assessment_id: str, session=Depends(candidate)):
        return service.assessment(session.uid, assessment_id)

    @app.post("/api/assessments/{assessment_id}/submit", response_model=AssessmentRecord, response_model_exclude_none=True)
    def submit(assessment_id: str, body: Submission, session=Depends(candidate)):
        return service.submit(session.uid, assessment_id, body.answers)

    @app.get("/api/roadmap", response_model=RoadmapRecord)
    def roadmap(session=Depends(candidate)):
        return service.roadmap(session.uid)

    @app.get("/api/lessons/{skill}", response_model=LessonRecord)
    def lesson(skill: str, session=Depends(candidate)):
        return service.lesson(session.uid, skill)

    @app.post("/api/lessons/{skill}/complete", response_model=AssessmentRecord, response_model_exclude_none=True)
    def complete_lesson(skill: str, session=Depends(candidate)):
        return service.complete_lesson(session.uid, skill)

    @app.get("/api/matches", response_model=list[MatchRecord])
    def matches(session=Depends(candidate)):
        return service.matches(session.uid)

    @app.post("/api/jobs", response_model=Job)
    def create_job(body: JobCreate, session=Depends(employer)):
        return service.create_job(session.uid, body)

    @app.get("/api/employer/jobs", response_model=list[Job])
    def employer_jobs(session=Depends(employer)):
        return [j for j in service.jobs() if j.get("employer_id") == session.uid]

    @app.get("/api/employer/jobs/{job_id}/candidates", response_model=list[CandidateMatch])
    def candidates(job_id: str, session=Depends(employer)):
        return service.candidates(session.uid, job_id)

    @app.post("/api/chat", response_model=ChatResponse)
    def chat_endpoint(body: ChatRequest, session=Depends(authenticated)):
        with session.lock:
            try:
                response, _ = chat(service, settings, session.uid, session.role, body.message, session.history)
            except Exception as exc:
                logging.getLogger(__name__).warning("Agent request failed: %s", type(exc).__name__)
                raise HTTPException(503, "The AI service could not complete this request. Your evidence is safe. Retry or use the dashboard controls.") from exc
            # Retain only conversational text; specialists reload authoritative records.
            session.history.extend([{"role": "user", "content": [{"text": body.message}]},
                                    {"role": "assistant", "content": [{"text": response.message}]}])
            session.history = session.history[-12:]
            return response

    return app


app = create_app()
