import pytest

from openverify.adapters.demo import demo_registry
from openverify.engine import Engine
from openverify.engine.admission import admit
from openverify.errors import ProtocolError
from openverify.model import AdmissionPolicy, Capability
from tests.helpers import context, definition


@pytest.mark.parametrize("p,expected", [(0.0, "SKIP"), (1.0, "RUN")])
def test_boundaries_and_skipped_provenance(p: float, expected: str) -> None:
    d = definition()
    policy = d.execution_policy.model_copy(
        update={"admission": AdmissionPolicy(strategy="PROBABILITY", probability=p)}
    )
    d = d.model_copy(update={"execution_policy": policy})
    assert admit(d, "o").outcome == expected
    run = Engine(demo_registry()).run(d, context(), opportunity_id="o")
    assert run.admission.outcome == expected
    if p == 0:
        assert all(n.result is not None and n.result.disposition == "SKIPPED" for n in run.nodes)


def test_repeatable_sampling_and_always() -> None:
    d = definition()
    assert admit(d, "o").outcome == "RUN"
    d = d.model_copy(
        update={
            "execution_policy": d.execution_policy.model_copy(
                update={"admission": AdmissionPolicy(strategy="PROBABILITY", probability=0.2)}
            )
        }
    )
    first = [admit(d, str(i)) for i in range(200)]
    assert first == [admit(d, str(i)) for i in range(200)]
    assert {a.outcome for a in first} == {"RUN", "SKIP"}
    # Checks deterministic behavior, not a flaky frequency estimate.


@pytest.mark.parametrize("p", [-0.1, 1.1])
def test_invalid_probability(p: float) -> None:
    d = definition()
    d = d.model_copy(
        update={
            "execution_policy": d.execution_policy.model_copy(
                update={"admission": AdmissionPolicy(strategy="PROBABILITY", probability=p)}
            )
        }
    )
    with pytest.raises(ProtocolError, match="PROTOCOL_STRUCTURE"):
        admit(d, "o")


def test_missing_identity_and_unimplemented_policies() -> None:
    d = definition()
    with pytest.raises(ProtocolError, match="ADMISSION_POLICY"):
        admit(d, "")
    d = d.model_copy(
        update={
            "execution_policy": d.execution_policy.model_copy(
                update={"activation": Capability(executor_ref="PERIODIC")}
            )
        }
    )
    with pytest.raises(ProtocolError, match="POLICY_UNSUPPORTED"):
        Engine(demo_registry()).run(d, context(), opportunity_id="o")
