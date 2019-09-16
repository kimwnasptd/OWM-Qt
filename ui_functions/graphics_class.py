from PyQt5 import QtWidgets, QtGui, QtCore
from PIL.ImageQt import ImageQt


class ImageItem(QtWidgets.QGraphicsObject):

    def __init__(self, image):
        super(ImageItem, self).__init__()

        # image = Image()
        image = image.resize((image.width * 2, image.height * 2))
        self.pixmap = QtGui.QPixmap.fromImage(ImageQt(image))

    def boundingRect(self):
        return QtCore.QRectF(self.pixmap.rect())

    def paint(self, painter, option, widget):
        painter.drawPixmap(QtCore.QPoint(0, 0), self.pixmap)
