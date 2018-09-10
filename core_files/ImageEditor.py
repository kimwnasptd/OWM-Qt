from PIL import Image
from core_files.core import *
from core_files.rom_api import *


PAL_TBL_PTRS = []
ORIG_PALS_NUM = 0
FREE_SPC = 0

global root
root = Root()

def initRoot(new_root):
    global root
    root = new_root

def resetRoot():
    global root
    root.__init__()

def OW(table_id, ow_id):
    return root.tables_list[table_id].ow_data_ptrs[ow_id]

def TABLE(table_id):
    return root.tables_list[table_id]

def change_image_editor_info(ptrs_list):
    global PAL_TBL_PTRS
    PAL_TBL_PTRS = ptrs_list
    ORIG_PALS_NUM = get_orig_palette_num()

def update_free_space(size, start_addr=FREE_SPC):
    global FREE_SPC
    FREE_SPC = find_free_space(size, start_addr, 2)

def write_two_pixels(index1, index2, addr):
    # Index <= 0xF
    index2 *= 16
    write_byte(addr, index1 + index2)

def import_frame(im, addr, ow_type, row_grid=0, column_grid=0):
    if ow_type == 1:
        row = 4
        col = 2
    elif ow_type == 2:
        row = 4
        col = 4
    elif ow_type == 3:
        row = 2
        col = 2
    elif ow_type == 4:
        row = 8
        col = 8
    elif ow_type == 5:
        row = 8
        col = 16
    else:
        row = 6
        col = 6

    for r in range(0, row):
        # Number of horizontal 8X8 squares

        for c in range(0, col):
            # Number of vertical 8x8 squares

            for i in range(0, 8):
                # Number of rows in the square

                for j in range(0, 7, 2):
                    # Number of columns in the square

                    byte1 = im.getpixel(((c * 8) + j + column_grid, (r * 8) + i + row_grid))
                    byte2 = im.getpixel(((c * 8) + j + 1 + column_grid, (r * 8) + i + row_grid))

                    write_two_pixels(byte1, byte2, addr)
                    addr += 1


# === ============== ===
# Palette Functions
def get_orig_palette_num():
    name_raw = get_word(0xA8)
    rom_name = capitalized_hex(name_raw)[2:]  # Removes the 0x
    name = hex_to_text(rom_name)
    print("NAME: "+name)

    if name in ["FIRE", "LEAF"]:
        return 18
    elif name in ["RUBY", "SAPP"]:
        return 27
    elif name == "EMER":
        return 35
    else:
        return None

def get_palette_id(addr):
    return read_half(addr + 4)

def write_palette_id(addr, palette_id):
    byte1 = int(palette_id / 256)
    byte2 = int(palette_id % 256)
    write_bytes(addr + 4, [byte2, byte1])

def is_palette_table_end(addr):
    rom.seek(addr)

    # test = rom.read_byte() + rom.read_byte() + rom.read_byte() + rom.read_byte()
    test = sum(read_bytes(addr, 4))
    if test == 0:
        if rom.read_byte() == 0xFF:
            return 1

    if not is_palette_ptr(addr):
        return 1
    return 0

def is_palette_ptr(addr):

    palette_ptr = 1
    try:
        if is_ptr(addr) != 1:
            palette_ptr = 0

        rom.seek(addr + 5)
        if rom.read_byte() != 0x11:
            palette_ptr = 0
        if rom.read_byte() != 0x0:
            palette_ptr = 0
        if rom.read_byte() != 0x0:
            palette_ptr = 0
    except IndexError:
        return 0
    return palette_ptr

def write_palette_table_end(addr):
    write_bytes(addr, [0x0, 0x0, 0x0, 0x0, 0xFF, 0xFF, 0x0, 0x0])

def replace_palette_id_in_ows(old_palette_id, new_palette_id):
    # Replaces the old palette with the new palette number in all the OWs

    for ow_table in root.tables_list:
        # Browse through all the Tables

        for ow in ow_table.ow_data_ptrs:
            # Browse through all the OWs

            if get_ow_palette_id(ow.ow_data_addr) == old_palette_id:
                # The OW has the specific Palette ID

                write_ow_palette_id(ow.ow_data_addr, new_palette_id)

