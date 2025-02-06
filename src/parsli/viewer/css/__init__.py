from __future__ import annotations

from pathlib import Path

serve_path = str(Path(__file__).with_name("serve").resolve())
serve = {"__css": serve_path}
styles = ["__css/core.css"]
