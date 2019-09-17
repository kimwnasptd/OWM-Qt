from PIL import Image
import core_files.core as core
import core_files.rom_api as rom
import core_files.statusbar as sts
import core_files.conversions as conv


def write_two_pixels(index1, index2, addr):
    # Index <= 0xF
    index2 *= 16
    rom.write_byte(addr, index1 + index2)


def import_frame(im, addr, ow_type, row_grid=0, column_grid=0):
    if ow_type == core.T16x32:
        row = 4
        col = 2
    elif ow_type == core.T32x32:
        row = 4
        col = 4
    elif ow_type == core.T16x16:
        row = 2
        col = 2
    elif ow_type == core.T64x64:
        row = 8
        col = 8
    elif ow_type == core.T128x64:
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

                    byte1 = im.getpixel((
                        (c * 8) + j + column_grid, (r * 8) + i + row_grid))
                    byte2 = im.getpixel((
                        (c * 8) + j + 1 + column_grid, (r * 8) + i + row_grid))

                    write_two_pixels(byte1, byte2, addr)
                    addr += 1


# === ============== ===
# Palette Functions
def get_orig_palette_num():
    name_raw = rom.get_word(0xA8)
    rom_name = conv.capitalized_hex(name_raw)[2:]  # Removes the 0x
    name = conv.hex_to_text(rom_name)
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
    return rom.read_half(addr + 4)


def write_palette_id(addr, palette_id):
    byte1 = int(palette_id / 256)
    byte2 = int(palette_id % 256)
    rom.write_bytes(addr + 4, [byte2, byte1])


def is_palette_table_end(addr):
    if sum(rom.read_bytes(addr, 4)) == 0:
        if rom.read_bytes(addr + 4, 2) == [0xff, 0x11]:
            return 1
        else:
            return 0

    if not is_palette_ptr(addr):
        return 1
    return 0


def is_palette_ptr(addr):
    palette_ptr = 1
    try:
        if rom.is_ptr(addr) != 1:
            palette_ptr = 0

        if rom.read_byte(addr + 5) != 0x11:
            palette_ptr = 0
        if rom.read_byte(addr + 6) != 0x0:
            palette_ptr = 0
        if rom.read_byte(addr + 7) != 0x0:
            palette_ptr = 0
    except IndexError:
        return 0
    return palette_ptr


def write_palette_table_end(addr):
    rom.write_bytes(addr, [0x0, 0x0, 0x0, 0x0, 0xFF, 0x11, 0x0, 0x0])


def remove_palette(palette_addr):
    # Remove the color data
    rom.fill_with_data(rom.ptr_to_addr(palette_addr), 32, 0xFF)

    # Move all the other palettes left (the palette to be removed will
    # be just be replaced)
    working_addr = palette_addr + 8
    while not is_palette_table_end(working_addr):
        # Move the palette data left
        rom.move_data(working_addr, working_addr - 8, 8, 0x0)
        working_addr += 8
    rom.move_data(working_addr, working_addr - 8, 8, 0x0)


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
    r = (red >> 3) & 31
    g = ((green >> 3) & 31) << 5
    b = ((blue >> 3) & 31) << 10
    gba_color = r | g | b

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
        if (bg_color[0] == palette[k]) and (bg_color[1] == palette[k + 1]) \
                and (bg_color[2] == palette[k + 2]):
            break

    bg_index = int(k / 3)
    swap_colors(0, bg_index, palette, image)


def write_color(color, addr):
    rom.write_bytes(addr, color)


def byte_to_pixels(byte):
    pixel1 = int(byte / 16)
    pixel2 = byte % 16

    return pixel2, pixel1


def create_image_from_addr(im_addr, width, height):
    row = int(height / 8)
    column = int(width / 8)

    obj = Image.new("P", (width, height))
    step = 0
    for r in range(0, row):
        # Number of horizontal 8X8 squares

        for c in range(0, column):
            # Number of vertical 8x8 squares

            for i in range(0, 8):
                # Number of rows in the square

                for j in range(0, 7, 2):
                    # Number of columns in the square
                    byte = rom.read_byte(im_addr + step)
                    step += 1

                    pixel1, pixel2 = byte_to_pixels(byte)
                    obj.putpixel(((c * 8) + j, (r * 8) + i), pixel1)
                    obj.putpixel(((c * 8) + j + 1, (r * 8) + i), pixel2)

    return obj


def create_palette_from_gba(palette_addr):
    palette = []
    for i in range(0, 16):
        byte1 = rom.read_byte(palette_addr + i*2)
        byte2 = rom.read_byte(palette_addr + i*2 + 1)

        color = byte1 * 256 + byte2
        red, green, blue = gba_to_rgb(color)

        palette.append(red)
        palette.append(green)
        palette.append(blue)

    return palette


