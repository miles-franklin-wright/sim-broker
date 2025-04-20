import pandas as pd
from sim_broker.clients.segments import create_clients

cfg = {
    "long_only": {
        "count": 3,
        "mean_orders_per_day": 0.3,
        "size_mu": 11,
        "size_sigma": 0.4,
    },
    "active": {"count": 2, "mean_orders_per_day": 2.0, "size_mu": 9, "size_sigma": 0.6},
}


def test_create_clients_shape():
    df = create_clients(cfg, seed=123)
    # Expecting 5 clients with 5 columns.
    assert df.shape == (5, 5)
    # Ensure the segments in the DataFrame match what we provided.
    assert set(df["segment"]) == {"long_only", "active"}


def test_create_clients_deterministic():
    df1 = create_clients(cfg, seed=42)
    df2 = create_clients(cfg, seed=42)
    pd.testing.assert_frame_equal(df1, df2)
