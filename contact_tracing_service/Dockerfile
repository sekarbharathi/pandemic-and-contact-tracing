FROM python:3.8-slim

# Set the working directory
WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    librdkafka-dev \
    wget && \
    wget https://github.com/jwilder/dockerize/releases/download/v0.6.1/dockerize-linux-amd64-v0.6.1.tar.gz && \
    tar -xvzf dockerize-linux-amd64-v0.6.1.tar.gz && \
    mv dockerize /usr/local/bin/ && \
    rm -rf dockerize-linux-amd64-v0.6.1.tar.gz

# Copy the requirements file
COPY requirements.txt /app/

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt


# Make sure to clean up
RUN rm -rf dockerize-linux-amd64-v0.6.1.tar.gz

# Copy the application code
COPY . /app/


# Add this ENTRYPOINT to wait for Kafka to be ready before starting the service
#ENTRYPOINT ["dockerize", "-wait", "tcp://kafka:9092", "-timeout", "120s", "python", "contact_tracing_service.py"]
ENTRYPOINT ["sh", "-c", "sleep 30 && dockerize -wait tcp://kafka:9092 -timeout 120s python contact_tracing_service.py"]


# Expose the gRPC port
EXPOSE 50051

# Command to run the application (if you want to override ENTRYPOINT)
CMD ["python", "contact_tracing_service.py"]