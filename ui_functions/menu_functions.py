from core_files.ImageEditor import *
from PyQt5 import QtWidgets, QtCore
import sys


def exit_app():
    sys.exit()


def export_ow_image(ui):
    image = make_image_from_rom(ui.selected_ow, ui.selected_table)

    # For the Palette
    palette_id = get_ow_palette_id(root.tables_list[ui.selected_table].ow_data_pointers[ui.selected_ow].ow_data_address)
    palette_address = ui.sprite_manager.get_palette_address(palette_id)
    sprite_palette = create_palette_from_gba(pointer_to_address(palette_address))

    image.putpalette(sprite_palette)

    name = '/' + str(ui.selected_table) + '_' + str(ui.selected_ow)

    fn, ext = QtWidgets.QFileDialog.getSaveFileName(ui, 'Export Frames Sheet',
                                                  QtCore.QDir.homePath() + name,
                                                  "PNG File (*.png);;All files (*)")

    if not fn:
        return
    fn += ext.split(" ")[2][2:-1]
    image.save(fn)


