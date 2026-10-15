"""Disposable files stay inside the authorized workspace, including children."""

import os
import tempfile
from pathlib import Path


def configure():
    root = Path(__file__).resolve().parents[2] / ".pytest_cache" / "golden-v02-temp"
    root.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(root)
    os.environ["TMP"] = os.environ["TEMP"] = str(root)


configure()
