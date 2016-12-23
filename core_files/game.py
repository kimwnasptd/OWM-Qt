#! /usr/bin/env python
"""
To organize all info about the game/ROM file in one place / Cosarara97's file
"""


class Game:
    def __init__(self, fn=None):
        self.rom_contents = None
        self.original_rom_contents = None
        self.rom_file_name = None
        self.rom_code = None
        self.rom_data = None
        self.name = None
        self.is_rom_open = 0
        self.rom_path = ""

        self.pos = 0

        if fn is not None:
            self.load_rom(fn)

    def load_rom(self, fn):
        with open(fn, "rb") as rom_file:
            self.rom_contents = rom_file.read()
        self.original_rom_contents = bytes(self.rom_contents)

        self.rom_contents = bytearray(self.rom_contents)
        self.rom_file_name = fn
        self.rom_code = self.rom_contents[0xAC:0xAC+4]

    def seek(self, pos):
        self.pos = pos

    def read_byte(self):
        self.pos += 1
        return int(self.rom_contents[self.pos - 1])

    def write_byte(self, val):
        if 0 <= val <= 255:
            self.rom_contents[self.pos] = val
            self.pos += 1

    def flush(self):
        pass

    def pos(self):
        return self.pos
        

