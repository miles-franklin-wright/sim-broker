import os
import json
from datetime import datetime, timedelta

import pyarrow as pa
import pyarrow.parquet as pq

from bytewax.dataflow import Dataflow
import bytewax.operators as op
from bytewax.inputs import SimplePollingSource

# Global writer instance
_writer = None


class TailSource(SimplePollingSource):
    """
    A Bytewax polling source that tails a JSONL file, yielding existing
    and new lines as they appear.
    """

    def __init__(self, path: str):
        super().__init__(interval=timedelta(seconds=1))
        self._path = path
        self._file = None

    def next_item(self):
        # Lazily open the file on first call
        if self._file is None:
            # Will create parent dirs before; file may not exist yet
            self._file = open(self._path, "r")
        line = self._file.readline()
        if not line:
            # No new line; retry after a short interval
            raise SimplePollingSource.Retry(timedelta(seconds=1))
        return line


def build_flow() -> Dataflow:
    """
    Bytewax flow to tail heartbeats from Bronze JSONL and append them
    into one Silver Parquet file as row-groups.
    """
    bronze_path = os.getenv("BRONZE_PATH", "lake/bronze/heartbeat.jsonl")
    silver_file = os.getenv("SILVER_FILE", "lake/silver/heartbeat/heartbeat.parquet")

    # Ensure the directories exist
    os.makedirs(os.path.dirname(bronze_path), exist_ok=True)
    os.makedirs(os.path.dirname(silver_file), exist_ok=True)

    flow = Dataflow("silver_heartbeat_flow")

    # 1) Use our TailSource to read all existing and new lines
    inp = op.input("in", flow, TailSource(bronze_path))

    # 2) Parse each line into a clean record
    def parse_record(line: str) -> dict:
        rec = json.loads(line)
        ts = datetime.fromtimestamp(rec["timestamp"])
        return {
            "timestamp": ts,
            "type": rec["type"],
        }

    records = op.map("parse", inp, parse_record)

    # 3) Side-effect: open one ParquetWriter and append each record
    def write_one(record: dict):
        global _writer
        table = pa.Table.from_pylist([record])
        if _writer is None:
            _writer = pq.ParquetWriter(silver_file, table.schema, compression="snappy")
        _writer.write_table(table)
        return []  # end of chain for this record

    op.flat_map("write", records, write_one)

    # 4) Terminal inspect so Bytewax knows this flow has an output
    op.inspect("noop_inspect", records, lambda _step, _item: None)

    return flow
