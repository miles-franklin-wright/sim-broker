# bytewax/flows/heartbeat_flow.py

import os
import json
from bytewax.dataflow import Dataflow
import bytewax.operators as op
from bytewax.connectors.kafka import KafkaSource
from bytewax.connectors.files import FileSink


def build_flow() -> Dataflow:
    # Read env vars with sensible defaults
    broker = os.getenv("REDPANDA_BROKER", "redpanda:9092")
    topic = os.getenv("HEARTBEAT_TOPIC", "heartbeat")
    bronze_path = os.getenv("BRONZE_PATH", "/lake/bronze/heartbeat.jsonl")

    # Define the flow
    flow = Dataflow("heartbeat_flow")

    # Step 1: Read from Kafka
    inp = op.input("in", flow, KafkaSource(topics=[topic], brokers=[broker]))

    # Step 2: Parse JSON
    kv_msgs = op.map(
        "to_kv", inp, lambda msg: ("heartbeat", json.dumps(json.loads(msg.value)))
    )

    # Step 3: Write to file
    op.output("out", kv_msgs, FileSink(bronze_path))

    return flow
