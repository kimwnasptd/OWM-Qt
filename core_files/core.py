from . import rom_api as rom
from . import conversions as conv

frametype1 = [0x0, 0x1]     # [16x32]
frametype2 = [0x0, 0x2]     # [32x32]
frametype3 = [0x80, 0x0]    # [16x16]
frametype4 = [0x0, 0x8]     # [64x64]
frametype5 = [0x0, 0x10]    # [128x64] FR Only
frametype6 = [0x80, 0x4]    # [48x48] Emerald only
frametype7 = [0x80, 0x5]    # [88x32] Emerald only
frametype8 = [0x80, 0x7]    # [96x40] Emerald only

# DEFINES
T16x32 = 1
T32x32 = 2
T16x16 = 3
T64x64 = 4
T128x64 = 5
T48x48 = 6
T88x32 = 7
T96x40 = 8


# ----------------------Functions------------------------------
def is_ow_data(addr):
    # Checks various bytes to see if they are the same with the templates
    try:
        if rom.read_byte(addr + 0x0) != 0xFF:
            return 0
        if rom.read_byte(addr + 0x1) != 0xFF:
            return 0

        if not rom.is_ptr(addr + 0x10):
            return 0
        if not rom.is_ptr(addr + 0x14) and rom.read_word(addr + 0x14) != 0:
            return 0
        if not rom.is_ptr(addr + 0x18):
            return 0
        if not rom.is_ptr(addr + 0x1c):
            return 0
        if not rom.is_ptr(addr + 0x20):
            return 0
    except IndexError:
        return 0
    return 1


def is_orig_table_ptr(addr):
    # Check if it is a Vanilla Table 1 (OW Data Pointers)
    if not rom.is_ptr(addr):
        return 0

    ow_data_ptr = rom.ptr_to_addr(addr)
    if not rom.is_ptr(ow_data_ptr):
        return 0

    ow_data = rom.ptr_to_addr(ow_data_ptr)
    if not is_ow_data(ow_data):
        return 0

    frames_ptrs = rom.ptr_to_addr(ow_data + 0x1C)
    if not is_frames_ptr(frames_ptrs):
        return 0
    return 1


def is_owm_table_ptr(addr):
    # Check if it is a Vanilla Table 1 (OW Data Pointers)
    if not rom.is_ptr(addr):
        return 0
    ow_data_ptr = rom.ptr_to_addr(addr)
    end_of_table = ow_data_ptr + 256 * 4

    # Check for OWM's signature
    if not rom.is_ptr(end_of_table):
        return 0
    if not rom.is_ptr(end_of_table + 4):
        return 0
    if not rom.is_ptr(end_of_table + 8):
        return 0

    # Check if the pointers are valid
    if rom.read_word(ow_data_ptr) == 0x11111111:
        return 1
    if not is_ow_data_ptr(ow_data_ptr):
        return 0
    else:
        return 1


def is_table_ptr(addr):
    # Used to check if addr is a ptr to OW Data Pointers Table
    return is_orig_table_ptr(addr) or is_owm_table_ptr(addr)


def is_jpan_ptr(addr):
    # If JPAN's patch was applied, then there should be a pointer in a
    # routine somewhere that points to the new Table 0 (0x1A2000 default addr)
    if not rom.is_ptr(addr):
        return 0
    maybe_tbl = rom.ptr_to_addr(addr)
    if not is_table_ptr(maybe_tbl):
        return 0

    # Finally in Table 0 it should either have pointers to Table 1 or 0x00
    if rom.read_word(maybe_tbl + 4) == 0x0:
        return 1
    if is_table_ptr(maybe_tbl + 4):
        return 1
    return 0


def is_ow_data_ptr(addr):
    return rom.is_ptr(addr) and is_ow_data(rom.ptr_to_addr(addr))


def is_frames_end(addr):
    if rom.ptr_to_addr(addr) == rom.FRAMES_END:
        return 1
    else:
        return 0


def sublist(pattern, mylist):
    for i in range(len(mylist)):
        if mylist[i] == pattern[0] and mylist[i:i+len(pattern)] == pattern:
            return 1
    return 0


