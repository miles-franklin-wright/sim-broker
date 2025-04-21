import os
import time
import json
from kafka import KafkaProducer


def get_producer():
    """Lazily initialize and return a KafkaProducer based on REDPANDA_BROKER env var."""
    broker = os.getenv("REDPANDA_BROKER")
    if not broker:
        raise EnvironmentError("REDPANDA_BROKER environment variable is required")
    return KafkaProducer(
        bootstrap_servers=[broker],
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )


def main():
    """Emit a heartbeat event every 5 seconds to the configured topic."""
    producer = get_producer()
    topic = os.getenv("HEARTBEAT_TOPIC", "heartbeat")
    while True:
        event = {"type": "heartbeat", "timestamp": time.time()}
        producer.send(topic, event)
        producer.flush()
        print(f"Sent heartbeat: {event}")
        time.sleep(5)


if __name__ == "__main__":
    main()
