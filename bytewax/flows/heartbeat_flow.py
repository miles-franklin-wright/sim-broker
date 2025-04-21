# bytewax/flows/heartbeat_flow.py

import os
import json
from bytewax.dataflow import Dataflow
import bytewax.operators as op
from bytewax.connectors.kafka import KafkaSource
from bytewax.connectors.files import FileSink


if __name__ == "__main__":
    # Read env vars with sensible defaults
    broker = os.getenv("REDPANDA_BROKER", "redpanda:9092")
    topic = os.getenv("HEARTBEAT_TOPIC", "heartbeat")
    bronze_path = os.getenv("BRONZE_PATH", "/lake/bronze/heartbeat.jsonl")

    # Define the flow
    flow = Dataflow("heartbeat_flow")

    # Step 1: Read from Kafka
    inp = op.input("in", flow, KafkaSource([topic], broker))

    # Step 2: Parse JSON
    prse = op.map("parse", inp, lambda msg: json.loads(msg.value))

    # Step 3: Write to file
    op.output("out", prse, FileSink(bronze_path))

    # Step 4: Run the flow
    flow.run()