def remove_palette(palette_addr):
    # Remove the color data
    fill_with_data(ptr_to_addr(palette_addr), 32, 0xFF)

    # Move all the other palettes left (the palette to be removed will be just be replaced
    working_addr = palette_addr + 8
    done = 0

    while done == 0:

        # Move the palette data left
        move_data(working_addr, working_addr - 8, 8, 0)

        # If the palette that moved left is the end of the table, break the loop
        if is_palette_table_end(working_addr - 8) == 1:
            done = 1

        # Set the working_addr to the addr of the next table
        working_addr += 8

def get_background_color(image):
    im_palette = image.getpalette()
    indexed_palette = im_palette[:48]

    # Get the Index of the background
    bg_index = image.getpixel((0, 0))

    color = [0, 0, 0]
    for i in range(0, 3):
        color[i] = indexed_palette[(3 * bg_index) + i]

    return color

def rgb_to_gba(red, green, blue):
    gba_color = (((red >> 3) & 31) | (((green >> 3) & 31) << 5) | (((blue >> 3) & 31) << 10))

    byte1 = gba_color % 256
    byte2 = int(gba_color / 256)

    return byte1, byte2

def gba_to_rgb(gba_color):
    # Switch the two bytes (gba logic :p)
    byte1 = gba_color % 256
    byte2 = int(gba_color / 256)
    gba_color = (byte1 * 256) + byte2

    red = (gba_color & 31) << 3
    green = ((gba_color >> 5) & 31) << 3
    blue = ((gba_color >> 10) & 31) << 3

    rgb_color = (red, green, blue)
    return rgb_color

def swap_colors(id1, id2, palette, image):
    t1 = palette[id1 * 3]
    t2 = palette[(id1 * 3) + 1]
    t3 = palette[(id1 * 3) + 2]

    palette[id1 * 3] = palette[(id2 * 3)]
    palette[(id1 * 3) + 1] = palette[(id2 * 3) + 1]
    palette[(id1 * 3) + 2] = palette[(id2 * 3) + 2]

    palette[(id2 * 3)] = t1
    palette[(id2 * 3) + 1] = t2
    palette[(id2 * 3) + 2] = t3

    image.putpalette(palette)

    # Change the image pixels accordingly
    for i in range(0, image.width):
        for j in range(0, image.height):
            if image.getpixel((i, j)) == id1:
                image.putpixel((i, j), id2)
            elif image.getpixel((i, j)) == id2:
                image.putpixel((i, j), id1)

def make_bg_color_first(image):
    bg_color = get_background_color(image)
    palette = image.getpalette()
    palette = palette[:48]

    # Get the index of the bg color in the palette
    for k in range(0, 48, 3):
        if (bg_color[0] == palette[k]) and (bg_color[1] == palette[k + 1]) and (bg_color[2] == palette[k + 2]):
            break

    bg_index = int(k / 3)
    swap_colors(0, bg_index, palette, image)

def write_color(color, addr):
    write_bytes(addr, color)

def byte_to_pixels(byte):
    pixel1 = int(byte / 16)
    pixel2 = byte % 16

    return pixel2, pixel1

def create_image_from_addr(im_addr, width, height):
    row = int(height / 8)
    column = int(width / 8)

    obj = Image.new("P", (width, height))

    global rom
    rom.seek(im_addr)
    for r in range(0, row):
        # Number of horizontal 8X8 squares

        for c in range(0, column):
            # Number of vertical 8x8 squares

            for i in range(0, 8):
                # Number of rows in the square

                for j in range(0, 7, 2):
                    # Number of columns in the square
                    byte = rom.read_byte()

                    pixel1, pixel2 = byte_to_pixels(byte)
                    obj.putpixel(((c * 8) + j, (r * 8) + i), pixel1)
                    obj.putpixel(((c * 8) + j + 1, (r * 8) + i), pixel2)

    return obj

def make_image_from_rom(working_ow, working_table):
    frames = root.tables_list[working_table].ow_data_ptrs[working_ow].frames.get_num()
    ow_type = root.tables_list[working_table].ow_data_ptrs[working_ow].frames.get_type()
    width, height = get_frame_dimensions(ow_type)

    final = Image.new('P', (width * frames, height))

    for i in range(0, frames):
        frames_addr = root.tables_list[working_table].ow_data_ptrs[working_ow].frames.frames_addr
        im_addr = (i * get_frame_size(ow_type)) + frames_addr

        im = create_image_from_addr(im_addr, width, height)

        final.paste(im, (width * i, 0))

    return final

