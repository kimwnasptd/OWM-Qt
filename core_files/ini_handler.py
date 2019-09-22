from . import conversions as conv
from . import statusbar as sts

log = sts.get_logger(__name__)

ini = None
try:
    ini = open('settings.ini', 'r')
except FileNotFoundError:
    log.info("Creating the settings.ini file")
    ini = open('settings.ini', 'w+')


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
            tbl_ptrs = [int(ptr, 16) for ptr in ptrs]
            return tbl_ptrs


def get_reserved_regions(profile_pos):
    '''
    Reads the ROM's profile at given position and returns the list of address
    ranges that should not be used.

    If the field Reserved Regions at profile_pos + 3 does not exist then it
    will return [].
    '''
    ini.seek(0)

    reserved_regions = []
    for i, line in enumerate(ini):
        if i == profile_pos + 3:
            if "Reserved Regions" not in line:
                log.info("Reserved Regions not in the Profile. OWM will "
                         "use the entire ROM's free space")
                break

            ranges = line.strip().split("=")[1].strip().split(", ")
            for rng in ranges:
                start, end = rng.split("-")
                reserved_regions.append(
                    (int(start, 16), int(end, 16))
                )

    return reserved_regions


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

    text += "OW Table Pointers = " + conv.HEX(ow_table_ptrs) + "\n"

    text += "Palette Table Pointers Address = "
    for ptr in palette_table_ptrs[:-1]:
        text += conv.HEX(ptr) + ", "
    text += conv.HEX(palette_table_ptrs[-1]) + "\n"

    text += "Reserved Regions = 0x00000000-0x00000001, 0x00000002-0x00000003\n"
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
