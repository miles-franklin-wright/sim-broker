from bytewax.dataflow import Dataflow

# adjust this import path to wherever you placed it
from bytewax.flows.silver_heartbeat_flow import build_flow


def test_build_silver_flow_returns_dataflow():
    """
    Ensure that build_flow() returns a Bytewax Dataflow object.
    """
    flow = build_flow()
    assert isinstance(
        flow, Dataflow
    ), "silver_heartbeat_flow.build_flow() must return a Dataflow"


def test_custom_env_vars(monkeypatch):
    # Point to a dummy path so FileSource doesn’t error in build_flow()
    monkeypatch.setenv("BRONZE_PATH", "does/not/exist.jsonl")
    monkeypatch.setenv("SILVER_PATH", "some/other/path")
    monkeypatch.setenv("BATCH_INTERVAL_SECONDS", "42")

    flow = build_flow()
    assert isinstance(flow, Dataflow)
    # Optionally, introspect flow.name or other metadata if you expose it
