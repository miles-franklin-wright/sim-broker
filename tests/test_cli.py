import subprocess
import sys
import json

from sim_broker.cli import generate_day


def test_generate_day_function(tmp_path):
    # Call the internal function (faster than spawning a subprocess)
    day_dir = generate_day(
        trade_date="2025-01-02",
        seed=123,
        out_root=tmp_path,
        overwrite=False,
        n_symbols=10,  # small for test speed
    )
    # Check meta.json exists and seed is correct
    meta = json.loads((day_dir / "meta.json").read_text())
    assert meta["seed"] == 123
    assert meta["rows"]["orders"] > 0
    assert meta["rows"]["trades"] > 0


def test_cli_subprocess(tmp_path):
    # Spawn the CLI as a subprocess to ensure entry‑point works
    cmd = [
        sys.executable,
        "-m",
        "sim_broker.cli",
        "2025-01-03",
        "--seed",
        "7",
        "--out",
        str(tmp_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    # Confirm output dir created
    assert (tmp_path / "2025-01-03").exists()
