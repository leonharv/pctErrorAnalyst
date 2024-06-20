from PyQt5.QtWidgets import QWidget, QVBoxLayout

from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonDataModel import vtkPlanes
from vtkmodules.vtkFiltersGeneral import vtkShrinkPolyData
from vtkmodules.vtkFiltersSources import vtkFrustumSource
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkCamera,
    vtkPolyDataMapper,
    vtkProperty,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkRenderer
)

class VolumeRendering(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        widget = QVTKRenderWindowInteractor()

        layout.addWidget(widget)

        renwin = widget.GetRenderWindow()

        colors = vtkNamedColors()

        camera = vtkCamera()
        camera.SetClippingRange(0.1, 0.4)
        planesArray = [0] * 24

        camera.GetFrustumPlanes(1.0, planesArray)

        planes = vtkPlanes()
        planes.SetFrustumPlanes(planesArray)

        frustumSource = vtkFrustumSource()
        frustumSource.ShowLinesOff()
        frustumSource.SetPlanes(planes)

        shrink = vtkShrinkPolyData()
        shrink.SetInputConnection(frustumSource.GetOutputPort())
        shrink.SetShrinkFactor(.9)

        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(shrink.GetOutputPort())

        back = vtkProperty()
        back.SetColor(colors.GetColor3d("Tomato"))

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().EdgeVisibilityOn()
        actor.GetProperty().SetColor(colors.GetColor3d("Banana"))
        actor.SetBackfaceProperty(back)

        # a renderer and render window
        renderer = vtkRenderer()
        renwin.AddRenderer(renderer)

        # an interactor
        renderWindowInteractor = vtkRenderWindowInteractor()
        renderWindowInteractor.SetRenderWindow(renwin)

        # add the actors to the scene
        renderer.AddActor(actor)
        renderer.SetBackground(colors.GetColor3d("Silver"))

        # Position the camera so that we can see the frustum
        renderer.GetActiveCamera().SetPosition(1, 0, 0)
        renderer.GetActiveCamera().SetFocalPoint(0, 0, 0)
        renderer.GetActiveCamera().SetViewUp(0, 1, 0)
        renderer.GetActiveCamera().Azimuth(30)
        renderer.GetActiveCamera().Elevation(30)
        renderer.ResetCamera()

        # render an image (lights and cameras are created automatically)
        renwin.Render()

        widget.Initialize()
        widget.Start()
