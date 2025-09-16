
FROM python:3.12-alpine3.22

WORKDIR /app

RUN pip install poetry==1.8.2

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-root --only main

COPY ./app ./app

ENV PYTHONPATH=/app

CMD ["sh", "-c", "poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir /app"]
