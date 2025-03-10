# Use a Python base image
FROM python:3.9-slim

# Install necessary system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    librdkafka-dev \
    wget && \
    wget https://github.com/jwilder/dockerize/releases/download/v0.6.1/dockerize-linux-amd64-v0.6.1.tar.gz && \
    tar -xvzf dockerize-linux-amd64-v0.6.1.tar.gz && \
    mv dockerize /usr/local/bin/ && \
    rm -rf dockerize-linux-amd64-v0.6.1.tar.gz

# Set the working directory
WORKDIR /app

# Copy the application files into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt


# Add this ENTRYPOINT to wait for Kafka to be ready before starting the service
ENTRYPOINT ["sh", "-c", "sleep 30 && dockerize -wait tcp://kafka:9092 -timeout 120s uvicorn prediction_service:app --host 0.0.0.0 --port 8004"]


# Expose the application port
EXPOSE 8004

# Command to run the application (if you want to override ENTRYPOINT)
CMD ["uvicorn", "prediction_service:app", "--host", "0.0.0.0", "--port", "8004"]