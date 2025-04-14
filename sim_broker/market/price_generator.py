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
    annual_vol: float = 0.18,
    seed: int | None = None,
) -> pd.DataFrame:
    """
    Simulate GBM minute-by-minute prices for all symbols.

    Parameters
    ----------
    date : str or datetime
        Trading date (YYYY‑MM‑DD or datetime). Clock starts at 09:30.
    symbols : sequence of str
        List of ticker symbols.
    minutes : int
        Number of 1‑minute bars to simulate (default = 390 for US regular session).
    start_price : float
        Opening price for all symbols.
    annual_vol : float
        Annualised volatility (sigma). 18 % ≈ S&P 500.
    seed : int or None
        RNG seed for determinism.

    Returns
    -------
    DataFrame
        Index → DatetimeIndex at 1‑min frequency  
        Columns → symbols  
        Values → mid prices (float64)
    """
    rng = np.random.default_rng(seed)

    # Create the time index: starts at 09:30 for 'minutes' intervals
    start_dt = (
        datetime.strptime(date, "%Y-%m-%d") if isinstance(date, str) else date
    ).replace(hour=9, minute=30, second=0, microsecond=0)
    index = pd.date_range(start=start_dt, periods=minutes, freq="min")

    # Calculate per-minute drift/volatility from annualized vol
    dt = 1 / (252 * minutes)  # 1 trading year ≈ 252 days × 390 minutes
    sigma_sqrt_dt = annual_vol * np.sqrt(dt)

    n_sym = len(symbols)
    eps = rng.standard_normal(size=(minutes - 1, n_sym))
    log_returns = sigma_sqrt_dt * eps
    cum_log = np.vstack([np.zeros((1, n_sym)), np.cumsum(log_returns, axis=0)])

    prices = start_price * np.exp(cum_log)

    df = pd.DataFrame(prices, index=index, columns=symbols)
    return df
