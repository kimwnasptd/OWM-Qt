import mmap
from core_files.rom_api import *

TemplateList = ['Template1', 'Template2', 'Template3', 'Template4', 'Template5', 'Template6', 'Template7', 'Template8']

Templates = []

frametype1 = [0x0, 0x1]     # [16x32]
frametype2 = [0x0, 0x2]     # [32x32]
frametype3 = [0x80, 0x0]    # [16x16]
frametype4 = [0x0, 0x8]     # [64x64]
frametype5 = [0x0, 0x10]    # [128x64] FR Only
frametype6 = [0x80, 0x4]    # [48x48] Emerald only
frametype7 = [0x80, 0x5]    # [88x32] Emerald only
frametype8 = [0x80, 0x7]    # [96x40] Emerald only

# DEFINES
TBL_0 = 0x0
FREE_SPC = 0x0
FRAMES_PER_OW = 15
FRAMES_END = 0x2135F0


# ----------------------Functions------------------------------

def change_core_info(ow_tbls_ptrs_tbl, free_space_area, files_path):
    global TBL_0, FREE_SPC
    TBL_0 = ow_tbls_ptrs_tbl
    FREE_SPC = free_space_area

    import os
    if os.path.exists(files_path):
        global TemplateList

        for i in range(0, 8):
            path = files_path + TemplateList[i]

            temp = open(path, 'r+b')
            template = mmap.mmap(temp.fileno(), 0)
            Templates.append(template)

def is_ow_data(addr):
    # Checks various bytes to see if they are the same with the templates
    try:
        rom.seek(addr)

        if rom.read_byte() != 0xFF:
            return 0
        if rom.read_byte() != 0xFF:
            return 0

        # if not rom.check_byte(addr + 0xE, 0x00):
        #     return 0
        # if not rom.check_byte(addr + 0xF, 0x00):
            return 0

        if is_ptr(addr + 0x10) != 1:
            return 0
        # if is_ptr(addr + 0x14) != 1:
            return 0
        if is_ptr(addr + 0x18) != 1:
            return 0
        if is_ptr(addr + 0x1c) != 1:
            return 0
        if is_ptr(addr + 0x20) != 1:
            return 0
    except IndexError:
        return 0
    return 1

def is_table_ptr(addr):
    # Used to check if addr is a ptr to OW Data Pointers Table
    if is_ptr(addr) == 0:
        return 0

    ow_data_ptr = ptr_to_addr(addr)
    if is_ow_data(ptr_to_addr(ow_data_ptr)) == 0:
        return 0

    return 1

def is_ow_data_ptr(addr):
    return is_ptr(addr) and is_ow_data(ptr_to_addr(addr))

def table_needs_repoint(addr):
    ow_ptr = ptr_to_addr(addr)
    end_of_table = ow_ptr + 256 * 4

    if read_word(ptr_to_addr(end_of_table)) == 0x22222222:
        return 0

    if not is_ow_data(ptr_to_addr(end_of_table)):
        return 1

    if not is_ptr(end_of_table + 4):
        return 1

    if read_word(ptr_to_addr(end_of_table + 4)) == 0x33333333:
        return 0

    if not is_frames_ptr(ptr_to_addr(end_of_table + 4)):
        return 1

    return 0

def update_frames_addr(num, addr, ow_type):
    for i in range(1, num + 1):
        addr += get_frame_size(ow_type)
    return addr

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

def clear_frames(addr, frames, size):
    rom.seek(addr)

    for i in range(0, frames * size):
        rom.write_byte(0xff)

    for i in range(0, 4):
        rom.write_byte(0xff)

def available_frames_ptr_addr(addr, num_of_frames):
    rom.seek(addr)

    for i in range(1, (num_of_frames * 8) + 1):
        if rom.read_byte() != 0x33:
            return 0
    return 1

def is_frames_end(addr):
    global FRAMES_END

    if ptr_to_addr(addr) == FRAMES_END:
        return 1
    else:
        return 0

