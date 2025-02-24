from __future__ import annotations

from trame.decorators import TrameApp, change
from trame.widgets import html
from trame.widgets import vuetify3 as v3
from vtkmodules.vtkCommonDataModel import vtkDataObject, vtkDataSetAttributes

from parsli.utils import expend_range, to_precision
from parsli.viewer.vtk import PRESETS, set_preset, to_image


@TrameApp()
class ControlPanel(v3.VCard):
    def __init__(self, toggle, scene_manager, reset_camera, reset_to_mesh):
        self._scene_manager = scene_manager

        super().__init__(
            classes="controller",
            elevation=5,
            rounded=(f"{toggle} || 'circle'",),
        )

        # allocate variable if does not exist
        self.state.setdefault(toggle, True)
        self.state.setdefault("subdivide", True)
        self.state.setdefault("show_segment", True)
        self.state.setdefault("show_surface", True)
        self.state.setdefault("light_surface", False)
        self.state.setdefault("light_segment", False)

        with self:
            with v3.VCardTitle(
                classes=(
                    f"`d-flex align-center pa-1 position-fixed bg-white ${{ {toggle} ? 'controller-content rounded-t border-b-thin':'rounded-circle'}}`",
                ),
                style="z-index: 1;",
            ):
                v3.VProgressLinear(
                    v_if=toggle,
                    indeterminate=("trame__busy",),
                    bg_color="rgba(0,0,0,0)",
                    absolute=True,
                    color="primary",
                    location="bottom",
                    height=2,
                )
                v3.VProgressCircular(
                    v_else=True,
                    bg_color="rgba(0,0,0,0)",
                    indeterminate=("trame__busy",),
                    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;",
                    color="primary",
                    width=3,
                )
                v3.VBtn(
                    icon="mdi-close",
                    v_if=toggle,
                    click=f"{toggle} = !{toggle}",
                    flat=True,
                    size="sm",
                )
                v3.VBtn(
                    icon="mdi-menu",
                    v_else=True,
                    click=f"{toggle} = !{toggle}",
                    flat=True,
                    size="sm",
                )

                html.Div(
                    "Control Panel",
                    v_show=toggle,
                    classes="text-h6 px-2",
                )

                v3.VSpacer()

                v3.VProgressCircular(
                    "{{ export_progress }}",
                    v_if=("exporting_movie", False),
                    model_value=("export_progress", 0),
                    size=30,
                    classes="text-caption",
                )

                v3.VBtn(
                    v_else=True,
                    icon="mdi-movie-open-settings-outline",
                    density="compact",
                    flat=True,
                    click=self.ctrl.export_movie,
                    loading=("exporting_movie",),
                )

                # ------------------------------------------------
                # We now have control below, so removing for now
                # ------------------------------------------------
                # v3.VCheckbox(
                #     v_show=toggle,
                #     v_model=("show_segment", True),
                #     true_icon="mdi-gesture",
                #     false_icon="mdi-gesture",
                #     hide_details=True,
                #     density="compact",
                # )
                # v3.VCheckbox(
                #     v_show=toggle,
                #     v_model=("show_surface", True),
                #     true_icon="mdi-texture-box",
                #     false_icon="mdi-texture-box",
                #     hide_details=True,
                #     density="compact",
                #     classes="mx-2",
                # )
                # ------------------------------------------------

            with v3.VCardText(
                v_show=(toggle, True),
                classes="controller-content mt-12 mb-1 pb-1 mx-0 px-1",
            ):
                # -------------------------------------------------------------
                # Longitude / Latitude cropping
                # -------------------------------------------------------------

                with v3.VRow(
                    "Longitude", classes="text-subtitle-2 ma-1 pt-2 align-center"
                ):
                    v3.VSpacer()
                    html.Span(
                        "{{ longitude_bnds[0].toFixed(1) }}",
                        classes="text-caption text-center",
                        style="width: 2.5rem;",
                    )
                    html.Span(
                        "{{ longitude_bnds[1].toFixed(1) }}",
                        classes="text-caption text-center",
                        style="width: 2.5rem;",
                    )

                v3.VRangeSlider(
                    v_model=("longitude_bnds", [0, 360]),
                    min=0,
                    max=360,
                    step=0.5,
                    density="compact",
                    hide_details=True,
                    classes="px-2",
                )

                with v3.VRow("Latitude", classes="text-subtitle-2 ma-1 align-center"):
                    v3.VSpacer()
                    html.Span(
                        "{{ latitude_bnds[0].toFixed(1) }}",
                        classes="text-caption text-center",
                        style="width: 2.5rem;",
                    )
                    html.Span(
                        "{{ latitude_bnds[1].toFixed(1) }}",
                        classes="text-caption text-center",
                        style="width: 2.5rem;",
                    )

                v3.VRangeSlider(
                    v_model=("latitude_bnds", [-90, 90]),
                    min=-90,
                    max=90,
                    step=0.5,
                    density="compact",
                    hide_details=True,
                    classes="px-2",
                )

                with v3.VRow(classes="ma-1"):
                    v3.VBtn(
                        icon="mdi-crop-free",
                        size="small",
                        flat=True,
                        density="compact",
                        hide_details=True,
                        click=reset_camera,
                    )
                    v3.VBtn(
                        icon="mdi-magnify-scan",
                        size="small",
                        flat=True,
                        density="compact",
                        hide_details=True,
                        classes="mx-2",
                        click=reset_to_mesh,
                    )

                    v3.VSpacer()
                    v3.VBtn(
                        icon="mdi-map-plus",
                        size="small",
                        flat=True,
                        density="compact",
                        hide_details=True,
                        classes="mx-2",
                        click=self._expand_bounds,
                    )

                    v3.VBtn(
                        icon="mdi-arrow-collapse-horizontal",
                        size="small",
                        flat=True,
                        density="compact",
                        hide_details=True,
                        click=self._crop_bounds_to_mesh,
                    )

                    v3.VBtn(
                        icon="mdi-arrow-expand-horizontal",
                        size="small",
                        flat=True,
                        density="compact",
                        hide_details=True,
                        classes="mx-2",
                        click=self._reset_bounds,
                    )

                # -------------------------------------------------------------

                v3.VDivider(classes="mt-2 mx-n3")

                # -------------------------------------------------------------
                # Projection: Spherical / Euclidean
                # -------------------------------------------------------------

                with html.Div(classes="d-flex"):
                    v3.VSelect(
                        prepend_inner_icon=(
                            "spherical ? 'mdi-earth' : 'mdi-earth-box'",
                        ),
                        v_model=("spherical", True),
                        items=(
                            "proj_modes",
                            [
                                {"title": "Spherical", "value": True},
                                {"title": "Euclidean", "value": False},
                            ],
                        ),
                        hide_details=True,
                        density="compact",
                        flat=True,
                        variant="solo",
                        classes="mx-n2",
                    )
                    v3.VCheckbox(
                        disabled=("!spherical",),
                        v_model=("show_earth_core", True),
                        true_icon="mdi-google-earth",
                        false_icon="mdi-google-earth",
                        hide_details=True,
                        density="compact",
                    )

                # -------------------------------------------------------------
                # Coast line regions
                # -------------------------------------------------------------

                v3.VSelect(
                    prepend_inner_icon="mdi-map-outline",
                    placeholder="Coast lines",
                    v_model=("coast_active_regions", []),
                    items=("coast_regions", []),
                    density="compact",
                    hide_details=True,
                    flat=True,
                    variant="solo",
                    chips=True,
                    closable_chips=True,
                    multiple=True,
                    classes="mx-n2",
                )
                # -------------------------------------------------------------

                v3.VDivider(classes="mx-n3 mb-1")

                # -------------------------------------------------------------
                # Opacity / Shadow
                # -------------------------------------------------------------

                v3.VSlider(
                    click_prepend="show_segment = !show_segment",
                    click_append="light_segment = !light_segment",
                    v_model=("segment_opacity", 100),
                    min=0,
                    max=1,
                    step=0.05,
                    prepend_icon="mdi-gesture",
                    append_icon=(
                        "light_segment ? 'mdi-lightbulb-outline' : 'mdi-lightbulb-off-outline'",
                    ),
                    hide_details=True,
                    density="compact",
                    flat=True,
                    variant="solo",
                    classes="mx-1",
                    style=("show_segment ? '' : 'opacity: 0.25'",),
                )

                v3.VSlider(
                    click_prepend="show_surface = !show_surface",
                    click_append="light_surface = !light_surface",
                    v_model=("surface_opacity", 100),
                    min=0,
                    max=1,
                    step=0.05,
                    prepend_icon="mdi-texture-box",
                    append_icon=(
                        "light_surface ? 'mdi-lightbulb-outline' : 'mdi-lightbulb-off-outline'",
                    ),
                    hide_details=True,
                    density="compact",
                    flat=True,
                    variant="solo",
                    classes="mx-1",
                    style=("show_surface ? '' : 'opacity: 0.25'",),
                )

                # -------------------------------------------------------------

                v3.VDivider(classes="mx-n3 mb-1")

                # -------------------------------------------------------------
                # Color mapping
                # -------------------------------------------------------------

                v3.VSelect(
                    placeholder="Color By",
                    prepend_inner_icon="mdi-format-color-fill",
                    v_model=("color_by", "dip_slip"),
                    items=("fields", []),
                    hide_details=True,
                    density="compact",
                    flat=True,
                    variant="solo",
                    classes="mx-n2",
                )

                with v3.VRow(no_gutters=True, classes="align-center mx-n2 mt-n2"):
                    with v3.VCol():
                        v3.VTextField(
                            v_model_number=("color_min", 0),
                            type="number",
                            hide_details=True,
                            density="compact",
                            flat=True,
                            variant="solo",
                            hide_spin_buttons=True,
                        )
                    with html.Div(classes="flex-0 mx-n3", style="z-index: 1;"):
                        v3.VBtn(
                            icon="mdi-arrow-expand-horizontal",
                            size="sm",
                            density="compact",
                            flat=True,
                            variant="solo",
                            classes="ml-2",
                            click=self.reset_color_range,
                        )
                        v3.VBtn(
                            icon="mdi-circle-half-full",
                            size="sm",
                            density="compact",
                            flat=True,
                            variant="solo",
                            classes="mr-2",
                            click=self.symetric_color_range,
                        )
                    with v3.VCol():
                        v3.VTextField(
                            v_model_number=("color_max", 1),
                            type="number",
                            hide_details=True,
                            density="compact",
                            flat=True,
                            variant="solo",
                            reverse=True,
                            classes="px-0",
                            hide_spin_buttons=True,
                        )

                html.Img(
                    src=("preset_img", None),
                    style="height: 1rem; width: 100%;",
                    classes="rounded-lg border-thin mb-n1",
                )

                v3.VSelect(
                    placeholder="Color Preset",
                    prepend_inner_icon="mdi-palette",
                    v_model=("color_preset", "Rycroft"),
                    items=("color_presets", list(PRESETS.keys())),
                    hide_details=True,
                    density="compact",
                    flat=True,
                    variant="solo",
                    classes="mx-n2",
                )

                v3.VDivider(classes="mx-n3 pb-1")

                # -------------------------------------------------------------
                # Contours
                # -------------------------------------------------------------

                with v3.VTooltip(
                    text=(
                        "`Number of contours: ${nb_contours} (${subdivide ? 'refined' : 'original'} mesh)`",
                    ),
                ):
                    with html.Template(v_slot_activator="{ props }"):
                        with html.Div(
                            classes="d-flex pr-2",
                            v_bind="props",
                        ):
                            v3.VSlider(
                                click_prepend="subdivide = !subdivide",
                                v_model=("nb_contours", 5),
                                min=1,
                                max=20,
                                step=1,
                                prepend_icon="mdi-fingerprint",
                                hide_details=True,
                                density="compact",
                                flat=True,
                                variant="solo",
                                style="margin: 0 2px;",
                            )

                # -------------------------------------------------------------
                # Time
                # -------------------------------------------------------------

                with v3.VTooltip(
                    text=("`Current timestep: ${time_index + 1} / ${nb_timesteps}`",),
                ):
                    with html.Template(v_slot_activator="{ props }"):
                        with html.Div(
                            classes="d-flex pr-2",
                            v_bind="props",
                        ):
                            v3.VSlider(
                                v_model=("time_index", 0),
                                min=0,
                                max=("nb_timesteps - 1",),
                                step=1,
                                prepend_icon="mdi-clock-outline",
                                hide_details=True,
                                density="compact",
                                flat=True,
                                variant="solo",
                                style="margin: 0 2px;",
                            )

    def _reset_bounds(self):
        self.state.latitude_bnds = [-90, 90]
        self.state.longitude_bnds = [0, 360]
        self.ctrl.view_update()

    def _expand_bounds(self):
        delta = 0.5
        self.state.latitude_bnds = [
            max(self.state.latitude_bnds[0] - delta, -90),
            min(self.state.latitude_bnds[1] + delta, 90),
        ]
        delta /= 2
        self.state.longitude_bnds = [
            max(self.state.longitude_bnds[0] - delta, 0),
            min(self.state.longitude_bnds[1] + delta, 360),
        ]
        self.ctrl.view_update()

    def _crop_bounds_to_mesh(self):
        source = self._scene_manager["meshes"].get("source")
        self.state.latitude_bnds = source.latitude_bounds
        self.state.longitude_bnds = source.longitude_bounds
        self.ctrl.view_update()

    @change("time_index")
    def _time_change(self, time_index, **_):
        source = self._scene_manager["meshes"].get("source")
        source.time_index = time_index
        self.ctrl.view_update()

    @change("coast_active_regions")
    def _on_regions(self, coast_active_regions, **_):
        source = self._scene_manager["coast"].get("source")
        source.active_regions = coast_active_regions
        self.ctrl.view_update()

    @change(
        "show_segment",
        "show_surface",
        "show_earth_core",
        "light_segment",
        "light_surface",
        "surface_opacity",
        "segment_opacity",
    )
    def _on_visibility(
        self,
        show_segment,
        show_surface,
        show_earth_core,
        light_segment,
        light_surface,
        surface_opacity,
        segment_opacity,
        **_,
    ):
        seg_actors = self._scene_manager["segment"].get("actors")
        surf_actors = self._scene_manager["meshes"].get("actors")
        earth_actors = self._scene_manager["earth_core"].get("actors")

        for actor in seg_actors:
            actor.SetVisibility(show_segment)
            actor.property.opacity = segment_opacity
            actor.property.lighting = not light_segment

        for actor in surf_actors:
            actor.SetVisibility(show_surface)
            actor.property.opacity = surface_opacity
            actor.property.lighting = not light_surface

        for actor in earth_actors:
            actor.SetVisibility(show_earth_core)

        self.ctrl.view_update()

    @change("latitude_bnds", "longitude_bnds")
    def _on_lat_lon_bnd(self, longitude_bnds, latitude_bnds, **_):
        if self._scene_manager["segment"]:
            reader = self._scene_manager["segment"].get("source")
            reader.longitude_bnds = longitude_bnds
            reader.latitude_bnds = latitude_bnds
        self.ctrl.view_update()

    @change("color_by", "color_preset", "color_min", "color_max", "nb_contours")
    def _on_color_preset(
        self, color_preset, color_min, color_max, color_by, nb_contours, **_
    ):
        lut = self._scene_manager.lut
        color_min = float(color_min)
        color_max = float(color_max)

        for mesh_type in ["segment", "meshes"]:
            if self._scene_manager[mesh_type]:
                mapper = self._scene_manager[mesh_type].get("mapper")
                mapper.SetScalarVisibility(1)

                if mesh_type == "segment":
                    mapper.SelectColorArray(color_by)
                    mapper.SetScalarRange(color_min, color_max)
                else:
                    bands = self._scene_manager[mesh_type].get("bands")

                    # The scalar we color on is an int starting
                    # at 0 for the first band.
                    # => Sample color at the center of the band by 0.5 shift
                    mapper.SetScalarRange(-0.5, nb_contours + 0.5)

        mesh_pipeline = self._scene_manager["meshes"]
        assign = mesh_pipeline.get("assign")
        assign.Assign(
            color_by,
            vtkDataSetAttributes.SCALARS,
            vtkDataObject.FIELD_ASSOCIATION_POINTS,
        )
        bands = mesh_pipeline.get("bands")

        # +2 because for 1 cut line we need 3 values [min, cut_line, max]
        bands.GenerateValues(nb_contours + 2, [color_min, color_max])
        bands.ClippingOn()

        if "color_preset" in self.state.modified_keys:
            set_preset(lut, color_preset)
            self.state.preset_img = to_image(lut, 255)

        self.ctrl.view_update()

    def symetric_color_range(self):
        max_bound = max(abs(self.state.color_min), abs(self.state.color_max))
        max_bound = to_precision(max_bound, 3)
        self.state.color_min = -max_bound
        self.state.color_max = max_bound

    def reset_color_range(self):
        pipeline_item = self._scene_manager["meshes"]
        source = pipeline_item.get("source")
        ds = source()

        total_range = None
        for array in ds.cell_data[self.state.color_by].Arrays:
            total_range = expend_range(total_range, array.GetRange())

        self.state.color_min = to_precision(total_range[0], 3)
        self.state.color_max = to_precision(total_range[1], 3)


