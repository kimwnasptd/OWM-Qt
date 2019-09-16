from core_files.game import Game
from core_files.core import Root

rom = Game()
root = Root()


def initRom(new_rom):
    global rom
    rom = new_rom


def initRoot(new_root):
    global root
    root = new_root


def resetRoot():
    global root
    root.__init__()
