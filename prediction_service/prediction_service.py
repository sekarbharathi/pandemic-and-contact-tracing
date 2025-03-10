import grpc
import joblib
import threading
import time
from collections import defaultdict
from confluent_kafka import Consumer, KafkaException, KafkaError
import json
import contact_tracing_pb2
import contact_tracing_pb2_grpc
from pydantic import BaseModel
from fastapi import FastAPI
import logging
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Initialize FastAPI app
app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the pre-trained outbreak prediction model
model = joblib.load('outbreak_prediction_model.pkl')

KAFKA_BROKER = "kafka:9092"
CONTACT_TRACING_GRPC = "contact_tracing_service:50051"

# Buffer to store messages
batch_buffer = []
buffer_lock = threading.Lock()  # Lock for thread safety

# Prometheus Metrics
messages_received = Counter("messages_received_total", "Total messages received from Kafka")
outbreaks_detected = Counter("outbreaks_detected_total", "Total outbreaks detected")
batch_runs = Counter("batch_runs_total", "Total batch processing runs")
buffer_size = Gauge("buffer_size", "Current size of the message buffer")

# Define the input data schema using Pydantic
class Location(BaseModel):
    name: str
    latitude: float
    longitude: float

class Checkin(BaseModel):
    checkinId: str
    timestamp: str
    location: Location
    symptoms: list

class LabReport(BaseModel):
    labReportId: str
    userId: str
    testType: str
    testDate: str
    result: str
    viralLoad: str
    viralStatus: str
    hospitalizationStatus: str
    testCenter: str

class Message(BaseModel):
    userId: str
    checkin: Checkin
    labReport: LabReport

# Function to send outbreak location to Contact Tracing Microservice
def send_outbreak_location(location_name, test_type):
    # Create gRPC channel and stub
    channel = grpc.insecure_channel(CONTACT_TRACING_GRPC)
    stub = contact_tracing_pb2_grpc.ContactTracingServiceStub(channel)

    # Create request message
    request = contact_tracing_pb2.OutbreakLocationRequest(
        location_name=location_name,
        test_type= test_type  # Send test type
    )

    try:
        # Send the request and receive response (we are not using the response in this case)
        stub.SendOutbreakLocation(request)
        logger.info(f"Outbreak detected at {location_name} with test type {test_type}. Sent to Contact Tracing.")
    except grpc.RpcError as e:
        logger.error(f"gRPC Error: {e}")
    finally:
        channel.close()


def batch_predict():
    global batch_buffer
    
    while True:
        time.sleep(600)  # Wait for 10 minutes
        batch_runs.inc()
        
        logger.info("Batch prediction process started.")

        with buffer_lock:  # Ensure thread safety
            if len(batch_buffer) == 0:
                continue  # Skip if buffer is empty
            
            # Dictionary to count positive cases per (location, test_type)
            outbreak_locations = defaultdict(int)
            
            for message_value in batch_buffer:
                location_name = message_value['checkin']['location']['name']
                test_type = message_value['labReport']['testType']  # Get the testType
                result = message_value['labReport']['result'].lower()

                if result == "positive":
                    outbreak_locations[(location_name, test_type)] += 1  # Increment count
            
            # Identify locations with multiple positive cases for the same test type
            for (location, test_type), count in outbreak_locations.items():
                if count > 1 and test_type == "COVID-19":  # Define your threshold, currently >1
                    logger.info(f"Outbreak detected at {location} with {count} positive cases for test type {test_type}.")
                    send_outbreak_location(location, test_type)
            
            # Clear the buffer after processing
            batch_buffer = []  # Clear buffer after processing
            buffer_size.set(0)  # Reset buffer metric
            logger.info("Batch processed and buffer cleared.")


# Kafka consumer thread
def consume_messages():
    consumer = Consumer({
        'bootstrap.servers': KAFKA_BROKER,  # Kafka server
        'group.id': 'prediction-group',
        'auto.offset.reset': 'earliest'
    })
    
    consumer.subscribe(['prediction_input'])
    
    try:
        while True:
            msg = consumer.poll(timeout=1.0)  # Poll with 1-second timeout
            
            if msg is None:
                continue  # Skip if no message is received
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    raise KafkaException(msg.error())
            
            # Decode the message
            message_value = json.loads(msg.value().decode('utf-8'))
            
            with buffer_lock:
                batch_buffer.append(message_value)

                buffer_size.set(len(batch_buffer))  # Update buffer size metric
                messages_received.inc()  # Increment message count
                
    
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()

# Run Kafka consumer and batch processing in separate threads
def start_kafka_consumer():
    consumer_thread = threading.Thread(target=consume_messages)
    consumer_thread.daemon = True
    consumer_thread.start()
    logger.info("Started Kafka consumer thread.")

    batch_thread = threading.Thread(target=batch_predict)
    batch_thread.daemon = True
    batch_thread.start()
    logger.info("Started batch prediction thread.")

# Start the Kafka consumer when FastAPI starts
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Kafka consumer and batch processing threads.")
    start_kafka_consumer()

# Health check endpoint
@app.get("/health")
def health_check():
    logger.info("Health check request received.")
    return {"status": "Healthy"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
