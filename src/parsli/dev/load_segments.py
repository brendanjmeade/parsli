# Let start by reading the line segments
from __future__ import annotations

from parsli.io.sample import SAMPLE_DATASET
from parsli.io.segment import VtkSegmentReader

reader = VtkSegmentReader()
reader.file_name = SAMPLE_DATASET

output = reader()
print(output)
