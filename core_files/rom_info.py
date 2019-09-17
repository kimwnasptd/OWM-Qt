import core_files.ini_handler as ini
import core_files.rom_api as rom
import core_files.conversions as conv


class RomInfo:
    name = ""
    original_ow_ptrs_addr = 0x0
    ow_table_ptr = 0x0
    palette_table_ptr_addr = []
    path = ''
    free_space = 0x0
    rom_successfully_loaded = 0

    Profiler = ini.ProfileManager("")

    def __init__(self):

        self.set_name()

        if ini.check_if_name_exists(self.name) == 1:
            self.rom_successfully_loaded = 1

            self.set_info(ini.get_name_line_index(self.name))
            self.Profiler = ini.ProfileManager(self.name)

            # Update the ROM's OW Table Info and Templates
            rom.update_ow_tables_pointers_table(self.ow_table_ptr)
            rom.update_rom_tamplates(self.path)
            # Update the palette table info
            rom.update_palette_table_pointers(self.palette_table_ptr_addr)

    def set_name(self):
        name_raw = rom.get_word(0xAC)
        rom_name = conv.capitalized_hex(name_raw)[2:]  # Removes the 0x
        self.name = conv.hex_to_text(rom_name)

        # Checks if Rom uses JPAN's Engine
        if rom.ptr_to_addr(0x160EE0) == 0x1A2000:
            self.name = "JPAN"

    def set_info(self, start_pos):
        self.ow_table_ptr = ini.get_line_offset(start_pos + 1)
        self.palette_table_ptr_addr = ini.get_palette_ptrs(start_pos + 2)
        self.path = 'Files/' + self.name + "/"

    def load_profile_data(self, profile):
        self.set_info(ini.get_name_line_index(profile))
        self.Profiler = ini.ProfileManager(self.name)

        # Update the ROM's OW Table Info and Templates
        rom.update_ow_tables_pointers_table(self.ow_table_ptr)
        rom.update_rom_tamplates(self.path)
        # Update the palette table info
        rom.update_palette_table_pointers(self.palette_table_ptr_addr)
