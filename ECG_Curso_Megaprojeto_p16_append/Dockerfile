FROM python:3.11-slim

# Minimal image to run the Dash app located at ECG_Curso_Megaprojeto_p16_append/web_app/dash_app
WORKDIR /opt/ecgcourse

# Copy only requirements first for layer caching
COPY requirements.txt ./requirements.txt

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libgl1 libglib2.0-0 \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy repository into image
COPY . .

WORKDIR /opt/ecgcourse/web_app/dash_app

ENV PORT=8050
EXPOSE 8050

# Use gunicorn to run the Dash (Flask) server. The wsgi.py in this folder exposes `application`.
CMD ["gunicorn", "--bind", "0.0.0.0:8050", "wsgi:application", "--workers", "2", "--worker-class", "gthread"]
