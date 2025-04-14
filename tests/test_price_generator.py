import pandas as pd
from sim_broker.market.price_generator import generate_prices


def test_price_shape_and_first_price():
    symbols = ["AAPL", "MSFT", "GOOG"]
    df = generate_prices("2025-01-02", symbols, seed=1)
    # 390 rows × 3 columns
    assert df.shape == (390, 3)
    # first minute prices equal start_price (100)
    assert (df.iloc[0] == 100.0).all()
    # no NaNs
    assert df.notna().all().all()


def test_price_determinism():
    symbols = ["AAPL", "MSFT"]
    df1 = generate_prices("2025-01-02", symbols, seed=42)
    df2 = generate_prices("2025-01-02", symbols, seed=42)
    pd.testing.assert_frame_equal(df1, df2)
