from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QComboBox
from PyQt5.QtCore import Qt

import numpy as np
import scipy

import matplotlib
matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.colorbar import Colorbar
from matplotlib.gridspec import GridSpec

import logging
logger = logging.getLogger('pctErrorAnalyst[' + __name__ +']')

class OverviewWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.generateData()

        fig = self.createFigure()
        self.overview = FigureCanvasQTAgg(fig)

        self.layout.addWidget(self.overview)
        self.layout.addWidget(self.generateBaseSelection())


    def generateData(self, metric='wasserstein', baseIdx=[0,0]):
        availableFilters = ['ramp', 'cosine', 'hamming', 'hann', 'shepp-logan']
        availableAngles = [int( 180 * angle / 16) for angle in np.arange(8, 17)]

        meanBase = np.load('/home/vik/Dokumente/Promotion/pCT/uncertainty-vis/Data/simple_pCT/Reconstruction/3D/RSP_angles{:d}_offset1_spotx130_exact_{:s}.npy'.format(availableAngles[baseIdx[1]], availableFilters[baseIdx[0]]))
        varianceBase = np.load('/home/vik/Dokumente/Promotion/pCT/uncertainty-vis/Data/simple_pCT/Variance/Variance_raedler_angles{:d}_offset1_spotx130_exact_{:s}_190_1226.npy'.format(availableAngles[baseIdx[1]], availableFilters[baseIdx[0]]))

        self.data = np.zeros((5,9))
        for idx,filter in enumerate(availableFilters):
            for jdx,angle in enumerate(availableAngles):
                if baseIdx[0] == idx and baseIdx[1] == jdx:
                    continue

                logger.info('Processing {:s}, {:d}'.format(filter, angle))

                mean = np.load('/home/vik/Dokumente/Promotion/pCT/uncertainty-vis/Data/simple_pCT/Reconstruction/3D/RSP_angles{:d}_offset1_spotx130_exact_{:s}.npy'.format(angle, filter))
                variance = np.load('/home/vik/Dokumente/Promotion/pCT/uncertainty-vis/Data/simple_pCT/Variance/Variance_raedler_angles{:d}_offset1_spotx130_exact_{:s}_190_1226.npy'.format(angle, filter))

                if metric == 'wasserstein':
                    self.data[idx, jdx] = self.wasserstein_matrix(meanBase.flatten(), varianceBase.flatten(), mean.flatten(), variance.flatten())

    
    def createFigure(self):
        fig = Figure(figsize=(6, 4), dpi=100)
        gs = GridSpec(2, 1, height_ratios=[0.1, 0.9])
        self.axes = fig.add_subplot(gs[1,0])

        img = self.axes.imshow(self.data)
        self.axes.set_xticks(np.arange(9))
        self.axes.set_xticklabels(['{:d}'.format(int( 180 * angle / 16)) for angle in np.arange(8, 17)])

        self.axes.set_yticks(np.arange(5))
        self.axes.set_yticklabels(['ramp', 'cosine', 'hamming', 'hann', 'shepp-logan'])

        self.caxes = fig.add_subplot(gs[0,0])
        self.cbar = Colorbar(self.caxes, img, orientation='horizontal', ticklocation='top', label=r'$W_2$')

        return fig

    
    def generateBaseSelection(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        title = QLabel('Base:')
        layout.addWidget(title)

        self.filterSelection = QComboBox()
        self.filterSelection.addItem('ramp')
        self.filterSelection.addItem('cosine')
        self.filterSelection.addItem('hamming')
        self.filterSelection.addItem('hann')
        self.filterSelection.addItem('shepp-logan')
        layout.addWidget(self.filterSelection)
        self.filterSelection.currentIndexChanged.connect(self.baseChanged)

        self.angleSelection = QComboBox()
        for angle in np.linspace(90, 180, 9, True):
            self.angleSelection.addItem('{:d}°'.format(int(angle)))
        layout.addWidget(self.angleSelection)
        self.angleSelection.currentIndexChanged.connect(self.baseChanged)

        layout.addStretch()

        title = QLabel('Metric:')
        layout.addWidget(title)

        self.metricSelection = QComboBox()
        self.metricSelection.addItem('Wasserstein')
        self.metricSelection.addItem('Kullback-Leibler')
        self.metricSelection.addItem('Total-Variation')
        self.metricSelection.addItem('contrast to noise')
        layout.addWidget(self.metricSelection)
        self.metricSelection.currentIndexChanged.connect(self.baseChanged)

        return widget
    
    def baseChanged(self, newIndex):
        metricIdx = self.metricSelection.currentIndex()
        availableMetrics = ['wasserstein', 'kullback-leibler', 'total-variation', 'contrast-to-noise']
        metric = availableMetrics[metricIdx]

        newBase = [
            self.filterSelection.currentIndex(),
            self.angleSelection.currentIndex()
        ]
        logger.info('Base changed: {:d},{:d} with {:s}.'.format(newBase[0], newBase[1], metric))
        self.generateData(metric=metric, baseIdx=newBase)
        fig = self.createFigure()
        self.overview.figure = fig
        self.overview.draw()
        self.update()

    
    def wasserstein_matrix(self, mu1, var1, mu2, var2):
        #print( np.trace( var1 ), np.trace( var2 ), np.trace(- 2 * np.transpose( np.transpose(var2) @ var1 @ np.transpose(var2) ) ) )
        return np.sqrt(
            np.linalg.norm( mu1.flatten() - mu2.flatten() )**2 + np.sum(
                var1 + var2 - 2 * np.sqrt( var2 * var1  )
            )
        )
