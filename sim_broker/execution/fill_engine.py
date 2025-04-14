"""
sim_broker.execution.fill_engine
----------------------------------
A simple fill engine that processes orders and produces trade records.

Order Types:
 - Market orders (MKT): Execute immediately with a small random slippage.
 - Limit orders (LMT): Execute if the limit condition is satisfied:
      • For BUY orders: fill if limit_px >= current mid price.
      • For SELL orders: fill if limit_px <= current mid price.
      
Assumptions for Sprint 0:
 - All fills are full (no partial fills).
 - Fee is computed based on a per-share commission rate.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from typing import Any, Dict, List, Optional

import numpy as np

# Constants for simulation
SLIPPAGE_MEAN = 0.0             # no directional bias
SLIPPAGE_STD = 0.0005           # typical slippage: 0.05%
COMMISSION_PER_SHARE = 0.0025   # USD commission per share
MIN_COMMISSION = 1.0            # minimum commission fee in USD

def fill_order(order: Dict[str, Any], mid_price: float, rng: np.random.Generator) -> Optional[Dict[str, Any]]:
    """
    Process a single order and return a trade record if the order is filled.

    Parameters
    ----------
    order : dict
        Order dictionary with keys:
         - order_id, side ("BUY" or "SELL"), order_type ("MKT" or "LMT"),
           qty, (limit_px if applicable), desk_id, ts_created, symbol.
    mid_price : float
        Current market mid-price for the order's symbol.
    rng : np.random.Generator
        Random generator (seeded for reproducibility).

    Returns
    -------
    trade : dict or None
        If the order conditions are met, returns a trade record with keys:
          - trade_id, order_id, desk_id, symbol, side, qty_exec, px_exec, fee, ts_exec.
        Otherwise, returns None.
    """
    order_type = order.get("order_type", "MKT").upper()
    side = order.get("side", "BUY").upper()
    qty = order.get("qty", 0)
    filled = False
    trade_price = mid_price

    if order_type == "MKT":
        # For market orders, fill immediately with small random slippage.
        slippage = rng.normal(SLIPPAGE_MEAN, SLIPPAGE_STD)
        trade_price = mid_price * (1 + slippage)
        filled = True
    elif order_type == "LMT":
        limit_px = order.get("limit_px")
        if limit_px is None:
            # If no limit provided, treat as market order.
            slippage = rng.normal(SLIPPAGE_MEAN, SLIPPAGE_STD)
            trade_price = mid_price * (1 + slippage)
            filled = True
        elif side == "BUY":
            if limit_px >= mid_price:
                trade_price = mid_price  # Fill at mid price.
                filled = True
        elif side == "SELL":
            if limit_px <= mid_price:
                trade_price = mid_price
                filled = True

    if not filled:
        return None

    # Calculate fee: per share commission with a minimum fee.
    fee = max(COMMISSION_PER_SHARE * qty, MIN_COMMISSION)

    trade = {
        "trade_id": str(uuid.UUID(int=(int(rng.integers(0, 1 << 64, dtype=np.uint64)) << 64)
                                      | int(rng.integers(0, 1 << 64, dtype=np.uint64)))),

        "order_id": order.get("order_id"),
        "desk_id": order.get("desk_id"),
        "symbol": order.get("symbol"),
        "side": side,
        "qty_exec": qty,
        "px_exec": trade_price,
        "fee": fee,
        "ts_exec": order.get("ts_created", datetime.now(timezone.utc).isoformat()),
    }
    return trade


def fill_orders(orders: List[Dict[str, Any]], current_prices: Dict[str, float], seed: int | None = None) -> List[Dict[str, Any]]:
    """
    Process a list of orders with the current mid prices for their symbols.
    
    Parameters
    ----------
    orders : list of dict
        A list of order dictionaries.
    current_prices : dict
        Mapping of symbol → current mid price.
    seed : int or None
        RNG seed to ensure deterministic behavior.
    
    Returns
    -------
    trades : list of dict
        A list of trade records (only for orders that meet fill conditions).
    """
    rng = np.random.default_rng(seed)
    trades: List[Dict[str, Any]] = []
    for order in orders:
        symbol = order.get("symbol")
        if symbol not in current_prices:
            continue  # Skip orders for which there is no price.
        mid_price = current_prices[symbol]
        trade = fill_order(order, mid_price, rng)
        if trade is not None:
            trades.append(trade)
    return trades
