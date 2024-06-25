from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSlot

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
    vtkRenderer
)

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

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.renderWindowInteractor = QVTKRenderWindowInteractor(self)
        layout.addWidget(self.renderWindowInteractor)

        self.renderWindow = self.renderWindowInteractor.GetRenderWindow()

        self.renderer = self.createRenderer()
        self.renderWindow.AddRenderer(self.renderer)

        self.renderWindowInteractor.Initialize()
        self.renderWindowInteractor.Start()

    def createRenderer(self):

        renderer = vtkRenderer()

        logger.info('Loading base %s, %d', self.baseFilter, self.baseAngle)
        meanBase = np.load('/home/vik/Dokumente/Promotion/pCT/uncertainty-vis/Data/simple_pCT/Reconstruction/3D/RSP_angles{:d}_offset1_spotx130_exact_{:s}.npy'.format(self.baseAngle, self.baseFilter))
        varianceBase = np.load('/home/vik/Dokumente/Promotion/pCT/uncertainty-vis/Data/simple_pCT/Variance/Variance_raedler_angles{:d}_offset1_spotx130_exact_{:s}_190_1226.npy'.format(self.baseAngle, self.baseFilter))

        logger.info('Loading compare %s, %d', self.compareFilter, self.compareAngle)
        meanCompare = np.load('/home/vik/Dokumente/Promotion/pCT/uncertainty-vis/Data/simple_pCT/Reconstruction/3D/RSP_angles{:d}_offset1_spotx130_exact_{:s}.npy'.format(self.compareAngle, self.compareFilter))
        varianceCompare = np.load('/home/vik/Dokumente/Promotion/pCT/uncertainty-vis/Data/simple_pCT/Variance/Variance_raedler_angles{:d}_offset1_spotx130_exact_{:s}_190_1226.npy'.format(self.compareAngle, self.compareFilter))

        logger.info('Comparing with %s', self.metric)
        if self.metric == 'wasserstein':
            difference = metrics.wasserstein(meanBase, varianceBase, meanCompare, varianceCompare)
        elif self.metric == 'kullback-leibler':
            difference = metrics.kullback_leibler(meanBase, varianceBase, meanCompare, varianceCompare)
        else:
            difference = metrics.wasserstein(meanBase, varianceBase, meanCompare, varianceCompare)

        differenceOrdered = np.ravel(difference, order='F')
        differenceString = differenceOrdered.tostring()

        imageImporter = vtkImageImport()
        imageImporter.CopyImportVoidPointer(differenceString, len(differenceString))
        imageImporter.SetDataScalarTypeToDouble()
        imageImporter.SetNumberOfScalarComponents(1)
        imageImporter.SetDataExtent(0, meanBase.shape[0]-1, 0, meanBase.shape[1]-1, 0, meanBase.shape[2]-1)
        imageImporter.SetWholeExtent(0, meanBase.shape[0]-1, 0, meanBase.shape[1]-1, 0, meanBase.shape[2]-1)

        alphaChannelFunc = vtkPiecewiseFunction()
        alphaChannelFunc.AddPoint(difference.min(), 0.0)
        alphaChannelFunc.AddPoint(difference.max(), 1.0)

        minValue = difference.min()
        valueRange = difference.max() - minValue

        colorFunc = vtkColorTransferFunction()
        with open('../etc/colormap/nic_CubicL.json') as file:
            colorMap = json.load(file)

            RGBPoints = np.reshape(colorMap[0]['RGBPoints'], (-1,4))
            RGBPoints[:,0] -= RGBPoints[:,0].min()
            RGBPoints[:,0] /= RGBPoints[:,0].max()
            for value, red, green, blue in RGBPoints:
                colorFunc.AddRGBPoint(value * valueRange + minValue, red, green, blue)
            else:
                colorFunc.AddRGBPoint(difference.min(), 0.0, 0.0, 0.0)
                colorFunc.AddRGBPoint(difference.max(), 0.0, 0.0, 1.0)

        volumeProperty = vtkVolumeProperty()
        volumeProperty.SetColor(colorFunc)
        volumeProperty.SetScalarOpacity(alphaChannelFunc)

        volumeMapper = vtkGPUVolumeRayCastMapper()
        volumeMapper.SetInputConnection(imageImporter.GetOutputPort())

        volume = vtkVolume()
        volume.SetMapper(volumeMapper)
        volume.SetProperty(volumeProperty)

        renderer.AddVolume(volume)

        renderer.SetBackground(1, 1, 1)

        return renderer


    @pyqtSlot(int, str, str)
    def setBase(self, angle, filter, metric):
        self.baseAngle = angle
        self.baseFilter = filter
        self.metric = metric

        self.update()

    @pyqtSlot(int, str)
    def setCompare(self, angle, filter):
        self.compareAngle = angle
        self.compareFilter = filter

        self.update()

    def update(self):
        super().update()

        self.renderWindow.RemoveRenderer(self.renderer)
        self.renderer = self.createRenderer()
        self.renderWindow.AddRenderer(self.renderer)

        self.renderWindowInteractor.Render()