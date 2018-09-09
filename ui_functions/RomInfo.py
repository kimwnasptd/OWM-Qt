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
            change_core_info(self.ow_table_ptr, self.free_space, self.path)

            # Initialize the palette table info
            change_image_editor_info(self.palette_table_ptr_addr, self.free_space)

            self.ow_fix()

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
        # Find ROM's Free Space
        SHOW("Searching for Free Space")
        self.free_spc = search_for_free_space(0x100000)
        print('free space: '+HEX(self.free_spc))
        self.path = 'Files/' + self.name + "/"

    def ow_fix(self):
        # Makes sure more OWs can be added
        name = self.name
        if name[:3] == "BPE":
            ow_fix_bytes = [0xEE, 0x29, 0x00, 0xD9, 0x05, 0x21, 0x03, 0x48, 0x89]
        elif name[:3] == "AXV" or name[:3] == "AXP":
            ow_fix_bytes = [0xD9, 0x29, 0x00, 0xD9, 0x05, 0x21, 0x03, 0x48, 0x89]
        else:
            ow_fix_bytes = [0x97, 0x29, 0x00, 0xD9, 0x10, 0x21, 0x03, 0x48, 0x89]

        ow_fix = find_bytes_in_rom(ow_fix_bytes)
        if ow_fix == -1:
            ow_fix_bytes[0] = 0xff # In case the OW Fix was applied
            ow_fix = find_bytes_in_rom(ow_fix_bytes)
        # If still no ow_fix addr, set it to 0x0
        if ow_fix == -1:
            ow_fix = 0x0

        self.ow_fix_addr = ow_fix
        if self.ow_fix_addr != 0:
            rom.seek(self.ow_fix_addr)
            rom.write_byte(0xff)

    def load_profile_data(self, profile):
        self.set_info(get_name_line_index(profile))
        self.Profiler = ProfileManager(self.name)

        # Initialize the OW Table Info
        change_core_info(self.ow_table_ptr, self.free_space, self.path)
        # Initialize the palette table info
        change_image_editor_info(self.palette_table_ptr_addr, self.free_space)
