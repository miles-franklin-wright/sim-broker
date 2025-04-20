import pytest
import tempfile
from sim_broker.output.writer import write_day
import pandas as pd


def _dummy():
    orders = [{"order_id": "o"}]
    trades = [{"trade_id": "t"}]
    df = pd.DataFrame({"x": [1]})
    return orders, trades, df, df


def test_writer_idempotent():
    orders, trades, pos, pnl = _dummy()
    with tempfile.TemporaryDirectory() as tmp:
        # first write
        write_day(tmp, "2025-02-03", orders, trades, pos, pnl, seed=1)
        # second write with same data should raise
        with pytest.raises(FileExistsError):
            write_day(
                tmp, "2025-02-03", orders, trades, pos, pnl, seed=1, overwrite=False
            )
