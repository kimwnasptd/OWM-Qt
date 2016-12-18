import mmap
from core_files.rom_api import *


TemplateList = ['Template1', 'Template2', 'Template3', 'Template4', 'Template5', 'Template6', 'Template7', 'Template8']

Templates = []

frametype1 = [0x0, 0x1, 0x0, 0x0]
frametype2 = [0x0, 0x2, 0x0, 0x0]
frametype3 = [0x80, 0x0, 0x0, 0x0]
frametype4 = [0x0, 0x8, 0x0, 0x0]
frametype5 = [0x0, 0x10, 0x0, 0x0]  # FR only
frametype6 = [0x80, 0x4, 0x0, 0x0]  # Emerald only
frametype7 = [0x80, 0x5, 0x0, 0x0]  # Emerald only
frametype8 = [0x80, 0x7, 0x0, 0x0]  # Emerald only

# DEFINES
OW_Tables_Pointers_Address = 0x0
original_table_pointer_address = 0x0
original_ow_pointers = 0x0
original_ow_data_pointers = 0x0
original_num_of_ows = 0
free_space = 0x0
frames_end = 2176496  # 0x2135F0


# ----------------------Functions------------------------------


def change_core_info(address, original_table_pointer, num_of_ows, ow_pointers, free_space_area, files_path):
    global OW_Tables_Pointers_Address, original_table_pointer_address, original_num_of_ows, original_ow_pointers \
        , free_space
    OW_Tables_Pointers_Address = address
    original_table_pointer_address = original_table_pointer
    original_num_of_ows = num_of_ows
    original_ow_pointers = ow_pointers
    free_space = free_space_area

    global TemplateList

    for i in range(0, 8):
        path = files_path + TemplateList[i]

        temp = open(path, 'r+b')
        template = mmap.mmap(temp.fileno(), 0)
        Templates.append(template)


def is_ow_data(address):
    # Checks various bytes to see if they are the same with the templates
    done = 1
    rom.seek(address)
    if rom.read_byte() != 255:
        done = 0
    if rom.read_byte() != 255:
        done = 0
    rom.seek(address + 32)
    Templates[0].seek(32)
    if rom.read_byte() != Templates[0].read_byte():
        done = 0
    if rom.read_byte() != Templates[0].read_byte():
        done = 0
    if rom.read_byte() != Templates[0].read_byte():
        done = 0
    if rom.read_byte() != Templates[0].read_byte():
        done = 0
    return done


def update_frames_address(num, address, ow_type):
    for i in range(1, num + 1):
        address += get_frame_size(ow_type)
    return address


def get_frame_size(ow_type):
    if ow_type == 1:
        return 256  # 0x100
    if ow_type == 2:
        return 512  # 0x200
    if ow_type == 3:
        return 128  # 0x80
    if ow_type == 4:
        return 2048  # 0x800
    if ow_type == 5:
        return 4096  # 0x1000
    if ow_type == 6:
        return 1152  # 0x480
    if ow_type == 7:
        return 1408  # 0x580
    if ow_type == 8:
        return 1920  # 0x780


def clear_frames(address, frames, size):
    rom.seek(address)

    for i in range(0, frames * size):
        rom.write_byte(0xff)

    for i in range(0, 4):
        rom.write_byte(0xff)


def available_frames_pointer_address(address, num_of_frames):
    rom.seek(address)

    for i in range(1, (num_of_frames * 8) + 1):
        if rom.read_byte() != 0x33:
            return 0
    return 1


def move_data(address_to_copy, address_to_write, num_of_bytes, write_byte=0xff):
    for i in range(1, num_of_bytes + 1):
        # Read the byte to write
        rom.seek(address_to_copy)
        byte = rom.read_byte()

        # Clear the moved byte
        rom.seek(address_to_copy)
        rom.write_byte(write_byte)

        # Write the byte to the address to move
        rom.seek(address_to_write)
        rom.write_byte(byte)
        rom.flush()

        address_to_copy += 1
        address_to_write += 1


