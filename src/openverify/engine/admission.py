"""Reference-local sampling; no cross-engine bucket identity is claimed."""

import hashlib
import json

from openverify.errors import ProtocolError
from openverify.fingerprint import fingerprint
from openverify.model import Admission, VerificationDefinition
from openverify.validation import validate_definition


def admit(definition: VerificationDefinition, opportunity_id: str) -> Admission:
    validate_definition(definition)
    if type(opportunity_id) is not str or not opportunity_id:
        raise ProtocolError("ADMISSION_POLICY", "A nonempty opportunity identity is required")
    policy = definition.execution_policy.admission
    if policy.strategy == "ALWAYS":
        return Admission(outcome="RUN", reason="ALWAYS")
    if policy.strategy != "PROBABILITY" or policy.probability is None:
        raise ProtocolError("POLICY_UNSUPPORTED", "Admission strategy is not implemented")
    # Length-separated JSON avoids ambiguity between identity tuples. Reference-only.
    identity = json.dumps(
        [fingerprint(definition), definition.subject.id, opportunity_id], separators=(",", ":")
    )
    bucket = int.from_bytes(hashlib.sha256(identity.encode()).digest(), "big") / (1 << 256)
    run = policy.probability == 1 or policy.probability != 0 and bucket < policy.probability
    return Admission(
        outcome="RUN" if run else "SKIP",
        reason=f"PROBABILITY p={policy.probability}; reference bucket={bucket}",
    )
