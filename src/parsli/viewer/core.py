from __future__ import annotations

import asyncio
import time
from pathlib import Path

from trame.app import asynchronous, get_server
from trame.decorators import TrameApp, change, controller
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import vtk as vtkw
from trame.widgets import vtklocal
from trame.widgets import vuetify3 as v3
from vtkmodules.vtkFiltersSources import vtkSphereSource
from vtkmodules.vtkIOParallelXML import vtkXMLPartitionedDataSetWriter

from parsli.io import VtkCoastLineSource, VtkMeshReader, VtkSegmentReader
from parsli.utils import expend_range, source, to_precision
from parsli.utils.earth import EARTH_RADIUS
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

        # earth core
        pipeline = self.scene_manager.add_geometry(
            "earth_core",
            vtkSphereSource(
                radius=EARTH_RADIUS - 100,
                theta_resolution=60,
                phi_resolution=60,
            ),
        )
        prop = pipeline.get("actor").property
        prop.opacity = 0.85

        # Latitude/Longitude bounding box
        pipeline = self.scene_manager.add_geometry(
            "bbox",
            source.VtkLatLonBound(),
        )
        bbox_prop = pipeline.get("actor").property
        bbox_prop.line_width = 2
        bbox_prop.color = (0.5, 0.5, 0.5)

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
        pipeline.get(
            "mapper"
        ).SetScalarModeToUseCellFieldData()  # Bands: Scalars on Cell
        self.state.fields = mesh_reader.available_fields
        self.state.time_index = mesh_reader.time_index
        self.state.nb_timesteps = mesh_reader.number_of_timesteps

        # Coast lines
        self.coast_lines = VtkCoastLineSource()
        self.state.coast_regions = self.coast_lines.available_regions
        self.state.coast_active_regions = []
        pipeline = self.scene_manager.add_geometry("coast", self.coast_lines, True)
        coast_props = pipeline.get("actor").property
        coast_props.line_width = 2
        coast_props.color = (0.5, 0.5, 0.5)

        if DEBUG_WRITE_MESH:
            writer = vtkXMLPartitionedDataSetWriter()
            writer.SetInputData(mesh_reader())
            writer.SetFileName("all_meshes.vtpd")
            writer.Write()

        self.readers = [mesh_reader, seg_reader]

        # setup camera to look at the data
        bounds = self.scene_manager["meshes"].get("actor").bounds
        self.scene_manager.focus_on(bounds)

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

        self.state.color_min = to_precision(total_range[0], 3)
        self.state.color_max = to_precision(total_range[1], 3)

    @change("spherical")
    def _on_projection_change(self, spherical, **_):
        self.state.show_earth_core = spherical

        for geo_name in ["segment", "meshes", "coast", "bbox"]:
            pipeline_item = self.scene_manager[geo_name]
            pipeline_item.get("source").spherical = spherical
            actors = pipeline_item.get("actors")

            scale = (1, 1, 1) if spherical else (1, 1, 0.01)
            for actor in actors:
                actor.scale = scale

        if spherical:
            bounds = self.scene_manager["meshes"].get("actor").bounds
            self.scene_manager.camera.focal_point = (0, 0, 0)
            self.scene_manager.camera.view_up = (0, 0, 1)
            self.scene_manager.focus_on(bounds)
        else:
            self.state.interaction_style = "trackball"
            self.scene_manager.camera.focal_point = (0, 0, 0)
            self.scene_manager.camera.position = (0, 0, 1)
            self.scene_manager.camera.view_up = (0, 1, 0)

        self.reset_to_mesh()

    @change("camera")
    def _on_camera(self, camera, **_):
        if camera is None:
            return

        self.ctrl.vtk_update_from_state(camera)

    @change("interaction_style")
    def _on_style_change(self, interaction_style, **_):
        self.scene_manager.update_interaction_style(interaction_style)
        self.ctrl.view_update(push_camera=True)

    @change("subdivide")
    def _on_subdivide(self, subdivide, **_):
        # source >> quality >> threshold >> geometry >> cell2point >> refine >> assign >> bands
        pipeline = self.scene_manager["meshes"]

        source = pipeline.get("source")
        assign = pipeline.get("assign")
        refine = pipeline.get("refine")
        cell2point = pipeline.get("cell2point")
        threshold = pipeline.get("threshold")
        geometry = pipeline.get("geometry")

        if subdivide:
            geometry.input_connection = threshold.output_port
            assign.input_connection = refine.output_port

            # debug
            # self.debug_check_quality()
        else:
            geometry.input_connection = source.output_port
            assign.input_connection = cell2point.output_port

        self.ctrl.view_update()

    @change("screenshot_export_path")
    def _on_export_path(self, screenshot_export_path, **_):
        self.state.screenshot_export_path_exits = Path(screenshot_export_path).exists()

    def reset_to_mesh(self):
        bounds = self.scene_manager["meshes"].get("actor").bounds
        self.scene_manager.reset_camera_to(bounds)
        self.ctrl.view_update(push_camera=True)

    def apply_zoom(self, scale):
        self.scene_manager.apply_zoom(scale)
        self.ctrl.view_update(push_camera=True)

    def update_view_up(self, view_up):
        self.scene_manager.update_view_up(view_up)
        self.ctrl.view_update(push_camera=True)

    # def debug_check_quality(self):
    #     filter = self.scene_manager["meshes"].get("quality").GetOutputDataObject(0)
    #     for array in filter.cell_data["Quality"].Arrays:
    #         print("Quality range", array.GetRange())

    async def _export_movie(self):
        t0 = time.time()
        await asyncio.sleep(0.1)

        # Export path handling
        base_directory = Path(self.state.screenshot_export_path)
        base_directory.mkdir(parents=True)
        print(  # noqa: T201
            "\n----------------------------------------"
            "\nExporting images:"
            f"\n => location: {base_directory.resolve()}"
            f"\n => number of frames: {self.state.nb_timesteps}"
        )

        # Update Render Window size
        original_size = self.scene_manager.get_size()
        self.scene_manager.set_size(
            self.state.screenshot_width, self.state.screenshot_height
        )
        self.scene_manager.show_scalar_bar(True)

        source = self.scene_manager["meshes"].get("source")
        futures = []
        nb_timesteps = self.state.nb_timesteps
        for t_idx in range(nb_timesteps):
            source.time_index = t_idx % self.state.nb_timesteps
            futures.append(
                self.scene_manager.write_screenshot(base_directory / f"{t_idx:012}")
            )
            progress = int(100 * (t_idx + 1) / nb_timesteps)
            if progress != self.state.export_progress:
                with self.state:
                    self.state.export_progress = progress
                await asyncio.sleep(0.001)

        # Ensure full completion
        for future in futures:
            future.result()

        t2 = time.time()
        print(f" => time: {t2 - t0:.1f}s")  # noqa: T201
        print(f" => fps: {nb_timesteps / (t2 - t0):.1f}")  # noqa: T201

        # Reset size to original
        self.scene_manager.set_size(*original_size)
        self.scene_manager.show_scalar_bar(False)

        with self.state:
            self.state.exporting_movie = False
            self.state.export_progress = 100

    @controller.set("export_movie")
    def export_movie(self):
        self.state.configure_screenshot_export = False
        self.state.export_progress = 0
        self.state.exporting_movie = True
        self.state.screenshot_export_path_exits = True
        asynchronous.create_task(self._export_movie())

    def _build_ui(self):
        self.state.trame__title = "Parsli"
        self.state.setdefault("camera", None)
        with VAppLayout(self.server, full_height=True) as layout:
            self.ui = layout

            # Screenshot Export Dialog
            with v3.VDialog(v_model=("configure_screenshot_export", False)):
                with v3.VCard(style="max-width: 50rem;", classes="mx-auto"):
                    with v3.VCardTitle("Export video", classes="d-flex align-center"):
                        v3.VSpacer()
                        v3.VBtn(
                            icon="mdi-close",
                            flat=True,
                            density="compact",
                            click="configure_screenshot_export = false",
                        )
                    v3.VDivider()
                    with v3.VCardText():
                        with v3.VRow(classes="my-1 align-center"):
                            v3.VTextField(
                                label="Width",
                                v_model=("screenshot_width", 3840),
                                type="number",
                                hide_details=True,
                                density="compact",
                                variant="outlined",
                                hide_spin_buttons=True,
                            )
                            v3.VTextField(
                                label="Height",
                                v_model=("screenshot_height", 2160),
                                type="number",
                                hide_details=True,
                                density="compact",
                                variant="outlined",
                                hide_spin_buttons=True,
                                classes="mx-2",
                            )
                            v3.VBtn(
                                "4K",
                                variant="flat",
                                color="primary",
                                click="screenshot_width=3840; screenshot_height=2160;",
                            )
                            v3.VBtn(
                                "1080p",
                                classes="mx-2",
                                color="secondary",
                                variant="flat",
                                click="screenshot_width=1920; screenshot_height=1080;",
                            )
                            v3.VBtn(
                                "x2",
                                variant="outlined",
                                classes="mx-2",
                                click="screenshot_width=2*screenshot_width; screenshot_height=2*screenshot_height;",
                            )
                            v3.VBtn(
                                "1/2",
                                variant="outlined",
                                click="screenshot_width=0.5*screenshot_width; screenshot_height=0.5*screenshot_height;",
                            )
                        with v3.VRow(classes="mt-3"):
                            v3.VTextField(
                                label="Export Path",
                                v_model=(
                                    "screenshot_export_path",
                                    str(Path.cwd().resolve() / "export"),
                                ),
                                density="compact",
                                variant="outlined",
                                error=("screenshot_export_path_exits",),
                                error_messages=(
                                    "screenshot_export_path_exits ? 'Path already exists' : null",
                                ),
                            )

                        with v3.VRow(classes=""):
                            v3.VSpacer()

                            v3.VBtn(
                                "Export",
                                color="primary",
                                variant="flat",
                                disabled=("screenshot_export_path_exits", False),
                                click=self.ctrl.export_movie,
                            )

            with v3.VContainer(
                fluid=True, classes="fill-height pa-0 ma-0 position-relative"
            ):
                if self.local_rendering:
                    with vtklocal.LocalView(
                        self.scene_manager.render_window,
                        20,
                        camera="camera = $event",
                    ) as view:
                        view.register_vtk_object(self.scene_manager.widget)
                        self.ctrl.view_update = view.update
                        self.ctrl.view_reset_camera = view.reset_camera
                        self.ctrl.vtk_update_from_state = view.vtk_update_from_state
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
                    apply_zoom=self.apply_zoom,
                    update_view_up=self.update_view_up,
                )

                # ScalarBar
                ui.ScalarBar()
