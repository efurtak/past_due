FROM python:3.12.13-slim-trixie AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /past_due_app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS development
COPY . .

RUN pip install --no-cache-dir "ruff==0.15.17"

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM base AS test
COPY . .

RUN pip install --no-cache-dir "pytest==9.0.3"

CMD ["pytest"]

FROM base AS production
COPY . .

RUN python manage.py collectstatic --noinput

RUN useradd -m appuser && chown -R appuser /past_due_app
USER appuser

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "past_due_project.asgi:application"]