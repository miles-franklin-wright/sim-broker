"""
sim_broker.cli
==============
Run a single simulated trading day from the command line.

Usage
-----
python -m sim_broker.cli 2025-01-02 --seed 42 --out out --overwrite
"""

from __future__ import annotations

import argparse
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
from rich import box
from rich.console import Console
from rich.table import Table

from sim_broker.market.price_generator import generate_prices
from sim_broker.clients.segments import create_clients
from sim_broker.execution.order_generator import create_orders
from sim_broker.execution.fill_engine import fill_orders
from sim_broker.desks.us_desk import USDesk
from sim_broker.output.writer import write_day
from sim_broker.config import cfg

console = Console()


def generate_day(
    trade_date: str,
    seed: int | None,
    out_root: Path,
    overwrite: bool = False,
    n_symbols: int = 100,
):
    rng = np.random.default_rng(seed)

    # 1. Generate price paths (use first row as mid prices for order gen/fill).
    symbols = [f"S{i:03d}" for i in range(n_symbols)]
    prices_df = generate_prices(trade_date, symbols, seed=seed)
    mid_prices = prices_df.iloc[0].to_dict()

    # 2. Create clients.
    cfg = {
        "long_only": {"count": 1500, "mean_orders_per_day": 0.3, "size_mu": 11, "size_sigma": 0.4},
        "active": {"count": 500, "mean_orders_per_day": 2.0, "size_mu": 9, "size_sigma": 0.6},
    }
    clients_df = create_clients(cfg, seed=seed)

    # 3. Generate orders.
    orders = create_orders(clients_df, symbols, trade_date, seed=seed)

    # 4. Fill orders into trades.
    trades = fill_orders(orders, mid_prices, seed=seed)

    # 5. Feed trades into desk.
    desk = USDesk()
    for tr in trades:
        desk.process_trade(tr)
    snapshot = desk.snapshot(mark_prices=mid_prices)

    # Convert positions and pnl snapshots to DataFrames for writer.
    positions_df = pd.DataFrame(
        [
            {
                "symbol": sym,
                "shares": pos.shares,
                "cost_basis": pos.cost_basis,
                "realised_pnl": pos.realised_pnl,
            }
            for sym, pos in desk.positions.items()
        ]
    )
    pnl_df = pd.DataFrame([snapshot])

    # 6. Persist to disk.
    day_dir = write_day(
        out_root,
        trade_date,
        orders,
        trades,
        positions_df,
        pnl_df,
        seed=seed,
        overwrite=overwrite,
    )

    # 7. Pretty summary.
    table = Table(title=f"Sim-Broker {trade_date}", box=box.SIMPLE_HEAD)
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row("Orders", str(len(orders)))
    table.add_row("Trades", str(len(trades)))
    table.add_row("Realised P&L", f"{snapshot['realised_pnl']:.2f}")
    table.add_row("Unreal P&L", f"{snapshot['unreal_pnl']:.2f}")
    table.add_row("Cash", f"{snapshot['cash']:.2f}")
    table.add_row("Output dir", str(day_dir))
    console.print(table)

    return day_dir  # handy for tests


def _parse_args():
    p = argparse.ArgumentParser(description="Run one simulated trading day.")
    p.add_argument("trade_date", help="YYYY-MM-DD")
    p.add_argument("--seed", type=int, default=None, help="RNG seed")
    p.add_argument("--out", default=cfg.paths.output_dir, help=f"root output directory (default {cfg.paths.output_dir})")
    p.add_argument("--overwrite", action="store_true", help="overwrite existing day folder")
    return p.parse_args()


def main():
    args = _parse_args()
    # Basic date validation
    try:
        datetime.strptime(args.trade_date, "%Y-%m-%d")
    except ValueError as e:
        console.print(f"[red]Invalid date: {e}[/red]")
        raise SystemExit(1)

    generate_day(
        trade_date=args.trade_date,
        seed=args.seed,
        out_root=Path(args.out),
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()
