"""
Package capturing all the readers available for parsing and processing data.
"""

from .coast import VtkCoastLineSource
from .mesh import VtkMeshReader
from .rivers import RiverReader
from .segment import VtkSegmentReader
from .topo import TopoReader

__all__ = [
    "RiverReader",
    "TopoReader",
    "VtkCoastLineSource",
    "VtkMeshReader",
    "VtkSegmentReader",
]
