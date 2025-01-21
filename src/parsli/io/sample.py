from __future__ import annotations

from pathlib import Path

BASE_DIRECTORY = Path(__file__).parent.parent.parent.parent
INPUT = "data/model_0000000878.hdf5"

SAMPLE_DATASET = (BASE_DIRECTORY / INPUT).resolve()