def check_frames_end(address):
    global frames_end

    if pointer_to_address(address) == frames_end:
        return 1
    else:
        return 0


def write_frames_end(address):
    global frames_end
    write_pointer(frames_end, address)


def get_frame_dimensions(ow_type):
    if ow_type == 1:
        width = 16
        height = 32
    elif ow_type == 2:
        width = 32
        height = 32
    elif ow_type == 3:
        width = 16
        height = 16
    elif ow_type == 4:
        width = 64
        height = 64
    elif ow_type == 5:
        width = 128
        height = 64
    elif ow_type == 6:
        width = 48
        height = 48
    elif ow_type == 7:
        width = 88
        height = 32
    elif ow_type == 8:
        width = 96
        height = 40

    return width, height


def get_template(ow_type):
    return Templates[ow_type - 1]


def copy_data(address_to_copy_from, address_to_copy_to, num_of_bytes):
    copied_bytes = []
    rom.seek(address_to_copy_from)
    for i in range(0, num_of_bytes):
        # Read the byte to write
        copied_bytes.append(rom.read_byte())

    rom.seek(address_to_copy_to)
    for i in range(0, num_of_bytes):
        rom.write_byte(copied_bytes[i])


def addresses_filter(new_table, ow_data_address, frames_pointers, frames_address):
    if new_table == 0:
        new_table = find_free_space((260 * 4), free_space, 4)  # 3 more for the table's info + 1 for rounding
    else:
        new_table = find_free_space((260 * 4), new_table, 4)

    if ow_data_address == 0:
        ow_data_address = find_free_space((256 * 36) + 4, new_table + 259 * 4, 4)
    else:
        ow_data_address = find_free_space((256 * 36) + 4, ow_data_address, 4)

    if frames_pointers == 0:
        frames_pointers = find_free_space((9 * 8 * 256) + 4, ow_data_address + (256 * 36) + 4, 4)
    else:
        frames_pointers = find_free_space((9 * 8 * 256) + 4, frames_address, 4)

    if frames_address == 0:
        frames_address = find_free_space(10000, frames_pointers + (9 * 8 * 256) + 4, 2)
    else:
        frames_address = find_free_space(10000, frames_address, 2)

    return new_table, ow_data_address, frames_pointers, frames_address


def get_ow_palette_id(address):
    rom.seek(address + 2)
    byte1 = rom.read_byte()
    byte2 = rom.read_byte()

    return (byte2 * 256) + byte1


def write_ow_palette_id(address, palette_id):
    rom.seek(address + 2)
    byte1 = int(palette_id / 256)
    byte2 = int(palette_id % 256)

    rom.write_byte(byte2)
    rom.write_byte(byte1)
    rom.flush()


def item_in_list(item, mylist):
    for it in mylist:
        if it == item:
            return 1
    return 0


def check_frames_pointer(address):
    check1 = check_pointer(address)

    # It checks first the type of the frames from the data next to the pointer
    frame = []

    rom.seek(address + 4)
    for i in range(0, 4):
        frame.append(rom.read_byte())

    if frame == frametype1:
        tp = 1
    elif frame == frametype2:
        tp = 2
    elif frame == frametype3:
        tp = 3
    elif frame == frametype4:
        tp = 4
    elif frame == frametype5:
        tp = 5
    elif frame == frametype6:
        tp = 6
    elif frame == frametype7:
        tp = 7
    elif frame == frametype8:
        tp = 8
    else:
        tp = 0

    if tp != 0:
        tp = 1
    return tp * check1


def get_palette_slot(data_address):
    rom.seek(data_address + 12)
    slot_compressed = rom.read_byte()

    return int(slot_compressed % 16)


def write_palette_slot(data_address, palette_slot):
    rom.seek(data_address + 12)
    byte = rom.read_byte()

    byte1 = int(byte / 16)
    slot = (byte1 * 16) + palette_slot
    rom.seek(data_address + 12)
    rom.write_byte(slot)
    rom.flush()


def capitalized_hex(address):
    string = hex(address)
    string = string.upper()

    string = string[2:]
    string = '0x' + string

    return string