def table_needs_repoint(addr):
    ow_ptr = rom.ptr_to_addr(addr)
    end_of_table = ow_ptr + 256 * 4

    if rom.read_word(rom.ptr_to_addr(end_of_table)) == 0x22222222:
        return 0

    if not is_ow_data(rom.ptr_to_addr(end_of_table)):
        return 1

    if not rom.is_ptr(end_of_table + 4):
        return 1

    if rom.read_word(rom.ptr_to_addr(end_of_table + 4)) == 0x33333333:
        return 0

    if not is_frames_ptr(rom.ptr_to_addr(end_of_table + 4)):
        return 1

    return 0


def update_frames_addr(num, addr, ow_type):
    for i in range(1, num + 1):
        addr += get_frame_size(ow_type)
    return addr


def get_frame_size(ow_type):
    if ow_type == T16x32:
        return 256  # 0x100
    if ow_type == T32x32:
        return 512  # 0x200
    if ow_type == T16x16:
        return 128  # 0x80
    if ow_type == T64x64:
        return 2048  # 0x800
    if ow_type == T128x64:
        return 4096  # 0x1000
    if ow_type == T48x48:
        return 1152  # 0x480
    if ow_type == T88x32:
        return 1408  # 0x580
    if ow_type == T96x40:
        return 1920  # 0x780


def clear_frames(addr, frames, size):
    # first check if FRAMES_END is inside the data (overlay: happens with 0xFF)
    if sublist([0xF0, 0x35, 0x21, 0x08], rom.read_bytes(addr, frames*size)):
        rom.write_word(addr + frames*size, 0xFFFFFFFF)
        print("WARNING: Found a colision")
        return

    rom.fill_with_data(addr, frames * size, 0xFF)
    print(conv.HEX(addr))
    rom.write_word(addr, 0xFFFFFFFF)


def available_frames_ptr_addr(addr, num_of_frames):
    for i in range(num_of_frames * 8):
        if rom.read_byte(addr + i) != 0x33:
            return 0
    return 1


def write_frames_end(addr):
    rom.write_ptr(rom.FRAMES_END, addr)


def get_frame_dimensions(ow_type):
    if ow_type == T16x32:
        width = 16
        height = 32
    elif ow_type == T32x32:
        width = 32
        height = 32
    elif ow_type == T16x16:
        width = 16
        height = 16
    elif ow_type == T64x64:
        width = 64
        height = 64
    elif ow_type == T128x64:
        width = 128
        height = 64
    elif ow_type == T48x48:
        width = 48
        height = 48
    elif ow_type == T88x32:
        width = 88
        height = 32
    elif ow_type == T96x40:
        width = 96
        height = 40

    return width, height


def get_template(ow_type):
    return rom.TEMPLATES[ow_type - 1]


def get_ow_palette_id(addr):
    byte1 = rom.read_byte(addr + 2)
    byte2 = rom.read_byte(addr + 3)

    return (byte2 * 256) + byte1


def addrs_filter(new_table, ow_data_addr, frames_ptrs, frames_addr):
    # 0xA000 is ~ 256 * (4 + 36 + FRAMES_PER_OW * 8)
    if new_table == 0:
        # 3 more for the table's info + 1 for rounding
        new_table = rom.find_free_space_update((260 * 4), rom.FREE_SPC, 4)
    else:
        new_table = rom.find_free_space((260 * 4), new_table, 4)

    if ow_data_addr == 0:
        ow_data_addr = rom.find_free_space_update(
            (256 * 36) + 4,
            new_table + 259 * 4,
            4
        )
    else:
        ow_data_addr = rom.find_free_space((256 * 36) + 4, ow_data_addr, 4)

    if frames_ptrs == 0:
        frames_ptrs = rom.find_free_space_update(
            (9 * 8 * 256) + 4,
            ow_data_addr + (256 * 36) + 4,
            4
        )
    else:
        frames_ptrs = rom.find_free_space((9 * 8 * 256) + 4, frames_addr, 4)

    if frames_addr == 0:
        frames_addr = rom.find_free_space_update(
            0x40000,
            frames_ptrs + (9 * 8 * 256) + 4,
            2)
    else:
        frames_addr = rom.find_free_space(0x40000, frames_addr, 2)

    print("Found Addresses: {} {} {} {}".format(
        conv.HEX(new_table),
        conv.HEX(ow_data_addr),
        conv.HEX(frames_ptrs),
        conv.HEX(frames_addr))
    )
    return new_table, ow_data_addr, frames_ptrs, frames_addr


