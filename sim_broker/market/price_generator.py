"""
sim_broker.market.price_generator
---------------------------------
Generate 1‑minute mid‑prices for a list of symbols using a simple
geometric random walk (GBM).

This is deliberately lightweight for Sprint 0.  We’ll swap in a more
realistic model later.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Sequence

import numpy as np
import pandas as pd


def generate_prices(
    date: str | datetime,
    symbols: Sequence[str],
    minutes: int = 390,
    start_price: float = 100.0,
    vol: float = 0.18,
    seed: int | None = None,
) -> pd.DataFrame:
    """
    Parameters
    ----------
    date
        Trading date (YYYY‑MM‑DD or datetime).  The clock starts at 09:30.
    symbols
        Iterable of ticker strings.
    minutes
        Number of 1‑minute bars to generate (US regular session = 390).
    start_price
        Starting price for *all* symbols (USD).
    vol
        Annualised volatility (sigma). 18 % ≈ typical S&P 500.
    seed
        RNG seed for determinism.

    Returns
    -------
    DataFrame
        Index → pandas DatetimeIndex (one row per minute)  
        Columns → symbols  
        Values → mid prices (float64)
    """
    rng = np.random.default_rng(seed)

    # time grid: 09:30 + n minutes
    start_dt = (
        datetime.strptime(date, "%Y-%m-%d") if isinstance(date, str) else date
    ).replace(hour=9, minute=30, second=0, microsecond=0)
    index = pd.date_range(start=start_dt, periods=minutes, freq="T")

    dt = 1 / (252 * minutes)  # 1 trading year ≈ 252 days
    sigma_sqrt_dt = vol * np.sqrt(dt)

    n_sym = len(symbols)
    # ε ~ N(0,1)   ->  log‑return r = σ√Δt * ε
    eps = rng.standard_normal(size=(minutes, n_sym))
    log_returns = sigma_sqrt_dt * eps

    # cumulative log returns; prepend zeros so first price = start_price
    log_price = np.vstack([np.zeros((1, n_sym)), np.cumsum(log_returns, axis=0)])
    prices = start_price * np.exp(log_price[1:])  # drop prepended row

    df = pd.DataFrame(prices, index=index, columns=symbols)
    return df