class ViewToolbar(v3.VCard):
    def __init__(self, reset_camera, reset_to_mesh, apply_zoom, update_view_up):
        super().__init__(
            classes="view-toolbar pa-1",
            rounded="lg",
        )

        self.state.setdefault("interaction_style", "trackball")

        with self:
            with v3.VTooltip(text="Reset camera"):
                with html.Template(v_slot_activator="{ props }"):
                    v3.VBtn(
                        v_bind="props",
                        flat=True,
                        density="compact",
                        icon="mdi-crop-free",
                        click=reset_camera,
                    )

            with v3.VTooltip(text="Reset camera centered on mesh"):
                with html.Template(v_slot_activator="{ props }"):
                    v3.VBtn(
                        v_bind="props",
                        flat=True,
                        density="compact",
                        icon="mdi-magnify-scan",
                        click=reset_to_mesh,
                    )
            v3.VDivider()
            with v3.VTooltip(text="Zoom in"):
                with html.Template(v_slot_activator="{ props }"):
                    v3.VBtn(
                        v_bind="props",
                        flat=True,
                        density="compact",
                        icon="mdi-magnify-plus-outline",
                        click=(apply_zoom, "[1.1]"),
                    )
            with v3.VTooltip(text="Zoom out"):
                with html.Template(v_slot_activator="{ props }"):
                    v3.VBtn(
                        v_bind="props",
                        flat=True,
                        density="compact",
                        icon="mdi-magnify-minus-outline",
                        click=(apply_zoom, "[0.9]"),
                    )

            v3.VDivider()
            with v3.VTooltip(text="Trackball interaction"):
                with html.Template(v_slot_activator="{ props }"):
                    v3.VBtn(
                        v_show="interaction_style == 'trackball'",
                        disabled=("!spherical",),
                        v_bind="props",
                        flat=True,
                        density="compact",
                        icon="mdi-rotate-orbit",
                        click="interaction_style = 'terrain'",
                    )

            with v3.VTooltip(text="Terrain interaction"):
                with html.Template(v_slot_activator="{ props }"):
                    v3.VBtn(
                        v_show="interaction_style == 'terrain'",
                        v_bind="props",
                        flat=True,
                        density="compact",
                        icon="mdi-axis-z-rotate-counterclockwise",
                        click="interaction_style = 'trackball'",
                    )

            with v3.VTooltip(text="Z up"):
                with html.Template(v_slot_activator="{ props }"):
                    v3.VBtn(
                        v_show="interaction_style == 'trackball' && spherical",
                        v_bind="props",
                        flat=True,
                        density="compact",
                        icon="mdi-axis-z-arrow",
                        click=(update_view_up, "[[0, 0, 1]]"),
                    )
            with v3.VTooltip(text="Y up"):
                with html.Template(v_slot_activator="{ props }"):
                    v3.VBtn(
                        v_show="!spherical",
                        v_bind="props",
                        flat=True,
                        density="compact",
                        icon="mdi-axis-y-arrow",
                        click=(update_view_up, "[[0, 1, 0]]"),
                    )