def write_ow_palette_id(addr, palette_id):
    byte1 = int(palette_id / 256)
    byte2 = int(palette_id % 256)

    rom.write_byte(addr + 2, byte2)
    rom.write_byte(addr + 3, byte1)


def is_frames_ptr(addr):
    check1 = rom.is_ptr(addr)

    # It checks first the type of the frames from the data next to the ptr
    frame = [rom.read_byte(addr + 4), rom.read_byte(addr + 5)]

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
    slot_compressed = rom.read_byte(data_addr + 12)
    return int(slot_compressed % 16)


def write_palette_slot(data_addr, palette_slot):
    byte = rom.read_byte(data_addr + 12)
    byte1 = int(byte / 16)
    slot = (byte1 * 16) + palette_slot
    rom.write_byte(data_addr + 12, slot)


def get_animation_addr(ow_data_addr):
    data_tuple = [0, 0]
    data_tuple[0] = rom.ptr_to_addr(ow_data_addr + 0x18)
    data_tuple[1] = rom.ptr_to_addr(ow_data_addr + 0x20)
    return data_tuple


def write_animation_ptr(ow_data_addr, data_tuple):
    rom.write_ptr(data_tuple[0], ow_data_addr + 0x18)
    rom.write_ptr(data_tuple[1], ow_data_addr + 0x20)


def get_text_color(ow_data_addr):
    return rom.read_byte(ow_data_addr + 0xE)


def set_text_color(ow_data_addr, val):
    rom.write_byte(ow_data_addr + 0xE, val)


def get_footprint(ow_data_addr):
    return rom.read_byte(ow_data_addr + 13)


def set_footprint(ow_data_addr, val):
    rom.write_byte(ow_data_addr + 13, val)


