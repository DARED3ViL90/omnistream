FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=10001:10001 . .

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/manifest.json', timeout=3)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

cat > compose.yaml <<'EOF'
services:
  omnistream:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: omnistream
    restart: unless-stopped
    init: true
    read_only: true
    tmpfs:
      - /tmp:size=16m,noexec,nosuid
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    networks:
      - pangolin_frontend
    healthcheck:
      test:
        - CMD
        - python
        - -c
        - "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/manifest.json', timeout=3)"
      interval: 30s
      timeout: 5s
      start_period: 15s
      retries: 3

networks:
  pangolin_frontend:
    external: true
    name: pangolin_frontend
EOF

cat > .dockerignore <<'EOF'
.git
.gitignore
__pycache__
*.pyc
.env
venv
.venv
EOF
