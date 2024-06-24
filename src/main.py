#!/usr/bin/env python

import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QComboBox


from OverviewWidget import OverviewWidget
from VolumeRendering import VolumeRendering

import numpy as np

import logging
logger = logging.getLogger('pctErrorAnalyst[' + __name__ + ']')

def generateCompareSelection():
    widget = QWidget()

    layout = QHBoxLayout()
    widget.setLayout(layout)

    title = QLabel('Compare to:')
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
    angleSelection.setCurrentIndex(1)
    layout.addWidget(angleSelection)

    return widget

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

    layout.addWidget(generateCompareSelection())

    rendering = QLabel("VTK Rendering", alignment=Qt.AlignCenter)
    layout.addWidget(rendering)

    renderer = VolumeRendering()
    layout.addWidget(renderer)

    

    window.show()

    return app.exec()

if __name__ == '__main__':
    main()