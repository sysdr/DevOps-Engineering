FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 5000 8001

CMD mlflow server \
     --backend-store-uri ${BACKEND_STORE_URI} \
     --default-artifact-root ${ARTIFACT_ROOT} \
     --host 0.0.0.0 \
     --port 5000
