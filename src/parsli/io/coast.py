from __future__ import annotations

from pathlib import Path

from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonDataModel import (
    vtkPartitionedDataSet,
)
from vtkmodules.vtkIOXML import vtkXMLPolyDataReader

BASE_DIRECTORY = Path(__file__).parent.with_name("assets").resolve()
RESIONS = [f.name.split("-")[0] for f in BASE_DIRECTORY.glob("*-spherical.vtp")]


def region_to_full_name(name, use_spherical):
    ext = "-cil-spherical.vtp" if use_spherical else "-cil-euclidean.vtp"
    output = BASE_DIRECTORY / f"{name}{ext}"
    # print(f"{name} => {output}")
    return str(output.resolve())


class VtkCoastLineSource(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(
            self,
            nInputPorts=0,
            nOutputPorts=1,
            outputType="vtkPartitionedDataSet",
        )
        self._proj_spherical = True
        self._active_regions = set()

    @property
    def spherical(self):
        return self._proj_spherical

    @spherical.setter
    def spherical(self, value):
        if self._proj_spherical != value:
            self._proj_spherical = value
            self.Modified()

    @property
    def available_regions(self):
        return RESIONS

    @property
    def active_regions(self):
        return self._active_regions

    @active_regions.setter
    def active_regions(self, value):
        new_region_set = set(value) & set(RESIONS)
        if self._active_regions != new_region_set:
            self._active_regions = new_region_set
            self.Modified()

    def RequestData(self, _request, _inInfo, outInfo):
        # Read file and generate mesh
        output = self.GetOutputData(outInfo, 0)
        all_meshes = vtkPartitionedDataSet()
        all_meshes.SetNumberOfPartitions(len(self._active_regions))

        # reader
        reader = vtkXMLPolyDataReader()

        # Projection selection
        for idx, name in enumerate(self._active_regions):
            reader.file_name = region_to_full_name(name, self.spherical)
            all_meshes.SetPartition(idx, reader())

        output.ShallowCopy(all_meshes)
        return 1
