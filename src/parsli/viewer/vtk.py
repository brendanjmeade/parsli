from __future__ import annotations

import base64
import json
from pathlib import Path

import numpy as np
import vtkmodules.vtkRenderingOpenGL2  # noqa: F401
from vtkmodules.vtkCommonCore import vtkLookupTable, vtkUnsignedCharArray
from vtkmodules.vtkCommonDataModel import (
    vtkDataObject,
    vtkDataSetAttributes,
    vtkImageData,
)
from vtkmodules.vtkFiltersCore import (
    vtkAssignAttribute,
    vtkCellDataToPointData,
    vtkThreshold,
)
from vtkmodules.vtkFiltersGeometry import vtkDataSetSurfaceFilter
from vtkmodules.vtkFiltersModeling import (
    vtkBandedPolyDataContourFilter,
    vtkLoopSubdivisionFilter,
)
from vtkmodules.vtkFiltersVerdict import vtkMeshQuality

# VTK factory initialization
from vtkmodules.vtkInteractionStyle import (
    vtkInteractorStyleSwitch,  # noqa: F401
    vtkInteractorStyleTerrain,
)
from vtkmodules.vtkInteractionWidgets import vtkOrientationMarkerWidget
from vtkmodules.vtkIOImage import vtkPNGWriter
from vtkmodules.vtkRenderingAnnotation import vtkAxesActor
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkColorTransferFunction,
    vtkCompositePolyDataMapper,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)

# Disable warning
vtkLoopSubdivisionFilter.GlobalWarningDisplayOff()


PRESETS = {
    item.get("Name"): item
    for item in json.loads(Path(__file__).with_name("presets.json").read_text())
}

LUTS = {}


def get_preset(preset_name: str) -> vtkColorTransferFunction:
    if preset_name in LUTS:
        return LUTS[preset_name]

    lut = LUTS.setdefault(preset_name, vtkColorTransferFunction())
    preset = PRESETS[preset_name]
    srgb = np.array(preset["RGBPoints"])
    color_space = preset["ColorSpace"]

    if color_space == "Diverging":
        lut.SetColorSpaceToDiverging()
    elif color_space == "HSV":
        lut.SetColorSpaceToHSV()
    elif color_space == "Lab":
        lut.SetColorSpaceToLab()
    elif color_space == "RGB":
        lut.SetColorSpaceToRGB()
    elif color_space == "CIELAB":
        lut.SetColorSpaceToLabCIEDE2000()

    if "NanColor" in preset:
        lut.SetNanColor(preset["NanColor"])

    # Always RGB points
    lut.RemoveAllPoints()
    for arr in np.split(srgb, len(srgb) / 4):
        lut.AddRGBPoint(arr[0], arr[1], arr[2], arr[3])

    return lut


def set_preset(lut: vtkLookupTable, preset_name: str, n_colors=255):
    colors = get_preset(preset_name)
    min, max = colors.GetRange()
    delta = max - min
    lut.SetNumberOfTableValues(n_colors)
    for i in range(n_colors):
        x = min + (delta * i / n_colors)
        rgb = colors.GetColor(x)
        lut.SetTableValue(i, *rgb)
    lut.Build()


def to_image(lut, samples=255):
    colorArray = vtkUnsignedCharArray()
    colorArray.SetNumberOfComponents(3)
    colorArray.SetNumberOfTuples(samples)

    dataRange = lut.GetRange()
    delta = (dataRange[1] - dataRange[0]) / float(samples)

    # Add the color array to an image data
    imgData = vtkImageData()
    imgData.SetDimensions(samples, 1, 1)
    imgData.GetPointData().SetScalars(colorArray)

    # Loop over all presets
    rgb = [0, 0, 0]
    for i in range(samples):
        lut.GetColor(dataRange[0] + float(i) * delta, rgb)
        r = int(round(rgb[0] * 255))
        g = int(round(rgb[1] * 255))
        b = int(round(rgb[2] * 255))
        colorArray.SetTuple3(i, r, g, b)

    writer = vtkPNGWriter()
    writer.WriteToMemoryOn()
    writer.SetInputData(imgData)
    writer.SetCompressionLevel(6)
    writer.Write()

    writer.GetResult()

    base64_img = base64.standard_b64encode(writer.GetResult()).decode("utf-8")
    return f"data:image/png;base64,{base64_img}"


