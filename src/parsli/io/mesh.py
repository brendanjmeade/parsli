from __future__ import annotations

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


class VtkMeshReader(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(
            self,
            nInputPorts=0,
            nOutputPorts=1,
            outputType="vtkPartitionedDataSet",
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

    @property
    def available_fields(self):
        if self._file_name is None or not self._file_name.exists():
            return []

        result = set()
        with h5py.File(self._file_name, "r") as hdf:
            meshes = hdf["meshes"]
            for mesh in meshes:
                for name in meshes[mesh]:
                    if name in {"mesh_name", "coordinates", "verts"}:
                        continue
                    result.add(name)

        return list(result)

    def RequestData(self, _request, _inInfo, outInfo):
        if self._file_name is None or not self._file_name.exists():
            return 1

        # Read file and generate mesh
        output = self.GetOutputData(outInfo, 0)
        all_meshes = vtkPartitionedDataSet()

        # Projection selection
        insert_pt = earth.insert_spherical if self.spherical else earth.insert_euclidian

        with h5py.File(self._file_name, "r") as hdf:
            meshes = hdf["meshes"]
            all_meshes.SetNumberOfPartitions(len(meshes))
            for idx, mesh in enumerate(meshes):
                vtk_mesh = vtkPolyData()
                all_meshes.SetPartition(idx, vtk_mesh)

                # Process known names first
                # - coordinates
                vtk_points = vtkPoints()
                vtk_points.SetDataTypeToDouble()
                vtk_mesh.points = vtk_points

                hdf_ds = meshes[mesh]["coordinates"]
                n_points = hdf_ds.shape[0]
                vtk_points.Allocate(n_points)

                for xyz in hdf_ds:
                    insert_pt(vtk_points, xyz[0], xyz[1], xyz[2])

                # - verts
                vtk_polys = vtkCellArray()
                vtk_mesh.polys = vtk_polys

                hdf_ds = meshes[mesh]["verts"]
                n_cells = hdf_ds.shape[0]
                vtk_polys.Allocate(4 * n_cells)
                assert hdf_ds.shape[1] == 3, "only triangles"

                for cell in hdf_ds:
                    vtk_polys.InsertNextCell(3)
                    vtk_polys.InsertCellPoint(cell[0])
                    vtk_polys.InsertCellPoint(cell[1])
                    vtk_polys.InsertCellPoint(cell[2])

                for name in meshes[mesh]:
                    if name in {"mesh_name", "coordinates", "verts"}:
                        continue

                    # This is a field
                    # print(f"Field {name}: {meshes[mesh][name][:].ravel().shape}")
                    vtk_mesh.cell_data[name] = meshes[mesh][name][:].ravel()

        output.ShallowCopy(all_meshes)
        return 1
