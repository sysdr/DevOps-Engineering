FROM python:3.11-slim

WORKDIR /app

COPY policy-engine/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY policy-engine/ .
COPY shared/ ./shared/

CMD ["python", "main.py"]
