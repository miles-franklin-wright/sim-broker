# Sim‑Broker – Work Log

## 2025-04-13
- Created project repo and virtual environment
- Added `.gitignore` to exclude `.venv/`
- Installed base dependencies (numpy, pandas, pydantic, etc.)
- Created project file structure (initial)
- Started working on initial market data and client simulation
- - Implemented `market/price_generator.py`
  - Generates 1‑minute GBM price paths for any symbol list
  - Deterministic via seed
- Added unit tests `test_price_generator.py` (shape & determinism)
- Updated client generator in `sim_broker/clients/segments.py`
  - Implemented deterministic UUID generation by combining two 64‑bit integers.
- Added corresponding unit tests.
- Implemented Order Generator module (`sim_broker/execution/order_generator.py`)
  - Now uses deterministic order IDs for reproducibility.
- Added unit tests for Order Generator.
- Implemented Fill Engine (`sim_broker/execution/fill_engine.py`)
  - Supports market and limit orders with slippage and fee calculation.
- Added unit tests for the fill engine.
- Added US agency desk (`sim_broker/desks/us_desk.py`) with position & P&L tracking.
- Implemented Writer utility (`sim_broker/output/writer.py`) for daily file output.
- Added CLI (`sim_broker/cli.py`) that orchestrates Sprint‑0 pipeline and writes outputs.
- Introduced YAML config + env/CLI override for output directory.
- Added system‑level tests: determinism, seed variation, writer idempotence.
