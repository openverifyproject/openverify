"""Fail-closed source selection, without Git processes during tests."""
from pathlib import Path
import hashlib
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "conformance/golden-v0.3.1"


def git_head(root):
    git = root / ".git"
    if git.is_file():
        git = (root / git.read_text(encoding="utf-8").strip().split(": ", 1)[1]).resolve()
    head = (git / "HEAD").read_text(encoding="utf-8").strip()
    if not head.startswith("ref: "):
        return head
    ref = head[5:]
    common = git
    if (git / "commondir").exists():
        common = (git / (git / "commondir").read_text().strip()).resolve()
    for directory in (git, common):
        if (directory / ref).is_file():
            return (directory / ref).read_text().strip()
    for line in (common / "packed-refs").read_text().splitlines():
        if line.endswith(" " + ref):
            return line.split()[0]
    raise RuntimeError("Cannot identify implementation Git commit")


def configure():
    metadata = json.loads((BASE / "metadata.json").read_text(encoding="utf-8"))
    explicit = os.environ.get("GOLDEN_IMPLEMENTATION")
    selected = Path(explicit).resolve() if explicit else ROOT
    source = selected / "src"
    if not (source / "openverify/relay/api.py").is_file():
        raise RuntimeError("GOLDEN_IMPLEMENTATION must be a production checkout with src/openverify/relay")
    # An earlier Golden conftest or site startup must never pick a different SUT.
    loaded = sys.modules.get("openverify")
    if loaded is not None and not Path(loaded.__file__).resolve().is_relative_to(source):
        raise RuntimeError("OpenVerify already imported from another checkout; run these suites independently")
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(source))
    hashes = {p.relative_to(selected).as_posix(): hashlib.sha256(p.read_text(encoding="utf-8").encode()).hexdigest()
              for p in sorted((source / "openverify").rglob("*.py"))}
    pinned = json.loads((BASE / "implementation-sources.json").read_text(encoding="utf-8"))
    if not explicit and hashes != pinned:
        raise RuntimeError("Default production source differs from pinned implementation; set GOLDEN_IMPLEMENTATION explicitly")
    head = git_head(selected)
    return {"implementation_location": str(selected), "checkout_commit": head,
            "production_commit": head if explicit else metadata["production_commit"],
            "production_source_sha256": hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest(),
            "explicit_target": bool(explicit)}
