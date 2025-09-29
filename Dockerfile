# Dockerfile
FROM python:3.12-alpine3.22

WORKDIR /app

RUN pip install poetry==1.8.2

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --no-root --only main

COPY ./app ./app
COPY alembic.ini ./
COPY alembic ./alembic

ENV PYTHONPATH=/app

CMD ["sh", "-c", "poetry run alembic upgrade head && poetry run gunicorn app.main:app -k uvicorn.workers.UvicornWorker --workers 8 --bind 0.0.0.0:8000"]