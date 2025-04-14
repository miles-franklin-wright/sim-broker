"""
Run the full generate_day() twice with the same seed
and assert byte‑identical JSONL/CSV outputs.
"""

import filecmp, tempfile, shutil, hashlib, json, csv
from pathlib import Path

from sim_broker.cli import generate_day

def _dir_hash(folder: Path) -> str:
    """Return a single SHA256 over all files in the folder (sorted by name)."""
    h = hashlib.sha256()
    for p in sorted(folder.rglob("*")):
        if p.is_file() and p.name != "meta.json":
            h.update(p.name.encode())
            h.update(p.read_bytes())
    return h.hexdigest()

def test_pipeline_determinism(tmp_path):
    day = "2025-02-01"
    d1 = generate_day(day, seed=999, out_root=tmp_path / "run1", overwrite=False, n_symbols=20)
    d2 = generate_day(day, seed=999, out_root=tmp_path / "run2", overwrite=False, n_symbols=20)

    # Compare folder contents byte‑for‑byte
    assert _dir_hash(d1) == _dir_hash(d2), "Outputs differ with same seed"
