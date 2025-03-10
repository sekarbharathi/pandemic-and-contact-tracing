import json
import random
import time
import requests
from datetime import datetime
import logging
from prometheus_client import start_http_server, Counter, Gauge

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# REST API URL for the preprocessing service (replace with your actual endpoint)
API_URL = "http://preprocessing-service:8002/process"

# Metrics
CHECKIN_REQUESTS = Counter("checkin_requests_total", "Total number of check-in requests sent")
LAB_REPORTS_SENT = Counter("lab_reports_total", "Total number of lab reports sent")
FAILED_REQUESTS = Counter("failed_requests_total", "Total number of failed requests")
LATENCY = Gauge("request_latency_seconds", "Time taken for API requests")

# Start Prometheus metrics server on port 8003
start_http_server(8003, addr="0.0.0.0")

# List of districts and neighborhoods in Oulu
oulu_locations = [
    "Linnanmaa", "Kaijonharju", "Tuira", "Karjasilta", "Holliha", "Toppila", 
    "Ritaharju", "Myllytulli", "Rajakylä", "Hintta", "Värttö", "Raksila", 
    "Peltola", "Pateniemi", "Koskela", "Kaukovainio", "Merikoski", "Taskila",
    "Hietasaari", "Oulunsalo"
]

# List of possible symptoms
symptoms_list = [
    "Fever", "Cough", "Sore Throat", "Fatigue", "Headache", "Shortness of Breath",
    "Runny Nose", "Muscle Pain", "Loss of Smell", "Loss of Taste", "Diarrhea",
    "Nausea", "Vomiting", "Chest Pain", "Chills", "Sweating", "Dizziness", "None"
]


def generate_checkin_data(user_id):
    location_name = random.choice(oulu_locations)
    symptoms = random.sample(symptoms_list, random.randint(1, 4))  # Randomly select 1-4 symptoms

    return {
        "checkinId": f"chk_{random.randint(100, 999)}",
        "userId": user_id,
        "timestamp": datetime.now().isoformat(),
        "location": {
            "name": location_name,
            "latitude": random.uniform(64.95, 65.1),  # Latitude range around Oulu
            "longitude": random.uniform(25.35, 25.75)  # Longitude range around Oulu
        },
        "symptoms": symptoms
    }

def generate_lab_report_data(user_id, symptoms):
    # Determine the relevant test type based on symptoms
    if "Loss of Smell" in symptoms or "Loss of Taste" in symptoms or "Shortness of Breath" in symptoms:
        test_type = "COVID-19"
        result = "positive" if random.choice([True, False]) else "negative"
        viral_status = "viral-positive" if result == "positive" else "viral-negative"
    elif "Fever" in symptoms or "Cough" in symptoms:
        test_type = "Fever"
        result = "positive" if random.choice([True, False]) else "negative"
        viral_status = "viral-positive" if result == "positive" else "viral-negative"
    elif "Fatigue" in symptoms or "Headache" in symptoms:
        test_type = "General Viral Infection"
        result = "positive" if random.choice([True, False]) else "negative"
        viral_status = "viral-positive" if result == "positive" else "viral-negative"
    else:
        test_type = "Antibody Check"
        result = "positive" if random.choice([True, False]) else "negative"
        viral_status = "viral-negative"  # Antibody tests usually detect past infection

    return {
        "labReportId": f"lab_{random.randint(100, 999)}",
        "userId": user_id,
        "testType": test_type,
        "testDate": datetime.now().isoformat(),
        "result": result,
        "viralLoad": random.choice(["detectable", "undetectable"]),
        "viralStatus": viral_status,
        "hospitalizationStatus": random.choice(["not-hospitalized", "hospitalized"]),
        "testCenter": "SynLab",
    }

# Function to send mock data via REST API
def send_mock_data():
    while True:
        user_id = f"user_{random.randint(1, 20000)}"
        checkin_data = generate_checkin_data(user_id)
        lab_report_data = generate_lab_report_data(user_id, checkin_data["symptoms"])  # Passing symptoms from checkin data

        # Prepare payload to send via POST request
        payload = {
            "checkin": checkin_data,
            "labreport": lab_report_data
        }

        # Send data to the REST API for preprocessing service
        try:
            start_time = time.time()

            response = requests.post(API_URL, json=payload)

            LATENCY.set(time.time() - start_time)

            if response.status_code == 200:

                CHECKIN_REQUESTS.inc()
                LAB_REPORTS_SENT.inc()

                logger.info(f"Data sent successfully for user {user_id}")
            else:
                FAILED_REQUESTS.inc()

                logger.warning(f"Failed to send data for user {user_id}, Status Code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            
            FAILED_REQUESTS.inc()

            logger.error(f"Error sending data for user {user_id}: {e}")
        
        time.sleep(5)  # Simulate real-time data generation every 5 seconds

if __name__ == "__main__":
    logger.info("Starting data generation process...")
    send_mock_data()
