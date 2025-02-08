from __future__ import annotations

from pathlib import Path

from trame.app import get_server
from trame.decorators import TrameApp, change
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import vtk as vtkw
from trame.widgets import vtklocal
from trame.widgets import vuetify3 as v3
from vtkmodules.vtkIOParallelXML import vtkXMLPartitionedDataSetWriter

from parsli.io import VtkCoastLineSource, VtkMeshReader, VtkSegmentReader
from parsli.utils import expend_range
from parsli.viewer import css, ui
from parsli.viewer.vtk import SceneManager

DEBUG_WRITE_MESH = False


@TrameApp()
class Viewer:
    def __init__(self, server=None):
        self.server = get_server(server, client_type="vue3")
        self.server.enable_module(css)
        self.server.cli.add_argument(
            "--data", help="Path of hdf5 file to load", required=True
        )
        self.server.cli.add_argument(
            "--wasm", help="Use local rendering", action="store_true"
        )

        # process cli
        args, _ = self.server.cli.parse_known_args()
        data_file = str(Path(args.data).resolve())
        self.local_rendering = args.wasm

        # Setup app
        self.scene_manager = SceneManager(self.server)
        self._build_ui()

        # load segments
        seg_reader = VtkSegmentReader()
        seg_reader.file_name = data_file
        pipeline = self.scene_manager.add_geometry("segment", seg_reader)
        pipeline.get("mapper").SetScalarModeToUseCellFieldData()

        # load meshes
        mesh_reader = VtkMeshReader()
        mesh_reader.file_name = data_file
        pipeline = self.scene_manager.add_geometry_with_contour(
            "meshes", mesh_reader, True
        )
        pipeline.get("mapper").SetScalarModeToUsePointFieldData()
        self.state.fields = mesh_reader.available_fields

        # Coast lines
        self.coast_lines = VtkCoastLineSource()
        self.state.coast_regions = self.coast_lines.available_regions
        self.state.coast_active_regions = []
        pipeline = self.scene_manager.add_geometry("coast", self.coast_lines, True)
        coast_props = pipeline.get("actor").property
        coast_props.line_width = 2
        coast_props.color = (0, 0, 0)

        if DEBUG_WRITE_MESH:
            writer = vtkXMLPartitionedDataSetWriter()
            writer.SetInputData(mesh_reader())
            writer.SetFileName("all_meshes.vtpd")
            writer.Write()

        self.readers = [mesh_reader, seg_reader]

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
        mapper_mesh = pipeline_item.get("mapper")
        mapper_seg = self.scene_manager["segment"].get("mapper")

        if color_by is None:
            mapper_mesh.SetScalarVisibility(0)
            mapper_seg.SetScalarVisibility(0)
            self.ctrl.view_update()
            return

        # Extract data range
        ds = source()

        total_range = None
        for array in ds.cell_data[color_by].Arrays:
            total_range = expend_range(total_range, array.GetRange())

        self.state.color_min = total_range[0]
        self.state.color_max = total_range[1]

    @change("spherical")
    def _on_projection_change(self, spherical, **_):
        for geo_name in ["segment", "meshes", "coast"]:
            pipeline_item = self.scene_manager[geo_name]
            pipeline_item.get("source").spherical = spherical
            actors = pipeline_item.get("actors")

            scale = (1, 1, 1) if spherical else (1, 1, 0.01)
            for actor in actors:
                actor.scale = scale

        self.ctrl.view_reset_camera()

    def reset_to_mesh(self):
        bounds = self.scene_manager["meshes"].get("actor").bounds
        self.scene_manager.reset_camera_to(bounds)
        self.ctrl.view_update(push_camera=True)

    def _build_ui(self):
        self.state.trame__title = "Parsli"
        with VAppLayout(self.server, full_height=True) as layout:
            self.ui = layout

            with v3.VContainer(
                fluid=True, classes="fill-height pa-0 ma-0 position-relative"
            ):
                if self.local_rendering:
                    with vtklocal.LocalView(
                        self.scene_manager.render_window,
                        20,
                    ) as view:
                        view.register_widget(self.scene_manager.widget)
                        self.ctrl.view_update = view.update
                        self.ctrl.view_reset_camera = view.reset_camera
                else:
                    with vtkw.VtkRemoteView(
                        self.scene_manager.render_window,
                        interactive_ratio=2,
                        still_ratio=2,
                    ) as view:
                        self.ctrl.view_update = view.update
                        self.ctrl.view_reset_camera = view.reset_camera

                # Control panel
                ui.ControlPanel(
                    toggle="show_panel",
                    scene_manager=self.scene_manager,
                    reset_camera=self.ctrl.view_reset_camera,
                    reset_to_mesh=self.reset_to_mesh,
                )

                # 3D View controls
                ui.ViewToolbar(
                    reset_camera=self.ctrl.view_reset_camera,
                    reset_to_mesh=self.reset_to_mesh,
                )
