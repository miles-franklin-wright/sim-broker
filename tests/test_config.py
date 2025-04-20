import importlib
import pytest
from pydantic import ValidationError

import sim_broker.config as sbcfg


def test_defaults():
    assert sbcfg.cfg.random.seed == 42
    out_dir = sbcfg.cfg.paths.output_dir
    assert isinstance(out_dir, str)
    assert out_dir != ""


def test_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("SIM_BROKER_OUTDIR", str(tmp_path))
    importlib.reload(sbcfg)  # re‑import with env var
    assert sbcfg.cfg.paths.output_dir == str(tmp_path)


def test_immutable():
    with pytest.raises(ValidationError):
        sbcfg.cfg.market.n_symbols = 200


def test_validation_error(tmp_path):
    bad_yaml = tmp_path / "bad.yml"
    bad_yaml.write_text("random:\n  seed: abc\n")  # seed must be int
    from sim_broker.config import ConfigModel, _load_yaml

    with pytest.raises(ValidationError):
        ConfigModel(**_load_yaml(bad_yaml))
