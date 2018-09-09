from core_files.game import *
from random import randint

global rom
rom = Game()
global prntbar
prntbar = ""

def initRom(fn):
    global rom
    rom.load_rom(fn)

# The StatusBar in QtApplication
def initBar(bar):
    global prntbar
    prntbar = bar

def SHOW(msg):
    global prntbar
    prntbar.showMessage(msg)

# Functions may throw IndexError
def get_word(addr):
    # Big endian
    rom.seek(addr)
    byte1 = rom.read_byte() << 24
    byte2 = rom.read_byte() << 16
    byte3 = rom.read_byte() << 8
    byte4 = rom.read_byte()
    return byte4 | byte3 | byte2 | byte1

# Free Space Searching
def aggressive_search(size, start_addr=0, ending=0):
    # Searches really fast, but may not be able to find
    # the free space, even if it exists in the ROM
    size += ending
    free_spc = [0xFF for i in range(size)]

    # Search by Blocks
    for addr in range(start_addr, rom.rom_size, size):
        if not rom.check_byte(addr, 0xFF):
            continue
        if not rom.check_byte(addr, 0xFF):
            continue
        if not rom.check_byte(addr, 0xFF):
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

            if not rom.check_byte(i, 0xFF):
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
        if rom.check_byte(working_addr, 0xFF):
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
    if addr: return addr
    if not start_addr: addr = aggressive_search(size, 0, ending)
    if not start_addr and addr: return addr

    addr = slow_search(size, start_addr, ending)
    if addr: return addr
    if not start_addr: addr = slow_search(size, 0, ending)
    if not start_addr and addr: return addr

    # The ROM is seriously running out of space
    SHOW("ERROR: No Free Space available. Closing")
    from time import sleep
    sleep(2)
    exit()

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

def read_word(addr):
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

def find_ptr_in_rom(pointing_addr, search_for_all=None):

    ptrs_addr = []
    for addr in range(0, rom.rom_size, 4):
        if is_ptr(addr) and ptr_to_addr(addr) == pointing_addr:
            if search_for_all is None:
                return addr
            else:
                ptrs_addr += [addr]

    if search_for_all:
        return ptrs_addr
    else:
        return 0

def fill_with_data(addr, num_of_bytes, write_data):
    # If write_data is < 0, then a random number is selected (where 0<= write_data <= 254)
    if write_data < 0:
        write_data = randint(0x1, 0xE)
        write_data += write_data * 16

    rom.seek(addr)
    for i in range(1, num_of_bytes + 1):
        rom.write_byte(write_data)
    rom.flush()

def copy_data(addr_to_copy_from, addr_to_copy_to, num_of_bytes):
    copied_bytes = []
    rom.seek(addr_to_copy_from)
    for i in range(0, num_of_bytes):
        # Read the byte to write
        copied_bytes.append(rom.read_byte())

    rom.seek(addr_to_copy_to)
    for i in range(0, num_of_bytes):
        rom.write_byte(copied_bytes[i])

def move_data(addr_to_copy, addr_to_write, num_of_bytes, write_byte=0xff):
    copy_data(addr_to_copy, addr_to_write, num_of_bytes)
    fill_with_data(addr_to_copy, num_of_bytes, write_byte)

def capitalized_hex(addr):
    string = hex(addr)
    string = string.upper()

    string = string[2:]
    string = '0x' + string

    return string

def HEX(addr):
    return capitalized_hex(addr)

def HEX_LST(bytes):
    return str([HEX(byte) for byte in bytes])

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