# -----------------Classes--------------------
class FramesPointers:
    frames_ptrs_addr = 0x0
    frames_addr = 0x0
    frames_ptrs_addr_start = 0x0
    frames_addr_start = 0x0

    def __init__(self, frames_ptrs_addr=0x0, frames_addr=0x0,
                 frames_ptrs_addr_start=0, frames_addr_start=0):
        self.frames_ptrs_addr = frames_ptrs_addr
        self.frames_addr = frames_addr
        self.frames_ptrs_addr_start = frames_ptrs_addr_start
        self.frames_addr_start = frames_addr_start

    def add_frames_ptrs(self, ow_type, num_of_frames):

        frames_addr = self.find_frames_free_space(ow_type, num_of_frames)
        frames_ptrs_addr = self.find_available_frames_ptrs_addr(num_of_frames)
        # Write changes to the class' variables
        self.frames_ptrs_addr = frames_ptrs_addr
        self.frames_addr = frames_addr

        # Initialize the actual data of the frames
        rom.fill_with_data(frames_addr,
                           num_of_frames * get_frame_size(ow_type),
                           -1)
        # Write the frame_end prefix
        rom.write_ptr(rom.FRAMES_END,
                      frames_addr + num_of_frames * get_frame_size(ow_type))

        self.write_frames_ptrs(ow_type, num_of_frames)

    def find_frames_free_space(self, ow_type, frames_num, addr=0):

        working_addr = self.frames_addr_start
        if addr != 0:
            working_addr = addr

        frame_size = get_frame_size(ow_type)
        size = frame_size * frames_num
        # working_addr = find_free_space(size + 4, working_addr, 2)
        working_addr = rom.find_free_space(size + 4, working_addr, 2)

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
        if ow_type == T16x32:
            frametype = frametype1
        elif ow_type == T32x32:
            frametype = frametype2
        elif ow_type == T16x16:
            frametype = frametype3
        elif ow_type == T64x64:
            frametype = frametype4
        elif ow_type == T128x64:
            frametype = frametype5
        elif ow_type == T48x48:
            frametype = frametype6
        elif ow_type == T88x32:
            frametype = frametype7
        elif ow_type == T96x40:
            frametype = frametype8

        # Write the frames Pointers
        for i in range(0, frames_num):
            rom.write_ptr(frame_addr, frame_ptr_addr)
            rom.write_bytes(frame_ptr_addr + 4, frametype + [0x0, 0x0])

            frame_ptr_addr += 8
            frame_addr += get_frame_size(ow_type)

    def repoint_frames(self, new_frames_addr):

        frames_num = self.get_num()
        ow_type = self.get_type()

        rom.new_addr = self.find_frames_free_space(ow_type,
                                                   frames_num,
                                                   new_frames_addr)

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

            # if (addr == 0xc6921a):
            #     print("HELLOOOOO")
        return i

    def clear(self):
        ow_type = self.get_type()
        frames_num = self.get_num()

        # Clear the ptrs addr
        rom.fill_with_data(self.frames_ptrs_addr, frames_num * 8, 0x33)
        # Clear the actual data of the frames, watch out for overlays
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
        for i in range(0x24):
            rom.write_byte(template.read_byte())

        # Write the ptr to the frames
        rom.write_ptr(frames_ptrs_addr, ow_data_addr + 0x1c)

    def find_available_ow_data_addr(self):

        working_addr = self.ow_data_addr_start

        while 1:
            if is_ow_data(working_addr) == 0:
                return working_addr
            else:
                working_addr += 0x24

    def clear(self):
        self.frames.clear()
        rom.fill_with_data(self.ow_data_addr, 36, 0x22)  # 0x22 = 34

    def remove(self):
        # Clear itself
        self.clear()
        # Clear the ow_ptr
        rom.fill_with_data(self.ow_ptr_addr, 4, 0x22)  # 0x22

    def move_left(self):
        # Move the OW Data left
        rom.move_data(self.ow_data_addr, self.ow_data_addr - 36, 36, 0x22)
        # Change the ow_ptr to point to the new addr
        rom.write_ptr(self.ow_data_addr - 36, self.ow_ptr_addr)
        # Move the OW Pointer left
        rom.move_data(self.ow_ptr_addr, self.ow_ptr_addr - 4, 4, 0x22)

    def move_right(self):

        # Move the OW Data right
        rom.move_data(self.ow_data_addr, self.ow_data_addr + 36, 36, 0x22)

        # Change the ow_ptr to point to the new addr
        rom.write_ptr(self.ow_data_addr + 36, self.ow_ptr_addr)

        # Move the OW Pointer right
        rom.move_data(self.ow_ptr_addr, self.ow_ptr_addr + 4, 4, 0x22)


