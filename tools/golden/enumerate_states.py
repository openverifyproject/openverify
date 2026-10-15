"""Independent finite Result and policy enumeration, never invokes the SUT."""
import json
from collections import Counter
from tools.golden.oracle import result_axes, result_error


def counts():
    c = Counter("invalid" if result_error(r) else "valid" for r in result_axes())
    return {"axes": ["disposition", "execution_outcome", "applicability", "determination", "verdict"], "includes_omission_and_explicit_null": True, "total": sum(c.values()), **c}


if __name__ == "__main__":
    print(json.dumps(counts(), indent=2))
