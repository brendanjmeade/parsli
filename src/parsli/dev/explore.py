from __future__ import annotations

from pathlib import Path

import h5py

BASE_DIRECTORY = Path(__file__).parent.parent.parent.parent
INPUT = "data/model_0000000878.hdf5"


def explore_ds():
    data_file = BASE_DIRECTORY / INPUT

    with h5py.File(data_file, "r") as hdf:

        def print_info(name):
            print(name, "=", hdf[name])

        hdf.visit(print_info)

        print("~" * 60)
        print(hdf["earth_radius"][()])
        print("+" * 60)
        # 74 columns
        # lon(0), lat(1), lon(2), lat(3),
        print(hdf["segment"][0,])


if __name__ == "__main__":
    explore_ds()
