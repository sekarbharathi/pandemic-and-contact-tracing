import grpc
from concurrent import futures
import time
import contact_tracing_pb2
import contact_tracing_pb2_grpc
from pymongo import MongoClient
from confluent_kafka import Producer
import json
import logging
import sys
from prometheus_client import start_http_server, Counter

# Logging configuration
logging.basicConfig(
    level=logging.INFO,  # Capture all levels of logs
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]  # Force logs to stdout
)

logger = logging.getLogger(__name__)

# MongoDB connection details
MONGODB_URI = "mongodb://mongo:27017"
DATABASE_NAME = "health_data"
COLLECTION_NAME = "checkin_lab_reports"

KAFKA_BROKER = "kafka:9092"

# Kafka producer setup
conf = {'bootstrap.servers': KAFKA_BROKER}
producer = Producer(conf)

# Topic name
TOPIC_NAME = 'outbreak_alerts'

# Connect to MongoDB
client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Prometheus Metrics
REQUEST_COUNT = Counter('outbreak_requests_total', 'Total number of outbreak location requests')

# Function to deliver the Kafka message
def delivery_report(err, msg):
    if err is not None:
        logger.error(f"Message delivery failed: {err}")
    else:
        logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

class ContactTracingService(contact_tracing_pb2_grpc.ContactTracingServiceServicer):
    def SendOutbreakLocation(self, request, context):

        REQUEST_COUNT.inc()  # Increment Prometheus counter

        location_name = request.location_name
        test_type = request.test_type

        logger.info(f"Received outbreak location: {location_name} for {test_type}")

        try:
            # Query MongoDB to find users associated with the given location
            users = collection.find({
                "checkin.location.name": location_name,
                "labReport.testType": test_type,  # Ensure it's only for COVID-19
                "labReport.viralStatus": "viral-positive"  # Ensure only positive cases
            })

            # Collect user information (userId in this case, you can add more details if needed)
            user_list = [user["userId"] for user in users]

            # Log the user IDs found for the location
            logger.info(f"Users found for location {location_name}: {user_list}")

            # Send the list of users to Kafka using Confluent Kafka
            message = {'location': location_name, 'test_type': test_type, 'user_ids': user_list}
            producer.produce(TOPIC_NAME, json.dumps(message), callback=delivery_report)
            producer.flush()  # Ensure all messages are delivered
            logger.info(f"Sent outbreak alert with {test_type} disease to Kafka for location {location_name}.")

            # Respond with success and the list of users found
            return contact_tracing_pb2.OutbreakLocationResponse(
                status="success",
                user_ids=user_list  # Send the list of userIds
            )
        except Exception as e:
            logger.error(f"Error occurred while fetching data from MongoDB: {str(e)}")
            return contact_tracing_pb2.OutbreakLocationResponse(status="failure")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    contact_tracing_pb2_grpc.add_ContactTracingServiceServicer_to_server(ContactTracingService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logger.info("Contact Tracing Service is running on port 50051...")

    # Start Prometheus Metrics Server
    start_http_server(8009)  # Serves /metrics endpoint
    logger.info("Prometheus metrics available on port 50051 at /metrics")

    try:
        while True:
            time.sleep(86400)  # Keep the server running
    except KeyboardInterrupt:
        logger.warning("Shutting down server...")
        server.stop(0)

if __name__ == '__main__':
    serve()
