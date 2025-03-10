import json
import logging
import requests
from fastapi import FastAPI, Request
from confluent_kafka import Producer
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time

# Initialize FastAPI app
app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API_URL and Kafka settings
API_URL = "http://database-service:8001/api/v1/data"
KAFKA_BROKER = "kafka:9092"
KAFKA_TOPIC = "prediction_input"

producer = Producer({'bootstrap.servers': KAFKA_BROKER})

# Prometheus Metrics
REQUEST_COUNT = Counter("preprocessing_requests_total", "Total number of requests")
REQUEST_LATENCY = Histogram("preprocessing_request_latency_seconds", "Request latency in seconds")

# Log Kafka message delivery status
def delivery_report(err, msg):
    if err is not None:
        logger.error(f"❌ Kafka delivery failed: {err}")
    else:
        logger.info(f"✅ Kafka message delivered to {msg.topic()} [{msg.partition()}]")

def send_to_prediction(data):
    logger.info(f"📤 Sending data to Kafka: {data}")
    try:
        if "userId" not in data:
            raise ValueError("Missing 'userId' in the data.")
        
        json_message = json.dumps(data)
        producer.produce(KAFKA_TOPIC, key=data["userId"], value=json_message, callback=delivery_report)
        producer.flush()
        logger.info(f"✅ Data sent to Kafka for user {data['userId']}")
    except Exception as e:
        logger.error(f"❌ Error sending data to Kafka: {e}")
        raise

def send_to_database(data):
    try:
        logger.info(f"📤 Sending data to database: {data}")
        response = requests.post(API_URL, json=data)
        if response.status_code == 200:
            logger.info(f"✅ Data sent to database for user {data['userId']}")
        else:
            logger.error(f"❌ Failed to send data to database for user {data['userId']} (HTTP {response.status_code})")
    except requests.exceptions.RequestException as e:
        logger.warning(f"⚠️ Error sending data to database: {e}")
        raise

def combine_data(user_id, checkin_data, lab_report_data):
    return {
        "userId": user_id,
        "checkin": checkin_data,
        "labReport": lab_report_data
    }

def process_data(checkin_data, lab_report_data):
    logger.debug(f"📥 Received checkin data: {checkin_data}")
    logger.debug(f"📥 Received lab report data: {lab_report_data}")

    try:
        if checkin_data.get("userId") == lab_report_data.get("userId"):
            logger.info("✅ userIds match")
            combined_data = combine_data(checkin_data["userId"], checkin_data, lab_report_data)

            send_to_prediction(combined_data)
            send_to_database(combined_data)
        else:
            logger.error(f"❌ Mismatch in userId between checkin and lab report: {checkin_data.get('userId')} vs {lab_report_data.get('userId')}")
    except Exception as e:
        logger.error(f"❌ Error in process_data: {e}")
        raise

@app.post("/process")
async def process_endpoint(data: dict):
    REQUEST_COUNT.inc()  # Increment request count
    start_time = time.time()

    logger.info(f"🟢 Received request data: {data}")
    try:
        user_id = data.get("checkin", {}).get("userId") or data.get("labreport", {}).get("userId")
        logger.debug(f"📤 User id: {user_id}")
        
        if user_id is None:
            logger.error("❌ Missing userId in request data")
            return {"status": "error", "message": "Missing userId in request data"}

        checkin_data = data.get("checkin")
        lab_report_data = data.get("labreport")

        if not checkin_data or not lab_report_data:
            logger.error("❌ Missing checkin or lab report data")
            return {"status": "error", "message": "Missing checkin or lab report data"}

        logger.info("📤 Calling process_data function...")
        process_data(checkin_data, lab_report_data)

        REQUEST_LATENCY.observe(time.time() - start_time)  # Observe request duration
        return {"status": "success", "message": "Data processed successfully"}

    except Exception as e:
        logger.error(f"❌ Error processing request: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
