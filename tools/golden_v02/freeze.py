"""Seal an authored release once; never computes or changes expectations."""
import hashlib
import json
from datetime import UTC, datetime
from tools.golden_v02.verify_manifest import ROOT, baseline


def freeze():
    base = baseline()
    marker = base / "FROZEN"
    if marker.exists():
        raise SystemExit("release already frozen; create a new revision")
    manifest = json.loads((base / "checksum-manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["files"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    marker.write_text(datetime.now(UTC).isoformat() + "\nGolden 0.2.0: new revision required for corrections.\n", encoding="utf-8", newline="\n")
    manifest["files"][marker.relative_to(ROOT).as_posix()] = hashlib.sha256(marker.read_bytes()).hexdigest()
    (base / "checksum-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("Sealed " + str(base))


if __name__ == "__main__":
    freeze()
