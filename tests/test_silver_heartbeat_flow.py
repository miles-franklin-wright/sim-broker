from bytewax.dataflow import Dataflow
from flows.silver_heartbeat_flow import build_flow


def test_build_flow_returns_dataflow():
    """
    Ensure that build_flow() returns a Bytewax Dataflow object.
    """
    flow = build_flow()
    assert isinstance(flow, Dataflow), "build_flow() should return a Dataflow"


def test_env_vars_create_dirs(monkeypatch, tmp_path):
    """
    Setting custom BRONZE_PATH and SILVER_FILE should create their parent directories
    and still return a Dataflow without errors.
    """
    # Define custom paths
    custom_bronze = tmp_path / "bronze" / "heartbeat.jsonl"
    custom_silver = tmp_path / "silver" / "heartbeat.parquet"

    # Override environment variables
    monkeypatch.setenv("BRONZE_PATH", str(custom_bronze))
    monkeypatch.setenv("SILVER_FILE", str(custom_silver))

    # Calling build_flow should not error and should create the dirs
    flow = build_flow()
    assert isinstance(flow, Dataflow)

    # Parent directories must exist
    assert (
        custom_bronze.parent.exists()
    ), f"Bronze parent dir missing: {custom_bronze.parent}"
    assert (
        custom_silver.parent.exists()
    ), f"Silver parent dir missing: {custom_silver.parent}"
