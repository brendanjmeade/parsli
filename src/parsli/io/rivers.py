from __future__ import annotations

import logging
from pathlib import Path

import h5py
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import (
    vtkCellArray,
    vtkPartitionedDataSet,
    vtkPolyData,
)

from parsli.utils import earth

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


class RiverReader(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(
            self,
            nInputPorts=0,
            nOutputPorts=1,
            outputType="vtkPartitionedDataSet",
        )
        self._file_name = None
        self._proj_spherical = True
        self._longitude_bnd = [0, 360]
        self._latitude_bnd = [-90, 90]
        self._vertical_scale = 1
        self._max_depth = 0

    @property
    def file_name(self):
        return self._file_name

    @file_name.setter
    def file_name(self, path):
        self._file_name = Path(path)
        if not self._file_name.exists():
            msg = f"Invalid file path: {self._file_name.resolve()}"
            raise ValueError(msg)

        self.Modified()

    @property
    def spherical(self):
        return self._proj_spherical

    @spherical.setter
    def spherical(self, value):
        if self._proj_spherical != value:
            self._proj_spherical = value
            self.Modified()

    @property
    def vertical_scale(self):
        return self._vertical_scale

    @vertical_scale.setter
    def vertical_scale(self, value):
        if self._vertical_scale != value:
            self._vertical_scale = value
            self.Modified()

    @property
    def maximum_depth(self):
        return self._max_depth

    @property
    def longitude_bounds(self):
        return self._longitude_bnd

    @property
    def latitude_bounds(self):
        return self._latitude_bnd

    def _expend_bounds(self, longitude, latitude, depth):
        self._longitude_bnd[0] = min(longitude, self._longitude_bnd[0])
        self._longitude_bnd[1] = max(longitude, self._longitude_bnd[1])

        self._latitude_bnd[0] = min(latitude, self._latitude_bnd[0])
        self._latitude_bnd[1] = max(latitude, self._latitude_bnd[1])

        self._max_depth = max(depth, self._max_depth)

    def RequestData(self, _request, _inInfo, outInfo):
        if self._file_name is None or not self._file_name.exists():
            return 1

        # Reset bounds
        self._longitude_bnd = [360, 0]
        self._latitude_bnd = [90, -90]
        self._max_depth = 0

        # Read file and generate mesh
        output = self.GetOutputData(outInfo, 0)
        all_rivers = vtkPartitionedDataSet()

        # Projection selection
        insert_pt = earth.insert_spherical if self.spherical else earth.insert_euclidian

        with h5py.File(self._file_name, "r") as hdf:
            rivers = hdf["lines"]
            n_rivers = len(rivers)
            all_rivers.SetNumberOfPartitions(n_rivers)
            for idx, name in enumerate(rivers):
                river = rivers[name]
                vtk_mesh = vtkPolyData()
                all_rivers.SetPartition(idx, vtk_mesh)

                # Process known names first
                # - coordinates
                shape = river.shape

                # Generate points
                vtk_points = vtkPoints()
                vtk_points.SetDataTypeToDouble()
                vtk_points.Allocate(shape[0])
                vtk_mesh.points = vtk_points
                vtk_lines = vtkCellArray()
                vtk_mesh.lines = vtk_lines
                vtk_lines.InsertNextCell(shape[0])

                for i in range(shape[0]):
                    lon = river[i][0]
                    lat = river[i][1]
                    elevation = river[i][2]
                    self._expend_bounds(lon, lat, elevation * self._vertical_scale)
                    insert_pt(vtk_points, lon, lat, elevation * self._vertical_scale)
                    vtk_lines.InsertCellPoint(i)

        output.ShallowCopy(all_rivers)
        return 1
