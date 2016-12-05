from PyQt5 import QtGui, QtWidgets
import sys


def exit_app():
    sys.exit()


def open_file():
    dlg = QtWidgets.QFileDialog()
    path = dlg.getOpenFileName(None, "Open ROM", '', "GBA Rom files (*.gba)")

    print(path)