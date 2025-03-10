FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt


EXPOSE 8002

CMD ["sh", "-c", "sleep 10 && uvicorn preprocessing_service:app --host 0.0.0.0 --port 8002"]
