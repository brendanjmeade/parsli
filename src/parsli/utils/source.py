from __future__ import annotations

import math

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
        self._n_gridline_per_degree = 1
        self._show_grid_lines = True

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
    def grid_lines(self):
        return self._show_grid_lines

    @grid_lines.setter
    def grid_lines(self, value):
        if self._show_grid_lines != value:
            self._show_grid_lines = value
            self.Modified()

    @property
    def grid_lines_per_degree(self):
        return self._show_grid_lines

    @grid_lines_per_degree.setter
    def grid_lines_per_degree(self, value):
        if self._n_gridline_per_degree != value:
            self._n_gridline_per_degree = value
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
    def depth(self):
        return self._depth

    @depth.setter
    def depth(self, new_depth):
        if self._depth != new_depth:
            self._depth = new_depth
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

            if self.grid_lines:
                if self.grid_lines_per_degree < 0:
                    # 1 line per n degree
                    nb_points = n_lon_pts * 4 + n_lat_pts * 4
                    nb_lines = (1 + n_lon_pts) * 4 + (1 + n_lat_pts) * 4 + 8

                    modulo = abs(self._n_gridline_per_degree)

                    # vertical lines
                    lon = math.floor(self.longitude_bnds[0])
                    while lon < self.longitude_bnds[1]:
                        if lon < self.longitude_bnds[0]:
                            lon += 1
                            continue

                        if lon % modulo != 0:
                            lon += 1
                            continue

                        nb_points += n_lat_pts
                        nb_lines += 1 + n_lat_pts
                        lon += modulo

                    # horizontal lines
                    lat = math.floor(self._latitude_bnd[0])
                    while lat < self._latitude_bnd[1]:
                        if lat < self._latitude_bnd[0]:
                            lat += 1
                            continue

                        if lat % modulo != 0:
                            lat += 1
                            continue

                        nb_points += n_lon_pts
                        nb_lines += 1 + n_lon_pts
                        lat += modulo

                    vtk_points.Allocate(nb_points)
                    nb_lines.Allocate(nb_lines)
                else:
                    # n lines per 1 degree
                    n_vlines = int(delta_lon * self.grid_lines_per_degree)
                    n_hlines = int(delta_lat * self.grid_lines_per_degree)
                    vtk_points.Allocate(
                        n_lon_pts * 4  # bbox horizontal lines pts
                        + n_lat_pts * 4  # bbox vertical lines pts
                        + n_lon_pts * n_hlines  # grid horizontal pts
                        + n_lat_pts * n_vlines  # grid vertical pts
                    )
                    vtk_lines.Allocate(
                        (1 + n_lon_pts) * 4  # horizontal bbox lines
                        + (1 + n_lat_pts) * 4  # vertical bbox lines
                        + 8  # depth lines
                        + n_vlines * n_lat_pts  # vertical grid lines
                        + n_hlines * n_lon_pts  # horizontal grid lines
                    )

            else:
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

            # Generate depth lines
            next_layer_offset = 2 * n_lon_pts + 2 * n_lat_pts
            steps = [0, n_lon_pts, n_lat_pts, n_lon_pts]
            offset = 0
            for step in steps:
                offset += step
                vtk_lines.InsertNextCell(2)
                vtk_lines.InsertCellPoint(offset)
                vtk_lines.InsertCellPoint(offset + next_layer_offset)

            # Generate grid lines
            if self.grid_lines:
                if self._n_gridline_per_degree < 0:
                    # number of degree between lines
                    modulo = abs(self._n_gridline_per_degree)

                    # vertical lines
                    lon = math.floor(self.longitude_bnds[0])
                    while lon < self.longitude_bnds[1]:
                        if lon < self.longitude_bnds[0]:
                            lon += 1
                            continue

                        if lon % modulo != 0:
                            lon += 1
                            continue

                        vtk_lines.InsertNextCell(n_lat_pts)
                        for lat_idx in range(n_lat_pts):
                            lat = self._latitude_bnd[0] + lat_idx * delta_lat / (
                                n_lat_pts - 1
                            )
                            vtk_lines.InsertCellPoint(
                                insert_pt(vtk_points, lon, lat, self._depth)
                            )

                        lon += modulo

                    # horizontal lines
                    lat = math.floor(self._latitude_bnd[0])
                    while lat < self._latitude_bnd[1]:
                        if lat < self._latitude_bnd[0]:
                            lat += 1
                            continue

                        if lat % modulo != 0:
                            lat += 1
                            continue

                        vtk_lines.InsertNextCell(n_lon_pts)
                        for lon_idx in range(n_lon_pts):
                            lon = self._longitude_bnd[0] + lon_idx * delta_lon / (
                                n_lon_pts - 1
                            )
                            vtk_lines.InsertCellPoint(
                                insert_pt(vtk_points, lon, lat, self._depth)
                            )

                        lat += modulo
                else:
                    # vertical lines
                    step = 1 / self._n_gridline_per_degree
                    lon = math.floor(self.longitude_bnds[0])
                    while lon < self.longitude_bnds[1]:
                        if lon < self.longitude_bnds[0]:
                            lon += step
                            continue

                        vtk_lines.InsertNextCell(n_lat_pts)
                        for lat_idx in range(n_lat_pts):
                            lat = self._latitude_bnd[0] + lat_idx * delta_lat / (
                                n_lat_pts - 1
                            )
                            vtk_lines.InsertCellPoint(
                                insert_pt(vtk_points, lon, lat, self._depth)
                            )

                        lon += step

                    # horizontal lines
                    step = 1 / self._n_gridline_per_degree
                    lat = math.floor(self._latitude_bnd[0])
                    while lat < self._latitude_bnd[1]:
                        if lat < self._latitude_bnd[0]:
                            lat += step
                            continue

                        vtk_lines.InsertNextCell(n_lon_pts)
                        for lon_idx in range(n_lon_pts):
                            lon = self._longitude_bnd[0] + lon_idx * delta_lon / (
                                n_lon_pts - 1
                            )
                            vtk_lines.InsertCellPoint(
                                insert_pt(vtk_points, lon, lat, self._depth)
                            )

                        lat += step

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
