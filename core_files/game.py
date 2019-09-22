#! /usr/bin/env python
"""
To organize all info about the game/ROM file in one place / Cosarara97's file
"""


class Game:
    def __init__(self, fn=None):
        self.rom_contents = None
        self.original_rom_contents = None
        self.layered_reserved_rom_contents = None
        self.rom_file_name = None
        self.rom_code = None
        self.rom_data = None
        self.name = None
        self.is_rom_open = 0
        self.rom_path = ""
        self.rom_size = 0

        self.pos = 0

        if fn is not None:
            self.load_rom(fn)

    def load_rom(self, fn):
        with open(fn, "rb") as rom_file:
            self.rom_contents = rom_file.read()
        self.original_rom_contents = bytes(self.rom_contents)

        self.rom_contents = bytearray(self.rom_contents)
        self.rom_size = len(self.rom_contents)
        self.rom_file_name = fn
        self.rom_code = self.rom_contents[0xAC:0xAC+4]
        self.layered_reserved_rom_contents = [0xFF for b in
                                              range(self.rom_size)]

    def update_layered_rom_contents(self, reserved_ranges):
        self.layered_reserved_rom_contents = [0xFF for b in
                                              range(self.rom_size)]

        # Set to 0x01 the bytes in the reserved_ranges
        for rng in reserved_ranges:
            for b in range(rng[0], rng[1]):
                self.layered_reserved_rom_contents[b] = 0x01

    def seek(self, pos):
        if pos > self.rom_size:
            raise IndexError
        self.pos = pos

    def read_byte(self):
        self.pos += 1
        return int(self.rom_contents[self.pos - 1])

    def write_byte(self, val):
        if 0 <= val <= 255:
            self.rom_contents[self.pos] = val
            self.pos += 1

    def check_byte(self, addr, val):
        try:
            self.seek(addr)
            if self.read_byte() == val:
                return 1
            return 0
        except IndexError:
            return 0

    def check_free_byte(self, addr):
        try:
            self.seek(addr)
            if self.read_byte() == 0xFF and\
                    self.layered_reserved_rom_contents[addr] == 0xFF:
                return True
            return False
        except IndexError:
            return False

    def pos(self):
        return self.pos
