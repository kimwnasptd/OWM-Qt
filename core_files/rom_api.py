from core_files.game import *
from random import randint

# The functions may throw IndexError

rom = Game()


def get_word(address):
    rom.seek(address)
    byte1 = rom.read_byte() << 24
    byte2 = rom.read_byte() << 16
    byte3 = rom.read_byte() << 8
    byte4 = rom.read_byte()
    return byte4 | byte3 | byte2 | byte1

def search_for_free_space(size, start_addr=0):
    free_spc = [0xFF for i in range(size)]

    for addr in range(start_addr, rom.rom_size, size):
        if not rom.check_byte(addr, 0xFF):
            continue
        if not rom.check_byte(addr, 0xFF):
            continue
        if not rom.check_byte(addr, 0xFF):
            continue

        # Search that spectrum for the FFs
        addr = addr - size
        ffs = 0
        candidate_addr = addr
        for i in range(addr, addr + 2*size):
            if ffs == size:
                return candidate_addr

            if not rom.check_byte(i, 0xFF):
                candidate_addr = i + 1
                ffs = 0
                continue
            ffs += 1
    error()
    return None # Force an error

def find_free_space(size, start_address=0, ending=0):
    working_address = start_address
    target_addr = start_address
    ffs = 0
    while ffs < size + ending:
        if rom.check_byte(working_address, 0xFF):
            ffs += 1
        else:
            ffs = 0
            target_addr = working_address + 1
        working_address += 1

        if working_address > rom.rom_size:
            return None

    if (ending != 0) and (target_addr % ending != 0):
        target_addr += target_addr % ending
    return target_addr

def check_pointer(address):
    try:
        rom.seek(address + 3)
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

def write_word(value, address):
    rom.seek(address)

    for i in range(0, 4):
        byte = get_bytes_bits(value, 1, 8)
        rom.write_byte(byte)
        value >>= 8

def write_pointer(pointer_address, address_to_write):
    write_word(pointer_address + 0x08000000, address_to_write)

def read_word(address):
    rom.seek(address)
    byte1 = rom.read_byte()

    byte2 = rom.read_byte()
    byte2 <<= 8

    byte3 = rom.read_byte()
    byte3 <<= 16

    byte4 = rom.read_byte()
    byte4 <<= 24

    return byte1 + byte2 + byte3 + byte4

def read_half(address):
    rom.seek(address)
    return rom.read_byte() + (rom.read_byte() << 8)

def pointer_to_address(address):
    rom.seek(address)
    byte1 = rom.read_byte()
    byte2 = rom.read_byte() << 8
    byte3 = rom.read_byte() << 16
    subfix = rom.read_byte()

    if subfix == 9:
        return byte3 + byte2 + byte1 + 0x1000000
    else:
        return byte3 + byte2 + byte1

def pointer_to_address_n(address, n):
    for i in range(1, n + 1):
        address = pointer_to_address(address)
    return address

def find_bytes_in_rom(bytes_to_find):
    # https://stackoverflow.com/questions/10106901/elegant-find-sub-list-in-list
    pattern = bytearray(bytes_to_find)
    mylist = rom.rom_contents
    for i in range(len(mylist)):
        if mylist[i] == pattern[0] and mylist[i:i+len(pattern)] == pattern:
            return i
    return -1

def find_pointer_in_rom(pointing_address, search_for_all=None):

    pointers_address = []
    for addr in range(0, rom.rom_size, 4):
        if check_pointer(addr) and pointer_to_address(addr) == pointing_address:
            if search_for_all is None:
                return addr
            else:
                pointers_address += [addr]

    if search_for_all:
        return pointers_address
    else:
        return 0

def fill_with_data(address, num_of_bytes, write_data):
    # If write_data is < 0, then a random number is selected (where 0<= write_data <= 254)
    if write_data < 0:
        write_data = randint(0x1, 0xe)
        write_data += write_data * 16

    rom.seek(address)
    for i in range(1, num_of_bytes + 1):
        rom.write_byte(write_data)
    rom.flush()

def copy_data(address_to_copy_from, address_to_copy_to, num_of_bytes):
    copied_bytes = []
    rom.seek(address_to_copy_from)
    for i in range(0, num_of_bytes):
        # Read the byte to write
        copied_bytes.append(rom.read_byte())

    rom.seek(address_to_copy_to)
    for i in range(0, num_of_bytes):
        rom.write_byte(copied_bytes[i])

def move_data(address_to_copy, address_to_write, num_of_bytes, write_byte=0xff):
    copy_data(address_to_copy, address_to_write, num_of_bytes)
    fill_with_data(address_to_copy, num_of_bytes, write_bytee)

def capitalized_hex(address):
    string = hex(address)
    string = string.upper()

    string = string[2:]
    string = '0x' + string

    return string
