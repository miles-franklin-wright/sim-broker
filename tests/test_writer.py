import json
import pandas as pd
import tempfile

from sim_broker.output.writer import write_day


def make_dummy():
    orders = [{"order_id": "o1"}, {"order_id": "o2"}]
    trades = [{"trade_id": "t1"}, {"trade_id": "t2"}, {"trade_id": "t3"}]
    positions = pd.DataFrame({"symbol": ["AAPL"], "shares": [100]})
    pnl = pd.DataFrame({"desk_id": ["US_AGENCY"], "realised_pnl": [120.0]})
    return orders, trades, positions, pnl


def test_write_day_creates_files():
    orders, trades, positions, pnl = make_dummy()
    with tempfile.TemporaryDirectory() as tmp:
        day_dir = write_day(tmp, "2025-01-02", orders, trades, positions, pnl, seed=42)
        # Check files exist
        expected = [
            "orders.jsonl",
            "trades.jsonl",
            "positions.csv",
            "pnl.csv",
            "meta.json",
        ]
        for fname in expected:
            assert (day_dir / fname).exists()

        # Validate meta.json content
        meta = json.loads((day_dir / "meta.json").read_text())
        assert meta["rows"]["orders"] == 2
        assert meta["rows"]["trades"] == 3
        assert meta["seed"] == 42


def test_overwrite_flag():
    orders, trades, positions, pnl = make_dummy()
    with tempfile.TemporaryDirectory() as tmp:
        # First write succeeds
        write_day(tmp, "2025-01-02", orders, trades, positions, pnl, seed=None)
        # Second write without overwrite should raise
        import pytest

        with pytest.raises(FileExistsError):
            write_day(
                tmp,
                "2025-01-02",
                orders,
                trades,
                positions,
                pnl,
                seed=None,
                overwrite=False,
            )
        # With overwrite=True should succeed
        write_day(
            tmp, "2025-01-02", orders, trades, positions, pnl, seed=None, overwrite=True
        )
