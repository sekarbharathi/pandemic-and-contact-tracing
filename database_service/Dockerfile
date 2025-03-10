# Use the official Python image from Docker Hub
FROM python:3.9-slim

# Set the working directory to /app inside the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the application will run on
EXPOSE 8001

# Set the default command to run the FastAPI app with uvicorn
CMD ["uvicorn", "database_service:app", "--reload", "--host", "0.0.0.0", "--port", "8001"]
