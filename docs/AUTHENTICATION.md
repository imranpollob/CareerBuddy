# Accounts and local sign-in

SkillPilot supports email/password signup and login for new candidates and employers. The application has no identity selector and no passwordless demo-login endpoints. Each signed-in user gets their own profile, assessments, learning progress, matches, and employer postings.

No accounts or fictional profiles are precreated by default. Keep `SKILLPILOT_SEED_ACCOUNTS=false` for normal use. Signup creates the candidate or employer account; only actual submissions create assessment evidence. Old fixture logins and sessions are rejected when sample seeding is disabled. Isolated tests explicitly enable their own sample data in separate repositories.

To clean an existing DynamoDB Local database, run these commands from the repository root:

```bash
uv run python -m scripts.remove_sample_accounts --dry-run
uv run python -m scripts.remove_sample_accounts
```

The utility targets only known fixture IDs, their account/session records, owned sample jobs and derived matches. It preserves signup identities and their evidence, even when a display name matches a fixture. It accepts only a local DynamoDB endpoint and never targets AWS. Remove the obsolete ignored `.local/actor-accounts.json` credential file after cleanup.

Signup asks only for name, email, password, and account purpose. After account creation, candidates answer exactly four numbered background questions: role, education, years of experience (0–30), and expertise (four levels). Progress persists across reloads. Confirmation saves background context before a personalized assessment is generated; it does not create verified skills. Employers start with an empty job list. Candidate discovery defaults to off. New profiles are non-synthetic, and candidates must submit actual assessments to add evidence.

Passwords use `pwdlib`'s recommended Argon2 configuration. Account lookup uses a normalized email hash as the key. Signup atomically inserts the credential record and profile, conditional on the email record being absent. Duplicate email attempts cannot overwrite an account or leave an orphan profile. Passwords are never stored in profile records or returned in responses.

The browser receives a random, HttpOnly, SameSite=Strict session cookie. Only its SHA-256 digest is stored in the table. Sessions expire after four hours by default; login rotates the token and logout revokes it. Session identity and onboarding interviews persist through an API restart when using DynamoDB; general assistant chat also persists privately (latest 24 messages, with the latest 12 supplied as model context). In-memory mode resets accounts and records on restart and is intended only for isolated development.

Login failures use the same response for an unknown email and a wrong password, and run a dummy password verification for unknown users. Per-process attempt limits apply to IP addresses and normalized emails. Mutating endpoints reject unrelated origins. Backend routes derive user IDs and roles from authenticated records, never caller-selected IDs. Profile updates cannot change roles or assessment evidence.

Configuration:

```dotenv
SKILLPILOT_SEED_ACCOUNTS=false
SKILLPILOT_SECURE_COOKIES=false
```

Use `SKILLPILOT_SECURE_COOKIES=true` when serving through HTTPS. False is for local HTTP. This MVP has no email verification, password reset, MFA, or independent employer verification, and its rate limiter is single-process. It is not a complete production identity service.

| Route | Purpose |
| --- | --- |
| `POST /api/auth/signup` | Create a new account and establish its session |
| `POST /api/auth/login` | Check credentials and establish a fresh session |
| `POST /api/auth/logout` | Revoke the current session and clear its cookie |
| `GET /api/session` | Return only the signed-in profile and email |

The application still uses one `SkillPilot` table:

| PK | SK | Contents |
| --- | --- | --- |
| `ACCOUNT#<email-hash>` | `CREDENTIALS` | User ID, normalized email, Argon2 password hash |
| `SESSION#<token-hash>` | `AUTH_SESSION` | User ID, email, expiry; revoked sessions have expiry zero |

No cloud authentication service or new AWS resource is required. Expired session records are rejected in code; automatic TTL cleanup is not provisioned.

Implementation references: [FastAPI password hashing](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/), [OWASP session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html).
