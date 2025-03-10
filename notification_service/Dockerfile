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

ENTRYPOINT ["sh", "-c", "sleep 30 && dockerize -wait tcp://kafka:9092 -timeout 120s python notification_service.py"]

# Expose the port (adjust if the script uses a specific port)
EXPOSE 8006

# Command to run the service (assuming it's a script)
CMD ["python", "notification_service.py"]