class SceneManager:
    def __init__(self, server):
        self.server = server

        self._lut = vtkLookupTable()
        set_preset(self._lut, "Fast")

        self.geometries = {}

        self.renderer = vtkRenderer(background=(1.0, 1.0, 1.0))
        self.interactor = vtkRenderWindowInteractor()
        self.render_window = vtkRenderWindow(off_screen_rendering=1)

        self.style = vtkInteractorStyleTerrain()

        self.render_window.AddRenderer(self.renderer)
        self.interactor.SetRenderWindow(self.render_window)
        # self.interactor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()
        self.interactor.SetInteractorStyle(self.style)

        camera = self.renderer.active_camera
        camera.position = (1, 0, 0)
        camera.focal_point = (0, 0, 0)
        camera.view_up = (0, 0, 1)

        self.interactor.Initialize()

        axes_actor = vtkAxesActor()
        self.widget = vtkOrientationMarkerWidget()
        self.widget.SetOrientationMarker(axes_actor)
        self.widget.SetInteractor(self.interactor)
        self.widget.SetViewport(0.85, 0, 1, 0.15)
        self.widget.EnabledOn()
        self.widget.InteractiveOff()

    @property
    def ctrl(self):
        return self.server.controller

    def __getitem__(self, key):
        return self.geometries.get(key)

    def reset_camera_to(self, bounds):
        self.renderer.ResetCamera(bounds)

    @property
    def camera(self):
        return self.renderer.active_camera

    def update_view_up(self, view_up):
        self.renderer.active_camera.view_up = view_up

    def apply_zoom(self, scale):
        self.renderer.active_camera.Zoom(scale)

    @property
    def lut(self):
        return self._lut

    def add_geometry(self, name, source, composite=False):
        item = {"name": name, "source": source, "composite": composite}

        if not composite:
            geometry = vtkDataSetSurfaceFilter(input_connection=source.output_port)
            mapper = vtkPolyDataMapper(
                input_connection=geometry.output_port,
                lookup_table=self.lut,
            )
            mapper.InterpolateScalarsBeforeMappingOn()
            item["geometry"] = geometry
            item["mapper"] = mapper
        else:
            mapper = vtkCompositePolyDataMapper(
                input_connection=source.output_port,
                lookup_table=self.lut,
            )
            mapper.InterpolateScalarsBeforeMappingOn()
            item["mapper"] = mapper

        actor = vtkActor(mapper=mapper)
        item["actor"] = actor
        item["actors"] = [actor]

        self.geometries[name] = item

        self.renderer.AddActor(actor)
        self.renderer.ResetCamera()
        self.render_window.Render()

        self.ctrl.view_update()

        return item

    def add_geometry_with_contour(self, name, source, composite=False):
        # pipeline filters
        quality = vtkMeshQuality()
        quality.SetTriangleQualityMeasureToEdgeRatio()
        threshold = vtkThreshold(
            threshold_function=vtkThreshold.THRESHOLD_LOWER,
            lower_threshold=3.99,  # magic number for vtkLoopSubdivisionFilter
        )
        threshold.SetInputArrayToProcess(
            0, 0, 0, vtkDataObject.FIELD_ASSOCIATION_CELLS, "Quality"
        )
        geometry = vtkDataSetSurfaceFilter()
        cell2point = vtkCellDataToPointData()
        refine = vtkLoopSubdivisionFilter(
            number_of_subdivisions=1
        )  # Adjust subdivision quality
        assign = vtkAssignAttribute()
        assign.Assign(
            "dip_slip",  # Will be overridden later
            vtkDataSetAttributes.SCALARS,
            vtkDataObject.FIELD_ASSOCIATION_POINTS,
        )
        bands = vtkBandedPolyDataContourFilter(generate_contour_edges=1)
        # bands.SetScalarModeToIndex()

        # connect pipeline
        (
            source
            >> quality
            >> threshold
            >> geometry
            >> cell2point
            >> refine
            >> assign
            >> bands
        )
        for_surface = refine

        # bands.Update()
        # print(bands.GetOutputDataObject(0))

        item = {
            "name": name,
            "source": source,
            "composite": composite,
            "cell2point": cell2point,
            "refine": refine,
            "assign": assign,
            "bands": bands,
        }

        if not composite:
            # surface
            mapper = vtkPolyDataMapper(
                input_connection=for_surface.output_port,
                lookup_table=self.lut,
            )
            mapper.InterpolateScalarsBeforeMappingOn()
            item["mapper"] = mapper
            # lines
            mapper_lines = vtkPolyDataMapper(
                input_connection=bands.GetOutputPort(1),
            )
            mapper_lines.SetResolveCoincidentTopologyToPolygonOffset()
            item["mapper_lines"] = mapper_lines
        else:
            # surface
            mapper = vtkCompositePolyDataMapper(
                input_connection=for_surface.output_port,
                lookup_table=self.lut,
            )
            mapper.InterpolateScalarsBeforeMappingOn()
            item["mapper"] = mapper
            # lines
            mapper_lines = vtkCompositePolyDataMapper(
                input_connection=bands.GetOutputPort(1),
                scalar_visibility=0,
            )
            mapper_lines.SetResolveCoincidentTopologyToPolygonOffset()
            item["mapper_lines"] = mapper_lines

        # Surface actor
        actor = vtkActor(mapper=mapper)
        item["actor"] = actor

        # Lines actor
        actor_lines = vtkActor(mapper=mapper_lines)
        actor_lines.property.color = (0, 0, 0)
        actor_lines.property.line_width = 2
        # actor_lines.property.render_line_as_tube = 1
        item["actor_lines"] = actor_lines

        item["actors"] = [actor, actor_lines]

        self.geometries[name] = item

        self.renderer.AddActor(actor)
        self.renderer.AddActor(actor_lines)
        self.renderer.ResetCamera()
        self.render_window.Render()

        self.ctrl.view_update()

        return item
