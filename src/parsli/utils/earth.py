from __future__ import annotations

import math

EARTH_RADIUS = 6371.0


def normalize(xyz):
    norm = math.sqrt(xyz[0] * xyz[0] + xyz[1] * xyz[1] + xyz[2] * xyz[2])
    return (
        xyz[0] / norm,
        xyz[1] / norm,
        xyz[2] / norm,
    )


def dot(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def left_direction(longitude):
    longitude = math.pi * longitude / 180
    return (
        math.sin(longitude),
        -math.cos(longitude),
        0,
    )


def right_direction(longitude):
    longitude = math.pi * longitude / 180
    return (
        -math.sin(longitude),
        math.cos(longitude),
        0,
    )


def to_normal(location, direction):
    xyz = normalize(location)
    axis = normalize(direction)
    tmp_axis = dot(xyz, axis)
    return dot(tmp_axis, xyz)


def to_spherical(longitude, latitude, depth):
    longitude = math.pi * longitude / 180
    latitude = math.pi * latitude / 180
    h = EARTH_RADIUS - depth
    return (
        h * math.cos(longitude) * math.cos(latitude),
        h * math.sin(longitude) * math.cos(latitude),
        h * math.sin(latitude),
    )


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


def interpolate(a_longitude, a_latitude, b_longitude, b_latitude, distance):
    a_xyz = (
        EARTH_RADIUS * math.cos(a_longitude) * math.cos(a_latitude),
        EARTH_RADIUS * math.sin(a_longitude) * math.cos(a_latitude),
        EARTH_RADIUS * math.sin(a_latitude),
    )
    b_xyz = (
        EARTH_RADIUS * math.cos(b_longitude) * math.cos(b_latitude),
        EARTH_RADIUS * math.sin(b_longitude) * math.cos(b_latitude),
        EARTH_RADIUS * math.sin(b_latitude),
    )
    ab_xyz = (b_xyz[0] - a_xyz[0], b_xyz[1] - a_xyz[1], b_xyz[2] - a_xyz[2])
    ab_dist = math.sqrt(
        ab_xyz[0] * ab_xyz[0] + ab_xyz[1] * ab_xyz[1] + ab_xyz[2] * ab_xyz[2]
    )
    ratio = distance / ab_dist
    return (
        ratio * (b_longitude - a_longitude) + a_longitude,
        ratio * (b_latitude - a_latitude) + a_latitude,
    )
