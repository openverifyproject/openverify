"""Canonical-master replacement-port witnesses; no extra runtime graph."""
from copy import deepcopy
import json

from tests.golden_v031.target import BASE
from tests.golden_v031.runtime_adapter import prepare, invoke
from tests.golden_v031.record_oracle import audit
from tools.golden_v02.compare import equal


async def execute(case, definition, report):
    from openverify.errors import ProtocolError
    from openverify.relay.adapters.binder import DeterministicBinder
    from openverify.relay.adapters.local import LocalDriver
    from openverify.relay.adapters.memory import MemoryStore
    stimuli = deepcopy(next(c for c in json.loads((BASE / "scenarios.json").read_text(encoding="utf-8"))
                            if c["id"] == "master.normal"))
    s, relay, calls, observer = prepare(stimuli, definition)
    identity = case["id"].removeprefix("master.port.")
    failure = RuntimeError("scripted replacement port failure")
    touched = []

    class Catalog:
        def providers(self):
            touched.append("catalog")
            if identity == "catalog_failure":
                raise failure
            return None

    class Binder:
        def bind(self, requirement, providers, explicit=None):
            touched.append("binder")
            if identity == "binder_failure":
                raise failure
            if identity == "binder_invalid":
                return None
            return DeterministicBinder().bind(requirement, providers, explicit)

    class Driver:
        async def execute(self, provider, request, timeout, emit):
            touched.append("driver")
            return await LocalDriver().execute(provider, request, timeout, emit)

    class Store:
        def __init__(self):
            self.memory = MemoryStore()

        def put(self, record):
            touched.append("store")
            if identity == "store_failure":
                raise failure
            self.memory.put(record)

        def get(self, run_id):
            return self.memory.get(run_id)

    class Observer:
        def observe(self, event):
            touched.append("observer")
            if identity == "observer_failure":
                raise failure
            observer.observe(event)

    if identity.startswith("catalog_"):
        relay.catalog = Catalog()
    elif identity.startswith("binder_"):
        relay.binder = Binder()
    elif identity == "driver_replace":
        relay.driver = Driver()
    elif identity.startswith("store_"):
        relay.store = Store()
    elif identity.startswith("observer_"):
        relay.observer = Observer()
    try:
        run = await invoke(relay, definition, s["inputs"], report)
    except ProtocolError as exc:
        equal(case["error_code"], str(exc.code))
        assert not calls, "Failed catalog/binding boundary invoked providers"
        assert touched
        return
    except RuntimeError as exc:
        assert identity == "store_failure" and exc is failure
        assert touched.count("store") == 1
        return
    assert "error_code" not in case and identity != "store_failure"
    record = json.loads(run.to_json())
    audit(record, s, calls)
    assert touched
    if identity == "store_replace":
        assert touched.count("store") == 1
        equal(record["run_id"], relay.store.get(record["run_id"]).run_id)