def get_animation_address(ow_data_address):
    data_tuple = [0, 0, 0, 0]
    data_tuple[0] = pointer_to_address(ow_data_address + 0x10)
    data_tuple[1] = pointer_to_address(ow_data_address + 0x14)
    data_tuple[2] = pointer_to_address(ow_data_address + 0x18)
    data_tuple[3] = pointer_to_address(ow_data_address + 0x20)
    return data_tuple


def write_animation_pointer(ow_data_address, data_tuple):
    write_pointer(data_tuple[0], ow_data_address + 0x10)
    write_pointer(data_tuple[1], ow_data_address + 0x14)
    write_pointer(data_tuple[2], ow_data_address + 0x18)
    write_pointer(data_tuple[3], ow_data_address + 0x20)


def get_text_color(ow_data_address):
    rom.seek(ow_data_address + 0xE)
    return rom.read_byte()


def set_text_color(ow_data_address, val):
    rom.seek(ow_data_address + 0xE)
    rom.write_byte(val)


# -----------------Classes--------------------

class FramesPointers:
    frames_pointers_address = 0x0
    frames_address = 0x0
    frames_pointers_address_start = 0x0
    frames_address_start = 0x0

    def __init__(self, frames_pointers_address=0x0, frames_address=0x0, frames_pointers_address_start=0,
                 frames_address_start=0):
        self.frames_pointers_address = frames_pointers_address
        self.frames_address = frames_address
        self.frames_pointers_address_start = frames_pointers_address_start
        self.frames_address_start = frames_address_start

    def add_frames_pointers(self, ow_type, num_of_frames):

        frames_address = self.find_frames_free_space(ow_type, num_of_frames)
        frames_pointers_address = self.find_available_frames_pointers_address(num_of_frames)

        # Write changes to the class' variables
        self.frames_pointers_address = frames_pointers_address
        self.frames_address = frames_address

        # Initialize the actual data of the frames
        fill_with_data(frames_address, num_of_frames * get_frame_size(ow_type), -1)
        # Write the frame_end prefix
        write_pointer(frames_end, frames_address + num_of_frames * get_frame_size(ow_type))

        self.write_frames_pointers(ow_type, num_of_frames)

    def find_frames_free_space(self, ow_type, frames_num, address=0):

        working_address = self.frames_address_start
        if address != 0:
            working_address = address

        frame_size = get_frame_size(ow_type)

        working_address = find_free_space(frame_size * frames_num + 4, working_address, 2)

        return working_address

    def find_available_frames_pointers_address(self, frames_num):
        working_address = self.frames_pointers_address_start

        while 1:
            if available_frames_pointer_address(working_address, frames_num) == 1:
                return working_address
            else:
                working_address += 8

    def write_frames_pointers(self, ow_type, frames_num):

        frame_pointer_address = self.frames_pointers_address
        frame_address = self.frames_address

        frametype = []
        if ow_type == 1:
            frametype = frametype1
        elif ow_type == 2:
            frametype = frametype2
        elif ow_type == 3:
            frametype = frametype3
        elif ow_type == 4:
            frametype = frametype4
        elif ow_type == 5:
            frametype = frametype5
        elif ow_type == 6:
            frametype = frametype6
        elif ow_type == 7:
            frametype = frametype7
        elif ow_type == 8:
            frametype = frametype8

        # Write the frames Pointers
        for i in range(0, frames_num):
            write_pointer(frame_address, frame_pointer_address)

            # Write the prefix according to frametype
            rom.seek(frame_pointer_address + 4)
            for j in frametype:
                rom.write_byte(j)

            frame_pointer_address += 8
            frame_address += get_frame_size(ow_type)
        rom.flush()

    def repoint_frames(self, new_frames_address):

        frames_num = self.get_num()
        ow_type = self.get_type()

        new_address = self.find_frames_free_space(ow_type, frames_num, new_frames_address)

    def get_type(self):
        # It checks first the type of the frames from the data next to the pointer
        frame = []

        rom.seek(self.frames_pointers_address + 4)
        for i in range(0, 4):
            frame.append(rom.read_byte())

        tp = -1
        if frame == frametype1:
            tp = 1
        elif frame == frametype2:
            tp = 2
        elif frame == frametype3:
            tp = 3
        elif frame == frametype4:
            tp = 4
        elif frame == frametype5:
            tp = 5
        elif frame == frametype6:
            tp = 6
        elif frame == frametype7:
            tp = 7
        elif frame == frametype8:
            tp = 8

        return tp

    def get_num(self):

        ow_type = self.get_type()
        size = get_frame_size(ow_type)

        # Reads the total number of bytes
        address = self.frames_address
        i = 0
        while check_frames_end(address) != 1:
            i += 1
            address += 1

        # Then it divides that number with the size to get the num of frames
        return int(i / size)

    def clear(self):
        ow_type = self.get_type()
        frames_num = self.get_num()

        # Clear the pointers address
        fill_with_data(self.frames_pointers_address, frames_num * 8, 51)  # 0x33

        # Clear the actual data of the frames
        clear_frames(self.frames_address, frames_num, get_frame_size(ow_type))


