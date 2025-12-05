FROM python:3.11-slim

WORKDIR /app

COPY payment/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY payment/ .
COPY shared/ ./shared/

CMD ["python", "main.py"]
