from contextlib import asynccontextmanager
from dataclasses import dataclass, field
import logging
from threading import Lock

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from botocore.exceptions import BotoCoreError, ClientError
from pydantic import ValidationError

from backend.config import Settings
from backend.db import MemoryRepository, DynamoRepository, Conflict
from backend.models import ProfileUpdate, JobCreate, AssessmentCreate, Submission, ChatRequest, ChatResponse
from backend.models import Profile, Job, DashboardRecord, MarketRecord, AssessmentRecord, RoadmapRecord, LessonRecord, MatchRecord, CandidateMatch
from backend.orchestrator import chat
from backend.service import Service
from backend.auth import Auth, InvalidCredentials, TooManyAttempts, digest
from backend.models import LoginRequest, SignupRequest, AccountSession
from backend.models import OnboardingState, OnboardingAnswer, OnboardingConfirm
from backend.onboarding import Onboarding
from backend.intelligence import GenerationError
from backend.models import LearningRecord, PassportRecord, ConversationRecord
from backend import conversation

ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000", "http://127.0.0.1:8000"]


@dataclass
class Session:
    uid: str
    role: str
    email: str
    lock: Lock = field(default_factory=Lock)


def create_app(repo=None, settings=None):
    load_dotenv()
    settings = settings or Settings()
    if repo is None:
        repo = MemoryRepository() if settings.repository == "memory" else DynamoRepository(
            settings.table_name, settings.dynamodb_endpoint if settings.repository == "dynamodb-local" else None)
    service = Service(repo,settings)
    onboarding = Onboarding(service)
    auth = Auth(service, settings)
    sessions = {}

    @asynccontextmanager
    async def lifespan(app):
        service.seed()
        auth.seed_actors()
        yield

    app = FastAPI(title="CareerBuddy", version="0.2.0", lifespan=lifespan)
    app.state.service = service
    app.state.auth = auth
    app.state.settings = settings
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
        if isinstance(exc, ValidationError):
            # Never leak Pydantic internals (model names, input echoes, docs URLs) to users.
            logging.getLogger(__name__).warning("Validation failed: %s", exc.title)
            issue = exc.errors()[0] if exc.errors() else {}
            field = " ".join(str(p) for p in issue.get("loc", ()) if p != "body").replace("_", " ")
            message = str(issue.get("msg", "is invalid")).removeprefix("Value error, ")
            return JSONResponse(status_code=400, content={"detail": f"{field.capitalize()}: {message}" if field else message})
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(PermissionError)
    async def forbidden(request, exc):
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(Conflict)
    async def conflict(request, exc):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(InvalidCredentials)
    async def invalid_credentials(request, exc):
        return JSONResponse(status_code=401, content={"detail": str(exc)})

    @app.exception_handler(TooManyAttempts)
    async def throttled(request, exc):
        return JSONResponse(status_code=429, content={"detail": str(exc)}, headers={"Retry-After": "300"})

    @app.exception_handler(GenerationError)
    async def generation_failed(request,exc):
        return JSONResponse(status_code=503,content={"detail":str(exc)})

    async def storage_error(request, exc):
        logging.getLogger(__name__).warning("Storage unavailable: %s", type(exc).__name__)
        return JSONResponse(status_code=503, content={"detail": "Storage is unavailable. Check the configured repository and local service."})

    app.add_exception_handler(ClientError, storage_error)
    app.add_exception_handler(BotoCoreError, storage_error)

    def authenticated(request: Request):
        token = request.cookies.get("skillpilot_session")
        account = auth.session(token)
        key = digest(token)
        profile = service.profile(account["uid"])
        if key not in sessions:
            if len(sessions) >= 256:
                sessions.pop(next(iter(sessions)))
            sessions[key] = Session(uid=account["uid"], role=profile["role"], email=account["email"])
        return sessions[key]

    def candidate(session=Depends(authenticated)):
        if session.role != "candidate":
            raise HTTPException(403, "Candidate session required")
        return session

    def employer(session=Depends(authenticated)):
        if session.role != "employer":
            raise HTTPException(403, "Employer session required")
        return session

    def start_session(account, request, response):
        previous = request.cookies.get("skillpilot_session")
        if previous:
            auth.logout(previous)
            sessions.pop(digest(previous), None)
        token = auth.create_session(account)
        response.set_cookie("skillpilot_session", token, httponly=True, samesite="strict",
                            secure=settings.secure_cookies, max_age=settings.session_seconds)
        return {"profile": service.profile(account["uid"]), "email": account["email"], "mode": settings.ai_mode}

    @app.get("/api/health")
    def health():
        return {"status": "ok", "ai_mode": settings.ai_mode, "repository": settings.repository,
                "persistence": "temporary; resets on restart" if settings.repository == "memory" else "DynamoDB",
                "model_id": settings.model_id if settings.ai_mode == "bedrock" else "offline fixture"}

    @app.post("/api/auth/signup", response_model=AccountSession)
    def signup(body: SignupRequest, request: Request, response: Response):
        auth.throttle("signup", request.client.host if request.client else "unknown", str(body.email))
        return start_session(auth.signup(body), request, response)

    @app.post("/api/auth/login", response_model=AccountSession)
    def login(body: LoginRequest, request: Request, response: Response):
        auth.throttle("login", request.client.host if request.client else "unknown", str(body.email))
        return start_session(auth.login(body), request, response)

    @app.post("/api/auth/logout")
    def logout(request: Request, response: Response):
        token = request.cookies.get("skillpilot_session")
        auth.logout(token)
        if token:
            sessions.pop(digest(token), None)
        response.delete_cookie("skillpilot_session", httponly=True, samesite="strict", secure=settings.secure_cookies)
        return {"status": "signed_out"}

    @app.get("/api/session", response_model=AccountSession)
    def session_info(session=Depends(authenticated)):
        return {"profile": service.profile(session.uid), "email": session.email, "mode": settings.ai_mode}

    @app.get("/api/dashboard", response_model=DashboardRecord, response_model_exclude_none=True)
    def dashboard(session=Depends(candidate)):
        return service.dashboard(session.uid)

    @app.get("/api/onboarding",response_model=OnboardingState)
    def onboarding_state(session=Depends(candidate)):
        return onboarding.get(session.uid)

    @app.post("/api/onboarding/answer",response_model=OnboardingState)
    def onboarding_answer(body:OnboardingAnswer,session=Depends(candidate)):
        return onboarding.answer(session.uid,body.answer,body.revision)

    @app.post("/api/onboarding/complete",response_model=Profile)
    def onboarding_complete(body:OnboardingConfirm,session=Depends(candidate)):
        return onboarding.complete(session.uid,body.revision)

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
        return service.create_assessment(session.uid, body.skill,competency_id=body.competency_id)

    @app.get("/api/assessments/{assessment_id}", response_model=AssessmentRecord, response_model_exclude_none=True)
    def assessment(assessment_id: str, session=Depends(candidate)):
        return service.assessment(session.uid, assessment_id)

    @app.post("/api/assessments/{assessment_id}/submit", response_model=AssessmentRecord, response_model_exclude_none=True)
    def submit(assessment_id: str, body: Submission, session=Depends(candidate)):
        return service.submit(session.uid, assessment_id, body.answers)

    @app.get("/api/roadmap", response_model=RoadmapRecord)
    def roadmap(session=Depends(candidate)):
        return service.roadmap(session.uid)

    from backend.evaluation import Evaluation
    from backend.models import LearningEvaluation, LearningEvaluationAnswer
    evaluation=Evaluation(service)

    @app.get('/api/learning/evaluation',response_model=LearningEvaluation | None)
    def get_learning_evaluation(session=Depends(candidate)):
        return evaluation.get(session.uid)

    @app.post('/api/learning/evaluation',response_model=LearningEvaluation)
    def begin_learning_evaluation(session=Depends(candidate)):
        return evaluation.begin(session.uid)

    @app.post('/api/learning/evaluation/answer',response_model=LearningEvaluation)
    def answer_learning_evaluation(body:LearningEvaluationAnswer,session=Depends(candidate)):
        return evaluation.answer(session.uid,body.answer,body.revision,body.target_role,body.career_goal)

    @app.post('/api/learning/evaluation/complete',response_model=LearningRecord)
    def complete_learning_evaluation(body:OnboardingConfirm,session=Depends(candidate)):
        return evaluation.complete(session.uid,body.revision)

    @app.get("/api/learning",response_model=LearningRecord)
    def learning_plan(session=Depends(candidate)):
        return service.learning.plan(session.uid)

    def require_learning_evaluation(uid):
        if (not service.profile(uid)['goal_confirmed'] and not service.profile(uid)['synthetic']) or not (service.repo.get(f'USER#{uid}','CAREER_PATH#active') or {}).get('evaluation_id'):
            raise Conflict('Evaluate your profile in Learning before creating a roadmap.')

    @app.post("/api/learning",response_model=LearningRecord)
    def create_learning_plan(session=Depends(candidate)):
        require_learning_evaluation(session.uid)
        return service.learning.plan(session.uid)

    @app.post("/api/learning/{skill}/expand",response_model=LearningRecord)
    def expand_learning(skill:str,session=Depends(candidate)):
        require_learning_evaluation(session.uid)
        return service.learning.expand(session.uid,skill)

    @app.get("/api/competencies/{competency_id}/lesson",response_model=LessonRecord)
    def competency_lesson(competency_id:str,session=Depends(candidate)):
        return service.learning.lesson(session.uid,competency_id)

    @app.post("/api/competencies/{competency_id}/practice",response_model=AssessmentRecord,response_model_exclude_none=True)
    def competency_practice(competency_id:str,session=Depends(candidate)):
        return service.learning.practice(session.uid,competency_id)

    @app.post("/api/assessments/next",response_model=AssessmentRecord,response_model_exclude_none=True)
    def next_assessment(session=Depends(candidate)):
        require_learning_evaluation(session.uid)
        return service.learning.next_assessment(session.uid)

    @app.get("/api/passport",response_model=PassportRecord)
    def passport(session=Depends(candidate)):
        return service.learning.passport(session.uid)

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

    @app.get("/api/chat/history",response_model=ConversationRecord)
    def chat_history(session=Depends(authenticated)):
        return conversation.history(repo,session.uid)

    runtime_client = None

    def invoke_runtime(uid, token, message):
        """Run the agent on AgentCore Runtime; the runtime re-validates the session itself."""
        nonlocal runtime_client
        import json
        import boto3
        from botocore.config import Config as BotoConfig
        if runtime_client is None:
            runtime_client = boto3.client("bedrock-agentcore", config=BotoConfig(read_timeout=120, retries={"max_attempts": 1}))
        result = runtime_client.invoke_agent_runtime(
            agentRuntimeArn=settings.agent_runtime_arn, qualifier="DEFAULT",
            runtimeSessionId=f"careerbuddy-session-{uid}".ljust(33, "0")[:100],  # one warm session per user
            payload=json.dumps({"message": message, "session_token": token}).encode())
        body = result["response"].read() if hasattr(result["response"], "read") else b"".join(result["response"])
        return ChatResponse.model_validate(json.loads(body))

    @app.post("/api/chat", response_model=ChatResponse)
    def chat_endpoint(body: ChatRequest, request: Request, session=Depends(authenticated)):
        if settings.agent_runtime_arn:
            with session.lock:
                try:
                    return invoke_runtime(session.uid, request.cookies.get("skillpilot_session"), body.message)
                except Exception as exc:
                    logging.getLogger(__name__).warning("AgentCore runtime request failed: %s", type(exc).__name__)
                    raise HTTPException(503, "The AI service could not complete this request. Your evidence is safe. Retry or use the dashboard controls.") from exc
        with session.lock:
            saved_history=conversation.history(repo,session.uid)
            try:
                response, _ = chat(service, settings, session.uid, session.role, body.message, conversation.model_messages(saved_history))
            except Exception as exc:
                logging.getLogger(__name__).warning("Agent request failed: %s", type(exc).__name__)
                raise HTTPException(503, "The AI service could not complete this request. Your evidence is safe. Retry or use the dashboard controls.") from exc
            conversation.append(repo,session.uid,saved_history,body.message,response)
            return response

    return app


app = create_app()