class OWData:
    ow_pointer_address = 0x0
    ow_data_address = 0x0
    ow_data_address_start = 0x0
    frames = FramesPointers()

    def __init__(self, ow_data_address, pointer_address, ow_data_address_start):
        self.ow_data_address = ow_data_address
        self.ow_pointer_address = pointer_address
        self.ow_data_address_start = ow_data_address_start

    def add_ow_data(self, ow_type, frames_pointers_address):
        # Type 1: The hero, Type 2: Hero Bike, Type 3: Lil girl
        template = get_template(ow_type)

        ow_data_address = self.find_available_ow_data_address()
        self.ow_data_address = ow_data_address

        rom.seek(ow_data_address)
        template.seek(0)
        for i in range(1, 37):
            rom.write_byte(template.read_byte())

        # Write the pointer to the frames
        write_pointer(frames_pointers_address, ow_data_address + 28)

    def find_available_ow_data_address(self):

        working_address = self.ow_data_address_start

        while 1:
            if is_ow_data(working_address) == 0:
                return working_address
            else:
                working_address += 36

    def clear(self):
        self.frames.clear()
        fill_with_data(self.ow_data_address, 36, 34)  # 0x22 = 34

    def remove(self):
        # Clear itself
        self.clear()
        # Clear the ow_pointer
        fill_with_data(self.ow_pointer_address, 4, 34)  # 0x22

    def move_left(self):

        # Move the OW Data left
        move_data(self.ow_data_address, self.ow_data_address - 36, 36, 34)  # 0x22

        # Change the ow_pointer to point to the new address
        write_pointer(self.ow_data_address - 36, self.ow_pointer_address)

        # Move the OW Pointer left
        move_data(self.ow_pointer_address, self.ow_pointer_address - 4, 4, 34)  # 0x22

    def move_right(self):

        # Move the OW Data right
        move_data(self.ow_data_address, self.ow_data_address + 36, 36, 34)  # 0x22

        # Change the ow_pointer to point to the new address
        write_pointer(self.ow_data_address + 36, self.ow_pointer_address)

        # Move the OW Pointer right
        move_data(self.ow_pointer_address, self.ow_pointer_address + 4, 4, 34)  # 0x22


