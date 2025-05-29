# ---------------------------------------------------------
# python -m parsli.tools.topo
# ---------------------------------------------------------
from __future__ import annotations

import h5py
import numpy as np

output_file = "./data/topo.hdf5"

min_lon = 231.8
max_lon = 238.2
min_lat = 39.4
max_lat = 51.1

lon_step_size = 1 / 3
lat_step_size = 1 / 3

# Each river will be a sinusoidal along the grids.
# Set parameters for each sinusoidal.
river_params = [
    # amplitude, period, slope, and intercept
    (0.1, 1, 1, 0),
    (0.2, 0.5, 0.5, -0.5),
    (0.3, 2, 0, 0.5),
]
num_river_coords = 100
river_step_size = 1 / (num_river_coords - 1)

# Compute the elevation grid
lon_vals = np.arange(min_lon, max_lon + lon_step_size, lon_step_size)
lat_vals = np.arange(min_lat, max_lat + lat_step_size, lat_step_size)
lon_grid, lat_grid = np.meshgrid(lon_vals, lat_vals)
elevation_grid = 15 * (np.cos(lon_grid * 2) + np.sin(lat_grid * 2))

# Compute the rivers
rivers = {}
river_idx = 1
for A, B, m, c in river_params:
    # Compute the river's fractional coordinates
    x_coords = np.arange(0, 1 + river_step_size, river_step_size)
    y_coords = A * np.sin(B * x_coords) + m * x_coords + c

    # Remove any out-of-bounds coordinates
    to_keep = ~((y_coords < 0) | (y_coords > 1))
    x_coords = x_coords[to_keep]
    y_coords = y_coords[to_keep]

    # Convert these to latitude and longitude
    # (0, 0) is at (min_lon, max_lat), and (1, 1) is at (max_lon, min_lat)
    lon_coords = x_coords * (max_lon - min_lon) + min_lon
    lat_coords = (1 - y_coords) * (max_lat - min_lat) + min_lat
    elevation = 15 * (np.cos(lon_coords * 2) + np.sin(lat_coords * 2))
    rivers[river_idx] = np.vstack((lon_coords, lat_coords, elevation)).T
    river_idx += 1

# Now write everything to the HDF5 file
with h5py.File(output_file, "w") as f:
    f["topo/bounds"] = [[min_lon, max_lon], [min_lat, max_lat]]
    f["topo/elevation"] = elevation_grid
    for idx, data in rivers.items():
        f[f"lines/river{idx}"] = data
