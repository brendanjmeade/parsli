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
        self._longitude_bnd = [0, 360]
        self._latitude_bnd = [-90, 90]

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

    @property
    def longitude_bounds(self):
        return self._longitude_bnd

    @property
    def latitude_bounds(self):
        return self._latitude_bnd

    def _expend_bounds(self, longitude, latitude):
        self._longitude_bnd[0] = min(longitude, self._longitude_bnd[0])
        self._longitude_bnd[1] = max(longitude, self._longitude_bnd[1])

        self._latitude_bnd[0] = min(latitude, self._latitude_bnd[0])
        self._latitude_bnd[1] = max(latitude, self._latitude_bnd[1])

    def RequestData(self, _request, _inInfo, outInfo):
        if self._file_name is None or not self._file_name.exists():
            return 1

        # Reset bounds
        self._longitude_bnd = [360, 0]
        self._latitude_bnd = [90, -90]

        # Read file and generate mesh
        output = self.GetOutputData(outInfo, 0)
        all_meshes = vtkPartitionedDataSet()

        # Projection selection
        insert_pt = earth.insert_spherical if self.spherical else earth.insert_euclidian

        with h5py.File(self._file_name, "r") as hdf:
            meshes = hdf["meshes"]
            n_meshes = len(meshes)
            logger.debug("n_meshes=%s", n_meshes)
            all_meshes.SetNumberOfPartitions(n_meshes)
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
                    self._expend_bounds(xyz[0], xyz[1])
                    insert_pt(vtk_points, xyz[0], xyz[1], -xyz[2])

                # - verts
                vtk_polys = vtkCellArray()
                vtk_mesh.polys = vtk_polys

                hdf_ds = meshes[mesh]["verts"]
                n_cells = hdf_ds.shape[0]
                vtk_polys.Allocate(4 * n_cells)
                assert hdf_ds.shape[1] == 3, "only triangles"

                logger.debug(" %s. mesh %s cells", idx, n_cells)

                for cell in hdf_ds:
                    vtk_polys.InsertNextCell(3)
                    vtk_polys.InsertCellPoint(cell[0])
                    vtk_polys.InsertCellPoint(cell[1])
                    vtk_polys.InsertCellPoint(cell[2])

                for name in meshes[mesh]:
                    if name in {"mesh_name", "coordinates", "verts"}:
                        continue

                    # This is a field
                    logger.debug("Field %s: %s", name, meshes[mesh][name].shape)
                    vtk_mesh.cell_data[name] = meshes[mesh][name][:].ravel()

        output.ShallowCopy(all_meshes)
        return 1
