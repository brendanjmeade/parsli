from __future__ import annotations

from pathlib import Path

from trame.app import get_server
from trame.decorators import TrameApp, change
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vtk as vtkw
from trame.widgets import vuetify3 as v3

from parsli.io import VtkMeshReader, VtkSegmentReader
from parsli.viewer.vtk import SceneManager

# from vtkmodules.vtkIOParallelXML import vtkXMLPartitionedDataSetWriter


def expend_range(current_range, new_range):
    if current_range is None:
        return new_range

    return [
        min(current_range[0], new_range[0]),
        max(current_range[1], new_range[1]),
    ]


@TrameApp()
class Viewer:
    def __init__(self, server=None):
        self.server = get_server(server, client_type="vue3")
        self.server.cli.add_argument(
            "--data", help="Path of hdf5 file to load", required=True
        )
        self.scene_manager = SceneManager(self.server)
        self._build_ui()

        # process cli
        args, _ = self.server.cli.parse_known_args()
        data_file = str(Path(args.data).resolve())

        # load segments
        seg_reader = VtkSegmentReader()
        seg_reader.file_name = data_file
        self.scene_manager.add_geometry("segment", seg_reader)

        # load meshes
        mesh_reader = VtkMeshReader()
        mesh_reader.file_name = data_file
        self.state.fields = mesh_reader.available_fields

        # writer = vtkXMLPartitionedDataSetWriter()
        # writer.SetInputData(mesh_reader())
        # writer.SetFileName("all_meshes.vtpd")
        # writer.Write()

        # print(mesh_reader())
        self.scene_manager.add_geometry("meshes", mesh_reader, True)

    @property
    def ctrl(self):
        return self.server.controller

    @property
    def state(self):
        return self.server.state

    @change("color_by")
    def _on_color_by(self, color_by, **_):
        pipeline_item = self.scene_manager["meshes"]
        source = pipeline_item.get("source")
        mapper = pipeline_item.get("mapper")

        if color_by is None:
            mapper.SetScalarVisibility(0)
            self.ctrl.view_update()
            return

        # Extract data range
        ds = source()

        total_range = None
        for array in ds.cell_data[color_by].Arrays:
            total_range = expend_range(total_range, array.GetRange())

        mapper.SelectColorArray(color_by)
        mapper.SetScalarModeToUseCellFieldData()
        mapper.InterpolateScalarsBeforeMappingOn()
        mapper.SetScalarVisibility(1)
        mapper.SetScalarRange(*total_range)

        self.ctrl.view_update()

    def _build_ui(self):
        with SinglePageLayout(self.server, full_height=True) as layout:
            self.ui = layout

            layout.title.set_text("Parsli")
            with layout.icon:
                v3.VIcon("mdi-earth")

            with layout.toolbar as tb:
                tb.density = "compact"
                v3.VSpacer()
                v3.VSelect(
                    v_model=("color_by", None),
                    items=("fields",),
                    density="compact",
                    hide_details=True,
                    variant="outlined",
                    flat=True,
                    style="max-width: 200px;",
                    classes="mr-2",
                )
                v3.VBtn(
                    icon="mdi-crop-free",
                    click=self.ctrl.view_reset_camera,
                )

            with layout.content:
                with v3.VContainer(fluid=True, classes="fill-height pa-0 ma-0"):
                    with vtkw.VtkRemoteView(
                        self.scene_manager.render_window,
                        interactive_ratio=1,
                    ) as view:
                        self.ctrl.view_update = view.update
                        self.ctrl.view_reset_camera = view.reset_camera
