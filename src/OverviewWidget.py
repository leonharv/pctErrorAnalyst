from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QComboBox
from PyQt5.QtCore import Qt

import numpy as np

import matplotlib
matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.colorbar import Colorbar
from matplotlib.gridspec import GridSpec

class OverviewWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.layout.addWidget(self.getOverview())
        self.layout.addWidget(self.generateBaseSelection())
        

    def getOverview(self):
        self.data = np.arange(45).reshape((5,9))

        fig = Figure(figsize=(6, 4), dpi=100)
        gs = GridSpec(2, 1, height_ratios=[0.1, 0.9])
        self.axes = fig.add_subplot(gs[1,0])

        img = self.axes.imshow(self.data)
        self.axes.set_xticks(np.arange(9))
        self.axes.set_xticklabels(['{:d}°'.format(int(angle)) for angle in np.linspace(90, 180, 9, True)])

        self.axes.set_yticks(np.arange(5))
        self.axes.set_yticklabels(['ramp', 'cosine', 'hann', 'hamming', 'shepp-logan'])

        self.caxes = fig.add_subplot(gs[0,0])
        self.cbar = Colorbar(self.caxes, img, orientation='horizontal', ticklocation='top', label=r'$W_2$')

        return FigureCanvasQTAgg(fig)
    
    def generateBaseSelection(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        title = QLabel('Base:')
        layout.addWidget(title)

        filterSelection = QComboBox()
        filterSelection.addItem('ramp')
        filterSelection.addItem('cosine')
        filterSelection.addItem('hann')
        filterSelection.addItem('hamming')
        filterSelection.addItem('shepp-logan')
        layout.addWidget(filterSelection)

        angleSelection = QComboBox()
        for angle in np.linspace(90, 180, 9, True):
            angleSelection.addItem('{:d}°'.format(int(angle)))
        layout.addWidget(angleSelection)

        layout.addStretch()

        title = QLabel('Metric:')
        layout.addWidget(title)

        metricSelection = QComboBox()
        metricSelection.addItem('Wasserstein')
        metricSelection.addItem('Kullback-Leibler')
        metricSelection.addItem('Total-Variation')
        metricSelection.addItem('contrast to noise')
        layout.addWidget(metricSelection)

        return widget
