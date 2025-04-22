# Sim‑Broker Reporting Platform: Project Overview

This document provides a high‑level overview of the Sim‑Broker reporting project to date, with a focus on the heartbeat pipeline infrastructure. It captures the components implemented so far, configuration conventions, and how to run and test the end‑to‑end heartbeat workflow.

---

## 1. Project Purpose

Sim‑Broker is a simulated broker‑dealer environment designed to generate realistic market data, ingest it through a streaming pipeline, transform and store it, and surface key metrics in Apache Superset. The first incremental milestone is establishing a robust **heartbeat** pipeline that validates connectivity and end‑to‑end infrastructure without yet implementing business logic.

## 2. Components Implemented

### 2.1 Simulator (sim_broker)
- **`main.py`**: Emits a heartbeat event every 5 seconds to a Kafka topic (default `heartbeat`) using `kafka-python`.
- **Env Vars**:  
  - `REDPANDA_BROKER` (e.g. `redpanda:9092`)  
  - `HEARTBEAT_TOPIC` (default `heartbeat`)

### 2.2 Message Broker (Redpanda)
- Deployed via Docker Compose.  
- Provides a Kafka‑compatible interface for the simulator and the ingestion flow.
- **Topic Initialization**: A helper container (`topic_init`) ensures the `heartbeat` topic is created before producers/consumers start.

### 2.3 Bronze Layer (heartbeat_flow)
- **`bytewax/flows/heartbeat_flow.py`**: A Bytewax `Dataflow` that:
  1. **Sources** from Kafka (`KafkaSource`).
  2. **Parses** incoming JSON messages.
  3. **Appends** them to a JSONL file (`/lake/bronze/heartbeat.jsonl`) via `FileSink`.

### 2.4 Silver Layer (silver_heartbeat_flow)
- **`bytewax/flows/silver_heartbeat_flow.py`**: A Bytewax `Dataflow` that:
  1. **Sources** lines from the Bronze JSONL file (`FileSource`).
  2. **Parses & enriches** each record into a flat schema with `timestamp`, `type`, and derived partition keys (`year`, `month`, `day`, `hour`).
  3. **Writes** each enriched record as Parquet files partitioned by date/hour under `/lake/silver/heartbeat`.
- **Directory Creation**: On startup, ensures the Bronze parent directory exists to avoid stat errors.

## 3. Configuration & Environment Variables

All paths and behavior are driven by the following environment variables (with defaults shown):

| Variable                 | Purpose                                           | Default                                 |
|--------------------------|---------------------------------------------------|-----------------------------------------|
| `REDPANDA_BROKER`        | Host:port for Redpanda/Kafka broker               | `redpanda:9092`                         |
| `HEARTBEAT_TOPIC`        | Kafka topic name for heartbeat events             | `heartbeat`                             |
| `BRONZE_PATH`            | File path for Bronze JSONL sink                   | `lake/bronze/heartbeat.jsonl`           |
| `SILVER_PATH`            | Directory root for Silver Parquet output          | `lake/silver/heartbeat`                 |
| `BATCH_INTERVAL_SECONDS` | Batch window size (used if re‑enabled)            | `15`                                    |

Configuration is managed via:
- Project‑root `.env` (for local development).  
- `infra/docker-compose.yml` (for containerized deployment).

## 4. Docker Compose Overview

Key services in `infra/docker-compose.yml`:

```yaml
version: "3.9"
services:
  redpanda:              # Kafka broker
    image: redpandadata/redpanda:latest
    volumes:
      - ../lake:/lake

  topic_init:            # Ensures heartbeat topic exists
    depends_on: [redpanda]

  postgres:              # Analytics database for Superset
    image: postgres:15
    env_file: ../.env
    volumes: [../pgdata:/var/lib/postgresql/data]

  superset:              # Dashboard server
    image: apache/superset:latest
    env_file: ../.env
    depends_on: [postgres]

  sim_broker:            # Heartbeat simulator
    build: ../sim_broker
    command: python main.py
    env_file: ../.env
    volumes: [../lake:/lake]
    depends_on: [redpanda, topic_init]

  bytewax:               # Bronze ingestion & Silver transformation
    build: ../bytewax
    command: python -m bytewax.run flows.silver_heartbeat_flow:build_flow
    env_file: ../.env
    volumes: [../lake:/lake]
    depends_on: [redpanda, topic_init]
```

## 5. Testing Strategy

- **Unit Tests** (pytest) cover:
  - `heartbeat_flow.build_flow()` returns a valid `Dataflow`.
  - `silver_heartbeat_flow.build_flow()` returns a valid `Dataflow` under default and custom environment settings.
  - Directory‑creation logic ensures no startup errors when paths don’t exist.

Example test for env‑var override:
```python
# tests/test_silver_env_vars.py
import os
from bytewax.dataflow import Dataflow
from bytewax.flows.silver_heartbeat_flow import build_flow

def test_custom_env_vars_do_not_fail(monkeypatch, tmp_path):
    monkeypatch.setenv("BRONZE_PATH", str(tmp_path/"file.jsonl"))
    monkeypatch.setenv("SILVER_PATH", str(tmp_path/"out"))
    monkeypatch.setenv("BATCH_INTERVAL_SECONDS", "42")
    flow = build_flow()
    assert isinstance(flow, Dataflow)
```

Running all tests:
```bash
poetry run pytest
```

## 6. How to Run Locally

1. **Install dependencies via Poetry**:
   ```bash
   poetry install
   poetry add bytewax pyarrow fsspec
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env   # if provided
   # or export vars manually
   export BRONZE_PATH=lake/bronze/heartbeat.jsonl
   export SILVER_PATH=lake/silver/heartbeat
   export REDPANDA_BROKER=localhost:29092
   ```

3. **Start infrastructure**:
   ```bash
   cd infra
   docker-compose up -d
   ```

4. **Run Bytewax flow** (in project root):
   ```bash
   poetry run python -m bytewax.run flows.silver_heartbeat_flow:build_flow
   ```

5. **Verify output**:
   - Bronze JSONL: `lake/bronze/heartbeat.jsonl`
   - Silver Parquet: under `lake/silver/heartbeat/year=.../part-*.parquet`
   - Superset dashboard: http://localhost:8088

---

This completes the high‑level documentation for everything implemented so far around the heartbeat pipeline. Future work will extend this pattern to orders, trades, and full business logic transforms.

