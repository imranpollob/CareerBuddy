# Prepared only. No build, push, or deployment runs automatically.
FROM public.ecr.aws/docker/library/python:3.13-slim
WORKDIR /app
COPY deployment/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend /app/backend
ENV PYTHONUNBUFFERED=1 \
    SKILLPILOT_AI_MODE=bedrock \
    SKILLPILOT_REPOSITORY=dynamodb
EXPOSE 8080
CMD ["python", "-m", "backend.main"]
