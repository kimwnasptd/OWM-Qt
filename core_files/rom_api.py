'''
This module is responsible for manipulating the ROM. Since the
`import rom_api as rom` will create the same object for every other module that
imports it, different parts can modify the ROM simultaneously.

In other words, any module that does `import rom_api as rom` will have a local
rom object that will reference the same object.
'''
import os
import mmap
from core_files import statusbar as sts
from core_files import conversions as conv
from core_files.game import Game
from random import randint

global rom
rom = Game()
log = sts.get_logger(__name__)

FREE_SPC = 0x0
PAL_TBL_PTRS = []
TBL_0 = 0x0
FRAMES_PER_OW = 15
FRAMES_END = 0x2135F0
TEMPLATES = []

# This will be used to determine the number of frames
# when repointing a table. Used in ow_initializer, repoint_table
FRAMES_PTRS_PTRS = set()


def initRom(fn):
    global rom
    rom.load_rom(fn)


def updateRom(new_rom):
    global rom
    rom = new_rom


def update_palette_table_pointers(ptrs_list):
    global PAL_TBL_PTRS
    PAL_TBL_PTRS = ptrs_list


def update_ow_tables_pointers_table(ow_tbls_ptrs_tbl):
    global TBL_0
    TBL_0 = ow_tbls_ptrs_tbl


def update_rom_tamplates(files_path):
    global TEMPLATES
    if os.path.exists(files_path):
        for tmpl in ["Template{}".format(i) for i in range(1, 9)]:
            path = files_path + tmpl
            temp = open(path, 'r+b')
            template = mmap.mmap(temp.fileno(), 0)
            TEMPLATES.append(template)


def update_resesrved_regions(new_regions):
    rom.update_layered_rom_contents(new_regions)


# Free Space Searching
def update_free_space(size, start_addr=FREE_SPC):
    global FREE_SPC
    FREE_SPC = find_free_space(size, start_addr, 2)


def find_free_space_update(size, start_addr=0, ending=0):
    addr = find_free_space(size, start_addr, ending)
    # Update the Free Space addr
    global FREE_SPC
    FREE_SPC = addr + size
    return addr


def aggressive_search(size, start_addr=0, ending=0):
    # Searches really fast, but may not be able to find
    # the free space, even if it exists in the ROM
    size += ending

    # Search by Blocks
    for addr in range(start_addr, rom.rom_size, size):
        if not rom.check_free_byte(addr):
            continue

        # Search that spectrum for the FFs
        addr = max(addr - size, start_addr)
        ffs = 0
        candidate_addr = addr
        for i in range(addr, addr + 2*size):
            if ffs == size:
                if (ending != 0) and (candidate_addr % ending != 0):
                    candidate_addr += candidate_addr % ending
                return candidate_addr

            if not rom.check_free_byte(i):
                candidate_addr = i + 1
                ffs = 0
            else:
                ffs += 1

    return None


def slow_search(size, start_addr=0, ending=0):
    # Linear search for free space. If the needed space exists after the
    # start_addr it will always find it. Significantly slower but reliable
    working_addr = start_addr
    target_addr = start_addr
    ffs = 0
    while ffs < size + ending:
        if rom.check_free_byte(working_addr):
            ffs += 1
        else:
            ffs = 0
            target_addr = working_addr + 1
        working_addr += 1

        if working_addr > rom.rom_size:
            return None

    if (ending != 0) and (target_addr % ending != 0):
        target_addr += target_addr % ending
    return target_addr


def find_free_space(size, start_addr=0, ending=0):
    # First try the fast search and if that fails, use the slow one
    addr = aggressive_search(size, start_addr, ending)
    if addr:
        return addr
    if not start_addr:
        addr = aggressive_search(size, 0, ending)
    if not start_addr and addr:
        return addr

    addr = slow_search(size, start_addr, ending)
    if addr:
        return addr
    if not start_addr:
        addr = slow_search(size, 0, ending)
    if not start_addr and addr:
        return addr

    # The ROM is seriously running out of space
    sts.show("ERROR: No Free Space available. Closing")
    log.error("Now Cant find free space in ROM: Size {} | Start Address {}"
              .format(conv.HEX(size), conv.HEX(start_addr)))
    from time import sleep
    sleep(2)
    exit()


# Data handling
def is_ptr(addr):
    try:
        rom.seek(addr + 3)
        byte = rom.read_byte()
        if (byte == 8) or (byte == 9):
            return 1
        return 0
    except IndexError:
        return 0


