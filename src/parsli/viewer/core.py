from __future__ import annotations

from pathlib import Path

from trame.app import get_server
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vtk as vtkw
from trame.widgets import vuetify3 as v3

from parsli.io.segment import VtkSegmentReader
from parsli.viewer.vtk import SceneManager


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

        # load segments
        seg_reader = VtkSegmentReader()
        seg_reader.file_name = str(Path(args.data).resolve())
        self.scene_manager.add_geometry("segment", seg_reader)

        # load meshes

    @property
    def ctrl(self):
        return self.server.controller

    def _build_ui(self):
        with SinglePageLayout(self.server, full_height=True) as layout:
            self.ui = layout

            layout.title.set_text("Parsli")
            with layout.icon:
                v3.VIcon("mdi-earth")

            with layout.toolbar as tb:
                tb.density = "compact"
                v3.VSpacer()
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