def write_frames_end(addr):
    global FRAMES_END
    write_ptr(FRAMES_END, addr)

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

def get_ow_palette_id(addr):
    rom.seek(addr + 2)
    byte1 = rom.read_byte()
    byte2 = rom.read_byte()

    return (byte2 * 256) + byte1

def addrs_filter(new_table, ow_data_addr, frames_ptrs, frames_addr):
    if new_table == 0:
        new_table = find_free_space((260 * 4), FREE_SPC, 4)  # 3 more for the table's info + 1 for rounding
    else:
        new_table = find_free_space((260 * 4), new_table, 4)

    if ow_data_addr == 0:
        ow_data_addr = find_free_space((256 * 36) + 4, new_table + 259 * 4, 4)
    else:
        ow_data_addr = find_free_space((256 * 36) + 4, ow_data_addr, 4)

    if frames_ptrs == 0:
        frames_ptrs = find_free_space((9 * 8 * 256) + 4, ow_data_addr + (256 * 36) + 4, 4)
    else:
        frames_ptrs = find_free_space((9 * 8 * 256) + 4, frames_addr, 4)

    if frames_addr == 0:
        frames_addr = find_free_space(10000, frames_ptrs + (9 * 8 * 256) + 4, 2)
    else:
        frames_addr = find_free_space(10000, frames_addr, 2)

    return new_table, ow_data_addr, frames_ptrs, frames_addr

def write_ow_palette_id(addr, palette_id):
    rom.seek(addr + 2)
    byte1 = int(palette_id / 256)
    byte2 = int(palette_id % 256)

    rom.write_byte(byte2)
    rom.write_byte(byte1)
    rom.flush()

def is_frames_ptr(addr):
    check1 = is_ptr(addr)

    # It checks first the type of the frames from the data next to the ptr
    frame = []

    rom.seek(addr + 4)
    frame = [rom.read_byte(), rom.read_byte()]

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

def get_palette_slot(data_addr):
    rom.seek(data_addr + 12)
    slot_compressed = rom.read_byte()

    return int(slot_compressed % 16)

def write_palette_slot(data_addr, palette_slot):
    rom.seek(data_addr + 12)
    byte = rom.read_byte()

    byte1 = int(byte / 16)
    slot = (byte1 * 16) + palette_slot
    rom.seek(data_addr + 12)
    rom.write_byte(slot)
    rom.flush()

def get_animation_addr(ow_data_addr):
    data_tuple = [0, 0]
    data_tuple[0] = ptr_to_addr(ow_data_addr + 0x18)
    data_tuple[1] = ptr_to_addr(ow_data_addr + 0x20)
    return data_tuple

def write_animation_ptr(ow_data_addr, data_tuple):
    write_ptr(data_tuple[0], ow_data_addr + 0x18)
    write_ptr(data_tuple[1], ow_data_addr + 0x20)

def get_text_color(ow_data_addr):
    rom.seek(ow_data_addr + 0xE)
    return rom.read_byte()

def set_text_color(ow_data_addr, val):
    rom.seek(ow_data_addr + 0xE)
    rom.write_byte(val)

# -----------------Classes--------------------

