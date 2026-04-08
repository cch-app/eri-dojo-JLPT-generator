FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 3000 8000

# Reflex serves frontend on 3000 and backend on 8000 in prod mode.
CMD ["reflex", "run", "--env", "prod"]

