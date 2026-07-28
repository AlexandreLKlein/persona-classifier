FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV DATABASE_PATH=/app/data/persona_classifier.db
RUN mkdir -p /app/data

EXPOSE 8000

# The database is seeded automatically on first startup if empty (see app/main.py's
# lifespan handler) -- no separate build-time seed step needed.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
