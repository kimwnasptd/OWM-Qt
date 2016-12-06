ini = open('settings.ini', 'r')


def check_if_name_exists(name):
    ini.seek(0)

    for i, line in enumerate(ini):

        if get_name_from_line(i) == name:
            return 1

    return 0


def hex_to_text(convert):
    with open('Files/Table.txt') as f:
        lines = f.read().splitlines()
    for i in range(0, len(lines)):
        lines[i] = lines[i].split('=')

    result = ""

    while convert != '':
        char = convert[:2]
        convert = convert[2:]

        for element in lines:
            if element[0] == char:
                result += (element[1])
    return result


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


def get_palette_pointers(pos):
    ini.seek(0)

    for i, line in enumerate(ini):
        if i == pos:
            line = line[:-1]
            offset = line.split(' = ')[1]
            pointers = offset.split(", ")
            pointers[0] = int(pointers[0], 16)
            pointers[1] = int(pointers[1], 16)
            pointers[2] = int(pointers[2], 16)
            return pointers


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

        self.rom_names.append('JPAN')

    def __init__(self, rom_name):
        self.default_profiles = []
        self.current_profile = 0
        self.init_rom_names()

        self.default_profiles.append(rom_name)
        # Initialize the profiles
        if rom_name == 'JPAN':
            self.current_profile = 1
            self.default_profiles.append(rom_name)
            rom_name = "BPRE"
            self.default_profiles[0] = rom_name

        # Add the user profiles
        ini.seek(0)
        for i, lines in enumerate(ini):

            if check_if_name(i) == 1:
                if not (get_name_from_line(i) in self.rom_names):

                    check_name = get_line_string(i + 14).split(" = ")[1]
                    if check_name == rom_name:
                        self.default_profiles.append(get_name_from_line(i))

        ini.seek(0)