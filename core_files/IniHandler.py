ini = open('settings.ini', 'r')

def check_if_name_exists(name):
    ini.seek(0)

    for i, line in enumerate(ini):

        if get_name_from_line(i) == name:
            return 1

    return 0

def get_line_string(pos):
    ini.seek(0)
    for i, line in enumerate(ini):
        if i == pos:
            line = line[:-1]
            return line

def get_line_offset(pos, profile=-1):
    # If profile != 1 return a decimal and not a hex
    ini.seek(0)
    for i, line in enumerate(ini):
        if i == pos:
            line = line[:-1]
            offset = line.split(' = ')[1]
            if profile != -1:
                return int(offset)
            return int(offset, 16)

def get_name_line_index(name):
    ini.seek(0)

    search_name = '[' + name + ']' + '\n'
    for i, line in enumerate(ini):
        if line == search_name:
            return i

def get_palette_ptrs(pos):
    ini.seek(0)

    for i, line in enumerate(ini):
        if i == pos:
            line = line[:-1]
            offset = line.split(' = ')[1]
            ptrs = offset.split(", ")
            ptrs[0] = int(ptrs[0], 16)
            ptrs[1] = int(ptrs[1], 16)
            ptrs[2] = int(ptrs[2], 16)
            return ptrs

def check_if_name(pos):
    ini.seek(0)

    for i, line in enumerate(ini):
        if i == pos:
            if (line[0] == '[') and (line[-2] == ']'):
                return 1
            return 0

def get_name_from_line(pos):
    ini.seek(0)

    for i, line in enumerate(ini):
        if i == pos:
            return line[1:-2]

def write_text_end(data):
    with open('settings.ini', 'a+') as current_ini:
        current_ini.write(data)

    global ini
    ini = open('settings.ini', 'r')

def create_profile(profile_name, ow_table_ptrs, original_table_ptrs, original_ow_ptrs, ow_num,
                   palette_table_ptrs, original_pal_table, pal_num, limiter_addr, free_space, rom_base):
    from core_files.core import capitalized_hex

    text = "\n" + "\n"
    text += '[' + profile_name + ']' + '\n' + '\n'
    text += "OW Table Pointers = " + capitalized_hex(ow_table_ptrs) + "\n"
    text += "Original OW Table Pointers = " + capitalized_hex(original_table_ptrs) + "\n"
    text += "Original OW Pointers Address = " + capitalized_hex(original_ow_ptrs) + "\n"
    text += "Original Num of OWs = " + str(ow_num) + "\n" + "\n"
    text += "Palette Table Pointers Address = " + capitalized_hex(
        palette_table_ptrs[0]) + ", " + capitalized_hex(palette_table_ptrs[1]) + ", " + capitalized_hex(
        palette_table_ptrs[2]) + "\n"
    text += "Original Palette Table Address = " + capitalized_hex(original_pal_table) + "\n"
    text += "Original Num of Palettes = " + str(pal_num) + "\n" + "\n"
    text += "OW Limiter Address = " + capitalized_hex(limiter_addr) + "\n" + "\n"
    text += "Free Space Start = " + capitalized_hex(free_space) + "\n"
    text += "Rom Base = " + rom_base + "\n" + "    "

    write_text_end(text)


class ProfileManager:
    rom_names = []
    default_profiles = []
    current_profile = 0

    def init_rom_names(self):
        subfix = ['E', 'I', 'S', 'F', 'D', 'J']
        body = ['BPR', 'BPE', 'AXV', 'AXP', "BPG"]
        self.rom_names = []

        for main in body:
            for sub in subfix:
                self.rom_names.append(main + sub)

        # self.rom_names.append('JPAN')

    def __init__(self, rom_name):
        self.default_profiles = []
        self.current_profile = 0
        self.init_rom_names()

        # self.default_profiles.append(rom_name)
        # Initialize the profiles
        if rom_name[:3] == "BPR":
            self.default_profiles.append("JPAN")

        # Add the user profiles
        ini.seek(0)
        for i, lines in enumerate(ini):

            if check_if_name(i) == 1:
                if not (get_name_from_line(i) in self.rom_names):

                    check_name = get_line_string(i + 14).split(" = ")[1]
                    if check_name[:4] == rom_name[:4]:
                        self.default_profiles.append(get_name_from_line(i))

        ini.seek(0)
