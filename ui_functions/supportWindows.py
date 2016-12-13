from PyQt5 import uic, QtGui, QtWidgets

addOWBase, addOWForm = uic.loadUiType("ui/addow.ui")
insertOWBase, insertOWForm = uic.loadUiType("ui/insertow.ui")
resizeOWBase, resizeOWForm = uic.loadUiType("ui/resizeow.ui")


def check_type_availability(ow_type, ui):

    if ui.rom_info.name[:3] == 'BPR' or ui.rom_info.name == 'JPAN' or ui.rom_info.name[:3] == 'BPG':
        if (ow_type >= 1) and (ow_type <= 5):
            return 1
        return 0
    elif ui.rom_info.name[:3] == 'BPE' or ui.rom_info.name[:3] == 'AXV':
        if (ow_type >= 1) and (ow_type <= 8):
            if ow_type != 5:
                return 1
            return 0


class addOWWindow(addOWBase, addOWForm):
    def __init__(self, ui, parent=None):
        super(addOWBase, self).__init__(parent)
        self.setupUi(self)

        self.owTypeLineEdit.setValidator(QtGui.QIntValidator(0, 9))
        self.framesNumLineEdit.setValidator(QtGui.QIntValidator(0, 1000))
        self.owNumLineEdit.setValidator(QtGui.QIntValidator(0, 256))

        self.buttonBox.accepted.connect(lambda: self.addOW(ui))

    def addOW(self, ui):

        ow_type = int(self.owTypeLineEdit.text())
        frames_num = int(self.framesNumLineEdit.text())
        ows_num = int(self.owNumLineEdit.text())

        if check_type_availability(ow_type, ui):

            if ui.tree_model.owsCount(ui.selected_table) + ows_num <= 256:
                ui.tree_model.insertOWs(-1, ui.selected_table, ows_num, ow_type, frames_num)
            else:
                message = "Cant add that number of OWs\nMax number of OWs a table can hold is 256"
                QtWidgets.QMessageBox.critical(QtWidgets.QMessageBox(), "Can't Add so many OWs", message)


class insertOWWindow(insertOWBase, insertOWForm):
    def __init__(self, ui, parent=None):
        super(insertOWBase, self).__init__(parent)
        self.setupUi(self)

        self.owTypeLineEdit.setValidator(QtGui.QIntValidator(1, 9))
        self.framesNumLineEdit.setValidator(QtGui.QIntValidator(1, 1000))
        self.owNumLineEdit.setValidator(QtGui.QIntValidator(1, 256))

        self.buttonBox.accepted.connect(lambda: self.insertOW(ui))

    def insertOW(self, ui):

        ow_type = int(self.owTypeLineEdit.text())
        frames_num = int(self.framesNumLineEdit.text())
        ows_num = int(self.owNumLineEdit.text())

        if check_type_availability(ow_type, ui):

            if ui.tree_model.owsCount(ui.selected_table) + ows_num <= 256:
                if ui.selected_ow is None:
                    ui.tree_model.insertOWs(0, ui.selected_table, ows_num, ow_type, frames_num)
                else:
                    ui.tree_model.insertOWs(ui.selected_ow, ui.selected_table, ows_num, ow_type, frames_num)
            else:
                message = "Cant insert that number of OWs\nMax number of OWs a table can hold is 256"
                QtWidgets.QMessageBox.critical(QtWidgets.QMessageBox(), "Can't Add so many OWs", message)


class resizeOWWindow(resizeOWBase, resizeOWForm):
    def __init__(self, ui, parent=None):
        super(resizeOWBase, self).__init__(parent)
        self.setupUi(self)

        self.owTypeLineEdit.setValidator(QtGui.QIntValidator(1, 9))
        self.framesNumLineEdit.setValidator(QtGui.QIntValidator(1, 1000))

        self.buttonBox.accepted.connect(lambda: self.resizeOW(ui))

    def resizeOW(self, ui):
        ow_type = int(self.owTypeLineEdit.text())
        frames_num = int(self.framesNumLineEdit.text())

        if check_type_availability(ow_type, ui):
            ui.tree_model.resizeOW(ui.selected_ow, ui.selected_table, ow_type, frames_num, ui)
        else:
            message = "Please insert a correct type"
            QtWidgets.QMessageBox.critical(QtWidgets.QMessageBox(), "Can't create OW with Type: " + str(ow_type), message)

