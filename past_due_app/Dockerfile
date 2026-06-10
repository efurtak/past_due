FROM python:3.12.13-slim-trixie AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /past_due_app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS development
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM base AS test
COPY . .

RUN pip install --no-cache-dir pytest

CMD ["pytest"]

FROM base AS production
COPY . .

RUN python manage.py collectstatic --noinput

RUN pip install --no-cache-dir gunicorn

RUN useradd -m appuser && chown -R appuser /past_due_app
USER appuser

CMD ["gunicorn", "past_due_project.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]