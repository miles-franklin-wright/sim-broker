#!/usr/bin/env python3
"""
infra/compactor.py

Usage:
  # Incrementally compact the previous hour (default):
  python infra/compactor.py

  # Backfill / compact *all* existing partitions:
  python infra/compactor.py --all
"""
import os
import glob
import datetime
import argparse
import logging

import pyarrow as pa
import pyarrow.parquet as pq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_SILVER = "lake/silver/heartbeat"


def compact_hour(year: int, month: int, day: int, hour: int):
    """
    Merge every small *.parquet in:
      {SILVER_PATH or DEFAULT_SILVER}/year=YYYY/month=MM/day=DD/hour=HH
    into one compacted.parquet, then delete the originals.
    """
    silver_root = os.getenv("SILVER_PATH", DEFAULT_SILVER)
    partition_dir = os.path.join(
        silver_root,
        f"year={year:04d}",
        f"month={month:02d}",
        f"day={day:02d}",
        f"hour={hour:02d}",
    )
    pattern = os.path.join(partition_dir, "*.parquet")
    # pick up only the “small” files, exclude any existing compacted.parquet
    to_merge = [p for p in glob.glob(pattern) if not p.endswith("compacted.parquet")]
    if not to_merge:
        logger.info(f"No files to compact in {partition_dir}")
        return

    # Read and merge
    tables = [pq.read_table(p) for p in to_merge]
    combined = pa.concat_tables(tables)

    # Write out the merged file
    out_path = os.path.join(partition_dir, "compacted.parquet")
    pq.write_table(combined, out_path, compression="snappy")
    logger.info(f"Wrote {out_path} ({combined.num_rows} rows)")

    # Remove originals
    for p in to_merge:
        try:
            os.remove(p)
        except Exception:
            logger.exception(f"Failed to remove {p}")


def compact_all():
    """
    Walk every hour partition under the Silver root and compact it.
    """
    silver_root = os.getenv("SILVER_PATH", DEFAULT_SILVER)
    # e.g. lake/silver/heartbeat/year=*/month=*/day=*/hour=*
    pattern = os.path.join(silver_root, "year=*", "month=*", "day=*", "hour=*")
    for partition in glob.glob(pattern):
        parts = partition.split(os.sep)[-4:]
        year = int(parts[0].split("=")[1])
        month = int(parts[1].split("=")[1])
        day = int(parts[2].split("=")[1])
        hour = int(parts[3].split("=")[1])
        logger.info(f"Backfilling partition {year}-{month:02d}-{day:02d} {hour:02d}h")
        compact_hour(year, month, day, hour)


def run_hourly_compaction():
    """
    Compact only the *previous* hour.
    """
    now = datetime.datetime.utcnow()
    prev = now - datetime.timedelta(hours=1)
    compact_hour(prev.year, prev.month, prev.day, prev.hour)


def main():
    parser = argparse.ArgumentParser(description="Silver Parquet compactor")
    parser.add_argument(
        "--all", action="store_true", help="Backfill all existing hour partitions"
    )
    args = parser.parse_args()

    if args.all:
        compact_all()
    else:
        run_hourly_compaction()


if __name__ == "__main__":
    main()
