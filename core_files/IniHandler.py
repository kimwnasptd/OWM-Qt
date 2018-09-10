from core_files.rom_api import HEX, HEX_LST

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

def create_profile(profile_name, ow_table_ptrs, palette_table_ptrs):
    text = '\n[' + profile_name + ']' + '\n'
    text += "OW Table Pointers = " + HEX(ow_table_ptrs) + "\n"
    text += "Palette Table Pointers Address = "
    text += HEX(palette_table_ptrs[0]) + ", "
    text += HEX(palette_table_ptrs[1]) + ", "
    text += HEX(palette_table_ptrs[2]) + "\n"
    write_text_end(text)


class ProfileManager:
    rom_names = []
    default_profiles = []
    current_profile = 0

    def __init__(self, rom_name):
        self.default_profiles = []
        self.current_profile = 0

        # Add the user profiles
        ini.seek(0)
        for i, lines in enumerate(ini):
            if check_if_name(i):
                check_name = get_name_from_line(i)
                if check_name[:4] == rom_name[:4]:
                    self.default_profiles.append(get_name_from_line(i))

        ini.seek(0)
