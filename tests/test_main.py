import os
import importlib
import pytest

MODULE = "sim_broker.main"


def teardown_function():
    importlib.invalidate_caches()


def test_get_producer_requires_broker(monkeypatch):
    # Remove the env so get_producer() errors
    monkeypatch.delenv("REDPANDA_BROKER", raising=False)
    import sim_broker.main as m

    with pytest.raises(EnvironmentError):
        m.get_producer()


def test_get_producer_returns_dummy(monkeypatch):
    # Arrange: Set both env vars
    monkeypatch.setenv("REDPANDA_BROKER", "localhost:9092")
    monkeypatch.setenv("HEARTBEAT_TOPIC", "hb_topic")

    # Dummy producer to capture calls
    sent = []

    class DummyProducer:
        def __init__(self, **kwargs):
            pass

        def send(self, topic, event):
            sent.append((topic, event))

        def flush(self):
            pass

    # Patch KafkaProducer so get_producer() returns our dummy
    monkeypatch.setenv("REDPANDA_BROKER", "dummy:9092")
    monkeypatch.setenv("HEARTBEAT_TOPIC", "hb_topic")
    monkeypatch.setattr("sim_broker.main.KafkaProducer", lambda **kw: DummyProducer())

    import sim_broker.main as m

    prod = m.get_producer()
    # Send a fake event
    prod.send(os.environ["HEARTBEAT_TOPIC"], {"foo": "bar"})
    assert sent == [("hb_topic", {"foo": "bar"})]
