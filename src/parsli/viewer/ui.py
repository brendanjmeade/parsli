from __future__ import annotations

from trame.decorators import TrameApp, change
from trame.widgets import html
from trame.widgets import vuetify3 as v3

from parsli.utils import expend_range
from parsli.viewer.vtk import PRESETS, set_preset, to_image


@TrameApp()
class ControlPanel(v3.VCard):
    def __init__(self, toggle, scene_manager):
        self._scene_manager = scene_manager

        super().__init__(
            classes="controller",
            rounded=(f"{toggle} || 'circle'",),
        )

        # allocate variable if does not exist
        self.state.setdefault(toggle, True)

        with self:
            with v3.VCardTitle(
                classes=(
                    f"`d-flex pa-1 position-fixed bg-white ${{ {toggle} ? 'controller-content rounded-t border-b-thin':'rounded-circle'}}`",
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

            with v3.VCardText(
                v_show=(toggle, True),
                classes="controller-content py-1 mt-10",
            ):
                # -------------------------------------------------------------
                # Longitude / Latitude cropping
                # -------------------------------------------------------------

                with v3.VRow("Longitude", classes="text-subtitle-2 ma-0 align-center"):
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
                    step=1,
                    density="compact",
                    hide_details=True,
                )

                with v3.VRow("Latitude", classes="text-subtitle-2 ma-0 align-center"):
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
                    step=1,
                    density="compact",
                    hide_details=True,
                )

                with v3.VRow(classes="ma-0"):
                    v3.VSpacer()
                    v3.VBtn(
                        icon="mdi-magnify-scan",
                        size="small",
                        flat=True,
                        density="compact",
                        hide_details=True,
                        classes="mx-2",
                        click=self._crop_bounds_to_mesh,
                    )
                    v3.VBtn(
                        icon="mdi-arrow-expand-all",
                        size="small",
                        flat=True,
                        density="compact",
                        hide_details=True,
                        classes="mx-2",
                        click="latitude_bnds = [-90, 90]; longitude_bnds = [0, 360]",
                    )

                # -------------------------------------------------------------
                # Color mapping
                # -------------------------------------------------------------
                v3.VDivider(classes="my-2 mx-n3")

                v3.VSelect(
                    placeholder="Color By",
                    prepend_inner_icon="mdi-format-color-fill",
                    v_model=("color_by", None),
                    items=("fields", []),
                    hide_details=True,
                    density="compact",
                    flat=True,
                    variant="solo",
                    classes="mx-n2",
                )

                v3.VDivider(classes="my-2 mx-n3")

                with v3.VRow(no_gutters=True, classes="align-center mr-0"):
                    with v3.VCol():
                        v3.VTextField(
                            v_model_number=("color_min", 0),
                            type="number",
                            hide_details=True,
                            density="compact",
                            flat=True,
                            variant="solo",
                            classes="px-0",
                            hide_spin_buttons=True,
                        )
                    with html.Div(classes="flex-0"):
                        v3.VBtn(
                            icon="mdi-arrow-split-vertical",
                            size="sm",
                            density="compact",
                            flat=True,
                            variant="outlined",
                            classes="mx-2",
                            click=self.reset_color_range,
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
                    classes="rounded-lg border-thin",
                )

                v3.VSelect(
                    placeholder="Color Preset",
                    prepend_inner_icon="mdi-palette",
                    v_model=("color_preset", "Fast"),
                    items=("color_presets", list(PRESETS.keys())),
                    hide_details=True,
                    density="compact",
                    flat=True,
                    variant="solo",
                )

                v3.VDivider(classes="my-2 mx-n3")

                v3.VSelect(
                    prepend_inner_icon=("spherical ? 'mdi-earth' : 'mdi-earth-box'",),
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
                )

    def _crop_bounds_to_mesh(self):
        source = self._scene_manager["meshes"].get("source")
        self.state.latitude_bnds = source.latitude_bounds
        self.state.longitude_bnds = source.longitude_bounds
        self.ctrl.view_update()

    @change("latitude_bnds", "longitude_bnds")
    def _on_lat_lon_bnd(self, longitude_bnds, latitude_bnds, **_):
        if self._scene_manager["segment"]:
            reader = self._scene_manager["segment"].get("source")
            reader.longitude_bnds = longitude_bnds
            reader.latitude_bnds = latitude_bnds
        self.ctrl.view_update()

    @change("color_preset", "color_min", "color_max")
    def _on_color_preset(self, color_preset, color_min, color_max, color_by, **_):
        lut = None
        color_min = float(color_min)
        color_max = float(color_max)
        for mesh_type in ["segment", "meshes"]:
            lut = self._scene_manager.get_lut(mesh_type)
            set_preset(lut, color_preset)

            if self._scene_manager[mesh_type]:
                mapper = self._scene_manager[mesh_type].get("mapper")
                mapper.SelectColorArray(color_by)
                mapper.SetScalarModeToUseCellFieldData()
                mapper.InterpolateScalarsBeforeMappingOn()
                mapper.SetScalarVisibility(1)
                mapper.SetScalarRange(color_min, color_max)

        self.state.preset_img = to_image(lut, 255)
        self.ctrl.view_update()

    def reset_color_range(self):
        pipeline_item = self._scene_manager["meshes"]
        source = pipeline_item.get("source")
        ds = source()

        total_range = None
        for array in ds.cell_data[self.state.color_by].Arrays:
            total_range = expend_range(total_range, array.GetRange())

        self.state.color_min = total_range[0]
        self.state.color_max = total_range[1]


class ViewToolbar(v3.VCard):
    def __init__(self, reset_camera, reset_to_mesh):
        super().__init__(
            classes="view-toolbar pa-1",
            rounded="lg",
        )

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
