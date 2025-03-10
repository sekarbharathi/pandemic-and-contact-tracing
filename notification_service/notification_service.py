import json
import logging
import sys
from confluent_kafka import Consumer, KafkaException, KafkaError
import threading
from prometheus_client import start_http_server, Counter

# Logging configuration (INFO and above only)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Kafka consumer setup
conf = {
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'notification_service',
    'auto.offset.reset': 'earliest'
}
consumer = Consumer(conf)
consumer.subscribe(['outbreak_alerts', 'hotspot_alerts'])  # Added 'risk_alerts'


# Prometheus metrics
MESSAGES_PROCESSED = Counter("messages_processed_total", "Total number of messages processed")
MESSAGES_ERROR = Counter("messages_error_total", "Total number of message processing errors")

# Start Prometheus metrics server on a separate thread
def start_metrics_server():
    start_http_server(8006, addr="0.0.0.0")  # Exposes metrics on port 8005
    logger.info("Metrics server started on port 8006")

metrics_thread = threading.Thread(target=start_metrics_server, daemon=True)
metrics_thread.start()


# Function to generate a deterministic phone number based on user_id
def generate_deterministic_phone_number(user_id):
    # Convert the user_id to a unique integer
    user_id_hash = hash(user_id) % (10 ** 8)  # Ensure it fits within the range of a phone number
    area_code = (user_id_hash % 900) + 100  # Ensure the area code is between 100 and 999
    prefix = (user_id_hash // 10**4) % 900 + 100  # The prefix is between 100 and 999
    line_number = user_id_hash % 10000  # Line number is between 0000 and 9999
    return f"+1 ({area_code}) {prefix}-{line_number:04d}"

# Function to process outbreak alerts and send notifications
def process_outbreak_alert(message):
    location = message['location']
    users = message['user_ids']
    alert_message = f"Alert: Outbreak detected in {location} with positive COVID cases. Please take necessary precautions."

    logger.info(f"Processing outbreak alert for location: {location}")

    for user_id in users:
        # Use the deterministic phone number
        phone_number = generate_deterministic_phone_number(user_id)
        logger.info(f"Sent SMS to {user_id} - {phone_number}: {alert_message}")

# Function to send hotspot notifications
def send_hotspot_notifications(message):
    hotspots = message['top_hotspots']
    user_ids = message['user_ids']
    top_hotspots = [hotspot['location'] for hotspot in hotspots[:3]]  # Extract the top 3 locations
    hotspots_message = ", ".join(top_hotspots)

    if user_ids:
        for user_id in user_ids:
            # Use deterministic phone number
            phone_number = generate_deterministic_phone_number(user_id)
            logger.info(f"Alert: Sent message to {user_id} - {phone_number}: Hotspot detected in locations with high COVID cases: {hotspots_message}")
    else:
        logger.warning("No user_ids found for hotspot notification.")

# Function to send risk notifications
# def send_risk_notifications(message):
#     location = message['location']
#     risk_level = message['risk_level']
#     reason = message['reason']
#     user_ids = message.get("user_ids", [])

#     alert_message = f"Risk Alert: {location} is at {risk_level} risk. Reason: {reason}"

#     if user_ids:
#         for user_id in user_ids:
#             # Use deterministic phone number
#             phone_number = generate_deterministic_phone_number(user_id)
#             logger.info(f"Sent SMS to {user_id} - {phone_number}: {alert_message}")
#     else:
#         logger.warning(f"Public Alert: {alert_message}")

# Function to listen for incoming alerts from Kafka
def listen_for_alerts():
    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    logger.error(f"Kafka error: {msg.error()}")
                    MESSAGES_ERROR.inc() 
                    raise KafkaException(msg.error())

            try:
                message = json.loads(msg.value().decode('utf-8'))
            except json.JSONDecodeError as e:
                logger.error(f"JSON decoding error: {e}")
                MESSAGES_ERROR.inc()  # Increment error counter
                continue

            if 'location' in message and 'user_ids' in message:
                process_outbreak_alert(message)

            if 'top_hotspots' in message and 'user_ids' in message:
                send_hotspot_notifications(message)

            # if 'risk_level' in message and 'reason' in message:
            #     send_risk_notifications(message)

            MESSAGES_PROCESSED.inc()  # Increment processed messages counter

    except KeyboardInterrupt:
        logger.info("Notification service shutting down...")
    finally:
        consumer.close()


if __name__ == '__main__':
    logger.info("Notification service started...")
    listen_for_alerts()