class FramesPointers:
    frames_ptrs_addr = 0x0
    frames_addr = 0x0
    frames_ptrs_addr_start = 0x0
    frames_addr_start = 0x0

    def __init__(self, frames_ptrs_addr=0x0, frames_addr=0x0, frames_ptrs_addr_start=0,
                 frames_addr_start=0):
        self.frames_ptrs_addr = frames_ptrs_addr
        self.frames_addr = frames_addr
        self.frames_ptrs_addr_start = frames_ptrs_addr_start
        self.frames_addr_start = frames_addr_start

    def add_frames_ptrs(self, ow_type, num_of_frames):

        frames_addr = self.find_frames_free_space(ow_type, num_of_frames)
        frames_ptrs_addr = self.find_available_frames_ptrs_addr(num_of_frames)
        # print("frames addr: " + capitalized_hex(frames_addr))
        # Write changes to the class' variables
        self.frames_ptrs_addr = frames_ptrs_addr
        self.frames_addr = frames_addr

        # Initialize the actual data of the frames
        fill_with_data(frames_addr, num_of_frames * get_frame_size(ow_type), -1)
        # Write the frame_end prefix
        write_ptr(FRAMES_END, frames_addr + num_of_frames * get_frame_size(ow_type))

        self.write_frames_ptrs(ow_type, num_of_frames)

    def find_frames_free_space(self, ow_type, frames_num, addr=0):

        working_addr = self.frames_addr_start
        if addr != 0:
            working_addr = addr

        frame_size = get_frame_size(ow_type)
        working_addr = find_free_space(frame_size * frames_num + 4, working_addr, 2)
        if not working_addr:
            working_addr = find_free_space(frame_size * frames_num + 4, 0x0, 2)

        return working_addr

    def find_available_frames_ptrs_addr(self, frames_num):
        working_addr = self.frames_ptrs_addr_start

        while 1:
            if available_frames_ptr_addr(working_addr, frames_num) == 1:
                return working_addr
            else:
                working_addr += 8

    def write_frames_ptrs(self, ow_type, frames_num):

        frame_ptr_addr = self.frames_ptrs_addr
        frame_addr = self.frames_addr

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
            write_ptr(frame_addr, frame_ptr_addr)
            write_bytes(frame_ptr_addr + 4, frametype + [0x0, 0x0])

            frame_ptr_addr += 8
            frame_addr += get_frame_size(ow_type)

    def repoint_frames(self, new_frames_addr):

        frames_num = self.get_num()
        ow_type = self.get_type()

        new_addr = self.find_frames_free_space(ow_type, frames_num, new_frames_addr)

    def get_type(self):
        # It checks first the type of the frames from the data next to the ptr
        frame = []

        rom.seek(self.frames_ptrs_addr + 4)
        frame = [rom.read_byte(), rom.read_byte()]

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

        # if tp == -1:
        #     print("get_type: Cant find type for " + HEX_LST(frame))
            # print(HEX_LST(read_bytes(self.frames_ptrs_addr, 8)))
        return tp

    def get_num(self):
        ow_type = self.get_type()
        size = get_frame_size(ow_type)

        # Reads the total number of bytes
        addr = self.frames_addr
        i = 0
        while is_frames_end(addr) != 1:
            i += 1
            addr += size

        return i

    def clear(self):
        ow_type = self.get_type()
        frames_num = self.get_num()

        # Clear the ptrs addr
        fill_with_data(self.frames_ptrs_addr, frames_num * 8, 0x33)

        # Clear the actual data of the frames
        clear_frames(self.frames_addr, frames_num, get_frame_size(ow_type))


