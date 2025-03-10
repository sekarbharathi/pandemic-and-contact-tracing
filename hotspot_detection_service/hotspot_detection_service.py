import asyncio
import logging
from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from datetime import datetime, timedelta
from collections import Counter as CollectionCounter
import json
from confluent_kafka import Producer
import sys
from prometheus_client import Counter, Histogram, generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST
from starlette.responses import Response

# Logging configuration (INFO and above only)
logging.basicConfig(
    level=logging.INFO,  # Logs INFO, WARNING, ERROR, and CRITICAL
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]  # Logs to stdout
)

logger = logging.getLogger(__name__)

app = FastAPI()

# MongoDB connection details
MONGODB_URI = "mongodb://mongo:27017"
DATABASE_NAME = "health_data"
COLLECTION_NAME = "checkin_lab_reports"

# Kafka producer configuration
KAFKA_CONF = {'bootstrap.servers': 'kafka:9092'}
producer = Producer(KAFKA_CONF)

# Connect to MongoDB
client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Prometheus Registry
registry = CollectorRegistry()
# Prometheus Metrics
hotspot_detections_total = Counter(
    "hotspot_detections_total", "Total number of detected COVID-19 hotspots", registry=registry
)
hotspot_requests_total = Counter(
    "hotspot_requests_total", "Total requests to /api/v1/hotspots", registry=registry
)
hotspot_detection_duration = Histogram(
    "hotspot_detection_duration_seconds", "Time taken to detect hotspots", registry=registry
)

# Function to send messages to Kafka
def send_to_kafka(message):
    try:
        producer.produce('outbreak_alerts', value=json.dumps(message))
        producer.flush()
        logger.info("Sent message to Kafka: %s", message)
    except Exception as e:
        logger.error(f"Failed to send message to Kafka: {e}")

@app.get("/api/v1/hotspots")
async def detect_hotspots():
    hotspot_requests_total.inc()  # Increment request count
    start_time = datetime.utcnow()

    try:
        current_time = datetime.utcnow()
        past_time = current_time - timedelta(minutes=60)
        past_time_str = past_time.isoformat()

        query = {
            "labReport.result": "positive",
            "labReport.testDate": {"$gte": past_time_str},
            "labReport.testType": "COVID-19"  # Ensure only COVID-19 cases are considered
        }

        # Run the blocking MongoDB query in a background thread
        data = await asyncio.to_thread(collection.find, query)
        raw_data = list(data)

        if not raw_data:
            return {"status": "success", "hotspots": []}

        location_counter = CollectionCounter()

        for record in raw_data:
            checkin_location = record['checkin']['location']
            location_name = checkin_location['name']

            location_counter[location_name] += 1

        # Get the top 3 COVID-19 hotspots
        top_3_hotspots = location_counter.most_common(3)
        
        hotspots_message = {
            "top_hotspots": [
                {
                    "location": location,
                    "count": count,
                    "disease": "COVID-19"  # Always print as "disease" instead of "testType"
                }
                for location, count in top_3_hotspots
            ]
        }

        send_to_kafka(hotspots_message)

        hotspot_detections_total.inc(len(top_3_hotspots))  # Track detected hotspots

        logger.info(f"Detected COVID-19 hotspots: {hotspots_message['top_hotspots']}")

        return {"status": "success", "hotspots": hotspots_message['top_hotspots']}
    except Exception as e:
        logger.error(f"Error during hotspot detection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        duration = (datetime.utcnow() - start_time).total_seconds()
        hotspot_detection_duration.observe(duration)  # Record processing time


# Metrics Endpoint
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)

# Background task to run the function every 30 minutes
async def hotspot_scheduler():
    while True:
        try:
            logger.info("Running scheduled COVID-19 hotspot detection...")
            await detect_hotspots()
        except Exception as e:
            logger.error(f"Error in scheduled task: {e}")
        await asyncio.sleep(1800)  # 30 minutes (updated from 120s to 1800s)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(hotspot_scheduler())
    logger.info("COVID-19 hotspot detection scheduler started.")
