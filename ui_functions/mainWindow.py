#!/usr/bin/env python3

from ui_functions import menu_buttons_functions
from ui_functions.graphics_class import ImageItem
from ui_functions.ui_updater import *
from ui_functions.supportWindows import *

# the root is defined in ImageEditor.py
# the rom is defined in the rom_api.py

base, form = uic.loadUiType("ui/mainwindow.ui")


class MyApp(base, form):
    def __init__(self, parent=None):
        super(base, self).__init__(parent)
        self.setupUi(self)

        # Variables
        self.sprite_manager = None
        self.rom_info = None
        self.selected_ow = None
        self.selected_table = None

        # TreeView
        self.treeRootNode = Node("root")
        self.tree_model = TreeViewModel(self.treeRootNode)
        self.OWTreeView.setModel(self.tree_model)
        self.tree_selection_model = self.OWTreeView.selectionModel()

        # Graphics Viewer
        self.ow_graphics_scene = QtWidgets.QGraphicsScene()

        # SpinBox
        self.framesSpinBox.valueChanged.connect(self.spinbox_changed)

        # ComboBoxes
        self.paletteIDComboBox.currentIndexChanged.connect(self.palette_id_changed)

        # Buttons
        self.addOwButton.clicked.connect(lambda: menu_buttons_functions.addOWButtonFunction(self))
        self.insertOwButton.clicked.connect(lambda: menu_buttons_functions.insertOWButtonFunction(self))
        self.resizeOwButton.clicked.connect(lambda: menu_buttons_functions.resizeOWButtonFunction(self))
        self.removeOwButton.clicked.connect(lambda: menu_buttons_functions.removeOWButtonFunction(self))

        # Menu
        self.actionOpen_ROM.triggered.connect(lambda: self.open_rom())
        self.actionSave_ROM.triggered.connect(lambda: self.save_rom(rom.rom_path))
        self.actionSave_ROM_As.triggered.connect(lambda: self.save_rom_as())
        self.actionExit_2.triggered.connect(menu_buttons_functions.exit_app)

        self.actionImport_Frames_Sheet.triggered.connect(lambda: menu_buttons_functions.import_frames_sheet(self))
        self.actionExport_Frames_Sheet.triggered.connect(lambda: menu_buttons_functions.export_ow_image(self))
        self.actionImport_OW.triggered.connect(lambda: menu_buttons_functions.import_ow_sprsrc(self))
        self.actionImport_Pokemon.triggered.connect(lambda: menu_buttons_functions.import_pokemon_sprsrc(self))
        self.actionPaletteCleanup.triggered.connect(lambda: menu_buttons_functions.palette_cleanup(self))

        # micro patches, fix the header sizes
        self.OWTreeView.resizeColumnToContents(1)
        self.OWTreeView.resizeColumnToContents(2)

    def open_rom(self, fn=None):
        """ If no filename is given, it'll prompt the user with a nice dialog """
        if fn is None:
            dlg = QtWidgets.QFileDialog()
            fn, _ = dlg.getOpenFileName(dlg, 'Open ROM file', QtCore.QDir.homePath(), "GBA ROM (*.gba)")
        if not fn:
            return

        rom.load_rom(fn)

        self.rom_info = RomInfo()
        rom.rom_path = fn

        if self.rom_info.rom_successfully_loaded == 1:

            self.statusbar.showMessage("Repointing OWs...")
            root.__init__()
            self.sprite_manager = ImageManager()

            self.rom_info = RomInfo()

            self.treeRootNode = Node("root")
            self.tree_model = TreeViewModel(self.treeRootNode)

            self.OWTreeView.setModel(self.tree_model)
            self.statusbar.showMessage("Ready")

            # Reset the selection model
            self.tree_selection_model = self.OWTreeView.selectionModel()
            self.tree_selection_model.currentChanged.connect(self.item_selected)

            self.selected_table = None
            self.selected_ow = None
            update_gui(self)
            self.initColorTextComboBox()
            self.initPaletteIdComboBox()

    def save_rom(self, fn=rom.rom_path):
        ''' The file might have changed while we were editing, so
                we reload it and apply the modifications to it. '''
        self.statusbar.showMessage("Saving...")
        if not rom.rom_file_name:
            QtWidgets.QMessageBox.critical(self, "ERROR!", "No ROM loaded!")
            return
        try:
            with open(rom.rom_file_name, "rb") as rom_file:
                actual_rom_contents = bytearray(rom_file.read())
        except FileNotFoundError:
            with open(rom.rom_file_name, "wb") as rom_file:
                rom_file.write(rom.rom_contents)
            return

        self.statusbar.showMessage("Saving... Writing...")

        for i in range(len(rom.rom_contents)):
            if rom.rom_contents[i] != rom.original_rom_contents[i]:
                actual_rom_contents[i] = rom.rom_contents[i]

        with open(fn, "wb+") as rom_file:
            rom_file.write(actual_rom_contents)

        # The new original rom contents are the edited contents
        rom.original_rom_contents = rom.rom_contents
        self.statusbar.showMessage("Saved {}".format(rom.rom_file_name))

    def save_rom_as(self):
        if not rom.rom_file_name:
            QtWidgets.QMessageBox.critical(self, "ERROR!", "No ROM loaded!")
            return

        fn, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save ROM file',
                                                      QtCore.QDir.homePath(),
                                                      "GBA ROM (*.gba);;"
                                                      "All files (*)")

        if not fn:
            self.statusbar.showMessage("Cancelled...")
            return

        fn += ".gba"
        import shutil
        shutil.copyfile(rom.rom_file_name, fn)
        rom.rom_file_name = fn
        self.save_rom(rom.rom_file_name)

    def paint_graphics_view(self, image):
        # Print an Image obj on the Graphics View

        self.ow_graphics_scene = QtWidgets.QGraphicsScene()
        self.owGraphicsView.setScene(self.ow_graphics_scene)

        if image is not None:
            image_to_draw = ImageItem(image)
            self.ow_graphics_scene.addItem(image_to_draw)
            self.ow_graphics_scene.update()

    def spinbox_changed(self, i):

        if self.selected_ow is None:
            self.framesSpinBox.setValue(0)
            return

        self.paint_graphics_view(self.sprite_manager.get_ow_frame(self.selected_ow, self.selected_table, i))

    def palette_id_changed(self, val):
        palette_id = self.paletteIDComboBox.itemText(val)
        # When the palette combobox gets cleared and the first item is added, the currentIndex changes
        combobox_gets_initialized = self.paletteIDComboBox.count() == 0 or self.paletteIDComboBox.count() == 1

        if palette_id != "" \
                and self.selected_ow is not None \
                and self.selected_table is not None \
                and not combobox_gets_initialized:
            palette_id = int(palette_id, 16)
            ow_data_address = root.tables_list[self.selected_table].ow_data_pointers[self.selected_ow].ow_data_address
            write_ow_palette_id(ow_data_address, palette_id)
            self.tree_model.initOW(self.selected_table, self.selected_ow)

        update_viewer(self)

    def item_selected(self, index):
        node = index.internalPointer()

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

    def initColorTextComboBox(self):
        # Text color ComboBox
        if self.rom_info.name[:3] == 'BPR':
            self.textColorComboBox.setEnabled(True)
            colors_list = ['Black', 'Blue', 'Red']
            self.textColorComboBox.clear()
            self.textColorComboBox.addItems(colors_list)

    def initPaletteIdComboBox(self):

        self.paletteIDComboBox.setEnabled(True)
        # Create the list with the palette IDs
        id_list = []
        self.paletteIDComboBox.clear()
        for pal_id in self.sprite_manager.used_palettes:
            id_list.append(capitalized_hex(pal_id))
            self.paletteIDComboBox.addItem(id_list[-1])