# === Classes ===
class PaletteManager:
    table_addr = 0x0
    palette_num = 0
    max_size = 0
    free_slots = 0
    used_palettes = []
    root = None

    def __init__(self, root):
        self.root = root
        self.table_addr = rom.ptr_to_addr(rom.PAL_TBL_PTRS[0])
        self.palette_num = self.get_palette_num()
        self.max_size = self.get_max_size()
        self.free_slots = self.max_size - self.palette_num\

        if self.free_slots == 0:
            print("Repointing the Palette Table")
            sts.show("Updating the Free Space Address for Palettes")
            rom.update_free_space(self.palette_num * 10)
            self.repoint_palette_table()

        self.set_used_palettes()

    def set_used_palettes(self):

        self.used_palettes = []

        working_addr = self.table_addr

        while is_palette_table_end(working_addr) == 0 and \
                is_palette_ptr(working_addr):
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
            for j in range(0, 8):
                adder += rom.read_byte(addr + j)

            if adder != 0:
                done = 1
            else:
                addr += 8
                i += 1
        return i

    def get_palette_num(self):
        working_addr = self.table_addr
        i = 0

        while is_palette_table_end(working_addr) == 0 and \
                rom.is_ptr(working_addr):
            if rom.is_ptr(working_addr) == 1:
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

    def get_used_pals(self):
        used_pals = set()
        # Search all the tables
        for table in self.root.tables_list:
            for ow in table.ow_data_ptrs:
                used_pals.add(core.get_ow_palette_id(ow.ow_data_addr))
        return used_pals

    def insert_rgb_to_gba_palette(self, palette):

        # Write the palette to the ROM
        palette_addr = rom.find_free_space(16 * 4, rom.FREE_SPC, 2)

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
        rom.move_data(table_end, table_end + 8, 8, 0)

        palette_id = self.get_max_palette_id() + 1
        # Make sure that the palette id is NOT
        # 0x11FF -> FF 11 (Palette Table End)
        if palette_id == 0x11FF:
            palette_id += 1

        rom.write_ptr(colors_addr, table_end)
        write_palette_id(table_end, palette_id)
        rom.write_bytes(table_end + 6, [0x0, 0x0])

    def repoint_palette_table(self):

        num_of_palettes = self.get_palette_num()
        # 9 = 8[palette end] + 1[table end]
        space_needed = (num_of_palettes * 8) + (256 * 8) + 9
        new_table_addr = rom.find_free_space(space_needed, rom.FREE_SPC, 4)

        # Insert 00s in the new table addr
        rom.fill_with_data(new_table_addr, space_needed + 2, 0)
        # Move the table's data
        rom.move_data(self.table_addr,
                      new_table_addr,
                      (num_of_palettes * 8) + 8)
        # Write the end of table
        rom.write_bytes(new_table_addr + (num_of_palettes * 8) + 4,
                        [0xFF, 0x11])

        # Change the ptrs pointing the table
        for ptr_addr in rom.PAL_TBL_PTRS:
            rom.write_ptr(new_table_addr, ptr_addr)

        # Change the OBJ's table_addr var
        self.table_addr = new_table_addr
        self.set_used_palettes()


