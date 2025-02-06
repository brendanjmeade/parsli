from __future__ import annotations

import base64
import json
from pathlib import Path

import numpy as np
import vtkmodules.vtkRenderingOpenGL2  # noqa: F401
from vtkmodules.vtkCommonCore import vtkLookupTable, vtkUnsignedCharArray
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkFiltersGeometry import vtkDataSetSurfaceFilter

# VTK factory initialization
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch  # noqa: F401
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

        self.geometries = {}

        self.renderer = vtkRenderer(background=(0.8, 0.8, 0.8))
        self.interactor = vtkRenderWindowInteractor()
        self.render_window = vtkRenderWindow(off_screen_rendering=1)

        self.render_window.AddRenderer(self.renderer)
        self.interactor.SetRenderWindow(self.render_window)
        self.interactor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

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

    def get_lut(self, name):
        return self.geometries.get(name, {}).get("lut")

    def add_geometry(self, name, source, composite=False):
        lut = vtkLookupTable()
        set_preset(lut, "Fast")

        item = {"name": name, "source": source, "composite": composite, "lut": lut}

        if not composite:
            geometry = vtkDataSetSurfaceFilter(input_connection=source.output_port)
            mapper = vtkPolyDataMapper(
                input_connection=geometry.output_port,
                lookup_table=lut,
            )
            item["geometry"] = geometry
            item["mapper"] = mapper
        else:
            mapper = vtkCompositePolyDataMapper(
                input_connection=source.output_port,
                lookup_table=lut,
            )
            item["mapper"] = mapper

        actor = vtkActor(mapper=mapper)
        item["actor"] = actor

        self.geometries[name] = item

        self.renderer.AddActor(actor)
        self.renderer.ResetCamera()
        self.render_window.Render()

        self.ctrl.view_update()
