# tests/test_load_parquet.py

import os
import datetime
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

# import your loader module
from loader import load_parquet

# --- Helpers to fake out psycopg2 and execute_values ---


class DummyCursor:
    def __init__(self):
        self.queries = []
        self.max_pk = None

    def execute(self, sql, params=None):
        # record every SQL statement
        self.queries.append(sql)

    def fetchone(self):
        # SELECT COALESCE(MAX(...)) → return our test max_pk
        return (self.max_pk,)


class DummyConnection:
    def __init__(self, cursor):
        self._cur = cursor

    def cursor(self):
        return self._cur

    def commit(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass


@pytest.fixture(autouse=True)
def patch_db_and_execute(monkeypatch):
    """
    Stub out psycopg2.connect and the execute_values bulk‐insert
    so we can capture what gets written.
    """
    # 1) fake connection & cursor
    dummy_cur = DummyCursor()
    dummy_conn = DummyConnection(dummy_cur)
    monkeypatch.setattr(load_parquet.psycopg2, "connect", lambda dsn: dummy_conn)

    # 2) capture execute_values calls
    captured = {}

    def fake_execute_values(cur, sql, values):
        captured["sql"] = sql
        captured["values"] = values

    monkeypatch.setattr(load_parquet, "execute_values", fake_execute_values)

    return dummy_cur, captured


# --- Tests ---


def test_inserts_only_new_rows(patch_db_and_execute, tmp_path):
    dummy_cur, captured = patch_db_and_execute

    # --- 1) prepare a tiny Parquet with two heartbeats ---
    rows = {
        "timestamp": [
            datetime.datetime(2025, 1, 1, 0, 0),
            datetime.datetime(2025, 1, 2, 0, 0),
        ],
        "type": ["old", "new"],
    }
    tbl = pa.Table.from_pydict(rows)
    parquet_file = tmp_path / "hb.parquet"
    pq.write_table(tbl, parquet_file)

    # --- 2) point the loader at our file + dummy DSN ---
    os.environ["PARQUET_PATH"] = str(parquet_file)
    os.environ["DB_DSN"] = "postgres://user:pass@host:1/db"

    # --- 3) pretend the DB already has the first timestamp ---
    dummy_cur.max_pk = datetime.datetime(2025, 1, 1, 0, 0)

    # --- 4) run the loader ---
    load_parquet.main()

    # --- 5) assertions ---
    # a) it should CREATE the table first
    assert any("CREATE TABLE IF NOT EXISTS heartbeat" in q for q in dummy_cur.queries)

    # b) it should SELECT the max(timestamp)
    assert any(
        q.strip().startswith("SELECT COALESCE(MAX(timestamp)")
        for q in dummy_cur.queries
    )

    # c) only the second row ("new") gets bulk‐inserted
    assert len(captured["values"]) == 1
    ts, tp = captured["values"][0]
    assert tp == "new"


def test_inserts_nothing_if_no_new_rows(patch_db_and_execute, tmp_path):
    dummy_cur, captured = patch_db_and_execute

    # Parquet file where every row is ≤ max_pk
    rows = {
        "timestamp": [
            datetime.datetime(2025, 1, 1, 0, 0),
            datetime.datetime(2025, 1, 1, 0, 0),
        ],
        "type": ["x", "y"],
    }
    tbl = pa.Table.from_pydict(rows)
    parquet_file = tmp_path / "hb2.parquet"
    pq.write_table(tbl, parquet_file)

    os.environ["PARQUET_PATH"] = str(parquet_file)
    os.environ["DB_DSN"] = "postgres://user:pass@host:1/db"

    dummy_cur.max_pk = datetime.datetime(2025, 1, 1, 0, 0)

    load_parquet.main()

    # Since no new rows, execute_values should never be called
    assert "values" not in captured
