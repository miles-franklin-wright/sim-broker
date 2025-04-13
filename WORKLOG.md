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
## 2025‑04‑13
- Updated client generator in `sim_broker/clients/segments.py`
  - Implemented deterministic UUID generation by combining two 64‑bit integers.
- Added corresponding unit tests.

