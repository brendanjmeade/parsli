from __future__ import annotations

from pathlib import Path

import h5py
import numpy as np
from pyproj import Geod
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import vtkFloatArray, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData

from parsli.utils import earth

APPROXIMATE_SCALING = 111.0


def km_to_degrees_lon(km, lat):
    return km / (APPROXIMATE_SCALING * np.cos(np.deg2rad(lat)))


def km_to_degrees_lat(km):
    return km / APPROXIMATE_SCALING


def get_segment_bottom_lon_lat(lon1, lat1, lon2, lat2, locking_depth, dip):
    # Get segment azimuths
    azimuth = Geod(ellps="WGS84").inv(lon1, lat1, lon2, lat2)[0]

    # Get segment length
    length_km = locking_depth / np.tan(np.deg2rad(dip))

    # Get longitude and latitude spans
    delta_lon_km = length_km * np.cos(np.deg2rad(azimuth))
    delta_lat_km = -length_km * np.sin(np.deg2rad(azimuth))

    # Get average latitude
    avg_lat = (lat1 + lat2) / 2.0
    delta_lon = km_to_degrees_lon(delta_lon_km, avg_lat)
    delta_lat = km_to_degrees_lat(delta_lat_km)

    # Calculate approximate longitude and latitudes of lower vertices
    lon3 = lon1 + delta_lon
    lon4 = lon2 + delta_lon
    lat3 = lat1 + delta_lat
    lat4 = lat2 + delta_lat
    return lon3, lat3, lon4, lat4


class EarthLocation:
    __slots__ = ("lat", "lon")

    def __ilshift__(self, other):
        self.lat = other.lat
        self.lon = other.lon

    def flip(self):
        self.lon *= -1
        self.lat *= -1

    def interpolate_from(self, start_lon, start_lat, end_lon, end_lat, distance):
        self.lon, self.lat = earth.interpolate(
            start_lon, start_lat, end_lon, end_lat, distance
        )


class QuadCell:
    __slots__ = ("dip", "end", "locking_depth", "normal", "point_a", "point_b", "start")

    def __init__(self):
        self.start = EarthLocation()
        self.point_a = EarthLocation()
        self.point_b = EarthLocation()
        self.end = EarthLocation()
        self.normal = EarthLocation()

    def update(self, row):
        if row[34]:
            # skip cell is column 34 is true
            return False

        if row[0] >= row[2]:
            self.start.lon = row[0]
            self.start.lat = row[1]
            self.end.lon = row[2]
            self.end.lat = row[3]
        else:
            self.end.lon = row[0]
            self.end.lat = row[1]
            self.start.lon = row[2]
            self.start.lat = row[3]

        self.dip = row[14]
        self.locking_depth = row[4]

        lon3, lat3, lon4, lat4 = get_segment_bottom_lon_lat(
            self.start.lon,
            self.start.lat,
            self.end.lon,
            self.end.lat,
            self.dip,
            self.locking_depth,
        )

        self.point_a.lon = lon3
        self.point_a.lat = lat3
        self.point_b.lon = lon4
        self.point_b.lat = lat4

        return True


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
        vtk_polys = vtkCellArray()
        vtk_mesh = vtkPolyData()
        vtk_mesh.points = vtk_points
        vtk_mesh.polys = vtk_polys

        # Dip field
        vtk_dip = vtkFloatArray()
        vtk_dip.SetName("dip")
        vtk_mesh.cell_data.AddArray(vtk_dip)

        # Locking depth field
        vtk_locking_depth = vtkFloatArray()
        vtk_locking_depth.SetName("Locking depth")
        vtk_mesh.cell_data.AddArray(vtk_locking_depth)

        # Projection selection
        insert_pt = earth.insert_spherical if self.spherical else earth.insert_euclidian

        with h5py.File(self._file_name, "r") as hdf:
            h5_ds = hdf["segment"]
            data_size = h5_ds.shape

            # making a line for now (should move to 4 once quad)
            vtk_points.Allocate(data_size[0] * 2)
            vtk_polys.Allocate(data_size[0] * 5)
            vtk_dip.Allocate(data_size[0])
            vtk_locking_depth.Allocate(data_size[0])

            cell = QuadCell()
            for row in h5_ds:
                if cell.update(row):
                    vtk_polys.InsertNextCell(4)
                    vtk_polys.InsertCellPoint(
                        insert_pt(vtk_points, cell.start.lon, cell.start.lat, 0)
                    )
                    vtk_polys.InsertCellPoint(
                        insert_pt(
                            vtk_points,
                            cell.point_a.lon,
                            cell.point_a.lat,
                            cell.locking_depth,
                        )
                    )
                    vtk_polys.InsertCellPoint(
                        insert_pt(
                            vtk_points,
                            cell.point_b.lon,
                            cell.point_b.lat,
                            cell.locking_depth,
                        )
                    )
                    vtk_polys.InsertCellPoint(
                        insert_pt(vtk_points, cell.end.lon, cell.end.lat, 0)
                    )
                    vtk_dip.InsertNextTuple1(cell.dip)
                    vtk_locking_depth.InsertNextTuple1(cell.locking_depth)

        output.ShallowCopy(vtk_mesh)
        return 1
