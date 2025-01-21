from __future__ import annotations

import vtkmodules.vtkRenderingOpenGL2  # noqa: F401
from vtkmodules.vtkCommonCore import vtkLookupTable
from vtkmodules.vtkFiltersGeometry import vtkDataSetSurfaceFilter

# VTK factory initialization
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch  # noqa: F401
from vtkmodules.vtkInteractionWidgets import vtkOrientationMarkerWidget
from vtkmodules.vtkRenderingAnnotation import vtkAxesActor
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)


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

        self.lut = vtkLookupTable()
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

    def add_geometry(self, name, source):
        geometry = vtkDataSetSurfaceFilter(input_connection=source.output_port)
        mapper = vtkPolyDataMapper(
            input_connection=geometry.output_port,
            lookup_table=self.lut,
        )
        actor = vtkActor(mapper=mapper)

        self.geometries[name] = {
            "name": name,
            "source": source,
            "geometry": geometry,
            "mapper": mapper,
            "actor": actor,
        }
        self.renderer.AddActor(actor)
        self.renderer.ResetCamera()
        self.render_window.Render()

        self.ctrl.view_update()