class OWData:
    ow_ptr_addr = 0x0
    ow_data_addr = 0x0
    ow_data_addr_start = 0x0
    frames = FramesPointers()

    def __init__(self, ow_data_addr, ptr_addr, ow_data_addr_start):
        self.ow_data_addr = ow_data_addr
        self.ow_ptr_addr = ptr_addr
        self.ow_data_addr_start = ow_data_addr_start

    def add_ow_data(self, ow_type, frames_ptrs_addr):
        # Type 1: The hero, Type 2: Hero Bike, Type 3: Lil girl
        template = get_template(ow_type)

        ow_data_addr = self.find_available_ow_data_addr()
        self.ow_data_addr = ow_data_addr

        rom.seek(ow_data_addr)
        template.seek(0)
        for i in range(1, 37):
            rom.write_byte(template.read_byte())

        # Write the ptr to the frames
        write_ptr(frames_ptrs_addr, ow_data_addr + 0x1c)

    def find_available_ow_data_addr(self):

        working_addr = self.ow_data_addr_start

        while 1:
            if is_ow_data(working_addr) == 0:
                return working_addr
            else:
                working_addr += 0x24

    def clear(self):
        self.frames.clear()
        fill_with_data(self.ow_data_addr, 36, 34)  # 0x22 = 34

    def remove(self):
        # Clear itself
        self.clear()
        # Clear the ow_ptr
        fill_with_data(self.ow_ptr_addr, 4, 34)  # 0x22

    def move_left(self):

        # Move the OW Data left
        move_data(self.ow_data_addr, self.ow_data_addr - 36, 36, 34)  # 0x22

        # Change the ow_ptr to point to the new addr
        write_ptr(self.ow_data_addr - 36, self.ow_ptr_addr)

        # Move the OW Pointer left
        move_data(self.ow_ptr_addr, self.ow_ptr_addr - 4, 4, 34)  # 0x22

    def move_right(self):

        # Move the OW Data right
        move_data(self.ow_data_addr, self.ow_data_addr + 36, 36, 34)  # 0x22

        # Change the ow_ptr to point to the new addr
        write_ptr(self.ow_data_addr + 36, self.ow_ptr_addr)

        # Move the OW Pointer right
        move_data(self.ow_ptr_addr, self.ow_ptr_addr + 4, 4, 34)  # 0x22


