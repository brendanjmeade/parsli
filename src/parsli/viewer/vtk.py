from __future__ import annotations

import base64
import json
import os
import queue
from concurrent.futures import ThreadPoolExecutor
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
from vtkmodules.vtkRenderingAnnotation import vtkAxesActor, vtkScalarBarActor
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkActor2D,
    vtkColorTransferFunction,
    vtkCompositePolyDataMapper,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkTextMapper,
    vtkTextProperty,
    vtkWindowToImageFilter,
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


def encode(writer, vtk_image, file_path, writer_queue):
    writer.file_name = file_path
    writer.input_data = vtk_image
    writer.Write()
    writer_queue.put(writer)


def update_range(lut: vtkColorTransferFunction, data_range):
    prev_min, prev_max = lut.GetRange()
    prev_delta = prev_max - prev_min

    if prev_delta < 0.001:
        return

    node = [0, 0, 0, 0, 0, 0]
    next_delta = data_range[1] - data_range[0]
    next_nodes = []

    for i in range(lut.GetSize()):
        lut.GetNodeValue(i, node)
        node[0] = next_delta * (node[0] - prev_min) / prev_delta + data_range[0]
        next_nodes.append(list(node))

    lut.RemoveAllPoints()
    for n in next_nodes:
        lut.AddRGBPoint(*n)