class OWPointerTable:
    table_ptr_addr = 0
    table_addr = 0x0
    ow_data_ptrs = []

    ow_data_addr = 0x0
    frames_ptrs_addr = 0x0
    frames_addr = 0x0
    end_of_table = 0x0

    def __init__(self, table_ptr_addr, table_addr, ow_data_addr, frames_ptrs,
                 frames_addr):
        self.table_ptr_addr = table_ptr_addr
        self.table_addr = table_addr
        self.ow_data_addr = ow_data_addr
        self.frames_ptrs_addr = frames_ptrs
        self.frames_addr = frames_addr
        self.ow_data_ptrs = []
        self.end_of_table = table_addr + (256 * 4)

        # Checks if the table was already there
        if rom.ptr_to_addr(self.table_addr) == 0xFFFFFF:
            # fill with bytes the OW Data Pointers Table,
            # OW Data Table and Frames Pointers Table(~20 frames/ow)
            rom.fill_with_data(self.table_addr, 256 * 4, 0x11)
            rom.fill_with_data(self.ow_data_addr, 256 * 36, 0x22)
            rom.fill_with_data(self.frames_ptrs_addr,
                               256 * 8 * rom.FRAMES_PER_OW,
                               0x33)

            # Write the table's info
            print("\ntbl_init: OW Pointers(WR): " + conv.HEX(self.table_addr))
            print("tbl_init: OW Data(WR): " + conv.HEX(self.ow_data_addr))
            print("tbl_init: Frames Pointers(WR): " +
                  conv.HEX(self.frames_ptrs_addr))
            print("tbl_init: Frames Address(WR): " +
                  conv.HEX(self.frames_addr))
            rom.write_ptr(self.ow_data_addr, self.end_of_table)
            rom.write_ptr(self.frames_ptrs_addr, self.end_of_table + 4)
            rom.write_ptr(self.frames_addr, self.end_of_table + 8)

        check_addr = self.table_addr
        while rom.is_ptr(check_addr) and check_addr != self.end_of_table:
            # There is an OW ptr
            self.ow_data_ptrs.append(self.ow_initializer(check_addr))
            check_addr += 4

    def ow_initializer(self, ow_ptr):
        ow_data_addr = rom.ptr_to_addr(ow_ptr)
        frames_ptrs_addr = rom.ptr_to_addr(ow_data_addr + 0x1C)
        frames_addr = rom.ptr_to_addr(frames_ptrs_addr)
        rom.FRAMES_PTRS_PTRS.add(frames_ptrs_addr)

        # Create the Frames OBJ
        FramesOBJ = FramesPointers(frames_ptrs_addr, frames_addr,
                                   self.frames_ptrs_addr,
                                   self.frames_addr)

        # Create the OW Data OBJ
        OWDataOBJ = OWData(ow_data_addr, ow_ptr, self.ow_data_addr)
        OWDataOBJ.frames = FramesOBJ

        return OWDataOBJ

    def find_available_ow_ptr(self):
        working_addr = self.table_addr

        while 1:
            if rom.is_ptr(working_addr) == 0:
                return working_addr
            else:
                working_addr += 4

    def re_initialize_ow(self):
        # Re-initialize the ow_ptrs
        self.ow_data_ptrs = []

        check_addr = self.table_addr
        while 1:
            if rom.is_ptr(check_addr) == 1:
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
        FramesOBJ = FramesPointers(0,
                                   0,
                                   self.frames_ptrs_addr,
                                   self.frames_addr)
        FramesOBJ.add_frames_ptrs(ow_type, num_of_frames)

        # Create OW Data
        ow_ptr = self.find_available_ow_ptr()

        OWDataOBJ = OWData(0, ow_ptr, self.ow_data_addr)
        OWDataOBJ.add_ow_data(ow_type, FramesOBJ.frames_ptrs_addr)
        OWDataOBJ.frames = FramesOBJ

        # Write the OW Pointer in the Table
        rom.write_ptr(OWDataOBJ.ow_data_addr, ow_ptr)

        # Re-initialise the ow ptrs
        self.re_initialize_ow()

        write_palette_slot(self.ow_data_ptrs[-1].ow_data_addr, 0xA)

    def remove_ow(self, ow_id):
        length = len(self.ow_data_ptrs)

        # Removes the data of the OW and changes all the ptrs
        self.ow_data_ptrs[ow_id].remove()

        for i in range(ow_id, length):
            # Without that if statement it would try to move_left
            # the ow_data_ptrs[length]
            if i != length - 1:
                self.ow_data_ptrs[i + 1].move_left()

        # Re-initialize the ow_ptrs
        self.re_initialize_ow()

    def insert_ow(self, pos, ow_type, num_of_frames):
        # Get number of OWs
        lngth = len(self.ow_data_ptrs)

        # Move the data and the ptrs of all the OWs to the right
        for i in range(lngth - 1, pos - 1, -1):
            self.ow_data_ptrs[i].move_right()

        # Insert the new OW
        self.add_ow(ow_type, num_of_frames)

        # Re-initialize the ow_ptrs
        self.re_initialize_ow()

    def resize_ow(self, pos, ow_type, num_of_frames):
        # Get info
        ow_data_addr = self.ow_data_ptrs[pos].ow_data_addr
        animation_ptr = get_animation_addr(ow_data_addr)
        palette_slot = get_palette_slot(ow_data_addr)
        footprint_byte = rom.read_byte(ow_data_addr + 13)

        self.ow_data_ptrs[pos].remove()
        self.add_ow(ow_type, num_of_frames)

        # Restore Info
        write_animation_ptr(ow_data_addr, animation_ptr)
        write_palette_slot(ow_data_addr, palette_slot)
        rom.write_byte(ow_data_addr + 13, footprint_byte)

        # Re-initialise the ow ptrs
        self.re_initialize_ow()


