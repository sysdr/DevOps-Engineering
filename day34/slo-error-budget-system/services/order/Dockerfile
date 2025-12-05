FROM python:3.11-slim

WORKDIR /app

COPY order/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY order/ .
COPY shared/ ./shared/

CMD ["python", "main.py"]
