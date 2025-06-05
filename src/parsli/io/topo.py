from __future__ import annotations

import logging
from pathlib import Path

import h5py
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkStructuredGrid
from vtkmodules.vtkCommonExecutionModel import vtkStreamingDemandDrivenPipeline

from parsli.utils import earth

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


class TopoReader(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(
            self,
            nInputPorts=0,
            nOutputPorts=1,
            outputType="vtkStructuredGrid",
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

    def _expand_bounds(self, longitude, latitude, depth):
        self._longitude_bnd[0] = min(longitude, self._longitude_bnd[0])
        self._longitude_bnd[1] = max(longitude, self._longitude_bnd[1])

        self._latitude_bnd[0] = min(latitude, self._latitude_bnd[0])
        self._latitude_bnd[1] = max(latitude, self._latitude_bnd[1])

        self._max_depth = max(depth, self._max_depth)

    def RequestInformation(self, request, inInfo, outInfo):
        with h5py.File(self._file_name, "r") as hdf:
            dims = hdf["topo/elevation"].shape
            whole_extent = (0, dims[1] - 1, 0, dims[0] - 1, 0, 0)
            outInfo.GetInformationObject(0).Set(
                vtkStreamingDemandDrivenPipeline.WHOLE_EXTENT(),
                *whole_extent,
            )

        return 1

    def RequestData(self, _request, _inInfo, outInfo):
        if self._file_name is None or not self._file_name.exists():
            return 1

        # Reset bounds
        self._longitude_bnd = [360, 0]
        self._latitude_bnd = [90, -90]
        self._max_depth = 0

        # Read file and generate mesh
        output = self.GetOutputData(outInfo, 0)
        topo = vtkStructuredGrid()

        # Projection selection
        insert_pt = earth.insert_spherical if self.spherical else earth.insert_euclidian

        with h5py.File(self._file_name, "r") as hdf:
            lon_lat_bounds = hdf["topo/bounds"]
            elevations = hdf["topo/elevation"]
            dims = elevations.shape

            # Extract data bounds
            min_lon = lon_lat_bounds[0][0]
            max_lon = lon_lat_bounds[0][1]
            delta_lon = max_lon - min_lon
            min_lat = lon_lat_bounds[1][0]
            max_lat = lon_lat_bounds[1][1]
            delta_lat = max_lat - min_lat

            # Generate points
            vtk_points = vtkPoints()
            vtk_points.SetDataTypeToDouble()
            vtk_points.Allocate(dims[0] * dims[1])

            for j in range(dims[0]):
                lat = min_lat + delta_lat * j / (dims[0] - 1)
                for i in range(dims[1]):
                    lon = min_lon + delta_lon * i / (dims[1] - 1)
                    elevation = elevations[j][i]

                    self._expand_bounds(lon, lat, elevation * self._vertical_scale)
                    insert_pt(vtk_points, lon, lat, elevation * self._vertical_scale)

            topo.SetDimensions(dims[1], dims[0], 1)
            topo.points = vtk_points

        output.ShallowCopy(topo)
        return 1
