#!/usr/bin/env python3

import os
import sys
import shutil
import core_files.rom_api as rom

from core_files import statusbar as sts
from core_files import core
from core_files import ini_handler as ini
from core_files import conversions as conv
from core_files import image_editor as img

from core_files.rom_info import RomInfo
from ui import tree_view_classes as model
from ui import menu_buttons_functions
from ui.ui_updater import update_gui, update_viewer
from ui.graphics_class import ImageItem
from ui.support_windows import uic

from PyQt5 import QtWidgets, QtCore

log = sts.get_logger(__name__)
base, form = uic.loadUiType("ui_templates/mainwindow.ui")


class MyApp(base, form):
    def __init__(self, parent=None):
        super(base, self).__init__(parent)
        self.setupUi(self)

        # Variables
        self.sprite_manager = None
        self.rom_info = None
        self.selected_ow = None
        self.selected_table = None
        self.root = core.Root()

        # TreeView
        self.treeRootNode = model.Node("root")
        self.tree_model = model.TreeViewModel(self.treeRootNode, self.root)
        self.OWTreeView.setModel(self.tree_model)
        self.tree_selection_model = self.OWTreeView.selectionModel()
        self.tree_selection_model.currentChanged.connect(self.item_selected)

        # Graphics Viewer
        self.ow_graphics_scene = QtWidgets.QGraphicsScene()

        # SpinBox
        self.framesSpinBox.valueChanged.connect(self.spinbox_changed)

        # ComboBoxes
        self.paletteIDComboBox.currentIndexChanged.connect(
            self.palette_id_changed)
        self.profilesComboBox.currentIndexChanged.connect(
            self.profile_selected)
        self.textColorComboBox.currentIndexChanged.connect(
            self.text_color_changed)
        self.footprintComboBox.currentIndexChanged.connect(
            self.footprint_changed)
        self.paletteSlotComboBox.currentIndexChanged.connect(
            self.palette_slot_changed)

        # Buttons
        self.addOwButton.clicked.connect(
            lambda: menu_buttons_functions.addOWButtonFunction(self))
        self.insertOwButton.clicked.connect(
            lambda: menu_buttons_functions.insertOWButtonFunction(self))
        self.resizeOwButton.clicked.connect(
            lambda: menu_buttons_functions.resizeOWButtonFunction(self))
        self.removeOwButton.clicked.connect(
            lambda: menu_buttons_functions.removeOWButtonFunction(self))
        self.removeTableButton.clicked.connect(
            lambda: menu_buttons_functions.remove_table(self))
        self.addTableButton.clicked.connect(
            lambda: menu_buttons_functions.addTableButtonFunction(self))

        # Menu
        self.actionOpen_ROM.triggered.connect(lambda: self.open_rom())
        self.actionOpen_and_Analyze_ROM.triggered.connect(
            lambda: self.open_analyze())
        self.actionSave_ROM.triggered.connect(
            lambda: self.save_rom(rom.rom.rom_path))
        self.actionSave_ROM_As.triggered.connect(
            lambda: self.save_rom_as())
        self.actionExit_2.triggered.connect(
            lambda: self.exit_app())

        self.actionImport_Frames_Sheet.triggered.connect(
            lambda: menu_buttons_functions.import_frames_sheet(self))
        self.actionExport_Frames_Sheet.triggered.connect(
            lambda: menu_buttons_functions.export_ow_image(self))
        self.actionImport_OW.triggered.connect(
            lambda: menu_buttons_functions.import_ow_sprsrc(self))
        self.actionImport_Pokemon.triggered.connect(
            lambda: menu_buttons_functions.import_pokemon_sprsrc(self))
        self.actionPaletteCleanup.triggered.connect(
            lambda: menu_buttons_functions.palette_cleanup(self))

        # micro patches, fix the header sizes
        self.OWTreeView.resizeColumnToContents(1)
        self.OWTreeView.resizeColumnToContents(2)
        self.initPaths()

        sts.initBar(self.statusbar)

    def open_rom(self, fn=None):
        """
        If no filename is given, it'll prompt the user with a nice dialog
        """
        if fn is None:
            dlg = QtWidgets.QFileDialog()
            fn, _ = dlg.getOpenFileName(dlg,
                                        'Open ROM file',
                                        self.paths['OPEN_ROM_PATH'],
                                        "GBA ROM (*.gba)")
        if not fn:
            return
        self.paths['OPEN_ROM_PATH'] = os.path.dirname(os.path.realpath(fn))

        log.info("Opened a new ROM: " + fn)
        sts.show("Opening ROM: "+fn)
        rom.rom.load_rom(fn)

        self.rom_info = RomInfo()
        rom.rom.rom_path = fn

        if self.rom_info.rom_successfully_loaded == 1:
            self.root.__init__()

            self.sprite_manager = img.ImageManager(self.root)
            self.statusbar.showMessage("Ready")

            self.selected_table = None
            self.selected_ow = None
            self.romNameLabel.setText(rom.rom.rom_path.split('/')[-1])

            update_gui(self)
            self.initColorTextComboBox()
            self.initFootprintComboBox()
            self.initPaletteIdComboBox()
            self.initProfileComboBox()
            self.initPaletteSlotComboBox()
        else:
            self.statusbar.showMessage(
                "Couldn't find a Profile in the INI for \
                your ROM. Open it with 'Open and Analyze\
                ROM'.")

    # ROM IO Functions
    def open_analyze(self):
        dlg = QtWidgets.QFileDialog()
        fn, _ = dlg.getOpenFileName(dlg,
                                    'Open and Analyze ROM file',
                                    self.paths['OPEN_ROM_PATH'],
                                    "GBA ROM (*.gba)")
        if not fn:
            return
        self.paths['OPEN_ROM_PATH'] = os.path.dirname(os.path.realpath(fn))

        log.info("Opened a new ROM: " + fn)
        sts.show("Opening ROM: "+fn)
        rom.rom.load_rom(fn)

        self.rom_info = RomInfo()
        rom.rom.rom_path = fn

        # If a profile with the rom base name exist, create a
        # profile with different name
        name = self.rom_info.name
        if ini.check_if_name_exists(name):
            i = 0
            while ini.check_if_name_exists(name + str(i)):
                i += 1
            name += str(i)
        self.rom_info.name = name

        ini.create_profile(name, *self.find_rom_offsets())

        self.rom_info.set_info(ini.get_name_line_index(name))
        self.create_templates(rom.ptr_to_addr(self.rom_info.ow_table_ptr))
        self.statusbar.showMessage("Analysis Finished!")

        self.load_from_profile(name)
        self.initProfileComboBox()
        self.profilesComboBox.setCurrentIndex(
            self.profilesComboBox.findText(name))
        self.romNameLabel.setText(rom.rom.rom_path.split('/')[-1])

    def find_rom_offsets(self):
        # Find OW Offsets
        self.statusbar.showMessage("Searching for OW Offsets")
        for addr in range(0, rom.rom.rom_size, 4):
            if core.is_jpan_ptr(addr):
                table_ptrs = rom.ptr_to_addr(addr)
                break
            elif core.is_orig_table_ptr(addr):
                table_ptrs = addr

        log.info(conv.HEX(table_ptrs))
        # Find Palette Offsets
        self.statusbar.showMessage("Searching for Palette Offsets")
        for addr in range(0, rom.rom.rom_size, 4):
            # Search for the first Palette Pointer
            if (rom.is_ptr(addr) and
                    img.is_palette_ptr(rom.ptr_to_addr(addr))):
                palette_table = rom.ptr_to_addr(addr)
                palette_table_ptrs = rom.find_ptr_in_rom(palette_table, 3)
                log.info("Found the Palette Table at " + conv.HEX(palette_table))
                break

        return [table_ptrs, palette_table_ptrs]

    def load_from_profile(self, profile):

        if profile != "":
            self.rom_info.load_profile_data(profile)

            # self.rom_info = RomInfo()
            self.statusbar.showMessage("Reloading ROM...")
            self.root.__init__()

            self.statusbar.showMessage("Done")
            self.sprite_manager = img.ImageManager(self.root)

            self.selected_table = None
            self.selected_ow = None

            from ui.ui_updater import update_gui, update_tree_model
            update_tree_model(self)
            update_gui(self)
            self.initColorTextComboBox()
            self.initFootprintComboBox()
            self.initPaletteIdComboBox()
            self.initPaletteSlotComboBox()

    def save_rom(self, fn=rom.rom.rom_path):
        ''' The file might have changed while we were editing, so
                we reload it and apply the modifications to it. '''
        self.statusbar.showMessage("Saving...")
        if not rom.rom.rom_file_name:
            QtWidgets.QMessageBox.critical(self, "ERROR!", "No ROM loaded!")
            return
        try:
            with open(rom.rom.rom_file_name, "rb") as rom_file:
                actual_rom_contents = bytearray(rom_file.read())
        except FileNotFoundError:
            with open(rom.rom.rom_file_name, "wb") as rom_file:
                rom_file.write(rom.rom.rom_contents)
            return

        self.statusbar.showMessage("Saving... Writing...")

        for i in range(len(rom.rom.rom_contents)):
            if rom.rom.rom_contents[i] != rom.rom.original_rom_contents[i]:
                actual_rom_contents[i] = rom.rom.rom_contents[i]

        with open(fn, "wb+") as rom_file:
            rom_file.write(actual_rom_contents)

        self.statusbar.showMessage("Saved {}".format(rom.rom.rom_file_name))
        self.romNameLabel.setText(rom.rom.rom_file_name.split('/')[-1])

    def save_rom_as(self):
        if not rom.rom.rom_file_name:
            QtWidgets.QMessageBox.critical(self, "ERROR!", "No ROM loaded!")
            return

        fn, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save ROM file',
            self.paths['SAVE_ROM_PATH'],
            "GBA ROM (*.gba)")

        if not fn:
            self.statusbar.showMessage("Cancelled...")
            return
        self.paths['SAVE_ROM_PATH'] = os.path.dirname(os.path.realpath(fn))

        if fn[-4:] != ".gba":
            fn += ".gba"

        if os.path.exists(fn):
            os.remove(fn)

        shutil.copyfile(rom.rom.rom_file_name, fn)

        rom.rom.rom_file_name = fn
        rom.rom.rom_path = fn

        self.save_rom(rom.rom.rom_file_name)
        self.romNameLabel.setText(rom.rom.rom_file_name.split('/')[-1])

    def create_templates(self, ow_ptrs_addr):

        rom_base = self.rom_info.name

        if os.path.exists("Files/" + rom_base):
            shutil.rmtree("Files/" + rom_base)

        # Remove the old folder, if it exists
        current_dir = os.getcwd()
        os.chdir("Files")
        os.mkdir(rom_base)
        os.chdir(current_dir)

        # Create the new templates
        templates = []
        for i in range(1, 9):
            templates.append(open("Files/" + rom_base + "/Template" + str(i),
                                  "wb+"))
            os.chmod("Files/" + rom_base + "/Template" + str(i), 0o777)

        # Create Template for Type 1
        rom.rom.seek(rom.ptr_to_addr(ow_ptrs_addr))
        template_bytes = bytearray([rom.rom.read_byte() for i in range(0x24)])
        templates[0].write(template_bytes)

        # Create Template for Type 2
        rom.rom.seek(rom.ptr_to_addr(ow_ptrs_addr + 4))
        template_bytes = bytearray([rom.rom.read_byte() for i in range(0x24)])
        templates[1].write(template_bytes)

        # Create Template for Type 3
        if rom_base[:3] == "BPR" or rom_base[:3] == "BPG":

            rom.rom.seek(rom.ptr_to_addr(ow_ptrs_addr + 16*4))
            template_bytes = bytearray(
                [rom.rom.read_byte() for i in range(0x24)])
            templates[2].write(template_bytes)
        else:
            rom.rom.seek(rom.ptr_to_addr(ow_ptrs_addr + 5 * 4))
            template_bytes = bytearray(
                [rom.rom.read_byte() for i in range(0x24)])
            templates[2].write(template_bytes)

        # Create Template for Type 4
        if rom_base[:3] == "BPR" or rom_base[:3] == "BPG":

            rom.rom.seek(rom.ptr_to_addr(ow_ptrs_addr + 108 * 4))
            template_bytes = bytearray(
                [rom.rom.read_byte() for i in range(0x24)])
            templates[3].write(template_bytes)
        else:
            rom.rom.seek(rom.ptr_to_addr(ow_ptrs_addr + 114 * 4))
            template_bytes = bytearray(
                [rom.rom.read_byte() for i in range(0x24)])
            templates[3].write(template_bytes)

        # Create Template for Type 5 // FR/LG only
        if rom_base[:3] == "BPR" or rom_base[:3] == "BPG":

            rom.rom.seek(rom.ptr_to_addr(ow_ptrs_addr + 151 * 4))
            template_bytes = bytearray(
                [rom.rom.read_byte() for i in range(0x24)])
            templates[4].write(template_bytes)
        else:
            rom.rom.seek(rom.ptr_to_addr(ow_ptrs_addr))
            template_bytes = bytearray(
                [rom.rom.read_byte() for i in range(0x24)])
            templates[4].write(template_bytes)

        # Create Template for Type 6 // EM/Rby/Sap only
        if rom_base[:3] == "BPR" or rom_base[:3] == "BPG":

            rom.rom.seek(rom.ptr_to_addr(ow_ptrs_addr))
            template_bytes = bytearray(
                [rom.rom.read_byte() for i in range(0x24)])
            templates[5].write(template_bytes)
        else:
            rom.rom.seek(rom.ptr_to_addr(ow_ptrs_addr + 94 * 4))
            template_bytes = bytearray(
                [rom.rom.read_byte() for i in range(0x24)])
            templates[5].write(template_bytes)

        # Create Template for Type 7 // EM/Rby/Sap only
        if rom_base[:3] == "BPR" or rom_base[:3] == "BPG":

            rom.rom.seek(rom.ptr_to_addr(ow_ptrs_addr))
            template_bytes = bytearray(
                [rom.rom.read_byte() for i in range(0x24)])
            templates[6].write(template_bytes)
        else:
            rom.rom.seek(rom.ptr_to_addr(ow_ptrs_addr + 141 * 4))
            template_bytes = bytearray(
                [rom.rom.read_byte() for i in range(0x24)])
            templates[6].write(template_bytes)

        # Create Template for Type 8 // EM/Rby/Sap only
        if rom_base[:3] == "BPR" or rom_base[:3] == "BPG":

            rom.rom.seek(rom.ptr_to_addr(ow_ptrs_addr))
            template_bytes = bytearray(
                [rom.rom.read_byte() for i in range(0x24)])
            templates[7].write(template_bytes)
        else:
            rom.rom.seek(rom.ptr_to_addr(ow_ptrs_addr + 140 * 4))
            template_bytes = bytearray(
                [rom.rom.read_byte() for i in range(0x24)])
            templates[7].write(template_bytes)

    def paint_graphics_view(self, image):
        # Print an Image obj on the Graphics View

        self.ow_graphics_scene = QtWidgets.QGraphicsScene()
        self.owGraphicsView.setScene(self.ow_graphics_scene)

        if image is not None:
            image_to_draw = ImageItem(image)
            self.ow_graphics_scene.addItem(image_to_draw)
            self.ow_graphics_scene.update()

    # Status Change Functions
    def spinbox_changed(self, i):

        if self.selected_ow is None:
            self.framesSpinBox.setValue(0)
            return

        image = self.sprite_manager.get_ow_frame(self.selected_ow,
                                                 self.selected_table,
                                                 i)
        self.paint_graphics_view(image)

    def palette_id_changed(self, val):
        palette_id = self.paletteIDComboBox.itemText(val)
        # When the palette combobox gets cleared and the first
        # item is added, the currentIndex changes
        combobox_gets_initialized = self.paletteIDComboBox.count() == 0 or \
            self.paletteIDComboBox.count() == 1

        if palette_id != "" \
                and self.selected_ow is not None \
                and self.selected_table is not None \
                and not combobox_gets_initialized:
            palette_id = int(palette_id, 16)
            log.info("Palette id will be written to " + conv.HEX(palette_id))

            tbl, ow = self.selected_table, self.selected_ow
            ow_data_addr = self.root.getOW(tbl, ow).ow_data_addr
            core.write_ow_palette_id(ow_data_addr, palette_id)
            self.tree_model.initOW(self.selected_table, self.selected_ow)

        update_viewer(self)

    def item_selected(self, index):
        node = index.internalPointer()

        if node is None:
            return

        if node.typeInfo() == "ow_node":
            self.selected_table = node.parent().getId()
            self.selected_ow = node.getId()
            self.paint_graphics_view(node.image)

            # Update the SpinBox
            self.framesSpinBox.setRange(0, node.frames - 1)
            self.framesSpinBox.setValue(0)
        else:
            self.selected_table = node.getId()
            self.selected_ow = None

            self.paint_graphics_view(None)

        update_gui(self)

    def profile_selected(self, val):
        c1 = self.rom_info.rom_successfully_loaded
        c2 = self.profilesComboBox.itemText(val)
        if c1 == 1 and c2 != "---":
            profile = self.profilesComboBox.itemText(val)
            if profile != "":
                self.load_from_profile(profile)

    def text_color_changed(self, byte):
        if self.selected_table is not None and self.selected_ow is not None:
            tbl, ow = self.selected_table, self.selected_ow
            ow_data_addr = self.root.getOW(tbl, ow).ow_data_addr
            core.set_text_color(ow_data_addr, byte)

    def footprint_changed(self, byte):
        if self.selected_table is not None and self.selected_ow is not None:
            tbl, ow = self.selected_table, self.selected_ow
            ow_data_addr = self.root.getOW(tbl, ow).ow_data_addr
            core.set_footprint(ow_data_addr, byte)

    def palette_slot_changed(self, byte):
        if self.selected_table is not None and self.selected_ow is not None:
            tbl, ow = self.selected_table, self.selected_ow
            ow_data_addr = self.root.getOW(tbl, ow).ow_data_addr
            core.write_palette_slot(ow_data_addr, byte)

    # Init Functions
    def initColorTextComboBox(self):
        # Text color ComboBox
        name = self.rom_info.name
        if name[:3] == 'BPR'\
                or name[:4] == 'JPAN'\
                or name[:4] == 'MrDS'\
                or name[:3] == 'BPG':
            self.textColorComboBox.clear()
            self.textColorComboBox.setEnabled(True)
            colors_list = ['Blue', 'Red', 'Black']
            self.textColorComboBox.clear()
            self.textColorComboBox.addItems(colors_list)
        else:
            self.textColorComboBox.setEnabled(False)

    def initFootprintComboBox(self):
        self.footprintComboBox.clear()
        self.footprintComboBox.setEnabled(True)
        steps_list = ['None', 'Steps', 'Bike']
        self.footprintComboBox.clear()
        self.footprintComboBox.addItems(steps_list)

    def initPaletteIdComboBox(self):

        self.paletteIDComboBox.setEnabled(True)
        # Create the list with the palette IDs
        self.paletteIDComboBox.clear()
        for pal_id in self.sprite_manager.used_palettes:
            self.paletteIDComboBox.addItem(conv.HEX(pal_id))

    def initProfileComboBox(self):

        profiles = self.rom_info.Profiler.default_profiles

        self.profilesComboBox.clear()
        self.profilesComboBox.addItem("---")
        self.profilesComboBox.addItems(profiles)
        # +1 because the combobox has one extra item in the beginning
        self.profilesComboBox.setCurrentIndex(
            self.rom_info.Profiler.current_profile + 1)

    def initPaletteSlotComboBox(self):

        items = []
        for i in range(16):
            items.append(conv.capitalized_hex(i))

        self.paletteSlotComboBox.clear()
        self.paletteSlotComboBox.addItems(items)

    def initPaths(self):
        import pickle
        self.paths = {}

        try:
            with open("Files/paths.pkl", 'rb') as f:
                self.paths = pickle.load(f)
        except FileNotFoundError:
            self.paths['OPEN_ROM_PATH'] = QtCore.QDir.homePath()
            self.paths['SAVE_ROM_PATH'] = QtCore.QDir.homePath()
            self.paths['EXP_FRMS_PATH'] = QtCore.QDir.homePath()
            self.paths['IMP_FRMS_PATH'] = QtCore.QDir.homePath()
            self.paths['OW_PATH']       = QtCore.QDir.homePath()
            self.paths['PKMN_PATH']     = QtCore.QDir.homePath()

            with open("Files/paths.pkl", 'wb') as f:
                pickle.dump(self.paths, f)

    def exit_app(self):
        import pickle

        with open("Files/paths.pkl", 'wb') as f:
            pickle.dump(self.paths, f)
        sys.exit()