def create_palette_from_gba(palette_addr):
    global rom
    rom.seek(palette_addr)
    palette = []

    for i in range(0, 16):
        byte1 = rom.read_byte()
        byte2 = rom.read_byte()

        color = byte1 * 256 + byte2
        red, green, blue = gba_to_rgb(color)

        palette.append(red)
        palette.append(green)
        palette.append(blue)

    return palette

def is_palette_used(palette_id):
    global root
    # Search all the tables
    for table in root.tables_list:
        # Search all the ows
        for ow in table.ow_data_ptrs:
            if get_ow_palette_id(ow.ow_data_addr) == palette_id:
                return 1
    return 0


# === Classes ===
class PaletteManager:
    table_addr = 0x0
    palette_num = 0
    max_size = 0
    free_slots = 0
    used_palettes = []

    def __init__(self):
        self.table_addr = ptr_to_addr(PAL_TBL_PTRS[0])
        self.palette_num = self.get_palette_num()
        self.max_size = self.get_max_size()
        self.free_slots = self.max_size - self.palette_num

        if self.free_slots == 0:
            print("Repointing the Palette Table")
            SHOW("Updating the Free Space Address for Palettes")
            update_free_space(self.palette_num*10)
            self.repoint_palette_table()

        self.set_used_palettes()

    def set_used_palettes(self):

        self.used_palettes = []

        working_addr = self.table_addr

        while is_palette_table_end(working_addr) == 0 and is_palette_ptr(working_addr):
            self.used_palettes.append(get_palette_id(working_addr))
            working_addr += 8

    def get_table_end(self):
        working_addr = self.table_addr

        while is_palette_table_end(working_addr) == 0:
            working_addr += 8

        return working_addr

    def get_max_size(self):
        # Go to the end of the table
        working_addr = self.table_addr
        while is_palette_table_end(working_addr) == 0:
            working_addr += 8
        working_addr += 8
        # Now we are after the end of the palette table

        i = self.get_free_slots()

        return self.palette_num + i

    def get_free_slots(self):
        addr = self.table_addr + self.get_palette_num() * 8 + 8

        i = 0
        done = 0
        while done == 0:
            adder = 0
            rom.seek(addr)
            for j in range(0, 8):
                adder += rom.read_byte()

            if adder != 0:
                done = 1
            else:
                addr += 8
                i += 1
        return i

    def get_palette_num(self):
        working_addr = self.table_addr
        i = 0

        while is_palette_table_end(working_addr) == 0 and is_ptr(working_addr):
            if is_ptr(working_addr) == 1:
                i += 1
            working_addr += 8

        return i

    def get_max_palette_id(self):
        max_id = -1
        working_addr = self.table_addr

        while is_palette_table_end(working_addr) == 0:
            if get_palette_id(working_addr) > max_id:
                # Found new max
                max_id = get_palette_id(working_addr)

            working_addr += 8

        return max_id

    def get_palette_addr(self, palette_id):

        working_addr = self.table_addr

        while is_palette_table_end(working_addr) == 0:

            if get_palette_id(working_addr) == palette_id:
                return working_addr

            working_addr += 8

        return 0

    def insert_rgb_to_gba_palette(self, palette):

        # Write the palette to the ROM
        palette_addr = find_free_space(16 * 4, FREE_SPACE, 2)

        working_addr = palette_addr
        for i in range(0, 48, 3):
            color = rgb_to_gba(palette[i], palette[i + 1], palette[i + 2])

            write_color(color, working_addr)
            working_addr += 2

        return palette_addr

    def import_palette(self, palette):

        # Import the palette in the ROM
        colors_addr = self.insert_rgb_to_gba_palette(palette)

        # Import the palette in the palette table
        table_end = self.get_table_end()
        move_data(table_end, table_end + 8, 8, 0)

        palette_id = self.get_max_palette_id() + 1
        # Make sure that the palette id is NOT 0x11FF -> FF 11 (Palette Table End)
        if palette_id == 0x11FF:
            palette_id += 1

        write_ptr(colors_addr, table_end)
        write_palette_id(table_end, palette_id)
        write_bytes(table_end + 6, [0x0, 0x0])

    def repoint_palette_table(self):

        num_of_palettes = self.get_palette_num()
        space_needed = (num_of_palettes * 8) + (256 * 8) + 9  # 9 = 8[palette end] + 1[table end]
        new_table_addr = find_free_space(space_needed, FREE_SPC, 4)

        # Insert 00s in the new table addr
        fill_with_data(new_table_addr, space_needed + 2, 0)
        # Move the table's data
        move_data(self.table_addr, new_table_addr, (num_of_palettes * 8) + 8)
        # Write the end of table
        write_bytes(new_table_addr + (num_of_palettes * 8) + 4, [0xFF, 0x11])

        # Change the ptrs pointing the table
        global PAL_TBL_PTRS
        for ptr_addr in PAL_TBL_PTRS:
            write_ptr(new_table_addr, ptr_addr)

        # Change the OBJ's table_addr var
        self.table_addr = new_table_addr
        self.set_used_palettes()


