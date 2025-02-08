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

    def __repr__(self):
        return f"Longitude: {self.lon}, Latitude: {self.lat}"


FIELD_COLS = {
    "strike_slip": 68,
    "dip_slip": 69,
    "tensile_slip": 70,
}
FIELD_NAMES = list(FIELD_COLS.keys())


class QuadCell:
    __slots__ = (
        "dip",
        "end",
        "latitude_bnds",
        "locking_depth",
        "longitude_bnds",
        "normal",
        "point_a",
        "point_b",
        "start",
    )

    def __init__(self, longitude_bnds, latitude_bnds):
        self.longitude_bnds = longitude_bnds
        self.latitude_bnds = latitude_bnds
        self.start = EarthLocation()
        self.point_a = EarthLocation()
        self.point_b = EarthLocation()
        self.end = EarthLocation()
        self.normal = EarthLocation()

    def update(self, row):
        if row[34]:
            # skip cell if column 34 is true
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

        if (
            self.start.lon < self.longitude_bnds[0]
            or self.end.lon > self.longitude_bnds[1]
            or self.start.lat < self.latitude_bnds[0]
            or self.end.lat > self.latitude_bnds[1]
        ):
            # print(f"skip {self.start} {self.end}")
            return False

        self.dip = row[4]
        self.locking_depth = row[14]

        lon3, lat3, lon4, lat4 = get_segment_bottom_lon_lat(
            self.start.lon,
            self.start.lat,
            self.end.lon,
            self.end.lat,
            self.locking_depth,
            self.dip,
        )

        self.point_a.lon = lon3
        self.point_a.lat = lat3
        self.point_b.lon = lon4
        self.point_b.lat = lat4

        return [(k, row[FIELD_COLS[k]]) for k in FIELD_NAMES]


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
        self._longitude_bnds = [0, 360]
        self._latitude_bnds = [-90, 90]

    @property
    def field_names(self):
        return FIELD_NAMES

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
    def longitude_bnds(self):
        return self._longitude_bnds

    @longitude_bnds.setter
    def longitude_bnds(self, value):
        if self._longitude_bnds != value:
            self._longitude_bnds = value
            self.Modified()

    @property
    def latitude_bnds(self):
        return self._latitude_bnds

    @latitude_bnds.setter
    def latitude_bnds(self, value):
        if self._latitude_bnds != value:
            self._latitude_bnds = value
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

        # Projection selection
        insert_pt = earth.insert_spherical if self.spherical else earth.insert_euclidian

        with h5py.File(self._file_name, "r") as hdf:
            cell = QuadCell(self.longitude_bnds, self.latitude_bnds)
            h5_ds = hdf["segment"]
            data_size = h5_ds.shape

            # making a line for now (should move to 4 once quad)
            vtk_points.Allocate(data_size[0] * 2)
            vtk_polys.Allocate(data_size[0] * 5)

            # Create fields and attach to mesh
            vtk_field_arrays = {}
            for name in FIELD_NAMES:
                array = vtkFloatArray()
                array.SetName(name)
                array.Allocate(data_size[0])
                vtk_mesh.cell_data.AddArray(array)
                vtk_field_arrays[name] = array

            for row in h5_ds:
                if fields := cell.update(row):
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

                    # Add fields values
                    for k, v in fields:
                        vtk_field_arrays[k].InsertNextTuple1(v)

        output.ShallowCopy(vtk_mesh)
        return 1