class OWPointerTable:
    table_pointer_address = 0
    table_address = 0x0
    ow_data_pointers = []

    ow_data_pointers_address = 0x0
    frames_pointers_address = 0x0
    frames_address = 0x0
    end_of_table = 0x0

    def __init__(self, table_pointer_address, table_address, ow_data_address, frames_pointers, frames_address):
        self.table_pointer_address = table_pointer_address
        self.table_address = table_address
        self.ow_data_pointers_address = ow_data_address
        self.frames_pointers_address = frames_pointers
        self.frames_address = frames_address
        self.ow_data_pointers = []
        self.end_of_table = table_address + (256 * 4)

        check_address = self.table_address
        while 1:
            if check_pointer(check_address) == 1:
                # Checks if its the end of the table
                if check_address == self.end_of_table:
                    break

                # There is an OW pointer
                self.ow_data_pointers.append(self.ow_initializer(check_address))
                check_address += 4
            else:
                break

        # Check if the table was there
        rom.seek(self.table_address)
        # Checks if the table was already there
        if pointer_to_address(self.table_address) == 0xffffff:
            rom.seek(self.table_address)

            # fill with bytes
            for i in range(0, 256 * 4):
                rom.write_byte(0x11)
            # Write the table's info
            write_pointer(self.ow_data_pointers_address, self.end_of_table)
            write_pointer(self.frames_pointers_address, self.end_of_table + 4)
            write_pointer(self.frames_address, self.end_of_table + 8)
            rom.flush()

            # Fill with bytes the OW Data Table
            rom.seek(self.ow_data_pointers_address)
            for i in range(0, 256 * 36):
                rom.write_byte(0x22)  # 0x22

            # Fill with bytes the Frames Pointers Table
            rom.seek(self.frames_pointers_address)
            for i in range(0, 256 * 8 * 10):
                rom.write_byte(0x33)  # 0x33

    def ow_initializer(self, ow_pointer):
        ow_data_address = pointer_to_address(ow_pointer)
        frames_pointers_address = pointer_to_address(ow_data_address + 28)
        frames_address = pointer_to_address(frames_pointers_address)

        # Create the Frames OBJ
        FramesOBJ = FramesPointers(frames_pointers_address, frames_address, self.frames_pointers_address,
                                   self.frames_address)

        # Create the OW Data OBJ
        OWDataOBJ = OWData(ow_data_address, ow_pointer, self.ow_data_pointers_address)
        OWDataOBJ.frames = FramesOBJ

        return OWDataOBJ

    def find_available_ow_pointer(self):
        working_address = self.table_address

        while 1:
            if check_pointer(working_address) == 0:
                return working_address
            else:
                working_address += 4

    def re_initialize_ow(self):
        # Re-initialize the ow_pointers
        self.ow_data_pointers = []

        check_address = self.table_address
        while 1:
            if check_pointer(check_address) == 1:
                # Checks if its the end of the table
                if check_address == self.end_of_table:
                    break
                # There is an OW pointer
                self.ow_data_pointers.append(self.ow_initializer(check_address))
                check_address += 4
            else:
                break

    def add_ow(self, ow_type, num_of_frames):

        # First create the frames
        FramesOBJ = FramesPointers(0, 0, self.frames_pointers_address, self.frames_address)
        FramesOBJ.add_frames_pointers(ow_type, num_of_frames)

        # Create OW Data
        ow_data_pointer = self.find_available_ow_pointer()

        OWDataOBJ = OWData(0, ow_data_pointer, self.ow_data_pointers_address)
        OWDataOBJ.add_ow_data(ow_type, FramesOBJ.frames_pointers_address)
        OWDataOBJ.frames = FramesOBJ

        # Write the OW Pointer in the Table
        write_pointer(OWDataOBJ.ow_data_address, ow_data_pointer)

        # Re-initialise the ow pointers
        self.re_initialize_ow()

    def remove_ow(self, ow_id):
        length = self.ow_data_pointers.__len__()

        # Removes the data of the OW and changes all the pointers
        self.ow_data_pointers[ow_id].remove()

        for i in range(ow_id, length):
            # Without that if statement it would try to move_left the ow_data_pointers[length]
            if i != length - 1:
                self.ow_data_pointers[i + 1].move_left()

        # Re-initialize the ow_pointers
        self.re_initialize_ow()

    def insert_ow(self, pos, ow_type, num_of_frames):
        # Get number of OWs
        l = self.ow_data_pointers.__len__()

        # Move the data and the pointers of all the OWs to the right
        for i in range(l - 1, pos - 1, -1):
            self.ow_data_pointers[i].move_right()

        # Insert the new OW
        self.add_ow(ow_type, num_of_frames)

        # Re-initialize the ow_pointers
        self.re_initialize_ow()

    def resize_ow(self, pos, ow_type, num_of_frames):
        # Get animation pointer
        animation_pointer = get_animation_address(self.ow_data_pointers[pos].ow_data_address)

        self.ow_data_pointers[pos].remove()
        self.add_ow(ow_type, num_of_frames)

        write_animation_pointer(self.ow_data_pointers[pos].ow_data_address, animation_pointer)

        # Re-initialise the ow pointers
        self.re_initialize_ow()


