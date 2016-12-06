from PyQt5 import QtWidgets, uic
from ui_functions.treeViewClasses import *
from ui_functions import menu_functions
from core_files import game
from core_files.IniHandler import *
from core_files.ImageEditor import *


class RomInfo:
    name = ""
    palette_table_address = 0x0
    original_ow_table_pointer = 0x0
    original_ow_pointers_address = 0x0
    ow_table_pointer = 0x0
    palette_table_pointer_address = []
    original_num_of_ows = 0x0
    original_num_of_palettes = 0x0
    original_palette_table_address = 0x0
    ow_fix_address = 0x0
    free_space = 0x0
    path = ''
    rom_base = ''
    rom_successfully_loaded = 0

    Profiler = ProfileManager("")

    def __init__(self):

        self.set_name()

        if check_if_name_exists(self.name) == 1:
            self.rom_successfully_loaded = 1

            self.set_info(get_name_line_index(self.name))
            self.Profiler = ProfileManager(self.name)

            # Initialize the OW Table Info
            change_core_info(self.ow_table_pointer, self.original_ow_table_pointer,
                             self.original_num_of_ows, self.original_ow_pointers_address, self.free_space, self.path)

            # Initialize the palette table info
            change_image_editor_info(self.palette_table_pointer_address, self.original_num_of_palettes,
                                     self.original_palette_table_address, self.free_space)

        else:
            message = "Your ROM's base name in 0xAC is [" + self.name + "]." + "\n"
            message += "There is no Profile with such a name in the INI." + '\n'
            message += "Please create a Custom Profile in the INI with that name and the appropriate addresses \n"
            QtWidgets.QMessageBox.critical(QtWidgets.QMessageBox(), "Can't load Profile from INI", message)

    def set_name(self):

        name_raw = get_word(0xAC)
        rom_name = capitalized_hex(name_raw)[2:]  # Removes the 0x
        self.name = hex_to_text(rom_name)

        # Checks if Rom uses JPAN's Engine
        if pointer_to_address(0x160EE0) == 0x1A2000:
            self.name = "JPAN"

        # Change the name if MrDS
        if self.name == "MrDS":
            self.name = "BPRE"

    def set_info(self, start_pos):

        self.ow_table_pointer = get_line_offset(start_pos + 2)
        self.original_ow_table_pointer = get_line_offset(start_pos + 3)
        self.original_ow_pointers_address = get_line_offset(start_pos + 4)
        self.original_num_of_ows = get_line_offset(start_pos + 5, 1)

        self.palette_table_pointer_address = get_palette_pointers(start_pos + 7)
        self.palette_table_address = pointer_to_address(self.palette_table_pointer_address[0])
        self.original_palette_table_address = get_line_offset(start_pos + 8)
        self.original_num_of_palettes = get_line_offset(start_pos + 9, 1)

        self.ow_fix_address = get_line_offset(start_pos + 11)

        self.free_space = get_line_offset(start_pos + 13)
        self.rom_base = get_line_string(start_pos + 14).split(" = ")[1]

        self.path = 'Files/' + self.rom_base + "/"

    def ow_fix(self):
        # Makes sure more OWs can be added
        if self.ow_fix_address != 0:
            rom.seek(self.ow_fix_address)
            rom.write_byte(255)
            rom.flush()

            message = "Changed byte in " + capitalized_hex(self.ow_fix_address) + " to 0xFF"
            QtWidgets.QMessageBox.critical(QtWidgets.QMessageBox(), "Completed!", message)

        else:
            message = "The OW Fix Address is set to 0x000000. To apply the fix provide \n"
            message += "the address of the OW Limiter"
            QtWidgets.QMessageBox.critical(QtWidgets.QMessageBox(), "Can't load Profile from INI", message)


