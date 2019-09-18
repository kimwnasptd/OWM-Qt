#!/usr/bin/env python3
from datetime import datetime as dt
from ui.main_window import MyApp
import core_files.statusbar as sts
from PyQt5 import QtWidgets, QtGui

# sts.init_logger()
log = sts.get_logger("OWM")
log.info("--- Opened OWM ({}) ---".format(dt.now()))

if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon("Files/App.ico"))

    window = MyApp()
    app.aboutToQuit.connect(window.exit_app)
    window.show()

    sys.exit(app.exec())