class Root:
    ow_tables_address = 0x0
    tables_list = []

    def __init__(self):

        self.tables_list = []
        self.ow_tables_address = OW_Tables_Pointers_Address
        address = self.ow_tables_address

        # Don't initialize in case a rom is not loaded
        if rom.rom_contents is None:
            return

        while 1:
            if check_pointer(address) == 1:

                if (pointer_to_address(address) == 0x39FFB0) or (pointer_to_address(address) == 0x39FEB0):
                    # Those addresses are after the original table but not needed according to JPAN
                    fill_with_data(address, 8, 0)
                    break
                elif pointer_to_address(address) == original_ow_pointers:
                    self.repoint_original_table()
                else:
                    table_pointer_address = address
                    table_address = pointer_to_address(address)
                    end_of_table = table_address + (256 * 4)
                    ow_data_address = pointer_to_address(end_of_table)
                    frames_pointers = pointer_to_address(end_of_table + 4)
                    frames_address = pointer_to_address(end_of_table + 8)
                    self.tables_list.append(
                            OWPointerTable(table_pointer_address, table_address, ow_data_address, frames_pointers,
                                           frames_address))

                address += 4
            else:
                break

    def custom_table_import(self, new_table, ow_data_address, frames_pointers, frames_address):

        self.import_OW_Table(*addresses_filter(new_table, ow_data_address, frames_pointers, frames_address))

    def clear_OW_Tables(self, ow_table_address=OW_Tables_Pointers_Address):
        # Clear all the table entries after the original OW Table
        ow_table_address += 4
        for i in range(ow_table_address, ow_table_address + 25):
            rom.seek(i)
            rom.write_byte(0)
        # Clear all the entries in the tables_list
        # by re-initializing
        self.tables_list = []
        self.__init__()

    def import_OW_Table(self, new_table, ow_data_address, frames_pointers, frames_address, ):
        # Imports a new OW Table
        write_address = self.ow_tables_address

        while 1:
            if check_pointer(write_address) == 0:
                # No pointer in the write_address
                write_pointer(new_table, write_address)
                # Make changes to the tables_list
                self.tables_list.append(
                        OWPointerTable(write_address,
                                       *addresses_filter(new_table, ow_data_address, frames_pointers, frames_address)))
                break
            else:
                write_address += 4

    def remove_table(self, i):
        n = self.tables_list[i].ow_data_pointers.__len__()

        for j in range(0, n):
            self.tables_list[i].ow_data_pointers[j].remove()

        # Clear all of the godam data
        fill_with_data(self.tables_list[i].frames_pointers_address, 256 * 8 * 10, 255)
        fill_with_data(self.tables_list[i].ow_data_pointers_address, 256 * 36, 255)
        fill_with_data(self.tables_list[i].table_address, 259 * 4, 255)

        # Move all the table pointers to the left
        address = self.ow_tables_address + (i * 4)
        fill_with_data(address, 4, 0)

        address += 4
        while pointer_to_address(address) != 0 and check_pointer(address) == 1:
            move_data(address, address - 4, 4, 0)

        # Re-initialise the entire root
        self.__init__()

    def get_table_num(self):
        return self.tables_list.__len__()

    def repoint_original_table(self):

        repointed_table = OWPointerTable(OW_Tables_Pointers_Address, *addresses_filter(0, 0, 0, 0))
        write_pointer(repointed_table.table_address, OW_Tables_Pointers_Address)
        write_pointer(repointed_table.table_address, original_table_pointer_address)
        self.tables_list.append(repointed_table)

        # Find the Frames Pointers for each OW
        frames_pointers = []
        for pointer in range(original_ow_pointers, original_ow_pointers + (4 * original_num_of_ows), 4):
            data_pointer = pointer_to_address(pointer)
            frames_pointers.append(pointer_to_address(data_pointer + 28))

        # Create a list with the num of frames for each OW
        frames = []
        for i in range(0, original_num_of_ows):
            check_address = frames_pointers[i] + 8
            frames_num = 1

            while 1:
                if (item_in_list(check_address, frames_pointers) == 1) or (check_frames_pointer(check_address) == 0):
                    break

                frames_num += 1
                check_address += 8

            frames.append(frames_num)

        # Create the list with all the animation addresses
        animation_addresses = []
        for pointer in range(original_ow_pointers, original_ow_pointers + (4 * original_num_of_ows), 4):
            data_pointer = pointer_to_address(pointer)
            animation_addresses.append(get_animation_address(data_pointer))

        # Text Color Bytes
        text_bytes = []
        for pointer in range(original_ow_pointers, original_ow_pointers + (4 * original_num_of_ows), 4):
            data_pointer = pointer_to_address(pointer)
            text_bytes.append(get_text_color(data_pointer))

        # Find the Type of each OW
        types = []
        for frames_pointers_address in frames_pointers:
            FramesAssistant = FramesPointers(frames_pointers_address)
            types.append(FramesAssistant.get_type())

        # Get the palette of each OW
        palettes = []
        for pointer in range(original_ow_pointers, original_ow_pointers + (4 * original_num_of_ows), 4):
            data_pointer = pointer_to_address(pointer)
            palettes.append(get_ow_palette_id(data_pointer))

        # Get the palette slot for each OW
        slots = []
        for pointer in range(original_ow_pointers, original_ow_pointers + (4 * original_num_of_ows), 4):
            data_pointer = pointer_to_address(pointer)
            slots.append(get_palette_slot(data_pointer))

        for i in range(0, original_num_of_ows):
            repointed_table.add_ow(types[i], frames[i])
            write_ow_palette_id(repointed_table.ow_data_pointers[-1].ow_data_address, palettes[i])
            write_palette_slot(repointed_table.ow_data_pointers[-1].ow_data_address, slots[i])
            write_animation_pointer(repointed_table.ow_data_pointers[-1].ow_data_address, animation_addresses[i])
            set_text_color(repointed_table.ow_data_pointers[-1].ow_data_address, text_bytes[i])

            # Copy the actual frames
            for j in range(0, frames[i]):
                copy_data(pointer_to_address(frames_pointers[i] + (j * 8)),
                          repointed_table.ow_data_pointers[-1].frames.frames_address + (j * get_frame_size(types[i])),
                          get_frame_size(types[i]))

        # 'Fix' for the Emerald/Ruby
        if frames.__len__() >= 200:
            for i in range(0, 256 - frames.__len__()):
                repointed_table.add_ow(1, 9)

        # Clean the data of the original table
        i = 0
        for ow_pointer in range(original_ow_pointers, original_ow_pointers + (4 * original_num_of_ows), 4):

            data_pointer = pointer_to_address(ow_pointer)
            fill_with_data(ow_pointer, 4, 255)

            ow_frames_pointers = pointer_to_address(data_pointer + 28)
            fill_with_data(data_pointer, 36, 255)

            for k in range(0, frames[i]):

                if ow_frames_pointers != 0xFFFFFF:
                    if check_frames_pointer(ow_frames_pointers) == 1:
                        frame_address = pointer_to_address(ow_frames_pointers)
                        fill_with_data(frame_address, get_frame_size(types[i]), 255)

                        fill_with_data(ow_frames_pointers, 8, 255)
                        ow_frames_pointers += 8

            i += 1

    def get_num_of_available_table_pointers(self):

        check_address = self.ow_tables_address

        while check_pointer(check_address) == 1:
            check_address += 4

        i = 0
        done = 0
        while done == 0:
            adder = 0
            rom.seek(check_address)
            for j in range(0, 4):
                adder += rom.read_byte()

            if adder != 0:
                done = 1
            else:
                check_address += 4
                i += 1
        return i

