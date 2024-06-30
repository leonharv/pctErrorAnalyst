from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QSlider,
    QLabel,
    QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSlot
from qtrangeslider import QRangeSlider

from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtkmodules.vtkRenderingOpenGL2
import vtkmodules.vtkInteractionStyle
import vtkmodules.vtkRenderingVolumeOpenGL2

from vtkmodules.vtkIOImage import vtkImageImport
from vtkmodules.vtkRenderingCore import (
    vtkColorTransferFunction,
    vtkVolumeProperty,
    vtkVolume
)
from vtkmodules.vtkRenderingVolume import vtkGPUVolumeRayCastMapper
from vtkmodules.vtkCommonDataModel import vtkPiecewiseFunction
from vtkmodules.vtkRenderingCore import (
    vtkPolyDataMapper,
    vtkRenderer
)
from vtkmodules.vtkRenderingLOD import vtkLODActor
from vtkmodules.vtkRenderingAnnotation import vtkScalarBarActor
from vtkmodules.vtkFiltersCore import vtkMarchingCubes
from vtkmodules.vtkFiltersGeometry import vtkGeometryFilter

import numpy as np
import metrics
import json

import logging
logger = logging.getLogger('pctErrorAnalyst[' + __name__ +']')

class VolumeRendering(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.baseAngle = 90
        self.baseFilter = 'ramp'
        self.metric = 'wasserstein'

        self.compareAngle = 101
        self.compareFilter = 'ramp'

        self.camera = None

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.renderWindowInteractor = QVTKRenderWindowInteractor(self)
        layout.addWidget(self.renderWindowInteractor)

        opacityScaleLabel = QLabel('Opacity scale')
        layout.addWidget(opacityScaleLabel)

        self.opacityScaleWidget = QSlider(Qt.Horizontal)
        self.opacityScaleWidget.setMinimum(0)
        self.opacityScaleWidget.setMaximum(100)
        self.opacityScaleWidget.setValue(100)
        self.opacityScaleWidget.valueChanged.connect(self.updateRendering)
        layout.addWidget(self.opacityScaleWidget)

        dataRangeLabel = QLabel('Data range')
        layout.addWidget(dataRangeLabel)

        self.dataRangeSlider = QRangeSlider(Qt.Horizontal)
        self.dataRangeSlider.setMinimum(0)
        self.dataRangeSlider.setMaximum(100)
        self.dataRangeSlider.setValue((0, 100))
        self.dataRangeSlider.valueChanged.connect(self.updateRendering)
        layout.addWidget(self.dataRangeSlider)

        self.lcpCheckbox = QCheckBox('Show LCP')
        self.lcpCheckbox.setChecked(False)
        self.lcpCheckbox.stateChanged.connect(self.onLCPShow)
        layout.addWidget(self.lcpCheckbox)

        self.lcpSlider = QSlider(Qt.Horizontal)
        self.lcpSlider.hide()
        self.lcpSlider.setMinimum(0)
        self.lcpSlider.setMaximum(100)
        self.lcpSlider.setValue(50)
        self.lcpSlider.valueChanged.connect(self.updateRendering)
        layout.addWidget(self.lcpSlider)

        self.renderWindow = self.renderWindowInteractor.GetRenderWindow()

        self.loadData()

        self.renderer = self.createRenderer()
        self.renderWindow.AddRenderer(self.renderer)

        self.renderWindow.SetSize(800,600)
        self.renderWindowInteractor.Initialize()
        self.renderWindowInteractor.Start()

    def loadData(self):
        logger.info('Loading base %s, %d', self.baseFilter, self.baseAngle)
        self.meanBase = np.load('/home/vik/Dokumente/Promotion/pCT/uncertainty-vis/Data/simple_pCT/Reconstruction/3D/RSP_angles{:d}_offset1_spotx130_exact_{:s}.npy'.format(self.baseAngle, self.baseFilter))
        self.varianceBase = np.load('/home/vik/Dokumente/Promotion/pCT/uncertainty-vis/Data/simple_pCT/Variance/Variance_raedler_angles{:d}_offset1_spotx130_exact_{:s}_190_1226.npy'.format(self.baseAngle, self.baseFilter))

        self.meanBase = self.meanBase[:,:,22:110]
        self.varianceBase = self.varianceBase[:,:,22:110]

        logger.info('Loading compare %s, %d', self.compareFilter, self.compareAngle)
        self.meanCompare = np.load('/home/vik/Dokumente/Promotion/pCT/uncertainty-vis/Data/simple_pCT/Reconstruction/3D/RSP_angles{:d}_offset1_spotx130_exact_{:s}.npy'.format(self.compareAngle, self.compareFilter))
        self.varianceCompare = np.load('/home/vik/Dokumente/Promotion/pCT/uncertainty-vis/Data/simple_pCT/Variance/Variance_raedler_angles{:d}_offset1_spotx130_exact_{:s}_190_1226.npy'.format(self.compareAngle, self.compareFilter))

        self.meanCompare = self.meanCompare[:,:,22:110]
        self.varianceCompare = self.varianceCompare[:,:,22:110]

        logger.info('Comparing with %s', self.metric)
        if self.metric == 'wasserstein':
            self.difference = metrics.wasserstein(self.meanBase, self.varianceBase, self.meanCompare, self.varianceCompare)
        elif self.metric == 'kullback-leibler':
            self.difference = metrics.kullback_leibler(self.meanBase, self.varianceBase, self.meanCompare, self.varianceCompare)
        elif self.metric == 'mean':
            self.difference = self.meanBase - self.meanCompare
        elif self.metric == 'variance':
            self.difference = self.varianceBase - self.varianceCompare
        else:
            self.difference = metrics.wasserstein(self.meanBase, self.varianceBase, self.meanCompare, self.varianceCompare)

        differenceOrdered = np.ravel(self.difference, order='F')
        self.differenceString = differenceOrdered.tostring()

    def createRenderer(self):

        renderer = vtkRenderer()

        imageImporter = vtkImageImport()
        imageImporter.CopyImportVoidPointer(self.differenceString, len(self.differenceString))
        imageImporter.SetDataScalarTypeToDouble()
        imageImporter.SetNumberOfScalarComponents(1)
        imageImporter.SetDataExtent(0, self.meanBase.shape[0]-1, 0, self.meanBase.shape[1]-1, 0, self.meanBase.shape[2]-1)
        imageImporter.SetWholeExtent(0, self.meanBase.shape[0]-1, 0, self.meanBase.shape[1]-1, 0, self.meanBase.shape[2]-1)

        dataValueScale = self.dataRangeSlider.value()

        differenceRange = self.difference.max() - self.difference.min()

        minValue = self.difference.min() + differenceRange * dataValueScale[0] / 100.
        maxValue = self.difference.min() + differenceRange * dataValueScale[1] / 100.
        valueRange = maxValue - minValue

        alphaChannelFunc = vtkPiecewiseFunction()
        alphaChannelFunc.AddPoint(minValue, 0.0)
        alphaChannelFunc.AddPoint(maxValue, self.opacityScaleWidget.value()/100.)
        alphaChannelFunc.AddPoint(maxValue + 0.001, 0)

        colorFunc = vtkColorTransferFunction()
        with open('../etc/colormap/nic_CubicL.json') as file:
            colorMap = json.load(file)

            RGBPoints = np.reshape(colorMap[0]['RGBPoints'], (-1,4))
            RGBPoints[:,0] -= RGBPoints[:,0].min()
            RGBPoints[:,0] /= RGBPoints[:,0].max()
            for value, red, green, blue in RGBPoints:
                colorFunc.AddRGBPoint(value * valueRange + minValue, red, green, blue)

        volumeProperty = vtkVolumeProperty()
        volumeProperty.SetColor(colorFunc)
        volumeProperty.SetScalarOpacity(alphaChannelFunc)

        scalarBar = vtkScalarBarActor()
        scalarBar.SetLookupTable(colorFunc)

        volumeMapper = vtkGPUVolumeRayCastMapper()
        volumeMapper.SetInputConnection(imageImporter.GetOutputPort())

        volume = vtkVolume()
        volume.SetMapper(volumeMapper)
        volume.SetProperty(volumeProperty)

        if self.lcpCheckbox.isChecked():
            meanRange = self.meanBase.max() - self.meanBase.min()
            isoValue = self.lcpSlider.value() / 100 * meanRange + self.meanBase.min()

            LCP1 = metrics.lcp(isoValue, self.meanBase, self.varianceBase)

            lcpOrdered = np.ravel(LCP1, order='F')
            lcpString = lcpOrdered.tostring()

            lcpImporter = vtkImageImport()
            lcpImporter.CopyImportVoidPointer(lcpString, len(lcpString))
            lcpImporter.SetDataScalarTypeToDouble()
            lcpImporter.SetNumberOfScalarComponents(1)
            lcpImporter.SetDataExtent(0, self.meanBase.shape[0]-1, 0, self.meanBase.shape[1]-1, 0, self.meanBase.shape[2]-1)
            lcpImporter.SetWholeExtent(0, self.meanBase.shape[0]-1, 0, self.meanBase.shape[1]-1, 0, self.meanBase.shape[2]-1)

            marchingCubes = vtkMarchingCubes()
            marchingCubes.SetInputConnection( lcpImporter.GetOutputPort() )
            marchingCubes.ComputeNormalsOn()
            marchingCubes.SetValue( 0, 0.49 )

            geoVolumeBone = vtkGeometryFilter()
            geoVolumeBone.SetInputConnection( marchingCubes.GetOutputPort() )

            geoBoneMapper = vtkPolyDataMapper()
            geoBoneMapper.SetInputConnection( geoVolumeBone.GetOutputPort() )
            geoBoneMapper.ScalarVisibilityOff()

            actorBone = vtkLODActor()
            actorBone.SetNumberOfCloudPoints( 1000000 )
            actorBone.SetMapper( geoBoneMapper )
            actorBone.GetProperty().SetColor( 1, 1, 1 )
            actorBone.GetProperty().SetOpacity( 1.0 )

            renderer.AddActor(actorBone)


        renderer.AddVolume(volume)
        renderer.AddActor2D(scalarBar)

        if self.camera == None:
            self.camera = renderer.GetActiveCamera()
            renderer.ResetCamera()
        else:
            renderer.SetActiveCamera(self.camera)
            

        renderer.SetBackground(1, 1, 1)

        return renderer

    @pyqtSlot(int, str, str)
    def setBase(self, angle, filter, metric):
        self.baseAngle = angle
        self.baseFilter = filter
        self.metric = metric

        self.loadData()
        self.update()

    @pyqtSlot(int, str)
    def setCompare(self, angle, filter):
        self.compareAngle = angle
        self.compareFilter = filter

        self.loadData()
        self.update()

    @pyqtSlot()
    def updateRendering(self):
        self.update()

    @pyqtSlot()
    def onLCPShow(self):
        if self.lcpCheckbox.isChecked():
            self.lcpSlider.show()
        else:
            self.lcpSlider.hide()

        self.update()

    def update(self):
        super().update()

        self.renderWindow.RemoveRenderer(self.renderer)
        self.renderer = self.createRenderer()
        self.renderWindow.AddRenderer(self.renderer)

        self.renderWindowInteractor.Render()