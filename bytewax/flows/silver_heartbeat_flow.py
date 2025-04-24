import os
import json
from datetime import datetime

from bytewax.dataflow import Dataflow
import bytewax.operators as op
from bytewax.connectors.files import FileSource

import pyarrow as pa
import pyarrow.parquet as pq


def build_flow() -> Dataflow:
    """
    Bytewax flow to read heartbeats from a Bronze JSONL and write partitioned Parquet files to Silver.
    """
    # Paths and settings from environment
    bronze_path = os.getenv("BRONZE_PATH", "lake/bronze/heartbeat.jsonl")
    silver_path = os.getenv("SILVER_PATH", "lake/silver/heartbeat")

    parent_dir = os.path.dirname(bronze_path)
    if parent_dir and not os.path.isdir(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    flow = Dataflow("silver_heartbeat_flow")

    # Step 1: Source - read lines from JSONL
    inp = op.input("in", flow, FileSource(bronze_path))

    # Step 2: Parse & Enrich each record
    def parse_and_enrich(line: str) -> dict:
        record = json.loads(line)
        print(f"Read line: {line}")
        ts = datetime.fromtimestamp(record.get("timestamp"))
        return {
            "timestamp": ts,
            "type": record.get("type"),
            "year": ts.year,
            "month": ts.month,
            "day": ts.day,
            "hour": ts.hour,
        }

    enriched = op.map("parse_enrich", inp, parse_and_enrich)

    # Step 3: Write with flat_map and side-effecting function
    def write_and_passthrough(record: dict):
        table = pa.Table.from_pylist([record])
        pq.write_to_dataset(
            table,
            root_path=silver_path,
            partition_cols=["year", "month", "day", "hour"],
            existing_data_behavior="overwrite_or_ignore",
        )
        return []  # flat_map expects iterable return

    op.flat_map("write", enriched, write_and_passthrough)

    op.inspect("noop_inspect", enriched, lambda record: None)

    return flow
