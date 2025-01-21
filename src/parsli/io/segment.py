from __future__ import annotations

from pathlib import Path

import h5py
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData

from parsli.utils import earth


class VtkSegmentReader(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(
            self,
            nInputPorts=0,
            nOutputPorts=1,
            outputType="vtkPolyData",
        )
        self._file_name = None
        self._proj_spherical = True

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

    def RequestData(self, _request, _inInfo, outInfo):
        if self._file_name is None or not self._file_name.exists():
            return 1

        # Read file and generate mesh
        output = self.GetOutputData(outInfo, 0)
        vtk_points = vtkPoints()
        vtk_points.SetDataTypeToDouble()
        vtk_lines = vtkCellArray()
        vtk_mesh = vtkPolyData()
        vtk_mesh.points = vtk_points
        vtk_mesh.lines = vtk_lines

        # Projection selection
        insert_pt = earth.insert_spherical if self.spherical else earth.insert_euclidian

        with h5py.File(self._file_name, "r") as hdf:
            h5_ds = hdf["segment"]
            data_size = h5_ds.shape

            # making a line for now (should move to 4 once quad)
            vtk_points.Allocate(data_size[0] * 2)
            vtk_lines.Allocate(data_size[0] * 3)

            for row in h5_ds:
                id0 = insert_pt(vtk_points, row[0], row[1], 0)
                id1 = insert_pt(vtk_points, row[2], row[3], 0)
                vtk_lines.InsertNextCell(2)
                vtk_lines.InsertCellPoint(id0)
                vtk_lines.InsertCellPoint(id1)

        output.ShallowCopy(vtk_mesh)
        return 1
