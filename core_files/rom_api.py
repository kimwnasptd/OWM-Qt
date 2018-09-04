from core_files.game import *
from random import randint

rom = Game()


def get_word(address):
    rom.seek(address)
    byte1 = rom.read_byte() << 24
    byte2 = rom.read_byte() << 16
    byte3 = rom.read_byte() << 8
    byte4 = rom.read_byte()
    return byte4 | byte3 | byte2 | byte1


def find_free_space(size, start_address=0, ending=0):
    working_address = start_address
    while 1:
        rom.seek(working_address)
        found = 1
        i = 0
        while found == 1:
            if i == size + ending:
                working_address = working_address - size - ending

                if (ending != 0) and (working_address % ending != 0):
                    working_address += working_address % ending

                return working_address
            if rom.read_byte() != 255:
                found = 0

            i += 1
            working_address += 1


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
    try:
        pos = 0
        while 1:
            rom.seek(pos)
            if check_pointer(pos):
                if pointer_to_address(pos) == pointing_address:
                    if search_for_all is None:
                        # Once its finds a pointer, it returns it
                        return pos
                    else:
                        pointers_address.append(pos)

            pos += 1
    except IndexError:
        if search_for_all:
            return pointers_address
        print("\nCouldn't find Pointer for address: " + capitalized_hex(pointing_address) + '\n')
        return pointers_address[0]


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
