#!/usr/bin/env python

import sys
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QComboBox


from OverviewWidget import OverviewWidget
from VolumeRendering import VolumeRendering

import numpy as np

import logging
logger = logging.getLogger('pctErrorAnalyst[' + __name__ + ']')


class CompareSectionWidget(QWidget):
    compareChanged = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout()
        self.setLayout(layout)

        title = QLabel('Compare to:')
        layout.addWidget(title)

        self.filterSelection = QComboBox()
        self.filterSelection.addItem('ramp')
        self.filterSelection.addItem('cosine')
        self.filterSelection.addItem('hann')
        self.filterSelection.addItem('hamming')
        self.filterSelection.addItem('shepp-logan')
        layout.addWidget(self.filterSelection)
        self.filterSelection.currentIndexChanged.connect(self.onCompareChanged)

        self.angleSelection = QComboBox()
        for angle in np.linspace(90, 180, 9, True):
            self.angleSelection.addItem('{:d}°'.format(int(angle)))
        self.angleSelection.setCurrentIndex(1)
        layout.addWidget(self.angleSelection)
        self.angleSelection.currentIndexChanged.connect(self.onCompareChanged)

    @pyqtSlot(int)
    def onCompareChanged(self, newIndex):
        availableFilters = ['ramp', 'cosine', 'hamming', 'hann', 'shepp-logan']
        availableAngles = [int( 180 * angle / 16) for angle in np.arange(8, 17)]

        filterIdx = self.filterSelection.currentIndex()
        filter = availableFilters[filterIdx]
        angleIdx = self.angleSelection.currentIndex()
        angle = availableAngles[angleIdx]
        self.compareChanged.emit(angle, filter)


def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    app = QApplication(sys.argv)

    window = QMainWindow()

    layout = QVBoxLayout()
    widget = QWidget(window)
    widget.setLayout(layout)

    window.setCentralWidget(widget)

    overview = OverviewWidget()
    layout.addWidget(overview)

    compareWidget = CompareSectionWidget()
    layout.addWidget(compareWidget)

    rendering = QLabel("VTK Rendering", alignment=Qt.AlignCenter)
    layout.addWidget(rendering)

    renderer = VolumeRendering()
    layout.addWidget(renderer)
    overview.baseChanged.connect(renderer.setBase)
    compareWidget.compareChanged.connect(renderer.setCompare)

    window.show()

    return app.exec()

if __name__ == '__main__':
    main()