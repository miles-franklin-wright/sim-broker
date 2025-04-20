"""
sim_broker.config
-----------------
Load YAML → pydantic model → immutable singleton `cfg`.

Output directory precedence
1. CLI flag  --out /path   (handled in cli.py)
2. ENV       SIM_BROKER_OUTDIR=/path
3. YAML      paths.output_dir
"""

from __future__ import annotations
from pathlib import Path
import os
import yaml
from pydantic import BaseModel, Field


# ------------------ pydantic models ------------------ #
class Paths(BaseModel, frozen=True):
    output_dir: str = "out"


class RandomCfg(BaseModel, frozen=True):
    seed: int | None = None


class MarketCfg(BaseModel, frozen=True):
    n_symbols: int = 100
    start_price: float = 100.0
    volatility: float = 0.18


class SegmentCfg(BaseModel, frozen=True):
    count: int
    mean_orders_per_day: float
    size_mu: float
    size_sigma: float


class ClientsCfg(BaseModel, frozen=True):
    long_only: SegmentCfg
    active: SegmentCfg


class ConfigModel(BaseModel, frozen=True):
    random: RandomCfg = Field(default_factory=RandomCfg)
    paths: Paths = Field(default_factory=Paths)
    market: MarketCfg = Field(default_factory=MarketCfg)
    clients: ClientsCfg


# ------------------ load & merge ------------------ #
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "base.yml"


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


_raw = _load_yaml(CONFIG_PATH)

# ENV override (does not modify YAML on disk)
env_outdir = os.getenv("SIM_BROKER_OUTDIR")
if env_outdir:
    _raw.setdefault("paths", {})["output_dir"] = env_outdir

cfg: ConfigModel = ConfigModel(**_raw)