class OWPointerTable:
    table_ptr_addr = 0
    table_addr = 0x0
    ow_data_ptrs = []

    ow_data_ptrs_addr = 0x0
    frames_ptrs_addr = 0x0
    frames_addr = 0x0
    end_of_table = 0x0

    def __init__(self, table_ptr_addr, table_addr, ow_data_addr, frames_ptrs, frames_addr):
        self.table_ptr_addr = table_ptr_addr
        self.table_addr = table_addr
        self.ow_data_addr = ow_data_addr
        self.frames_ptrs_addr = frames_ptrs
        self.frames_addr = frames_addr
        self.ow_data_ptrs = []
        self.end_of_table = table_addr + (256 * 4)

        # Checks if the table was already there
        if ptr_to_addr(self.table_addr) == 0xFFFFFF:
            # fill with bytes the OW Data Pointers Table,
            # OW Data Table and Frames Pointers Table(~20 frames/ow)
            fill_with_data(self.table_addr, 256 * 4, 0x11)
            fill_with_data(self.ow_data_addr, 256 * 36, 0x22)
            fill_with_data(self.frames_ptrs_addr, 256 * 8 * FRAMES_PER_OW, 0x33)

            # Write the table's info
            print("\ntbl_init: OW Pointers(WR): "+HEX(self.table_addr))
            print("tbl_init: OW Data(WR): "+HEX(self.ow_data_addr))
            print("tbl_init: Frames Pointers(WR): "+HEX(self.frames_ptrs_addr))
            print("tbl_init: Frames Address(WR): "+HEX(self.frames_addr))
            write_ptr(self.ow_data_addr, self.end_of_table)
            write_ptr(self.frames_ptrs_addr, self.end_of_table + 4)
            write_ptr(self.frames_addr, self.end_of_table + 8)
        else:
            check_addr = self.table_addr
            while is_ptr(check_addr) and check_addr != self.end_of_table:
                # There is an OW ptr
                self.ow_data_ptrs.append(self.ow_initializer(check_addr))
                check_addr += 4

    def ow_initializer(self, ow_ptr):
        ow_data_addr = ptr_to_addr(ow_ptr)
        frames_ptrs_addr = ptr_to_addr(ow_data_addr + 0x1C)
        frames_addr = ptr_to_addr(frames_ptrs_addr)

        # Create the Frames OBJ
        FramesOBJ = FramesPointers(frames_ptrs_addr, frames_addr,
            self.frames_ptrs_addr, self.frames_addr)

        # Create the OW Data OBJ
        OWDataOBJ = OWData(ow_data_addr, ow_ptr, self.ow_data_ptrs_addr)
        OWDataOBJ.frames = FramesOBJ

        return OWDataOBJ

    def find_available_ow_ptr(self):
        working_addr = self.table_addr

        while 1:
            if is_ptr(working_addr) == 0:
                return working_addr
            else:
                working_addr += 4

    def re_initialize_ow(self):
        # Re-initialize the ow_ptrs
        self.ow_data_ptrs = []

        check_addr = self.table_addr
        while 1:
            if is_ptr(check_addr) == 1:
                # Checks if its the end of the table
                if check_addr == self.end_of_table:
                    break
                # There is an OW ptr
                self.ow_data_ptrs.append(self.ow_initializer(check_addr))
                check_addr += 4
            else:
                break

    def add_ow(self, ow_type, num_of_frames):

        # First create the frames
        FramesOBJ = FramesPointers(0, 0, self.frames_ptrs_addr, self.frames_addr)
        FramesOBJ.add_frames_ptrs(ow_type, num_of_frames)

        # Create OW Data
        ow_ptr = self.find_available_ow_ptr()

        OWDataOBJ = OWData(0, ow_ptr, self.ow_data_ptrs_addr)
        OWDataOBJ.add_ow_data(ow_type, FramesOBJ.frames_ptrs_addr)
        OWDataOBJ.frames = FramesOBJ

        # Write the OW Pointer in the Table
        write_ptr(OWDataOBJ.ow_data_addr, ow_ptr)

        # Re-initialise the ow ptrs
        self.re_initialize_ow()

        write_palette_slot(self.ow_data_ptrs[-1].ow_data_addr, 0xA)

    def remove_ow(self, ow_id):
        length = self.ow_data_ptrs.__len__()

        # Removes the data of the OW and changes all the ptrs
        self.ow_data_ptrs[ow_id].remove()

        for i in range(ow_id, length):
            # Without that if statement it would try to move_left the ow_data_ptrs[length]
            if i != length - 1:
                self.ow_data_ptrs[i + 1].move_left()

        # Re-initialize the ow_ptrs
        self.re_initialize_ow()

    def insert_ow(self, pos, ow_type, num_of_frames):
        # Get number of OWs
        l = self.ow_data_ptrs.__len__()

        # Move the data and the ptrs of all the OWs to the right
        for i in range(l - 1, pos - 1, -1):
            self.ow_data_ptrs[i].move_right()

        # Insert the new OW
        self.add_ow(ow_type, num_of_frames)

        # Re-initialize the ow_ptrs
        self.re_initialize_ow()

    def resize_ow(self, pos, ow_type, num_of_frames):
        # Get info
        animation_ptr = get_animation_addr(self.ow_data_ptrs[pos].ow_data_addr)
        palette_slot = get_palette_slot(self.ow_data_ptrs[pos].ow_data_addr)

        self.ow_data_ptrs[pos].remove()
        self.add_ow(ow_type, num_of_frames)

        # Restore Info
        write_animation_ptr(self.ow_data_ptrs[pos].ow_data_addr, animation_ptr)
        write_palette_slot(self.ow_data_ptrs[pos].ow_data_addr, palette_slot)

        # Re-initialise the ow ptrs
        self.re_initialize_ow()


