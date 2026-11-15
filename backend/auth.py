"""Email/password accounts and opaque cookie sessions in the existing table."""
from collections import defaultdict, deque
from hashlib import sha256
import json
import os
from pathlib import Path
import secrets
from threading import RLock
import time
from uuid import uuid4

from pwdlib import PasswordHash
from backend.db import item, Conflict
from backend.models import Profile

ACTORS = {
    "candidate": {"uid": "candidate-demo", "email": "alex@example.com"},
    "student": {"uid": "student-demo", "email": "priya@example.com"},
    "employer": {"uid": "employer-demo", "email": "jordan@example.com"},
}


class InvalidCredentials(Exception):
    pass


class TooManyAttempts(Exception):
    pass


def digest(value):
    return sha256(value.encode()).hexdigest()


def account_key(email):
    return f"ACCOUNT#{digest(str(email).strip().lower())}", "CREDENTIALS"


class Auth:
    def __init__(self, service, settings):
        self.service, self.repo, self.settings = service, service.repo, settings
        self.passwords = PasswordHash.recommended()
        self.dummy_hash = self.passwords.hash(secrets.token_urlsafe(24))
        self.attempts = defaultdict(deque)
        self.lock = RLock()

    def throttle(self, operation, ip, email):
        now = time.monotonic()
        with self.lock:
            for key, maximum in [(f"{operation}:ip:{ip}", 50), (f"{operation}:email:{digest(email.lower())}", 8)]:
                queue = self.attempts[key]
                while queue and queue[0] < now - 300:
                    queue.popleft()
                if len(queue) >= maximum:
                    raise TooManyAttempts("Too many attempts. Please try again in a few minutes.")
                queue.append(now)

    def signup(self, request):
        email = str(request.email).strip().lower()
        pk, sk = account_key(email)
        if self.repo.get(pk, sk):
            raise Conflict("An account with this email already exists. Sign in instead.")
        uid = uuid4().hex
        profile = Profile(id=uid, name=request.name.strip(), role=request.role,
                          current_role=request.current_role.strip(), target_role=request.target_role.strip(),
                          claimed_skills=request.claimed_skills, marketplace_opt_in=False, synthetic=False,
                          candidate_track="employer" if request.role == "employer" else request.candidate_track,
                          onboarding_completed=request.role == "employer")
        account = {"uid": uid, "email": email, "password_hash": self.passwords.hash(request.password.get_secret_value())}
        self.repo.write([item(pk, sk, account), item(f"USER#{uid}", "PROFILE", profile.model_dump())], absent=(pk, sk))
        return account

    def login(self, request):
        email = str(request.email).strip().lower()
        account = self.repo.get(*account_key(email))
        valid = self.passwords.verify(request.password.get_secret_value(), account["password_hash"] if account else self.dummy_hash)
        if not account or not valid:
            raise InvalidCredentials("Email or password is incorrect.")
        with self.lock:
            self.attempts.pop(f"login:email:{digest(email)}", None)
        return account

    def create_session(self, account):
        token = secrets.token_urlsafe(32)
        data = {"uid": account["uid"], "email": account["email"], "expires_at": int(time.time()) + self.settings.session_seconds}
        self.repo.write([item(f"SESSION#{digest(token)}", "AUTH_SESSION", data)])
        return token

    def session(self, token):
        if not token or len(token) > 128:
            raise InvalidCredentials("Please sign in to continue.")
        session = self.repo.get(f"SESSION#{digest(token)}", "AUTH_SESSION")
        if not session or session["expires_at"] <= time.time():
            raise InvalidCredentials("Your session has expired. Please sign in again.")
        return session

    def logout(self, token):
        if token and len(token) <= 128 and self.repo.get(f"SESSION#{digest(token)}", "AUTH_SESSION"):
            self.repo.write([item(f"SESSION#{digest(token)}", "AUTH_SESSION", {"expires_at": 0})])

    def seed_actors(self):
        if not self.settings.seed_accounts:
            return
        path = Path(self.settings.actor_credentials_path)
        if path.exists():
            credentials = json.loads(path.read_text())
        else:
            # Bootstrap passwords are local-only, never returned by an API.
            credentials = {name: {"email": actor["email"], "password": secrets.token_urlsafe(18)} for name, actor in ACTORS.items()}
            path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as stream:
                json.dump(credentials, stream, indent=2)
                stream.write("\n")
        path.chmod(0o600)
        for name, actor in ACTORS.items():
            pk, sk = account_key(actor["email"])
            if self.repo.get(pk, sk):
                continue
            account = {"uid": actor["uid"], "email": actor["email"], "password_hash": self.passwords.hash(credentials[name]["password"])}
            try:
                self.repo.write([item(pk, sk, account)], absent=(pk, sk))
            except Conflict:
                pass
