from __future__ import annotations

import math

EARTH_RADIUS = 6371.0


def insert_spherical(vtk_points, longitude, latitude, depth):
    longitude = math.pi * longitude / 180
    latitude = math.pi * latitude / 180
    h = EARTH_RADIUS - depth
    return vtk_points.InsertNextPoint(
        h * math.cos(longitude) * math.cos(latitude),
        h * math.sin(longitude) * math.cos(latitude),
        h * math.sin(latitude),
    )


def insert_euclidian(vtk_point, longitude, latitude, depth):
    return vtk_point.InsertNextPoint(
        longitude,
        latitude,
        depth,
    )