class Root:
    ow_tables_addr = 0x0    # Talbe 0
    ow_tables_addrs = []    # [ptr:Table 2] or Table 1's entries
    tables_list = []

    def __init__(self):
        # Don't initialize in case a rom is not loaded
        if rom.rom_contents is None:
            return

        self.tables_list = []
        self.ow_tables_addr = TBL_0

        # Get addresses of OW Data Pointers Tables (Table 1)
        addr = self.ow_tables_addr
        ow_tbls_addrs = []  #[ptr:Table 1] or Table 0's entries
        while is_table_ptr(addr):
            ow_tbls_addrs.append(addr)
            self.ow_tables_addrs.append(ptr_to_addr(addr))
            addr += 4

        print("\nroot: About to check: "+HEX(addr))
        for addr in ow_tbls_addrs:
            if (ptr_to_addr(addr) == 0x39FFB0) or (ptr_to_addr(addr) == 0x39FEB0):
                # Those addrs are after the original table but not needed according to JPAN
                fill_with_data(addr, 4, 0)
                break
            elif table_needs_repoint(addr):
                print("root: Repointing Table: "+HEX(addr))
                self.repoint_table(addr)
                print("root: Finished Repointing!")
            else:
                table_ptr_addr = addr
                table_addr = ptr_to_addr(addr)
                end_of_table = table_addr + (256 * 4)
                ow_data_addr = ptr_to_addr(end_of_table)
                frames_ptrs = ptr_to_addr(end_of_table + 4)
                frames_addr = ptr_to_addr(end_of_table + 8)
                print("root: Tables Table: "+HEX(table_ptr_addr))
                print("root: Table: " + HEX(ptr_to_addr(self.ow_tables_addr)))
                print("root: OW Data: "+HEX(ow_data_addr))
                print("root: Frames Pointers: "+HEX(frames_ptrs))
                print("root: Frames Address: "+HEX(frames_addr))
                # Create the Table Object
                ptr_tbl_obj = OWPointerTable(table_ptr_addr, table_addr,
                    ow_data_addr, frames_ptrs, frames_addr)
                self.tables_list.append(ptr_tbl_obj)

            addr += 4
            print("\nroot: About to check: "+HEX(addr))

    def custom_table_import(self, new_table, ow_data_addr, frames_ptrs, frames_addr):

        self.import_OW_Table(*addrs_filter(new_table, ow_data_addr, frames_ptrs, frames_addr))

    def clear_OW_Tables(self, ow_table_addr=TBL_0):
        # Clear all the table entries after the original OW Table
        ow_table_addr += 4
        for i in range(ow_table_addr, ow_table_addr + 25):
            rom.seek(i)
            rom.write_byte(0)
        # Clear all the entries in the tables_list
        # by re-initializing
        self.tables_list = []
        self.__init__()

    def import_OW_Table(self, new_table, ow_data_addr, frames_ptrs, frames_addr, ):
        # Imports a new OW Table
        write_addr = self.ow_tables_addr

        while is_ptr(write_addr):
            write_addr += 4

        # No ptr in the write_addr
        write_ptr(new_table, write_addr)
        # Make changes to the tables_list
        self.tables_list.append(
                OWPointerTable(write_addr,
                               *addrs_filter(new_table, ow_data_addr, frames_ptrs, frames_addr)))

    def remove_table(self, i):
        n = len(self.tables_list[i].ow_data_ptrs)
        for j in range(n):
            self.tables_list[i].ow_data_ptrs[j].remove()

        # Clear all of the godam data
        fill_with_data(self.tables_list[i].frames_ptrs_addr, 256 * 8 * FRAMES_PER_OW, 0xFF)
        fill_with_data(self.tables_list[i].ow_data_ptrs_addr, 256 * 36, 0xFF)
        fill_with_data(self.tables_list[i].table_addr, 259 * 4, 0xFF)

        # Move all the table ptrs to the left
        addr = self.ow_tables_addr + (i * 4)
        fill_with_data(addr, 4, 0)

        addr += 4
        while ptr_to_addr(addr) != 0 and is_ptr(addr) == 1:
            move_data(addr, addr - 4, 4, 0)

        # Re-initialise the entire root
        self.__init__()

    def get_table_num(self):
        return len(self.tables_list)

    def repoint_table(self, table_ptrs_addr):

        # Find number of OWs
        ow_ptrs_addr = ptr_to_addr(table_ptrs_addr)
        ows_num = 0
        addr = ow_ptrs_addr
        while is_ow_data_ptr(addr) and ows_num <= 256:
            # Don't continue if OW is part of another Table
            if ows_num > 1 and addr in self.ow_tables_addrs:
                break
            ows_num += 1
            addr += 4

        # Create the new table and fix the previous ptrs
        repointed_table = OWPointerTable(TBL_0, *addrs_filter(0, 0, 0, 0))
        print("root: rewriting ptr: "+HEX(table_ptrs_addr))
        write_ptr(repointed_table.table_addr, table_ptrs_addr)
        self.tables_list.append(repointed_table)

        # Find the Frames Pointers for each OW
        original_frames_ptrs = []
        for ow_ptr in range(ow_ptrs_addr, ow_ptrs_addr + (4 * ows_num), 4):
            data_ptr = ptr_to_addr(ow_ptr)
            original_frames_ptrs.append(ptr_to_addr(data_ptr + 0x1C))

        # Create a list with the num of frames for each OW
        frames = []
        for ow in range(ows_num):
            check_addr = original_frames_ptrs[ow] + 8
            frames_num = 1

            # Check if current has different palette with the next one
            basic_cond = (check_addr not in original_frames_ptrs) and is_frames_ptr(check_addr)
            size_cond = read_word(check_addr + 0x4) == read_word(check_addr - 0x8 + 0x4)

            while basic_cond and size_cond:
                frames_num += 1
                check_addr += 8
                basic_cond = (check_addr not in original_frames_ptrs) and is_frames_ptr(check_addr)
                size_cond = read_word(check_addr + 0x4) == read_word(check_addr - 0x8 + 0x4)

            frames.append(frames_num)

        # Find the Type of each OW
        types = []
        for frames_ptrs_addr in original_frames_ptrs:
            FramesAssistant = FramesPointers(frames_ptrs_addr)
            types.append(FramesAssistant.get_type())

        # Restore the Data
        for i in range(0, ows_num):
            print("root: Adding OW: " + str(i))
            print("root: Frames: " + str(frames[i]))
            print("OW Data Pointer: "+HEX(ow_ptrs_addr+4*i))
            # print("Type: "+str(types[i]))
            repointed_table.add_ow(types[i], frames[i])
            new_frames_ptr = read_word(repointed_table.ow_data_ptrs[-1].ow_data_addr + 0x1C)
            copy_data(ptr_to_addr(ow_ptrs_addr + i * 4),
                      repointed_table.ow_data_ptrs[-1].ow_data_addr,
                      0x24)
            write_word(new_frames_ptr, repointed_table.ow_data_ptrs[-1].ow_data_addr + 0x1C)

            # Copy the actual frames
            for j in range(frames[i]):
                copy_data(ptr_to_addr(original_frames_ptrs[i] + (j * 8)),
                          repointed_table.ow_data_ptrs[-1].frames.frames_addr + (j * get_frame_size(types[i])),
                          get_frame_size(types[i]))

        if len(frames) >= 218:
            for i in range(0, 256 - len(frames)):
                repointed_table.add_ow(1, 9)

        # Clean the data of the original table
        i = 0
        for ow_ptr in range(ow_ptrs_addr, ow_ptrs_addr + (4 * ows_num), 4):

            data_ptr = ptr_to_addr(ow_ptr)
            fill_with_data(ow_ptr, 4, 255)

            ow_frames_ptrs = ptr_to_addr(data_ptr + 28)
            fill_with_data(data_ptr, 36, 255)

            for k in range(0, frames[i]):
                if ow_frames_ptrs != 0xFFFFFF:
                    if is_frames_ptr(ow_frames_ptrs) == 1:
                        frame_addr = ptr_to_addr(ow_frames_ptrs)
                        fill_with_data(frame_addr, get_frame_size(types[i]), 0xFF)

                        fill_with_data(ow_frames_ptrs, 8, 0xFF)
                        ow_frames_ptrs += 8

            i += 1

    def get_num_of_available_table_ptrs(self):

        check_addr = self.ow_tables_addr

        while is_ptr(check_addr) == 1:
            check_addr += 4

        i = 0
        done = 0
        while done == 0:
            adder = 0
            rom.seek(check_addr)
            for j in range(0, 4):
                adder += rom.read_byte()

            if adder != 0:
                done = 1
            else:
                check_addr += 4
                i += 1
        return i