class ImageManager(PaletteManager):
    def __init__(self, root):
        PaletteManager.__init__(self, root)

    def make_image_from_rom(self, working_ow, working_table):
        ow = self.root.getOW(working_table, working_ow)
        frames = ow.frames.get_num()
        ow_type = ow.frames.get_type()
        width, height = core.get_frame_dimensions(ow_type)

        final = Image.new('P', (width * frames, height))

        for i in range(0, frames):
            frames_addr = ow.frames.frames_addr
            im_addr = (i * core.get_frame_size(ow_type)) + frames_addr
            im = create_image_from_addr(im_addr, width, height)

            final.paste(im, (width * i, 0))

        return final

    def import_pokemon(self, pokemon_image, working_table, working_ow):
        '''
        Import a pokemon that is taken from Spriter's Resource sheets.
        The pokemon_image will be a square that has all the different sides
        of the pokemon. This function will map the tiles of the image to the
        correct OW's images/sides.
        '''
        # Check if the image is indexed
        palette = pokemon_image.getpalette()
        if palette is None:
            pokemon = pokemon_image.convert('P',
                                            palette=Image.ADAPTIVE,
                                            colors=16)
        else:
            pokemon = pokemon_image

        make_bg_color_first(pokemon)
        palette = pokemon.getpalette()

        # Insert the palette
        self.import_palette(palette)
        palette_id = self.get_max_palette_id()

        ow = self.root.getOW(working_table, working_ow)
        core.write_ow_palette_id(ow.ow_data_addr, palette_id)

        working_addr = ow.frames.frames_addr

        positions = [(3, 0), (0, 0), (1, 1), (3, 0), (2, 0),
                     (1, 0), (0, 0), (1, 1), (0, 1)]
        for pos in positions:
            row = pos[0] * 32
            column = pos[1] * 32
            working_addr += core.get_frame_size(2)
            import_frame(pokemon, working_addr, core.T32x32, row, column)

        self.set_used_palettes()

    def import_ow(self, ow_image, working_table, working_ow):
        '''
        Import an OW that is taken from Spriter's Resource sheets. The ow_image
        will be a square that has the sides of the OW. It was designed with the
        HGSS sprites in mind.
        '''
        # Check if the image is indexed
        palette = ow_image.getpalette()
        if palette is None:
            ow_image_indexed = ow_image.convert('P',
                                                palette=Image.ADAPTIVE,
                                                colors=16)
        else:
            ow_image_indexed = ow_image

        make_bg_color_first(ow_image_indexed)
        palette = ow_image_indexed.getpalette()
        ow = self.root.getOW(working_table, working_ow)

        # Insert the palette
        self.import_palette(palette)
        palette_id = self.get_max_palette_id()
        core.write_ow_palette_id(ow.ow_data_addr, palette_id)

        # Insert the 9 frames
        positions = [(1, 2), (0, 0), (2, 0), (3, 2), (2, 2),
                     (0, 2), (3, 1), (1, 0), (3, 0)]
        working_addr = ow.frames.frames_addr
        for pos in positions:
            row = pos[0] * 32
            column = pos[1] * 32
            working_addr += core.get_frame_size(2)
            import_frame(ow_image_indexed,
                         working_addr,
                         core.T32x32,
                         row, column)

        self.set_used_palettes()

    def import_sprites(self, sprite_image, working_table, working_ow):
        # Check if the image is indexed
        palette = sprite_image.getpalette()
        if palette is None:
            sprite = sprite_image.convert('P',
                                          palette=Image.ADAPTIVE,
                                          colors=16)
        else:
            sprite = sprite_image

        make_bg_color_first(sprite)
        palette = sprite.getpalette()

        # Insert the palette
        self.import_palette(palette)
        palette_id = self.get_max_palette_id()

        ow = self.root.getOW(working_table, working_ow)
        core.write_ow_palette_id(ow.ow_data_addr, palette_id)

        # Import the frames
        working_addr = ow.frames.frames_addr
        num_of_frames = ow.frames.get_num()
        sprite_type = ow.frames.get_type()
        dimensions = core.get_frame_dimensions(sprite_type)
        frame_width = dimensions[0]

        row = 0
        for i in range(0, num_of_frames):
            column = i * frame_width
            import_frame(sprite, working_addr, sprite_type, row, column)

            working_addr += core.get_frame_size(sprite_type)

        self.set_used_palettes()

    def palette_cleanup(self):
        orig_pals_num = get_orig_palette_num()
        palette_num = self.get_palette_num()
        users_palettes = palette_num - orig_pals_num

        # Get the addres of the non-used palettes
        used_palettes = self.get_used_pals()

        # Find the addresses of the unused palettes
        unused_palettes_addres = []
        working_addr = self.table_addr + (orig_pals_num * 8)
        for i in range(0, users_palettes):
            palette_id = get_palette_id(working_addr + (i * 8))
            # Check every palette to see if it is used
            if palette_id not in used_palettes:
                print("Image: Removing pal: " + conv.HEX(palette_id))
                unused_palettes_addres.append(working_addr + (i * 8))

        # Delete all the unused palettes
        for addr in reversed(unused_palettes_addres):
            remove_palette(addr)

        self.set_used_palettes()

    def get_ow_frame(self, ow_num, table_num, frame_num):
        ow = self.root.getOW(table_num, ow_num)
        ow_type = ow.frames.get_type()
        frames_addr = ow.frames.frames_addr
        width, height = core.get_frame_dimensions(ow_type)

        # For the palette
        palette_id = core.get_ow_palette_id(ow.ow_data_addr)
        palette_addr = self.get_palette_addr(palette_id)
        sprite_palette = create_palette_from_gba(rom.ptr_to_addr(palette_addr))
        frame_size = core.get_frame_size(ow_type)

        image = create_image_from_addr((frame_num * frame_size) + frames_addr,
                                       width,
                                       height)
        image.putpalette(sprite_palette)

        return image
