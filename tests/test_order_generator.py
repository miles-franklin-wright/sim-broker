import pandas as pd
import pytest
from datetime import datetime

from sim_broker.execution.order_generator import create_orders
from sim_broker.clients.segments import create_clients

# Sample configuration for a minimal client DataFrame.
cfg = {
    "long_only": {"count": 2, "mean_orders_per_day": 1.0, "size_mu": 2, "size_sigma": 0.1},
    "active": {"count": 1, "mean_orders_per_day": 3.0, "size_mu": 1.5, "size_sigma": 0.2},
}

@pytest.fixture
def clients_df():
    from sim_broker.clients.segments import create_clients
    return create_clients(cfg, seed=123)

def test_create_orders_returns_list(clients_df):
    symbols = ["AAPL", "MSFT", "GOOG"]
    orders = create_orders(clients_df, symbols, "2025-01-02", seed=42)
    # Check that we get a list.
    assert isinstance(orders, list)
    # Each order should be a dict containing required keys.
    required_keys = [
        "order_id", "client_id", "desk_id", "symbol", "side",
        "order_type", "qty", "ts_created",
    ]
    for order in orders:
        for key in required_keys:
            assert key in order, f"Missing key '{key}' in order {order}"
        # For limit orders, limit_px must be set; for market orders, limit_px should be None.
        if order["order_type"] == "LMT":
            assert order["limit_px"] is not None
        else:
            assert order["limit_px"] is None

def test_create_orders_determinism(clients_df):
    symbols = ["AAPL", "MSFT", "GOOG"]
    orders1 = create_orders(clients_df, symbols, "2025-01-02", seed=99)
    orders2 = create_orders(clients_df, symbols, "2025-01-02", seed=99)
    # Both order lists should be identical (including deterministic order_id).
    assert orders1 == orders2

def test_orders_timestamp_within_session(clients_df):
    symbols = ["AAPL"]
    orders = create_orders(clients_df, symbols, "2025-01-02", seed=101)
    session_start = datetime.strptime("2025-01-02 09:30:00", "%Y-%m-%d %H:%M:%S")
    session_end = session_start + pd.Timedelta(minutes=390)
    for order in orders:
        ts = datetime.fromisoformat(order["ts_created"])
        assert session_start <= ts <= session_end
