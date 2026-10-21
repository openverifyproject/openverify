"""A clean release checkout must fetch the pinned historical Golden commit."""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import run_frozen_golden  # noqa: E402


@pytest.mark.parametrize("present", [False, True])
def test_pinned_baseline_is_available_from_clean_checkout(present, tmp_path, monkeypatch):
    calls = []
    baseline = run_frozen_golden.BASELINE

    def run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0 if present else 1)

    monkeypatch.setattr(run_frozen_golden.subprocess, "run", run)
    monkeypatch.setattr(
        run_frozen_golden.subprocess,
        "check_output",
        lambda *args, **kwargs: baseline + "\n",
    )
    run_frozen_golden.ensure_baseline_available(tmp_path, baseline)
    assert calls[0] == ["git", "cat-file", "-e", f"{baseline}^{{commit}}"]
    assert (["git", "fetch", "--no-tags", "origin", baseline] in calls) is not present


def test_pinned_baseline_rejects_unexpected_commit(tmp_path, monkeypatch):
    monkeypatch.setattr(
        run_frozen_golden.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0),
    )
    monkeypatch.setattr(
        run_frozen_golden.subprocess,
        "check_output",
        lambda *args, **kwargs: "0" * 40 + "\n",
    )
    with pytest.raises(RuntimeError, match="pinned SHA"):
        run_frozen_golden.ensure_baseline_available(tmp_path)
