FROM python:3.11-slim

WORKDIR /app

COPY slo-calculator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY slo-calculator/ .
COPY shared/ ./shared/

CMD ["python", "main.py"]
