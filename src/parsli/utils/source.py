from __future__ import annotations

from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import vtkPoints, vtkTypeFloat32Array
from vtkmodules.vtkCommonDataModel import (
    vtkCellArray,
    vtkPlanes,
    vtkPolyData,
)

from parsli.utils import earth


class VtkLatLonBound(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(
            self,
            nInputPorts=0,
            nOutputPorts=1,
            outputType="vtkPolyData",
        )
        self._file_name = None
        self._proj_spherical = True
        self._longitude_bnd = [0, 360]
        self._latitude_bnd = [-90, 90]
        self._sampling_per_degree = 5
        self._depth = 100
        self._cut_planes = vtkPlanes()
        self._cut_planes_origin = vtkPoints()
        self._cut_planes_normal = vtkTypeFloat32Array()
        self._cut_planes_normal.SetNumberOfComponents(3)
        self._cut_planes.SetPoints(self._cut_planes_origin)
        self._cut_planes.SetNormals(self._cut_planes_normal)

    @property
    def cut_planes(self):
        return self._cut_planes

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
        return self._longitude_bnd

    @longitude_bnds.setter
    def longitude_bnds(self, lon_bnd):
        if self._longitude_bnd != lon_bnd:
            self._longitude_bnd = lon_bnd
            self.Modified()

    @property
    def latitude_bnds(self):
        return self._latitude_bnd

    @latitude_bnds.setter
    def latitude_bnds(self, lat_bnd):
        if self._latitude_bnd != lat_bnd:
            self._latitude_bnd = lat_bnd
            self.Modified()

    @property
    def valid(self):
        if self._proj_spherical:
            delta_lon = self._longitude_bnd[1] - self._longitude_bnd[0]
            delta_lat = self._latitude_bnd[1] - self._latitude_bnd[0]
            if delta_lon > 180 or delta_lat > 90:
                return False

        return True

    def RequestData(self, _request, _inInfo, outInfo):
        self.cut_planes.Modified()

        if not self.valid:
            self._cut_planes_origin.SetNumberOfPoints(0)
            self._cut_planes_normal.SetNumberOfTuples(0)
            return 1

        # Read file and generate mesh
        output = self.GetOutputData(outInfo, 0)

        vtk_mesh = vtkPolyData()
        vtk_points = vtkPoints()
        vtk_points.SetDataTypeToDouble()
        vtk_mesh.points = vtk_points
        vtk_lines = vtkCellArray()
        vtk_mesh.lines = vtk_lines

        # Projection selection
        if self.spherical:
            insert_pt = earth.insert_spherical
            delta_lon = self._longitude_bnd[1] - self._longitude_bnd[0]
            delta_lat = self._latitude_bnd[1] - self._latitude_bnd[0]
            mid_lon = 0.5 * (self._longitude_bnd[0] + self._longitude_bnd[1])

            n_lon_pts = int(delta_lon * self._sampling_per_degree + 0.5)
            n_lat_pts = int(delta_lat * self._sampling_per_degree + 0.5)

            vtk_points.Allocate(n_lon_pts * 4 + n_lat_pts * 4)
            vtk_lines.Allocate((1 + n_lon_pts) * 4 + (1 + n_lat_pts) * 4 + 8)

            # Compute cut planes
            self._cut_planes_origin.SetNumberOfPoints(4)
            self._cut_planes_normal.SetNumberOfTuples(4)

            # top
            lon = mid_lon
            lat = self._latitude_bnd[1]
            center = earth.to_spherical(lon, lat, 0)
            normal = earth.to_normal(center, (0, 0, -1))
            self._cut_planes_origin.SetPoint(0, center)
            self._cut_planes_normal.SetTuple3(0, *normal)

            # bottom
            lon = mid_lon
            lat = self._latitude_bnd[0]
            center = earth.to_spherical(lon, lat, 0)
            self._cut_planes_origin.SetPoint(1, center)
            self._cut_planes_normal.SetTuple3(1, *earth.to_normal(center, (0, 0, 1)))

            # right
            self._cut_planes_origin.SetPoint(2, 0, 0, 0)
            self._cut_planes_normal.SetTuple3(
                2, *earth.left_direction(self._longitude_bnd[1])
            )

            # left
            self._cut_planes_origin.SetPoint(3, 0, 0, 0)
            self._cut_planes_normal.SetTuple3(
                3, *earth.right_direction(self._longitude_bnd[0])
            )

            # Generate points and cells
            for depth in [self._depth, 0]:
                # Start bottom left
                lon = self._longitude_bnd[0]
                lat = self._latitude_bnd[0]

                # Bottom
                vtk_lines.InsertNextCell(n_lon_pts)
                for lon_idx in range(n_lon_pts):
                    lon = self._longitude_bnd[0] + lon_idx * delta_lon / (n_lon_pts - 1)
                    vtk_lines.InsertCellPoint(insert_pt(vtk_points, lon, lat, depth))

                # Right
                vtk_lines.InsertNextCell(n_lat_pts)
                for lat_idx in range(n_lat_pts):
                    lat = self._latitude_bnd[0] + lat_idx * delta_lat / (n_lat_pts - 1)
                    vtk_lines.InsertCellPoint(insert_pt(vtk_points, lon, lat, depth))

                # Top
                vtk_lines.InsertNextCell(n_lon_pts)
                for lon_idx in range(n_lon_pts)[::-1]:
                    lon = self._longitude_bnd[0] + lon_idx * delta_lon / (n_lon_pts - 1)
                    vtk_lines.InsertCellPoint(insert_pt(vtk_points, lon, lat, depth))

                # Left
                vtk_lines.InsertNextCell(n_lat_pts)
                for lat_idx in range(n_lat_pts)[::-1]:
                    lat = self._latitude_bnd[0] + lat_idx * delta_lat / (n_lat_pts - 1)
                    vtk_lines.InsertCellPoint(insert_pt(vtk_points, lon, lat, depth))

            # Generate vertical lines
            next_layer_offset = 2 * n_lon_pts + 2 * n_lat_pts
            steps = [0, n_lon_pts, n_lat_pts, n_lon_pts]
            offset = 0
            for step in steps:
                offset += step
                vtk_lines.InsertNextCell(2)
                vtk_lines.InsertCellPoint(offset)
                vtk_lines.InsertCellPoint(offset + next_layer_offset)

        else:
            vtk_points.Allocate(8)

            vtk_points.InsertNextPoint(
                self._longitude_bnd[0], self._latitude_bnd[0], -self._depth
            )
            vtk_points.InsertNextPoint(
                self._longitude_bnd[1], self._latitude_bnd[0], -self._depth
            )
            vtk_points.InsertNextPoint(
                self._longitude_bnd[1], self._latitude_bnd[1], -self._depth
            )
            vtk_points.InsertNextPoint(
                self._longitude_bnd[0], self._latitude_bnd[1], -self._depth
            )

            vtk_points.InsertNextPoint(self._longitude_bnd[0], self._latitude_bnd[0], 0)
            vtk_points.InsertNextPoint(self._longitude_bnd[1], self._latitude_bnd[0], 0)
            vtk_points.InsertNextPoint(self._longitude_bnd[1], self._latitude_bnd[1], 0)
            vtk_points.InsertNextPoint(self._longitude_bnd[0], self._latitude_bnd[1], 0)

            vtk_lines.Allocate(5 + 5 + 2 * 4)

            # Bottom
            vtk_lines.InsertNextCell(5)
            vtk_lines.InsertCellPoint(0)
            vtk_lines.InsertCellPoint(1)
            vtk_lines.InsertCellPoint(2)
            vtk_lines.InsertCellPoint(3)
            vtk_lines.InsertCellPoint(0)

            # Top
            vtk_lines.InsertNextCell(5)
            vtk_lines.InsertCellPoint(4)
            vtk_lines.InsertCellPoint(5)
            vtk_lines.InsertCellPoint(6)
            vtk_lines.InsertCellPoint(7)
            vtk_lines.InsertCellPoint(4)

            # Edges
            vtk_lines.InsertNextCell(2)
            vtk_lines.InsertCellPoint(0)
            vtk_lines.InsertCellPoint(4)

            vtk_lines.InsertNextCell(2)
            vtk_lines.InsertCellPoint(1)
            vtk_lines.InsertCellPoint(5)

            vtk_lines.InsertNextCell(2)
            vtk_lines.InsertCellPoint(2)
            vtk_lines.InsertCellPoint(6)

            vtk_lines.InsertNextCell(2)
            vtk_lines.InsertCellPoint(3)
            vtk_lines.InsertCellPoint(7)

            # Compute cut planes
            self._cut_planes_origin.SetNumberOfPoints(4)
            self._cut_planes_normal.SetNumberOfTuples(4)

            # top
            self._cut_planes_origin.SetPoint(
                0, self._longitude_bnd[1], self._latitude_bnd[1], 0
            )
            self._cut_planes_normal.SetTuple3(0, 0, -1, 0)
            # bottom
            self._cut_planes_origin.SetPoint(
                1, self._longitude_bnd[0], self._latitude_bnd[0], 0
            )
            self._cut_planes_normal.SetTuple3(1, 0, 1, 0)
            # left
            self._cut_planes_origin.SetPoint(
                2, self._longitude_bnd[0], self._latitude_bnd[0], 0
            )
            self._cut_planes_normal.SetTuple3(2, 1, 0, 0)
            # right
            self._cut_planes_origin.SetPoint(
                3, self._longitude_bnd[1], self._latitude_bnd[1], 0
            )
            self._cut_planes_normal.SetTuple3(3, -1, 0, 0)

        output.ShallowCopy(vtk_mesh)
        return 1
