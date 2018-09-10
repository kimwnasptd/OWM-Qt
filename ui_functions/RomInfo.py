from core_files.ImageEditor import *
from core_files.IniHandler import *
from core_files.rom_api import *
from PyQt5 import QtWidgets

class RomInfo:
    name = ""
    original_ow_ptrs_addr = 0x0
    ow_table_ptr = 0x0
    palette_table_ptr_addr = []
    path = ''
    free_space = 0x0
    rom_successfully_loaded = 0

    Profiler = ProfileManager("")

    def __init__(self):

        self.set_name()

        if check_if_name_exists(self.name) == 1:
            self.rom_successfully_loaded = 1

            self.set_info(get_name_line_index(self.name))
            self.Profiler = ProfileManager(self.name)

            # Initialize the OW Table Info
            change_core_info(self.ow_table_ptr, self.path)
            # Initialize the palette table info
            change_image_editor_info(self.palette_table_ptr_addr)

    def set_name(self):
        name_raw = get_word(0xAC)
        rom_name = capitalized_hex(name_raw)[2:]  # Removes the 0x
        self.name = hex_to_text(rom_name)

        # Checks if Rom uses JPAN's Engine
        if ptr_to_addr(0x160EE0) == 0x1A2000:
            self.name = "JPAN"

    def set_info(self, start_pos):
        self.ow_table_ptr = get_line_offset(start_pos + 1)
        self.palette_table_ptr_addr = get_palette_ptrs(start_pos + 2)
        self.path = 'Files/' + self.name + "/"

    def load_profile_data(self, profile):
        self.set_info(get_name_line_index(profile))
        self.Profiler = ProfileManager(self.name)

        # Initialize the OW Table Info
        change_core_info(self.ow_table_ptr, self.path)
        # Initialize the palette table info
        change_image_editor_info(self.palette_table_ptr_addr)