class ScalarBar(v3.VTooltip):
    def __init__(
        self,
        img_src="preset_img",
        color_min="color_min",
        color_max="color_max",
        **kwargs,
    ):
        super().__init__(location="top")

        self.state.setdefault("scalarbar_probe", [])
        self.state.client_only("scalarbar_probe", "scalarbar_probe_available")

        with self:
            # Content
            with html.Template(v_slot_activator="{ props }"):
                with html.Div(
                    classes="scalarbar",
                    rounded="pill",
                    v_bind="props",
                    **kwargs,
                ):
                    html.Div(f"{{{{ {color_min} }}}}", classes="scalarbar-left")
                    html.Img(
                        src=(img_src, None),
                        style="height: 100%; width: 100%;",
                        classes="rounded-lg border-thin",
                        mousemove="scalarbar_probe = [$event.x, $event.target.getBoundingClientRect()]",
                        mouseenter="scalarbar_probe_available = 1",
                        mouseleave="scalarbar_probe_available = 0",
                        __events=["mousemove", "mouseenter", "mouseleave"],
                    )
                    html.Div(
                        v_show=("scalarbar_probe_available", False),
                        classes="scalar-cursor",
                        style=(
                            "`left: ${scalarbar_probe?.[0] - scalarbar_probe?.[1]?.left}px`",
                        ),
                    )
                    html.Div(f"{{{{ {color_max} }}}}", classes="scalarbar-right")
            html.Span(
                f"{{{{ (({color_max} - {color_min}) * (scalarbar_probe?.[0] - scalarbar_probe?.[1]?.left) / scalarbar_probe?.[1]?.width + {color_min}).toFixed(3) }}}}"
            )