class ImageManager(PaletteManager):
    def __init__(self):
        PaletteManager.__init__(self)

    def import_pokemon(self, pokemon_image, working_table, working_ow):
        # Check if the image is indexed
        palette = pokemon_image.getpalette()
        if palette is None:
            pokemon = pokemon_image.convert('P', palette=Image.ADAPTIVE, colors=16)
        else:
            pokemon = pokemon_image

        make_bg_color_first(pokemon)
        palette = pokemon.getpalette()

        # Insert the palette
        self.import_palette(palette)
        palette_id = self.get_max_palette_id()
        write_ow_palette_id(root.tables_list[working_table].ow_data_ptrs[working_ow].ow_data_addr, palette_id)

        working_addr = root.tables_list[working_table].ow_data_ptrs[working_ow].frames.frames_addr
        row = 3 * 32
        column = 0 * 32

        # Insert the frames
        import_frame(pokemon, working_addr, 2, row, column)

        # 2nd Frame
        row = 0 * 32
        column = 0 * 32
        working_addr += get_frame_size(2)
        import_frame(pokemon, working_addr, 2, row, column)

        # 3d Frame
        row = 1 * 32
        column = 1 * 32
        working_addr += get_frame_size(2)
        import_frame(pokemon, working_addr, 2, row, column)

        # 4th Frame
        row = 3 * 32
        column = 0 * 32
        working_addr += get_frame_size(2)
        import_frame(pokemon, working_addr, 2, row, column)

        # 5th Frame
        row = 2 * 32
        column = 0 * 32
        working_addr += get_frame_size(2)
        import_frame(pokemon, working_addr, 2, row, column)

        # 6th Frame
        row = 1 * 32
        column = 0 * 32
        working_addr += get_frame_size(2)
        import_frame(pokemon, working_addr, 2, row, column)

        # 7th Frame
        row = 0 * 32
        column = 0 * 32
        working_addr += get_frame_size(2)
        import_frame(pokemon, working_addr, 2, row, column)

        # 8th Frame
        row = 1 * 32
        column = 1 * 32
        working_addr += get_frame_size(2)
        import_frame(pokemon, working_addr, 2, row, column)

        # 9th Frame
        row = 0 * 32
        column = 1 * 32
        working_addr += get_frame_size(2)
        import_frame(pokemon, working_addr, 2, row, column)

        self.set_used_palettes()

    def import_sprites(self, sprite_image, working_table, working_ow):
        # Check if the image is indexed
        palette = sprite_image.getpalette()
        if palette is None:
            sprite = sprite_image.convert('P', palette=Image.ADAPTIVE, colors=16)
        else:
            sprite = sprite_image

        make_bg_color_first(sprite)
        palette = sprite.getpalette()

        # Insert the palette
        self.import_palette(palette)
        palette_id = self.get_max_palette_id()
        write_ow_palette_id(root.tables_list[working_table].ow_data_ptrs[working_ow].ow_data_addr, palette_id)

        # Import the frames
        working_addr = root.tables_list[working_table].ow_data_ptrs[working_ow].frames.frames_addr

        num_of_frames = root.tables_list[working_table].ow_data_ptrs[working_ow].frames.get_num()
        sprite_type = root.tables_list[working_table].ow_data_ptrs[working_ow].frames.get_type()
        dimensions = get_frame_dimensions(sprite_type)
        frame_width = dimensions[0]

        row = 0
        for i in range(0, num_of_frames):
            column = i * frame_width
            import_frame(sprite, working_addr, sprite_type, row, column)

            working_addr += get_frame_size(sprite_type)

        self.set_used_palettes()

    def import_ow(self, ow_image, working_table, working_ow):
        # Check if the image is indexed
        palette = ow_image.getpalette()
        if palette is None:
            ow_image_indexed = ow_image.convert('P', palette=Image.ADAPTIVE, colors=16)
        else:
            ow_image_indexed = ow_image

        make_bg_color_first(ow_image_indexed)
        palette = ow_image_indexed.getpalette()

        # Insert the palette
        self.import_palette(palette)
        palette_id = self.get_max_palette_id()
        write_ow_palette_id(root.tables_list[working_table].ow_data_ptrs[working_ow].ow_data_addr, palette_id)

        working_addr = root.tables_list[working_table].ow_data_ptrs[working_ow].frames.frames_addr
        row = 1 * 32
        column = 2 * 32

        # Insert the frames
        import_frame(ow_image_indexed, working_addr, 2, row, column)

        # 2nd Frame
        row = 0 * 32
        column = 0 * 32
        working_addr += get_frame_size(2)
        import_frame(ow_image_indexed, working_addr, 2, row, column)

        # 3d Frame
        row = 2 * 32
        column = 0 * 32
        working_addr += get_frame_size(2)
        import_frame(ow_image_indexed, working_addr, 2, row, column)

        # 4th Frame
        row = 3 * 32
        column = 2 * 32
        working_addr += get_frame_size(2)
        import_frame(ow_image_indexed, working_addr, 2, row, column)

        # 5th Frame
        row = 2 * 32
        column = 2 * 32
        working_addr += get_frame_size(2)
        import_frame(ow_image_indexed, working_addr, 2, row, column)

        # 6th Frame
        row = 0 * 32
        column = 2 * 32
        working_addr += get_frame_size(2)
        import_frame(ow_image_indexed, working_addr, 2, row, column)

        # 7th Frame
        row = 3 * 32
        column = 1 * 32
        working_addr += get_frame_size(2)
        import_frame(ow_image_indexed, working_addr, 2, row, column)

        # 8th Frame
        row = 1 * 32
        column = 0 * 32
        working_addr += get_frame_size(2)
        import_frame(ow_image_indexed, working_addr, 2, row, column)

        # 9th Frame
        row = 3 * 32
        column = 0 * 32
        working_addr += get_frame_size(2)
        import_frame(ow_image_indexed, working_addr, 2, row, column)

        self.set_used_palettes()

    def palette_cleanup(self):

        palette_num = self.get_palette_num()
        users_palettes = palette_num - ORIG_PALS_NUM  # The game's original palettes are 18 total

        # Get the addres of the non-used palettes
        unused_palettes_addres = []
        working_addr = self.table_addr + (ORIG_PALS_NUM * 8)
        for i in range(0, users_palettes):
            palette_id = get_palette_id(working_addr + (i * 8))
            # Check every palette to see if it is used
            if is_palette_used(palette_id) == 0:
                unused_palettes_addres.append(working_addr + (i * 8))

        # Delete all the unused palettes
        for addr in reversed(unused_palettes_addres):
            remove_palette(addr)

        self.set_used_palettes()

    def get_ow_frame(self, ow_num, table_num, frame_num):
        ow_type = root.tables_list[table_num].ow_data_ptrs[ow_num].frames.get_type()
        frames_addr = root.tables_list[table_num].ow_data_ptrs[ow_num].frames.frames_addr
        width, height = get_frame_dimensions(ow_type)

        # For the palette
        palette_id = get_ow_palette_id(root.tables_list[table_num].ow_data_ptrs[ow_num].ow_data_addr)
        palette_addr = self.get_palette_addr(palette_id)
        sprite_palette = create_palette_from_gba(ptr_to_addr(palette_addr))
        frame_size = get_frame_size(ow_type)

        image = create_image_from_addr((frame_num * frame_size) + frames_addr, width, height)
        image.putpalette(sprite_palette)

        return image
