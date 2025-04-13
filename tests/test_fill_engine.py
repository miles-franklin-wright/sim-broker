import math
from datetime import datetime

import numpy as np
import pandas as pd
import pytest
from sim_broker.execution.fill_engine import fill_order, fill_orders

# Define some sample orders to test our fill engine:
ORDER_MKT_BUY = {
    "order_id": "order-001",
    "desk_id": "US_AGENCY",
    "symbol": "AAPL",
    "side": "BUY",
    "order_type": "MKT",
    "qty": 100,
    "ts_created": "2025-01-02T09:31:00"
}

ORDER_LMT_BUY_FILL = {
    "order_id": "order-002",
    "desk_id": "US_AGENCY",
    "symbol": "AAPL",
    "side": "BUY",
    "order_type": "LMT",
    "limit_px": 101.0,  # Should fill if mid price (100.0) <= limit
    "qty": 50,
    "ts_created": "2025-01-02T09:32:00"
}

ORDER_LMT_BUY_NOFILL = {
    "order_id": "order-003",
    "desk_id": "US_AGENCY",
    "symbol": "AAPL",
    "side": "BUY",
    "order_type": "LMT",
    "limit_px": 99.0,   # Should NOT fill if mid price (100.0) > limit
    "qty": 50,
    "ts_created": "2025-01-02T09:33:00"
}

ORDER_LMT_SELL_FILL = {
    "order_id": "order-004",
    "desk_id": "US_AGENCY",
    "symbol": "AAPL",
    "side": "SELL",
    "order_type": "LMT",
    "limit_px": 99.0,   # Should fill if mid price (100.0) >= limit
    "qty": 75,
    "ts_created": "2025-01-02T09:34:00"
}

ORDER_LMT_SELL_NOFILL = {
    "order_id": "order-005",
    "desk_id": "US_AGENCY",
    "symbol": "AAPL",
    "side": "SELL",
    "order_type": "LMT",
    "limit_px": 101.0,  # Should NOT fill if mid price (100.0) < limit
    "qty": 75,
    "ts_created": "2025-01-02T09:35:00"
}


def test_fill_order_market():
    rng = np.random.default_rng(42)
    mid_price = 100.0
    trade = fill_order(ORDER_MKT_BUY, mid_price, rng)
    assert trade is not None
    # Check that the executed price is near 100 (allowing for slippage)
    assert abs(trade["px_exec"] - 100.0) < 0.5
    # Check fee computation: fee = max(0.0025 * qty, 1.0)
    expected_fee = max(0.0025 * ORDER_MKT_BUY["qty"], 1.0)
    assert math.isclose(trade["fee"], expected_fee, rel_tol=1e-5)


def test_fill_order_limit_buy_fills():
    rng = np.random.default_rng(123)
    mid_price = 100.0
    trade = fill_order(ORDER_LMT_BUY_FILL, mid_price, rng)
    assert trade is not None
    # For limit orders that fill, we use mid price.
    assert abs(trade["px_exec"] - mid_price) < 0.001


def test_fill_order_limit_buy_nofill():
    rng = np.random.default_rng(123)
    mid_price = 100.0
    trade = fill_order(ORDER_LMT_BUY_NOFILL, mid_price, rng)
    assert trade is None


def test_fill_order_limit_sell_fills():
    rng = np.random.default_rng(123)
    mid_price = 100.0
    trade = fill_order(ORDER_LMT_SELL_FILL, mid_price, rng)
    assert trade is not None
    assert abs(trade["px_exec"] - mid_price) < 0.001


def test_fill_order_limit_sell_nofill():
    rng = np.random.default_rng(123)
    mid_price = 100.0
    trade = fill_order(ORDER_LMT_SELL_NOFILL, mid_price, rng)
    assert trade is None


def test_fill_orders_batch():
    orders = [
        ORDER_MKT_BUY,
        ORDER_LMT_BUY_FILL,
        ORDER_LMT_BUY_NOFILL,
        ORDER_LMT_SELL_FILL,
        ORDER_LMT_SELL_NOFILL,
    ]
    # Provide current mid prices for each symbol
    current_prices = {"AAPL": 100.0}
    trades = fill_orders(orders, current_prices, seed=42)
    # Expect three orders to fill: the market order, the BUY limit that qualifies, and the SELL limit that qualifies.
    assert len(trades) == 3
    # Ensure each trade has the expected keys.
    expected_keys = ["trade_id", "order_id", "desk_id", "symbol", "side", "qty_exec", "px_exec", "fee", "ts_exec"]
    for trade in trades:
        for key in expected_keys:
            assert key in trade
