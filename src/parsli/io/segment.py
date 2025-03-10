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
    length_km = locking_depth / np.tan(np.deg2rad(-1.0 * dip))

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

    def __init__(self):
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
        self._field_names = []
        self._time_index = 0
        self._n_times = -1
        self._vertical_scale = 1

    @property
    def field_names(self):
        if self.number_of_timesteps > 1:
            return self._field_names
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

        self._n_times = -1
        self._time_index = 0
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
    def time_index(self):
        return self._time_index

    @time_index.setter
    def time_index(self, v):
        if v == self._time_index:
            return

        if v == 0 or v < self.number_of_timesteps:
            self._time_index = v
            self.Modified()

    @property
    def number_of_timesteps(self):
        if self._n_times < 0:
            with h5py.File(self._file_name, "r") as hdf:
                if "segments" in hdf:
                    segments = hdf["segments"]
                    self._field_names = list(segments.keys())
                    for field in segments:
                        n_times = len(segments[field].keys())
                        if n_times > self._n_times:
                            self._n_times = int(n_times)
                else:
                    self._n_times = 1

        return self._n_times

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
            cell = QuadCell()
            h5_ds = hdf["segment"]
            data_size = h5_ds.shape

            # extract time dependent fields
            hdf_field_arrays = None
            if "segments" in hdf:
                hdf_field_arrays = {}
                segments = hdf["segments"]
                time_field_key = f"{self._time_index:012}"
                for field in segments:
                    hdf_field_arrays[field] = segments[field][time_field_key]

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

            for row_idx, row in enumerate(h5_ds):
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
                            cell.locking_depth * self._vertical_scale,
                        )
                    )
                    vtk_polys.InsertCellPoint(
                        insert_pt(
                            vtk_points,
                            cell.point_b.lon,
                            cell.point_b.lat,
                            cell.locking_depth * self._vertical_scale,
                        )
                    )
                    vtk_polys.InsertCellPoint(
                        insert_pt(vtk_points, cell.end.lon, cell.end.lat, 0)
                    )

                    # Add fields values
                    if hdf_field_arrays is None:
                        for k, v in fields:
                            vtk_field_arrays[k].InsertNextTuple1(v)
                    else:
                        for k, v in hdf_field_arrays.items():
                            vtk_field_arrays[k].InsertNextTuple1(v[row_idx])

        output.ShallowCopy(vtk_mesh)
        return 1
