# Pandemic Response Contact Tracing System

A distributed platform designed to enhance pandemic response through real-time contact tracing, outbreak modeling, and predictive analytics. The system integrates data from mobile app check-ins, hospital records, and lab reports to efficiently detect infection patterns and predict potential outbreaks.

---

##  Overview

This system combines microservices, AI, and real-time messaging to:

- Collect and preprocess pandemic-related data
- Detect hotspots and predict potential outbreaks
- Perform contact tracing and alert users in real-time
- Provide AI-generated risk assessments and preventive guidelines

---

##  Key Features

- **Microservices Architecture**  
  Built with Python, FastAPI, and gRPC — each service is modular and independently scalable.

- **Real-time Data Processing**  
  REST APIs for ingestion, Kafka for asynchronous communication between services.

- **Scalability**  
  Fully containerized with Docker and orchestrated using Kubernetes for smooth deployment and scalability.

- **Monitoring**  
  Integrated with **Prometheus** and **Grafana** for real-time performance monitoring and visualization.

- **AI Integration**  
  GPT-3.5-turbo is used in the Risk Assessment Service to provide smart precautionary suggestions.

---

##  System Components

| Microservice               | Description                                                                 |
|----------------------------|-----------------------------------------------------------------------------|
| **Realtime Data**          | Collects raw data from mobile check-ins, hospitals, and lab reports         |
| **Pre-processing**         | Cleans and stores data in MongoDB; publishes messages to Kafka              |
| **Prediction Service**     | Predicts potential outbreaks using processed data                           |
| **Hotspot Detection**      | Detects geographic hotspots with high case density                          |
| **Contact Tracing**        | Traces individuals who were in contact with infected persons                |
| **Notification Service**   | Sends alerts and updates to users via Kafka                                 |
| **Risk Assessment Service**| Uses OpenAI's GPT model to suggest preventative measures                    |

---

## Technologies Used

- **Backend:** Python, FastAPI, gRPC
- **Database:** MongoDB
- **Messaging:** Apache Kafka
- **Containerization:** Docker
- **Orchestration:** Kubernetes (Minikube for local, Docker Hub for cloud)
- **Monitoring:** Prometheus, Grafana
- **AI:** OpenAI GPT-3.5-turbo API (Risk Assessment)

---

## Deployment

### Local Setup

#### Prerequisites
- Docker
- Kubernetes (Minikube)
  
#### Steps


# Clone the repository
    git clone https://github.com/sekarbharathi/pandemic-and-contact-tracing.git
    cd pandemic-and-contact-tracing

# Build and run containers 
    docker compose build
    docker compose up
    docker images

# Deploy to Kubernetes 
    minikube start --driver=docker
    kubectl apply -f .
    kubectl get pods
    minikube dashboard


