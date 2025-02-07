from __future__ import annotations

import argparse
from pathlib import Path

from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import (
    vtkCellArray,
    vtkPolyData,
)
from vtkmodules.vtkIOXML import vtkXMLPolyDataWriter

from parsli.utils import earth


def to_polydata(input_file: Path, use_spherical_proj):
    vtk_points = vtkPoints()
    vtk_lines = vtkCellArray()
    dataset = vtkPolyData(points=vtk_points, lines=vtk_lines)
    insert = earth.insert_spherical if use_spherical_proj else earth.insert_euclidian

    with input_file.open() as txt_file:
        line = txt_file.readline()
        while line:
            if "segment" in line:
                n_points = int(line.split("points")[1])
                vtk_lines.InsertNextCell(n_points)
                for _ in range(n_points):
                    line = txt_file.readline()
                    lat, lon = map(float, line.split())
                    vtk_lines.InsertCellPoint(insert(vtk_points, lon, lat, 0))
            else:
                print("Don't know what to do with line:", line)  # noqa: T201

            line = txt_file.readline()

    return dataset


def write_file(input_file, use_spherical_proj):
    projection = "spherical" if use_spherical_proj else "euclidean"
    output_name = str(input_file.parent / f"{input_file.stem}-{projection}.vtp")

    writer = vtkXMLPolyDataWriter()
    writer.file_name = output_name
    writer.input_data = to_polydata(input_file, use_spherical_proj)
    writer.SetCompressorTypeToZLib()
    writer.SetDataModeToBinary()
    writer.SetCompressionLevel(6)
    writer.Write()


def main():
    parser = argparse.ArgumentParser(
        prog="parsli.tools.wdb",
        description="Parsli conversion tool to generate vtp files from coastline text file",
    )
    (
        parser.add_argument(
            "--input", help="Path to the wdb file to convert", required=True
        ),
    )
    parser.add_argument(
        "-s", "--spherical", help="Project lat/lon on sphere", action="store_true"
    )
    args, _ = parser.parse_known_args()
    input_file = Path(args.input).resolve()
    if not input_file.exists():
        print(f"Invalid input path: {input_file}")  # noqa: T201
        return

    use_spherical_proj = args.spherical
    if input_file.is_dir:
        for f in input_file.glob("*.txt"):
            write_file(f, use_spherical_proj)
    elif input_file.is_file:
        write_file(input_file, use_spherical_proj)
    else:
        print("Invalid input type")  # noqa: T201


if __name__ == "__main__":
    main()
