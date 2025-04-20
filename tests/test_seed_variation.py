from sim_broker.cli import generate_day
from pathlib import Path
import hashlib


def _file_hash(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_different_seeds_produce_different_orders(tmp_path):
    day = "2025-02-02"
    d1 = generate_day(
        day, seed=1, out_root=tmp_path / "s1", overwrite=False, n_symbols=15
    )
    d2 = generate_day(
        day, seed=2, out_root=tmp_path / "s2", overwrite=False, n_symbols=15
    )

    orders1 = _file_hash(d1 / "orders.jsonl")
    orders2 = _file_hash(d2 / "orders.jsonl")
    assert orders1 != orders2, "Changing seed should change order stream"
