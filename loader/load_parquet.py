import os
import pyarrow.parquet as pq
import psycopg2
from psycopg2.extras import execute_values

# Configuration of tables to load
TABLES = {
    "heartbeat": {
        "ddl": """
CREATE TABLE IF NOT EXISTS heartbeat (
    timestamp TIMESTAMP PRIMARY KEY,
    type      TEXT
);
""",
        "pk": "timestamp",
        "columns": ["timestamp", "type"],
    },
    # Extend for more tables as needed
}


def main():
    # Read environment variables at runtime
    db_dsn = os.getenv("DB_DSN")
    parquet_path = os.getenv("PARQUET_PATH")

    if not db_dsn or not parquet_path:
        raise RuntimeError("Environment variables DB_DSN and PARQUET_PATH must be set")

    # Open the Parquet dataset
    ds = pq.ParquetFile(parquet_path)

    # Connect to Postgres and load data
    with psycopg2.connect(db_dsn) as conn:
        cur = conn.cursor()

        for table_name, cfg in TABLES.items():
            # Ensure the table exists
            cur.execute(cfg["ddl"])

            # Determine the last loaded primary key
            cur.execute(f"SELECT COALESCE(MAX({cfg['pk']}), 'epoch') FROM {table_name}")
            (max_pk,) = cur.fetchone()

            # Gather new rows
            to_insert = []
            for rg in range(ds.num_row_groups):
                batch = ds.read_row_group(rg, columns=cfg["columns"])
                df = batch.to_pandas()
                new_rows = df[df[cfg["pk"]] > max_pk]
                for _, row in new_rows.iterrows():
                    to_insert.append(tuple(row[col] for col in cfg["columns"]))

            # Bulk insert, skipping duplicates
            if to_insert:
                cols = ", ".join(cfg["columns"])
                sql = (
                    f"INSERT INTO {table_name}({cols}) VALUES %s "
                    f"ON CONFLICT ({cfg['pk']}) DO NOTHING"
                )
                execute_values(cur, sql, to_insert)

        conn.commit()


if __name__ == "__main__":
    main()
