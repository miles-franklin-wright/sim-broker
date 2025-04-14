"""
sim_broker.execution.order_generator
--------------------------------------
Generate simulated orders for a given trading day based on client data.

For each client (with attributes like orders_per_day, size_mu, size_sigma),
simulate the number of orders using a Poisson process, then create order records.

Order Fields:
  - order_id: Deterministic unique identifier (constructed using RNG)
  - client_id: From the client record
  - desk_id: Defaulted to "US_AGENCY"
  - symbol: Chosen randomly from a provided list
  - side: "BUY" or "SELL" (50/50 probability)
  - order_type: "MKT" (80% chance) or "LMT" (20% chance)
  - limit_px: For limit orders, set as a slight adjustment around a reference mid-price (100.0)
  - qty: Sampled from a log-normal distribution (using client's size_mu and size_sigma)
  - ts_created: Simulated order creation time (random minute offset from 09:30)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Sequence

import numpy as np
import pandas as pd

# Configuration constants for order generation
DEFAULT_REFERENCE_PRICE = 100.0  # used for limit orders in Sprint 0
SESSION_START = datetime.strptime("09:30", "%H:%M")
TRADING_MINUTES = 390
PROB_MARKET_ORDER = 0.8  # 80% chance of market order


def create_orders(
    clients: pd.DataFrame,
    symbols: Sequence[str],
    trading_date: str | datetime,
    seed: int | None = None,
) -> List[Dict[str, Any]]:
    """
    Generate a list of orders for a given trading day.

    Parameters
    ----------
    clients : DataFrame
        DataFrame produced by the client generator, with columns:
         'client_id', 'segment', 'orders_per_day', 'size_mu', 'size_sigma'
    symbols : list
        List of symbols to trade (e.g., ["AAPL", "MSFT", "GOOG"]).
    trading_date : str or datetime
        Trading date in "YYYY-MM-DD" format or a datetime object.
    seed : int, optional
        RNG seed for deterministic output.

    Returns
    -------
    List[order dict]
    """
    rng = np.random.default_rng(seed)

    if isinstance(trading_date, str):
        trading_date = datetime.strptime(trading_date, "%Y-%m-%d")

    orders = []
    session_start = trading_date.replace(hour=9, minute=30, second=0, microsecond=0)

    for _, client in clients.iterrows():
        # Determine number of orders for this client for the day.
        n_orders = rng.poisson(lam=client["orders_per_day"])
        for _ in range(n_orders):
            # Generate a deterministic order id using RNG:
            hi = int(rng.integers(0, high=1 << 64, dtype=np.uint64))
            lo = int(rng.integers(0, high=1 << 64, dtype=np.uint64))
            order_id = str(uuid.UUID(int=(hi << 64) | lo))

            client_id = client["client_id"]
            desk_id = "US_AGENCY"  # default for Sprint 0
            # Randomly choose a symbol.
            symbol = rng.choice(symbols)
            # Randomly choose side: BUY or SELL.
            side = rng.choice(["BUY", "SELL"])
            # Randomly decide order type.
            order_type = "MKT" if rng.uniform() < PROB_MARKET_ORDER else "LMT"
            # Sample quantity from a log-normal distribution.
            qty = int(rng.lognormal(mean=client["size_mu"], sigma=client["size_sigma"]))
            # Randomly assign a minute offset within the session.
            minute_offset = rng.integers(0, TRADING_MINUTES)
            ts_created = session_start + timedelta(minutes=int(minute_offset))
            # For limit orders, calculate a limit price adjustment.
            limit_px = None
            if order_type == "LMT":
                adjustment = rng.normal(0.001, 0.0005)  # approx. 0.1% deviation
                if side == "BUY":
                    limit_px = DEFAULT_REFERENCE_PRICE * (1 + abs(adjustment))
                else:
                    limit_px = DEFAULT_REFERENCE_PRICE * (1 - abs(adjustment))
            
            order = {
                "order_id": order_id,
                "client_id": client_id,
                "desk_id": desk_id,
                "symbol": symbol,
                "side": side,
                "order_type": order_type,
                "qty": qty,
                "limit_px": limit_px,  # None for market orders
                "ts_created": ts_created.isoformat(),
            }
            orders.append(order)
    return orders
