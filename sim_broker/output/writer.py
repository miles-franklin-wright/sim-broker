"""
sim_broker.output.writer
------------------------
Utility functions to persist a simulated trading day to disk.

Directory layout:
out/
 └─ 2025-01-02/
     ├─ orders.jsonl
     ├─ trades.jsonl
     ├─ positions.csv
     ├─ pnl.csv
     └─ meta.json
"""

from __future__ import annotations
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Union
from datetime import datetime, timezone

import pandas as pd
import sim_broker  # for version string


def _ensure_dir(path: Path, overwrite: bool):
    if path.exists():
        if not overwrite:
            raise FileExistsError(f"{path} already exists (use overwrite=True to replace)")
    else:
        path.mkdir(parents=True, exist_ok=True)


def _write_jsonl(path: Path, records: List[Dict[str, Any]]):
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, separators=(",", ":")) + "\n")


def _write_csv(path: Path, df: pd.DataFrame):
    df.to_csv(path, index=False)


def write_day(
    out_root: Union[str, Path],
    trade_date: str,
    orders: List[Dict[str, Any]],
    trades: List[Dict[str, Any]],
    positions_df: pd.DataFrame,
    pnl_df: pd.DataFrame,
    seed: int | None,
    overwrite: bool = False,
) -> Path:
    """
    Persist all daily outputs under out_root/<trade_date>/.

    Parameters
    ----------
    out_root : str or Path
        Base directory for outputs (e.g., "out/").
    trade_date : str
        Trading date in YYYY-MM-DD format.
    orders, trades : list of dict
        Event streams to write as JSONL.
    positions_df, pnl_df : DataFrame
        Snapshots to write as CSV.
    seed : int or None
        RNG seed used for the simulation (stored in meta.json).
    overwrite : bool
        If True, existing directory will be replaced.

    Returns
    -------
    Path
        Path object pointing to the created day directory.
    """
    day_dir = Path(out_root) / trade_date
    _ensure_dir(day_dir, overwrite)

    _write_jsonl(day_dir / "orders.jsonl", orders)
    _write_jsonl(day_dir / "trades.jsonl", trades)
    _write_csv(day_dir / "positions.csv", positions_df)
    _write_csv(day_dir / "pnl.csv", pnl_df)

    meta = {
        "trade_date": trade_date,
        "rows": {
            "orders": len(orders),
            "trades": len(trades),
            "positions": len(positions_df),
            "pnl": len(pnl_df),
        },
        "seed": seed,
        "sim_broker_version": sim_broker.__version__,
        "written_at": datetime.now(timezone.utc).isoformat(),
    }
    (day_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    return day_dir
