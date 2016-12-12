from PyQt5 import uic

addOWBase, addOWForm = uic.loadUiType("ui/addow.ui")


class addOWWindow(addOWBase, addOWForm):
    def __init__(self, parent=None):
        super(addOWBase, self).__init__(parent)
        self.setupUi(self)

