# bytewax/flows/heartbeat_flow.py

import os
from functools import partial

from bytewax.dataflow import Dataflow
from bytewax.testing import run_main  # helper that actually executes the flow in tests


def build_flow() -> Dataflow:
    # 1) Required env var check
    broker = os.getenv("REDPANDA_BROKER")
    if not broker:
        raise EnvironmentError("REDPANDA_BROKER must be set")

    # Optional, but you’ll probably want to validate these too:
    topic = os.getenv("HEARTBEAT_TOPIC")
    if not topic:
        raise EnvironmentError("HEARTBEAT_TOPIC must be set")

    bronze_path = os.getenv("BRONZE_PATH")
    if not bronze_path:
        raise EnvironmentError("BRONZE_PATH must be set")

    # 2) Construct your Dataflow
    flow = Dataflow("heartbeat_flow")
    # … your actual logic here:
    # e.g. flow.input(), flow.map(...), flow.capture(...), etc.

    # 3) Attach a `.run()` method so tests (and you) can just do flow.run()
    flow.run = partial(run_main, flow)

    return flow