def get_bytes_bits(byte, bit, to=0):
    if to == 0:
        to = bit

    bit_length = to - bit + 1

    result = byte << (32 - to)
    # Clear bits > 8
    mask = 0xffffffff
    result &= mask
    result >>= 32 - bit_length

    return result


def write_word(addr, value):
    rom.seek(addr)

    for i in range(0, 4):
        byte = get_bytes_bits(value, 1, 8)
        rom.write_byte(byte)
        value >>= 8


def write_ptr(ptr_addr, addr_to_write):
    write_word(addr_to_write, ptr_addr + 0x08000000)


def get_word(addr):
    '''Big endian'''
    rom.seek(addr)
    byte1 = rom.read_byte() << 24
    byte2 = rom.read_byte() << 16
    byte3 = rom.read_byte() << 8
    byte4 = rom.read_byte()
    return byte4 | byte3 | byte2 | byte1


def read_word(addr):
    '''Little endian'''
    rom.seek(addr)
    byte1 = rom.read_byte()

    byte2 = rom.read_byte()
    byte2 <<= 8

    byte3 = rom.read_byte()
    byte3 <<= 16

    byte4 = rom.read_byte()
    byte4 <<= 24

    return byte1 + byte2 + byte3 + byte4


def read_half(addr):
    rom.seek(addr)
    return rom.read_byte() + (rom.read_byte() << 8)


def read_byte(addr):
    rom.seek(addr)
    return rom.read_byte()


def write_byte(addr, val):
    rom.seek(addr)
    rom.write_byte(val)


def read_bytes(addr, num):
    rom.seek(addr)
    return [rom.read_byte() for _ in range(num)]


def write_bytes(addr, bytes):
    rom.seek(addr)
    for byte in bytes:
        rom.write_byte(byte)


def ptr_to_addr(addr):
    rom.seek(addr)
    byte1 = rom.read_byte()
    byte2 = rom.read_byte() << 8
    byte3 = rom.read_byte() << 16
    subfix = rom.read_byte()

    if subfix == 9:
        return byte3 + byte2 + byte1 + 0x1000000
    else:
        return byte3 + byte2 + byte1


def ptr_to_addr_n(addr, n):
    for i in range(1, n + 1):
        addr = ptr_to_addr(addr)
    return addr


def find_bytes_in_rom(bytes_to_find):
    # https://stackoverflow.com/questions/10106901/elegant-find-sub-list-in-list
    pattern = bytearray(bytes_to_find)
    mylist = rom.rom_contents
    for i in range(len(mylist)):
        if mylist[i] == pattern[0] and mylist[i:i+len(pattern)] == pattern:
            return i
    return -1


def find_ptr_in_rom(pointing_addr, search_for_all=False):
    '''
    Finds the addresses of all the pointers that point to a specific address
    INPUTS: pointing_addr, search_for_all=False
    '''
    ptrs_addr = []
    for addr in range(0, rom.rom_size, 4):
        if is_ptr(addr) and ptr_to_addr(addr) == pointing_addr:
            ptrs_addr += [addr]

            if not search_for_all:
                break

    return ptrs_addr


def fill_with_data(addr, num_of_bytes, write_data):
    '''
    If write_data is < 0, then a random number is selected
    (where 0<= write_data <= 254)
    '''
    if write_data < 0:
        write_data = randint(0x1, 0xE)
        write_data += write_data * 16

    rom.seek(addr)
    for i in range(1, num_of_bytes + 1):
        rom.write_byte(write_data)


def copy_data(addr_to_copy_from, addr_to_copy_to, num_of_bytes):
    '''
    Copies num_of_bytes from src to dst. The data in src is left untouched
    '''
    copied_bytes = []
    rom.seek(addr_to_copy_from)
    for i in range(0, num_of_bytes):
        # Read the byte to write
        copied_bytes.append(rom.read_byte())

    rom.seek(addr_to_copy_to)
    for i in range(0, num_of_bytes):
        rom.write_byte(copied_bytes[i])


def move_data(addr_to_copy, addr_to_write, num_of_bytes, write_byte=0xff):
    '''
    Copies num_of_bytes from src to dst. Then it will fill the old data with
    the value of write_byte (default 0xFF)
    '''
    copy_data(addr_to_copy, addr_to_write, num_of_bytes)
    fill_with_data(addr_to_copy, num_of_bytes, write_byte)
