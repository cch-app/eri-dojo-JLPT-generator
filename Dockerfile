FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 8000

# Flask serves on a single port (WSGI via gunicorn).
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "api.wsgi:app"]

