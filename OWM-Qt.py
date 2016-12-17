#!/usr/bin/env python3
from ui_functions.mainWindow import *

if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon("Files/App.ico"))

    window = MyApp()
    window.show()
    sys.exit(app.exec())