"""Reference-only deterministic identity; NOT portable canonical hashing."""

import hashlib

from openverify.model import VerificationDefinition
from openverify.serialization import serialize


def fingerprint(definition: VerificationDefinition) -> str:
    """Return local-sha256; exact bytes are SDK-local, not normative."""
    return "local-sha256:" + hashlib.sha256(serialize(definition).encode("utf-8")).hexdigest()
