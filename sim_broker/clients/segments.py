"""
sim_broker.clients.segments
---------------------------
Generate a DataFrame of synthetic clients with segment‐specific
trading‐behaviour parameters.
"""

from __future__ import annotations

import uuid
from typing import Dict, List

import numpy as np
import pandas as pd


def create_clients(cfg: Dict, seed: int | None = None) -> pd.DataFrame:
    """
    Parameters
    ----------
    cfg
        Parsed YAML for the `clients:` section, e.g.:
        {
          "long_only": { "count": 1500, "mean_orders_per_day": 0.3,
                         "size_mu": 11, "size_sigma": 0.4 },
          "active":    { "count": 500,  "mean_orders_per_day": 2.0,
                         "size_mu": 9,  "size_sigma": 0.6 }
        }
    seed
        RNG seed for reproducibility.

    Returns
    -------
    DataFrame with columns:
      client_id, segment, orders_per_day, size_mu, size_sigma
    """
    rng = np.random.default_rng(seed)
    records: List[Dict] = []

    for segment, p in cfg.items():
        for _ in range(p["count"]):
            # Generate two 64-bit unsigned integers. This allows the full 0 to 2^64 - 1 range.
            hi = int(rng.integers(0, high=1 << 64, dtype=np.uint64))
            lo = int(rng.integers(0, high=1 << 64, dtype=np.uint64))
            # Combine them into a single 128-bit integer.
            client_int = (hi << 64) | lo
            records.append(
                {
                    "client_id": str(uuid.UUID(int=client_int)),
                    "segment": segment,
                    "orders_per_day": p["mean_orders_per_day"],
                    "size_mu": p["size_mu"],
                    "size_sigma": p["size_sigma"],
                }
            )

    df = pd.DataFrame.from_records(records)
    return df
