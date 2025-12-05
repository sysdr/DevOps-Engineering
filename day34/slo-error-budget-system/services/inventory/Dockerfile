FROM python:3.11-slim

WORKDIR /app

COPY inventory/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY inventory/ .
COPY shared/ ./shared/

CMD ["python", "main.py"]