class Root:
    ow_tables_addr = 0x0    # Talbe 0
    ow_tables_addrs = []    # [ptr:Table 2] or Table 1's entries
    tables_list = []

    def __init__(self):
        # Don't initialize in case a rom is not loaded
        if rom.rom is None or rom.rom.rom_contents is None:
            return

        self.tables_list = []
        self.ow_tables_addr = rom.TBL_0
        rom.FRAMES_PTRS_PTRS = set()

        # Get addresses of OW Data Pointers Tables (Table 1)
        addr = self.ow_tables_addr
        # [ptr:Table 1] or Table 0's entries
        ow_tbls_addrs = []
        while is_table_ptr(addr):
            if rom.ptr_to_addr(addr) in [0x39FFB0, 0x39FEB0]:
                rom.fill_with_data(addr, 4, 0)
                continue
            ow_tbls_addrs.append(addr)
            self.ow_tables_addrs.append(rom.ptr_to_addr(addr))
            addr += 4

        for addr in ow_tbls_addrs:
            print("\nroot: About to check: {} ({})".format(
                conv.HEX(addr),
                conv.HEX(rom.ptr_to_addr(addr)))
            )
            if table_needs_repoint(addr):
                # If it was the first table, change any pointer in the
                # ROM that might be pointing to it
                if addr == self.ow_tables_addr:
                    rom.SHOW("Searching for Pointers for the Default OW Table")
                    ptrs = rom.find_ptr_in_rom(rom.ptr_to_addr(addr), True)
                    self.repoint_table(addr)
                    for ptr in ptrs:
                        rom.write_ptr(rom.ptr_to_addr(addr), ptr)
                else:
                    self.repoint_table(addr)
            else:
                table_ptr_addr = addr
                table_addr = rom.ptr_to_addr(addr)
                end_of_table = table_addr + (256 * 4)
                ow_data_addr = rom.ptr_to_addr(end_of_table)
                frames_ptrs = rom.ptr_to_addr(end_of_table + 4)
                frames_addr = rom.ptr_to_addr(end_of_table + 8)
                rom.SHOW("Loading Table (" + conv.HEX(table_addr) + ")")
                print("root: Tables Table: " + conv.HEX(table_ptr_addr))
                print("root: Table: " +
                      conv.HEX(rom.ptr_to_addr(self.ow_tables_addr)))
                print("root: OW Data: " + conv.HEX(ow_data_addr))
                print("root: Frames Pointers: " + conv.HEX(frames_ptrs))
                print("root: Frames Address: " + conv.HEX(frames_addr))
                # Create the Table Object
                ptr_tbl_obj = OWPointerTable(table_ptr_addr,
                                             table_addr,
                                             ow_data_addr,
                                             frames_ptrs,
                                             frames_addr)
                self.tables_list.append(ptr_tbl_obj)

            print("\nroot: About to check: {} ({})".format(
                conv.HEX(addr),
                conv.HEX(rom.ptr_to_addr(addr)))
            )
        print("\nroot: Not a ptr: Address {} | Pointing to {}".format(
            conv.HEX(addr),
            conv.HEX(rom.ptr_to_addr(addr)))
        )

    def reload(self):
        self.tables_list = []
        self.ow_tables_addr = rom.TBL_0

        # Get addresses of OW Data Pointers Tables (Table 1)
        addr = self.ow_tables_addr
        # [ptr:Table 1] or Table 0's entries
        ow_tbls_addrs = []
        while is_table_ptr(addr):
            ow_tbls_addrs.append(addr)
            self.ow_tables_addrs.append(rom.ptr_to_addr(addr))
            addr += 4

        for addr in ow_tbls_addrs:
            table_ptr_addr = addr
            table_addr = rom.ptr_to_addr(addr)
            end_of_table = table_addr + (256 * 4)
            ow_data_addr = rom.ptr_to_addr(end_of_table)
            frames_ptrs = rom.ptr_to_addr(end_of_table + 4)
            frames_addr = rom.ptr_to_addr(end_of_table + 8)
            rom.SHOW("Loading Table (" + conv.HEX(table_addr) + ")")

            # Create the Table Object
            ptr_tbl_obj = OWPointerTable(table_ptr_addr,
                                         table_addr,
                                         ow_data_addr,
                                         frames_ptrs,
                                         frames_addr)
            self.tables_list.append(ptr_tbl_obj)

    def custom_table_import(self, new_table, ow_data_addr, frames_ptrs,
                            frames_addr):
        self.import_OW_Table(
            *addrs_filter(new_table, ow_data_addr, frames_ptrs, frames_addr)
        )

    def clear_OW_Tables(self, ow_table_addr=rom.TBL_0):
        # Clear all the table entries after the original OW Table
        ow_table_addr += 4
        for i in range(ow_table_addr, ow_table_addr + 25):
            rom.write_byte(i, 0)

        # Clear all the entries in the tables_list
        # by re-initializing
        self.tables_list = []
        self.__init__()

    def import_OW_Table(self, new_table, ow_data_addr, frames_ptrs,
                        frames_addr):
        # Imports a new OW Table
        write_addr = self.ow_tables_addr
        # Find ptr addr to write
        while is_table_ptr(write_addr):
            write_addr += 4

        rom.write_ptr(new_table, write_addr)
        self.tables_list.append(OWPointerTable(write_addr, *addrs_filter(
            new_table, ow_data_addr, frames_ptrs, frames_addr)))

    def remove_table(self, i):
        tbl = self.tables_list[i]
        for ow in tbl.ow_data_ptrs:
            ow.remove()

        # Clear all of the godam data
        rom.fill_with_data(tbl.frames_ptrs_addr,
                           256 * 8 * rom.FRAMES_PER_OW,
                           0xFF)
        rom.fill_with_data(tbl.ow_data_addr, 256 * 36, 0xFF)
        rom.fill_with_data(tbl.table_addr, 259 * 4, 0xFF)

        # Move all the table ptrs to the left
        addr = self.ow_tables_addr + (i * 4)
        print("remove_table: about to remove: " + conv.HEX(addr))
        rom.fill_with_data(addr, 4, 0)

        addr += 4
        while is_table_ptr(addr):
            print("remove_table: Moving left ptr: " + conv.HEX(addr))
            rom.move_data(addr, addr - 4, 4, 0)
            addr += 4

        # Re-initialise the entire root
        self.reload()

    def tables_num(self):
        return len(self.tables_list)

    def repoint_table(self, table_ptrs_addr):
        # Find number of OWs
        rom.SHOW("Determining number of OWs for Table: " +
                 conv.HEX(table_ptrs_addr))
        ow_ptrs_addr = rom.ptr_to_addr(table_ptrs_addr)
        ows_num = 0
        addr = ow_ptrs_addr
        while is_ow_data_ptr(addr) and ows_num <= 256:
            # Don't continue if OW is part of another Table
            if ows_num > 1 and addr in self.ow_tables_addrs:
                break
            ows_num += 1
            addr += 4
        print("Found OWs: {} | Not OW Pointer: {} | Pointing to: {}".format(
            ows_num, conv.HEX(addr), conv.HEX(rom.ptr_to_addr(addr))))

        # Create the new table and fix the previous ptrs
        rom.SHOW("Searching Free Space for the New Table")
        repointed_table = OWPointerTable(rom.TBL_0, *addrs_filter(0, 0, 0, 0))
        rom.write_ptr(repointed_table.table_addr, table_ptrs_addr)
        self.tables_list.append(repointed_table)

        # Find the Frames Pointers for each OW
        original_frames_ptrs = []
        for ow_ptr in range(ow_ptrs_addr, ow_ptrs_addr + (4 * ows_num), 4):
            data_ptr = rom.ptr_to_addr(ow_ptr)
            original_frames_ptrs.append(rom.ptr_to_addr(data_ptr + 0x1C))
            rom.FRAMES_PTRS_PTRS.add(rom.ptr_to_addr(data_ptr + 0x1C))

        # Create a list with the num of frames for each OW
        frames = []
        for ow in range(ows_num):
            check_addr = original_frames_ptrs[ow] + 8
            frames_num = 1

            # Check if current has different palette with the next one
            basic_cond = (check_addr not in rom.FRAMES_PTRS_PTRS) \
                and is_frames_ptr(check_addr)
            size_cond = rom.read_word(check_addr + 0x4) == \
                rom.read_word(check_addr - 0x8 + 0x4)

            while basic_cond and size_cond:
                frames_num += 1
                check_addr += 8
                basic_cond = (check_addr not in original_frames_ptrs) and \
                    is_frames_ptr(check_addr)
                size_cond = rom.read_word(check_addr + 0x4) == \
                    rom.read_word(check_addr - 0x8 + 0x4)

            frames.append(frames_num)

        # Find the Type of each OW
        types = []
        for frames_ptrs_addr in original_frames_ptrs:
            FramesAssistant = FramesPointers(frames_ptrs_addr)
            types.append(FramesAssistant.get_type())

        # Restore the Data
        for i in range(0, ows_num):
            rom.SHOW("Repoining OW {}".format(i))
            repointed_table.add_ow(types[i], frames[i])
            new_frames_ptr = rom.read_word(
                repointed_table.ow_data_ptrs[-1].ow_data_addr + 0x1C)
            rom.copy_data(rom.ptr_to_addr(ow_ptrs_addr + i * 4),
                          repointed_table.ow_data_ptrs[-1].ow_data_addr,
                          0x24)
            rom.write_word(repointed_table.ow_data_ptrs[-1].ow_data_addr+0x1C,
                           new_frames_ptr)

            # Copy the actual frames
            for j in range(frames[i]):
                copy_from = rom.ptr_to_addr(original_frames_ptrs[i] + (j * 8))
                copy_to = repointed_table.ow_data_ptrs[-1].frames.frames_addr \
                    + (j * get_frame_size(types[i]))

                rom.copy_data(copy_from,
                              copy_to,
                              get_frame_size(types[i]))

        if len(frames) >= 218:
            rom.SHOW("Paddding the extra OWs")
            for i in range(0, 256 - len(frames)):
                repointed_table.add_ow(1, 9)

        # Clean the data of the original table
        rom.SHOW("Cleaning up...")
        i = 0
        for ow_ptr in range(ow_ptrs_addr, ow_ptrs_addr + (4 * ows_num), 4):

            data_ptr = rom.ptr_to_addr(ow_ptr)
            rom.fill_with_data(ow_ptr, 4, 0xFF)

            ow_frames_ptrs = rom.ptr_to_addr(data_ptr + 28)
            rom.fill_with_data(data_ptr, 36, 0xFF)

            for k in range(0, frames[i]):
                if ow_frames_ptrs != 0xFFFFFF:
                    if is_frames_ptr(ow_frames_ptrs) == 1:
                        frame_addr = rom.ptr_to_addr(ow_frames_ptrs)
                        rom.fill_with_data(frame_addr,
                                           get_frame_size(types[i]),
                                           0xFF)

                        rom.fill_with_data(ow_frames_ptrs, 8, 0xFF)
                        ow_frames_ptrs += 8

            i += 1

    def get_num_of_available_table_ptrs(self):

        check_addr = self.ow_tables_addr

        while rom.is_ptr(check_addr) == 1:
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

    def getTable(self, table_id):
        '''
        Return an OWPointerTable obj for the specified Table. Might throw
        an IndexError
        '''
        return self.tables_list[table_id]

    def getOW(self, table_id, ow_id):
        '''
        Return an OWData obj for the specified OW. Might throw an IndexError
        '''
        return self.tables_list[table_id].ow_data_ptrs[ow_id]
