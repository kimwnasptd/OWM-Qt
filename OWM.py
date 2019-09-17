#!/usr/bin/env python3
from ui.main_window import MyApp
from PyQt5 import QtWidgets, QtGui

if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon("Files/App.ico"))

    window = MyApp()
    app.aboutToQuit.connect(window.exit_app)
    window.show()

    sys.exit(app.exec())
