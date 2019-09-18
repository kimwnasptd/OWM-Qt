import os
import core_files.statusbar as sts
import core_files.image_editor as img
import core_files.rom_api as rom
import ui.support_windows as windows

from core_files import core
from PyQt5 import QtWidgets
from PIL import Image

log = sts.get_logger(__name__)


# Menu Functions
def export_ow_image(ui):
    tbl, ow = ui.selected_table, ui.selected_ow
    log.info("Exporting the frames of OW ({}, {})".format(tbl, ow))
    image = ui.sprite_manager.make_image_from_rom(ui.selected_ow,
                                                  ui.selected_table)
    # For the Palette
    addr = ui.root.getOW(tbl, ow).ow_data_addr
    palette_id = core.get_ow_palette_id(addr)
    palette_addr = ui.sprite_manager.get_palette_addr(palette_id)
    sprite_palette = img.create_palette_from_gba(rom.ptr_to_addr(palette_addr))
    image.putpalette(sprite_palette)

    name = '/' + str(ui.selected_table) + '_' + str(ui.selected_ow)
    fn, ext = QtWidgets.QFileDialog.getSaveFileName(
        ui,
        'Export Frames Sheet',
        ui.paths['EXP_FRMS_PATH'] + name,
        "PNG File (*.png);;"
        "BMP File (*.bmp);;"
        "JPEG File (*.jpg)")

    if not fn:
        return
    ui.paths['EXP_FRMS_PATH'] = os.path.dirname(os.path.realpath(fn))

    try:
        image.save(fn)
    except ValueError:
        fn += ext.replace(")", "").split("*")[-1]
        image.save(fn)
    sts.show("Saved "+fn)


def import_frames_sheet(ui):
    dlg = QtWidgets.QFileDialog()
    image_loc, _ = dlg.getOpenFileName(dlg,
                                       'Open Image file',
                                       ui.paths['IMP_FRMS_PATH'],
                                       "PNG Files (*.png);;"
                                       "BMP Files (*.bmp)")
    if not image_loc:
        return
    ui.paths['IMP_FRMS_PATH'] = os.path.dirname(os.path.realpath(image_loc))

    sprite = Image.open(image_loc)

    # Safety measures
    ow = ui.root.getOW(ui.selected_table, ui.selected_ow)
    ow_type = ow.frames.get_type()
    width, height = core.get_frame_dimensions(ow_type)
    frames_num = ow.frames.get_num()

    recom_width = width * frames_num

    if height != sprite.height:
        message = "The height should be {}, yours is {}\
                   \nThis means that your image is of different OW Type."\
            .format(height, sprite.height)
        QtWidgets.QMessageBox.critical(QtWidgets.QMessageBox(),
                                       "File has wrong size",
                                       message)
    elif recom_width != sprite.width:
        message = "Your image has a different number of  frames than the OW\n\
                   1) Check if the type of the OW is correct.\n\
                   2) Check how many frames are in your image"
        QtWidgets.QMessageBox.critical(QtWidgets.QMessageBox(),
                                       "Different number of Frames detected",
                                       message)
    else:
        ui.tree_model.importOWFrames(sprite,
                                     ui.selected_ow,
                                     ui.selected_table,
                                     ui)
        sts.show("Imported {} for Table[{}] : OW[{}]".format(image_loc,
                                                             ui.selected_table,
                                                             ui.selected_ow))


def import_ow_sprsrc(ui):
    dlg = QtWidgets.QFileDialog()
    image_loc, _ = dlg.getOpenFileName(dlg,
                                       'Open Image file',
                                       ui.paths['OW_PATH'],
                                       "PNG Files (*.png);;"
                                       "BMP Files (*.bmp)")
    if not image_loc:
        return
    ui.paths['OW_PATH'] = os.path.dirname(os.path.realpath(image_loc))

    sprite = Image.open(image_loc)

    # Safety measures
    if (sprite.width != 96) or (sprite.height != 128):
        message = "The size should be 96x128, yours is {}x{}".format(
            sprite.width, sprite.height)
        QtWidgets.QMessageBox.critical(QtWidgets.QMessageBox(),
                                       "File has wrong size",
                                       message)
    else:
        ui.tree_model.importOWSpr(sprite,
                                  ui.selected_ow,
                                  ui.selected_table,
                                  ui)
        sts.show("Imported {} for Table[{}] : OW[{}]".format(
            image_loc, ui.selected_table, ui.selected_ow))


def import_pokemon_sprsrc(ui):
    dlg = QtWidgets.QFileDialog()
    image_loc, _ = dlg.getOpenFileName(dlg,
                                       'Open Image file',
                                       ui.paths['PKMN_PATH'],
                                       "PNG Files (*.png);;"
                                       "BMP Files (*.bmp)")
    if not image_loc:
        return
    ui.paths['PKMN_PATH'] = os.path.dirname(os.path.realpath(image_loc))

    sprite = Image.open(image_loc)

    # Safety measures
    if (sprite.width != 64) or (sprite.height != 128):
        message = "The size should be 64x128, yours is {}x{}".format(
            sprite.width, sprite.height)
        QtWidgets.QMessageBox.critical(QtWidgets.QMessageBox(),
                                       "File has wrong size",
                                       message)
    else:
        ui.tree_model.importPokeSpr(sprite,
                                    ui.selected_ow,
                                    ui.selected_table,
                                    ui)
        sts.show("Imported {} for Table[{}] : OW[{}]".format(
            image_loc, ui.selected_table, ui.selected_ow))


def palette_cleanup(ui):
    log.info("Initiating the Palette Table cleanup...")
    ui.tree_model.paletteCleanup(ui)


def remove_table(ui):
    ui.tree_model.removeTable(ui.selected_table, ui)


# Buttons Functions
def addOWButtonFunction(ui):
    owWindow = windows.addOWWindow(ui)
    owWindow.exec()


def insertOWButtonFunction(ui):
    owWindow = windows.insertOWWindow(ui)
    owWindow.exec()


def resizeOWButtonFunction(ui):
    owWindow = windows.resizeOWWindow(ui)
    owWindow.exec()


def removeOWButtonFunction(ui):
    ui.tree_model.removeOWs(ui.selected_ow, ui.selected_table, 1, ui)


def addTableButtonFunction(ui):
    addTable = windows.addTableWindow(ui)
    addTable.exec()