'''

    def load_from_profile(self, profile):

        self.set_info(get_name_line_index(profile))

        # Initialize the OW Table Info
        change_core_info(self.ow_table_pointer, self.original_ow_table_pointer,
                         self.original_num_of_ows, self.original_ow_pointers_address, self.free_space, self.path)

        # Initialize the palette table info
        change_image_editor_info(self.palette_table_pointer_address, self.original_num_of_palettes,
                                 self.original_palette_table_address, self.free_space)

        global root, SpriteManager
        root = Root()
        SpriteManager = ImageManager()

        change_core_root(root)
        change_image_root(root)

        global app, working_ow, working_table
        app.OWs.delete(0, "end")
        app.OWList.delete(0, "end")
        app.PaletteCleanup['state'] = 'enabled'

        if root.get_table_num() != 0:
            working_table = 0
        else:
            working_table = -1
        working_ow = -1

        Update_OW_Table_Lists(app)

        Update_OW_Menu_Buttons(0)
        Update_OW_Info(0)
        Update_Table_Info(0)
        Update_Palette_Info(0)
        Update_Table_Menu_Buttons(0)
        Update_Menu_Buttons()

        if root.get_num_of_available_table_pointers() != 0:
            app.Insert_Table_Button['state'] = 'enabled'

'''

base, form = uic.loadUiType("ui/mainwindow.ui")


class MyApp(base, form):
    def __init__(self, parent=None):
        super(base, self).__init__(parent)
        self.setupUi(self)

        # Variables
        self.rom = game.Game()
        self.root = None
        self.sprite_manager = None
        self.rom_info = None

        rootNode = Node("Root")
        childNode0 = TransformNode("Table 0", rootNode)
        childNode1 = Node("Overworld 0", childNode0)
        childNode2 = CameraNode("Table 1", rootNode)
        childNode3 = Node("Overworld 0", childNode2)
        childNode4 = Node("Overworld 1", childNode2)
        childNode5 = LightNode("Overworld 2", childNode2)

        model = TreeViewModel(rootNode)
        self.OWTreeView.setModel(model)

        self.actionOpen_ROM.triggered.connect(lambda: self.open_rom(None, self))
        self.actionSave_ROM.triggered.connect(lambda: self.save_rom(self))
        self.actionExit_2.triggered.connect(menu_functions.exit_app)

    def open_rom(self, fn=None, ui=None):
        """ If no filename is given, it'll prompt the user with a nice dialog """
        if fn is None:
            dlg = QtWidgets.QFileDialog()
            fn, _ = dlg.getOpenFileName(dlg, 'Open ROM file', QtCore.QDir.homePath(), "GBA ROM (*.gba)")
        if not fn:
            return

        self.rom.load_rom(fn)

        change_core_rom(self.rom)
        change_image_rom(self.rom)

        self.rom_info = RomInfo()
        self.rom.rom_path = fn

        if self.rom_info.rom_successfully_loaded == 1:

            ui.statusbar.showMessage("Repointing OWs...")
            self.root = Root()
            self.sprite_manager = ImageManager()
            ui.statusbar.showMessage("Ready")

            change_core_root(self.root)
            change_image_root(self.root)

    def save_rom(self, app=None):
        ''' The file might have changed while we were editing, so
                we reload it and apply the modifications to it. '''
        app.statusbar.showMessage("Saving...")
        if not self.rom.rom_file_name:
            QtWidgets.QMessageBox.critical(self, "ERROR!", "No ROM loaded!")
            return
        try:
            with open(self.rom.rom_file_name, "rb") as rom_file:
                actual_rom_contents = bytearray(rom_file.read())
        except FileNotFoundError:
            with open(self.rom.rom_file_name, "wb") as rom_file:
                rom_file.write(self.rom.rom_contents)
            return

        app.statusbar.showMessage("Saving... Writing...")
        if self.rom.rom_contents == self.rom.original_rom_contents:
            self.statusbar.showMessage("Nothing to save")
            return

        for i in range(len(self.rom.rom_contents)):
            if self.rom.rom_contents[i] != self.rom.original_rom_contents[i]:
                actual_rom_contents[i] = self.rom.rom_contents[i]

        with open(self.rom.rom_file_name, "wb") as rom_file:
            rom_file.write(actual_rom_contents)

        # The new original rom contents are the edited contents
        self.rom.original_rom_contents = self.rom.rom_contents
        app.statusbar.showMessage("Saved {}".format(self.rom.rom_file_name))


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)

    window = MyApp()
    window.show()
    sys.exit(app.exec())
