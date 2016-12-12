from ui_functions.mainWindow import *

if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)

    window = MyApp()
    window.show()
    sys.exit(app.exec())