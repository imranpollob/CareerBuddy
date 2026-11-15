"""AgentCore Runtime entry file: registers the CareerBuddy agent entrypoint from backend.main."""
from backend.main import app  # noqa: F401  (importing registers @app.entrypoint)

if __name__ == "__main__":
    app.run()
