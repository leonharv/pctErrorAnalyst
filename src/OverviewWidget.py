from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QComboBox
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot

import numpy as np
import metrics

import matplotlib
matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.colorbar import Colorbar
from matplotlib.gridspec import GridSpec

import logging
logger = logging.getLogger('pctErrorAnalyst[' + __name__ +']')

class OverviewWidget(QWidget):
    baseChanged = pyqtSignal(int, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.availableMetrics = ['wasserstein', 'kullback-leibler']
        self.availableFilters = ['ramp', 'cosine', 'hamming', 'hann', 'shepp-logan']
        self.availableAngles = [int( 180 * angle / 16) for angle in np.arange(8, 17)]

        self.baseAngle = 90
        self.baseFilter = 'ramp'
        self.metric = 'wasserstein'

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.generateData()

        fig = self.createFigure()
        self.overview = FigureCanvasQTAgg(fig)

        self.layout.addWidget(self.overview)
        self.layout.addWidget(self.generateBaseSelection())


    def generateData(self):
        meanBase = np.load('/home/vik/Dokumente/Promotion/pCT/uncertainty-vis/Data/simple_pCT/Reconstruction/3D/RSP_angles{:d}_offset1_spotx130_exact_{:s}.npy'.format(self.baseAngle, self.baseFilter))
        varianceBase = np.load('/home/vik/Dokumente/Promotion/pCT/uncertainty-vis/Data/simple_pCT/Variance/Variance_raedler_angles{:d}_offset1_spotx130_exact_{:s}_190_1226.npy'.format(self.baseAngle, self.baseFilter))

        self.data = np.zeros((5,9))
        for idx,filter in enumerate(self.availableFilters):
            for jdx,angle in enumerate(self.availableAngles):
                if self.baseAngle == angle and self.baseFilter == filter:
                    continue

                logger.info('Processing {:s}, {:d}'.format(filter, angle))

                mean = np.load('/home/vik/Dokumente/Promotion/pCT/uncertainty-vis/Data/simple_pCT/Reconstruction/3D/RSP_angles{:d}_offset1_spotx130_exact_{:s}.npy'.format(angle, filter))
                variance = np.load('/home/vik/Dokumente/Promotion/pCT/uncertainty-vis/Data/simple_pCT/Variance/Variance_raedler_angles{:d}_offset1_spotx130_exact_{:s}_190_1226.npy'.format(angle, filter))

                if self.metric == 'wasserstein':
                    self.data[idx, jdx] = metrics.wasserstein_matrix(meanBase.flatten(), varianceBase.flatten(), mean.flatten(), variance.flatten())
                elif self.metric == 'kullback-leibler':
                    self.data[idx, jdx] = metrics.kullback_leibler_matrix(meanBase.flatten(), varianceBase.flatten(), mean.flatten(), variance.flatten())
                else:
                    self.data[idx, jdx] = metrics.wasserstein_matrix(meanBase.flatten(), varianceBase.flatten(), mean.flatten(), variance.flatten())

    
    def createFigure(self):
        fig = Figure(figsize=(6, 4), dpi=100)
        gs = GridSpec(2, 1, height_ratios=[0.1, 0.9])
        self.axes = fig.add_subplot(gs[1,0])

        img = self.axes.imshow(self.data)
        self.axes.set_xticks(np.arange(9))
        self.axes.set_xticklabels(['{:d}'.format(int( 180 * angle / 16)) for angle in np.arange(8, 17)])
        self.axes.set_xlabel('Number of scans')

        self.axes.set_yticks(np.arange(5))
        self.axes.set_yticklabels(['ramp', 'cosine', 'hamming', 'hann', 'shepp-logan'])
        self.axes.set_ylabel('Filter')

        self.caxes = fig.add_subplot(gs[0,0])
        self.cbar = Colorbar(self.caxes, img, orientation='horizontal', ticklocation='top')

        if self.metric == 'wasserstein':
            self.cbar.set_label(r'$W_2$')
        elif self.metric == 'kullback-leibler':
            self.cbar.set_label(r'$D_{KL}$')
        else:
            self.cbar.set_label(r'$W_2$')

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
        self.filterSelection.currentIndexChanged.connect(self.on_baseChanged)

        self.angleSelection = QComboBox()
        for angle in np.linspace(90, 180, 9, True):
            self.angleSelection.addItem('{:d}°'.format(int(angle)))
        layout.addWidget(self.angleSelection)
        self.angleSelection.currentIndexChanged.connect(self.on_baseChanged)

        layout.addStretch()

        title = QLabel('Metric:')
        layout.addWidget(title)

        self.metricSelection = QComboBox()
        self.metricSelection.addItem('Wasserstein')
        self.metricSelection.addItem('Kullback-Leibler')
        layout.addWidget(self.metricSelection)
        self.metricSelection.currentIndexChanged.connect(self.on_baseChanged)

        return widget
    
    @pyqtSlot(int)
    def on_baseChanged(self, newIndex):
        metricIdx = self.metricSelection.currentIndex()
        self.metric = self.availableMetrics[metricIdx]

        self.baseAngle = self.availableAngles[ self.angleSelection.currentIndex() ]
        self.baseFilter = self.availableFilters[ self.filterSelection.currentIndex() ]

        logger.info('Base changed: {:s},{:d} with {:s}.'.format(self.baseFilter, self.baseAngle, self.metric))
        self.generateData()
        fig = self.createFigure()
        self.overview.figure = fig

        self.baseChanged.emit(self.baseAngle, self.baseFilter, self.metric)

        self.overview.draw()
        self.update()