class SceneManager:
    def __init__(self, server):
        self.server = server

        self._lut = vtkLookupTable()
        self._lut_for_bar = vtkColorTransferFunction()
        set_preset(self._lut, "Fast")

        self.geometries = {}

        self.renderer = vtkRenderer(background=(1.0, 1.0, 1.0))
        self.interactor = vtkRenderWindowInteractor()
        self.render_window = vtkRenderWindow(off_screen_rendering=1)

        self.render_window.AddRenderer(self.renderer)
        self.interactor.SetRenderWindow(self.render_window)
        self.interactor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

        self.style_terrain = vtkInteractorStyleTerrain()
        self.style_trackball = self.interactor.GetInteractorStyle()

        self.scalar_bar = vtkScalarBarActor()
        self.scalar_bar.SetOrientationToHorizontal()
        self.scalar_bar.SetLookupTable(self._lut_for_bar)
        self.scalar_bar.SetNumberOfLabels(3)
        self.scalar_bar.SetPosition(0.375, 0.01)
        self.scalar_bar.SetPosition2(0.25, 0.04)

        # labels
        self.scalar_bar.label_text_property.color = (0, 0, 0)
        self.scalar_bar.label_text_property.BoldOff()
        self.scalar_bar.label_text_property.ItalicOff()
        self.scalar_bar.SetTextPositionToPrecedeScalarBar()
        self.scalar_bar.SetTextPad(10)

        self.renderer.AddActor2D(self.scalar_bar)
        self.show_scalar_bar(False)

        # Time text
        text_property = vtkTextProperty()
        text_property.SetFontSize(16)
        text_property.SetJustificationToLeft()
        text_property.SetColor(0.2, 0.2, 0.2)

        self.time_mapper = vtkTextMapper(input="0.0", text_property=text_property)
        self.time_actor = vtkActor2D(mapper=self.time_mapper, position=(16, 16))
        self.renderer.AddActor(self.time_actor)

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

        self.window_image_filter = vtkWindowToImageFilter()
        self.window_image_filter.SetInput(self.render_window)
        self.window_image_filter.SetInputBufferTypeToRGB()

        print(f"Using {os.cpu_count()} thread for encoding")  # noqa: T201
        pool_size = os.cpu_count()
        self.encoder_pool = ThreadPoolExecutor(max_workers=pool_size)
        self.writer_queue = queue.Queue()

        # fill queue with writers
        self.writer_ext = ".png"
        for _ in range(pool_size):
            writer = vtkPNGWriter(compression_level=6)
            self.writer_queue.put(writer)

    @property
    def ctrl(self):
        return self.server.controller

    def set_time(self, time_value):
        self.time_mapper.input = f"t: {time_value}"

    def show_scalar_bar(self, show):
        self.scalar_bar.visibility = show

    def get_size(self):
        return self.render_window.GetSize()

    def set_size(self, width, height):
        self.render_window.SetSize(width, height)

    def screenshot(self):
        self.window_image_filter.Update()
        return self.window_image_filter.GetOutput()

    def write_screenshot(self, output_path):
        self.render_window.Render()
        self.window_image_filter.Modified()
        self.window_image_filter.Update()

        output = self.window_image_filter.output
        img = output.NewInstance()
        img.DeepCopy(output)

        writer = self.writer_queue.get()
        return self.encoder_pool.submit(
            encode, writer, img, f"{output_path}{self.writer_ext}", self.writer_queue
        )

    def __getitem__(self, key):
        return self.geometries.get(key)

    def reset_camera_to(self, bounds):
        self.renderer.ResetCamera(bounds)

    def reset_camera(self):
        self.renderer.ResetCamera()

    def focus_on(self, bounds):
        self.camera.position = (
            0.5 * (bounds[0] + bounds[1]),
            0.5 * (bounds[2] + bounds[3]),
            0.5 * (bounds[4] + bounds[5]),
        )
        self.reset_camera_to(bounds)

    def update_interaction_style(self, value):
        if value == "trackball":
            self.interactor.SetInteractorStyle(self.style_trackball)
        elif value == "terrain":
            camera = self.renderer.active_camera
            camera.view_up = (0, 0, 1)
            self.interactor.SetInteractorStyle(self.style_terrain)

    @property
    def camera(self):
        return self.renderer.active_camera

    @property
    def camera_state(self):
        return {
            "position": list(self.camera.position),
            "focal_point": list(self.camera.focal_point),
            "view_up": list(self.camera.view_up),
        }

    def update_camera(self, props):
        for k, v in props.items():
            setattr(self.renderer.active_camera, k, v)

    def update_view_up(self, view_up):
        self.renderer.active_camera.view_up = view_up

    def apply_zoom(self, scale):
        self.renderer.active_camera.Zoom(scale)

    def update_scalar_bar(self, color_preset, color_min, color_max):
        self._lut_for_bar.ShallowCopy(get_preset(color_preset))
        update_range(self._lut_for_bar, [color_min, color_max])

    def color_at(self, value, color_preset, color_min, color_max):
        color = [0, 0, 0]
        self.update_scalar_bar(color_preset, color_min, color_max)
        self._lut_for_bar.GetColor(value, color)
        return color

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
                interpolate_scalars_before_mapping=1,
            )
            item["geometry"] = geometry
            item["mapper"] = mapper
            mapper.SetResolveCoincidentTopologyToOff()
        else:
            mapper = vtkCompositePolyDataMapper(
                input_connection=source.output_port,
                lookup_table=self.lut,
                interpolate_scalars_before_mapping=1,
            )
            item["mapper"] = mapper
            mapper.SetResolveCoincidentTopologyToOff()

        actor = vtkActor(mapper=mapper)
        item["actor"] = actor

        self.geometries[name] = item

        self.renderer.AddActor(actor)
        self.renderer.ResetCamera()
        self.render_window.Render()

        self.ctrl.view_update()

        # Gather actors/mappers
        item["actors"] = [
            actor,
        ]
        item["mappers"] = [
            item["mapper"],
        ]

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
        for_surface = bands

        # bands.Update()
        # print(bands.GetOutputDataObject(0))

        item = {
            "name": name,
            "source": source,
            "quality": quality,
            "threshold": threshold,
            "geometry": geometry,
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
                interpolate_scalars_before_mapping=1,
            )
            mapper.SelectColorArray("Scalars")
            mapper.SetResolveCoincidentTopologyToOff()
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
                interpolate_scalars_before_mapping=1,
            )
            mapper.SelectColorArray("Scalars")
            mapper.SetResolveCoincidentTopologyToOff()
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

        self.geometries[name] = item

        self.renderer.AddActor(actor)
        self.renderer.AddActor(actor_lines)
        self.renderer.ResetCamera()
        self.render_window.Render()

        self.ctrl.view_update()

        # Gather actors/mappers
        item["actors"] = [
            item["actor"],
            item["actor_lines"],
        ]
        item["mappers"] = [
            item["mapper"],
            item["mapper_lines"],
        ]

        return item
