from __future__ import annotations

import math
from pathlib import Path

import h5py
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData

from parsli.utils import earth


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
    __slots__ = ("end", "normal", "point_a", "point_b", "start")

    def __init__(self):
        self.start = EarthLocation()
        self.point_a = EarthLocation()
        self.point_b = EarthLocation()
        self.end = EarthLocation()
        self.normal = EarthLocation()

    def update(self, row):
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

        dip = row[14]
        locking_depth = row[4]

        if dip == 90 or locking_depth <= 0:
            self.point_a <<= self.start
            self.point_b <<= self.end
            return False

        self.normal.lon = self.end.lat - self.start.lat
        self.normal.lat = -(self.end.lon - self.start.lon)

        dip_to_left = dip < 90
        if dip_to_left:
            self.normal.flip()

        dip_base = (90 - dip) if dip_to_left else (dip - 90)
        dip_angle = dip_base * (math.pi / 180)
        proj_dist = math.fabs(math.tan(dip_angle) * locking_depth)

        self.point_a.interpolate_from(
            self.start.lon,
            self.start.lat,
            self.start.lon + self.normal.lon,
            self.start.lat + self.normal.lat,
            proj_dist,
        )

        self.point_b.interpolate_from(
            self.end.lon,
            self.end.lat,
            self.end.lon + self.normal.lon,
            self.end.lat + self.normal.lat,
            proj_dist,
        )

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

        # Projection selection
        insert_pt = earth.insert_spherical if self.spherical else earth.insert_euclidian

        with h5py.File(self._file_name, "r") as hdf:
            h5_ds = hdf["segment"]
            data_size = h5_ds.shape

            # making a line for now (should move to 4 once quad)
            vtk_points.Allocate(data_size[0] * 2)
            vtk_polys.Allocate(data_size[0] * 5)

            cell = QuadCell()
            for row in h5_ds:
                if cell.update(row):
                    vtk_polys.InsertNextCell(4)
                    vtk_polys.InsertCellPoint(
                        insert_pt(vtk_points, cell.start.lon, cell.start.lat, 0)
                    )
                    vtk_polys.InsertCellPoint(
                        insert_pt(
                            vtk_points, cell.start.lon, cell.start.lat, 100
                        )  # go inside 100m
                    )
                    vtk_polys.InsertCellPoint(
                        insert_pt(
                            vtk_points, cell.end.lon, cell.end.lat, 100
                        )  # go inside 100m
                    )
                    vtk_polys.InsertCellPoint(
                        insert_pt(vtk_points, cell.end.lon, cell.end.lat, 0)
                    )

        output.ShallowCopy(vtk_mesh)
        return 1
