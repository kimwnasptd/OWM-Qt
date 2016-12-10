from tkinter import *
from tkinter import filedialog
from tkinter import ttk
from ImageEditor import *
from tkinter import messagebox
from PIL import ImageTk
from IniHandler import *
import webbrowser
from tkinter.colorchooser import *

# Globals: working_table, working_ow, file, rom, app, is_rom_open
is_rom_open = 0
working_table = -1
working_ow = -1
rom_path = ''


class RomInfo:
    name = ""
    palette_table_address = 0x0
    original_ow_table_pointer = 0x0
    original_ow_pointers_address = 0x0
    ow_table_pointer = 0x0
    palette_table_pointer_address = []
    original_num_of_ows = 0x0
    original_num_of_palettes = 0x0
    original_palette_table_address = 0x0
    ow_fix_address = 0x0
    free_space = 0x0
    path = ''
    rom_base = ''
    rom_successfully_loaded = 0

    Profiler = ProfileManager("")

    def __init__(self):

        self.set_name()

        if check_if_name_exists(self.name) == 1:
            self.rom_successfully_loaded = 1

            self.set_info(get_name_line_index(self.name))
            self.Profiler = ProfileManager(self.name)

            # Initialize the OW Table Info
            change_core_info(self.ow_table_pointer, self.original_ow_table_pointer,
                             self.original_num_of_ows, self.original_ow_pointers_address, self.free_space, self.path)

            # Initialize the palette table info
            change_image_editor_info(self.palette_table_pointer_address, self.original_num_of_palettes,
                                     self.original_palette_table_address, self.free_space)

        else:
            message = "Your ROM's base name in 0xAC is [" + self.name + "]." + "\n"
            message += "There is no Profile with such a name in the INI." + '\n'
            message += "Please create a Custom Profile in the INI with that name and the appropriate addresses \n"
            messagebox.showinfo("Can't load Profile from INI", message)

    def set_name(self):

        name_raw = get_word(0xAC)
        rom_name = capitalized_hex(name_raw)[2:]  # Removes the 0x
        self.name = hex_to_text(rom_name)

        # Checks if Rom uses JPAN's Engine
        if pointer_to_address(0x160EE0) == 0x1A2000:
            self.name = "JPAN"

        # Change the name if MrDS
        if self.name == "MrDS":
            self.name = "BPRE"

    def set_info(self, start_pos):

        self.ow_table_pointer = get_line_offset(start_pos + 2)
        self.original_ow_table_pointer = get_line_offset(start_pos + 3)
        self.original_ow_pointers_address = get_line_offset(start_pos + 4)
        self.original_num_of_ows = get_line_offset(start_pos + 5, 1)

        self.palette_table_pointer_address = get_palette_pointers(start_pos + 7)
        self.palette_table_address = pointer_to_address(self.palette_table_pointer_address[0])
        self.original_palette_table_address = get_line_offset(start_pos + 8)
        self.original_num_of_palettes = get_line_offset(start_pos + 9, 1)

        self.ow_fix_address = get_line_offset(start_pos + 11)

        self.free_space = get_line_offset(start_pos + 13)
        self.rom_base = get_line_string(start_pos + 14).split(" = ")[1]

        self.path = 'Files/' + self.rom_base + "/"

    def load_from_profile(self, profile):

        self.set_info(get_name_line_index(profile))

        # Initialize the OW Table Info
        change_core_info(self.ow_table_pointer, self.original_ow_table_pointer,
                         self.original_num_of_ows, self.original_ow_pointers_address, self.free_space, self.path)

        # Initialize the palette table info
        change_image_editor_info(self.palette_table_pointer_address, self.original_num_of_palettes,
                                 self.original_palette_table_address, self.free_space)

        global root, SpriteManager
        root = Root()
        SpriteManager = ImageManager()

        change_core_root(root)
        change_image_root(root)

        global app, working_ow, working_table
        app.OWs.delete(0, "end")
        app.OWList.delete(0, "end")
        app.PaletteCleanup['state'] = 'enabled'

        if root.get_table_num() != 0:
            working_table = 0
        else:
            working_table = -1
        working_ow = -1

        Update_OW_Table_Lists(app)

        Update_OW_Menu_Buttons(0)
        Update_OW_Info(0)
        Update_Table_Info(0)
        Update_Palette_Info(0)
        Update_Table_Menu_Buttons(0)
        Update_Menu_Buttons()

        if root.get_num_of_available_table_pointers() != 0:
            app.Insert_Table_Button['state'] = 'enabled'

    def ow_fix(self):
        # Makes sure more OWs can be added
        if self.ow_fix_address != 0:
            rom.seek(self.ow_fix_address)
            rom.write_byte(255)
            rom.flush()

            message = "Changed byte in " + capitalized_hex(self.ow_fix_address) + " to 0xFF"
            messagebox.showinfo("Completed!", message)

        else:
            message = "The OW Fix Address is set to 0x000000. To apply the fix provide \n"
            message += "the address of the OW Limiter"
            messagebox.showinfo("Can't load Profile from INI", message)


# --- OW Functions ---


def Add_OW():
    global working_ow, working_table
    ow_num = root.tables_list[working_table].ow_data_pointers.__len__()

    if ow_num == 256:
        message = "The table can't have more OWs"
        messagebox.showinfo("Can't Import more OWs", message)
    else:
        window = OWSettings()
        window.attributes("-topmost", True)


def create_ow(window):
    global working_ow, working_table

    ow_type = window.OW_Type_Entry.get()
    num_of_frames = window.OW_Frames_Entry.get()
    num_of_ows = window.OW_Num_Add_Entry.get()

    if ow_type == "":
        ow_type = 0
    if num_of_frames == "":
        num_of_frames = 0
    if num_of_ows == "":
        num_of_ows = 1
    else:
        num_of_ows = int(num_of_ows)

    available_ow_slots = 256 - root.tables_list[working_table].ow_data_pointers.__len__()

    if num_of_ows > available_ow_slots:
        message = "Cant insert that number of OWs\nMax number of OWs a table can hold is 256"
        messagebox.showinfo("Can't Import OWs", message)
    else:
        ow_type = int(ow_type)
        num_of_frames = int(num_of_frames)
        if check_type_availability(ow_type):

            for i in range(0, num_of_ows):
                root.tables_list[working_table].add_ow(ow_type, num_of_frames)

            global app, working_ow
            Update_OWs_List(app)

            # Set the selected items in the list

            app.OWs.selection_set('end')
            app.OWs.see('end')

            ow_selected(app)
            Update_Frames_Spinbox(1)
            Update_Palette_Info(1)
            Update_Viewer(1)
            Update_OW_Info(1)

            if working_ow == -1:
                working_ow = 0

            window.destroy()

        else:
            message = "Please insert a correct type"
            messagebox.showinfo("Can't Import OWs", message)


def Resize():
    window = OWResizeSettings()
    window.attributes("-topmost", True)


def resize_ow(window):
    global working_ow, working_table

    ow_type = window.OW_Type_Entry.get()
    num_of_frames = window.OW_Frames_Entry.get()

    btype = ow_type.isdigit()
    bframes = num_of_frames.isdigit()

    if (btype * bframes) != 0:
        ow_type = int(ow_type)
        num_of_frames = int(num_of_frames)
        if check_type_availability(ow_type):
            slot = get_palette_slot(root.tables_list[working_table].ow_data_pointers[working_ow].ow_data_address)
            root.tables_list[working_table].resize_ow(working_ow, ow_type, num_of_frames)
            write_palette_slot(root.tables_list[working_table].ow_data_pointers[working_ow].ow_data_address, slot)

            global app
            Update_OWs_List(app)

            # Set the selected items in the list
            app.OWs.selection_set(working_ow)
            app.OWs.see(working_ow)

            Update_Palette_Info(1)
            Update_Viewer(1)
            Update_OW_Info(1)
            Update_Frames_Spinbox(1)
            Update_Palette_Slot_Spinbox(1)

            ow_selected(app)

            window.destroy()

        else:
            message = "Please insert a correct type"
            messagebox.showinfo("Can't Import OWs", message)
    else:
        message = "Please insert a correct type"
        messagebox.showinfo("Can't Import OWs", message)


def Insert_OW():
    global working_ow, working_table
    ow_num = root.tables_list[working_table].ow_data_pointers.__len__()

    if ow_num == 256:
        message = "The table can't have more OWs"
        messagebox.showinfo("Can't Import more OWs", message)
    else:
        window = OWInsertSettings()
        window.attributes("-topmost", True)


def Insert_OW_fun(window):
    global working_ow, working_table, app

    ow_type = window.OW_Type_Entry.get()
    num_of_frames = window.OW_Frames_Entry.get()
    num_of_ows = window.OW_Num_Insert_Entry.get()

    if ow_type == "":
        ow_type = 0
    if num_of_frames == "":
        num_of_frames = 0
    if num_of_ows == "":
        num_of_ows = 1
    else:
        num_of_ows = int(num_of_ows)

    available_ow_slots = 256 - root.tables_list[working_table].ow_data_pointers.__len__()

    if num_of_ows > available_ow_slots:
        message = "Cant insert that number of OWs\nMax number of OWs a table can hold is 256"
        messagebox.showinfo("Can't Import OWs", message)
    else:
        ow_type = int(ow_type)
        num_of_frames = int(num_of_frames)
        if check_type_availability(ow_type):

            for i in range(0, num_of_ows):
                root.tables_list[working_table].insert_ow(working_ow, ow_type, num_of_frames)

            Update_OWs_List(app)

            # Set the selected items in the list

            app.OWs.selection_set(working_ow)
            app.OWs.see(working_ow)

            ow_selected(app)
            Update_Frames_Spinbox(1)
            Update_Palette_Info(1)
            Update_Viewer(1)
            Update_OW_Info(1)

            if working_ow == -1:
                working_ow = 0

            window.destroy()

        else:
            message = "Please insert a correct type"
            messagebox.showinfo("Can't Import OWs", message)


def Remove_OW():
    global app, working_ow, working_table

    root.tables_list[working_table].remove_ow(working_ow)
    Update_OWs_List(app)

    # Set the selected items in the list
    n = app.OWs.size()

    if n == working_ow:
        working_ow -= 1

    if working_ow == -1:
        Update_OW_Menu_Buttons(2)
    else:
        app.OWs.selection_set(working_ow)
        app.OWs.see(working_ow)

    ow_selected(app)


def Insert_Table():
    window = TableInsert()
    window.attributes("-topmost", True)


def create_table(layout):
    ow_pointers = layout.Table_pointers_Entr.get()
    data_pointers = layout.Table_Dt_Address_Entr.get()
    frames_pointers = layout.Table_Fr_Ptr_Entry.get()
    frames_address = layout.Table_Frames_Entry.get()

    if ow_pointers == "":
        ow_pointers = 0
    else:
        ow_pointers = int(ow_pointers, 16)

    if data_pointers == "":
        data_pointers = 0
    else:
        data_pointers = int(data_pointers, 16)

    if frames_pointers == "":
        frames_pointers = 0
    else:
        frames_pointers = int(frames_pointers, 16)

    if frames_address == "":
        frames_address = 0
    else:
        frames_address = int(frames_address, 16)

    root.custom_table_import(ow_pointers, data_pointers, frames_pointers, frames_address)

    Update_Palette_Info(0)
    Update_Table_Info(1)

    global app, working_table
    Update_OW_Table_Lists(app)

    working_table = root.get_table_num() - 1
    app.OWList.selection_set(working_table)
    app.OWList.see(working_table)

    ow_table_selected(app)

    layout.destroy()


def remove_table():
    window = RemoveTable()
    window.attributes("-topmost", True)


def yes_remove_table(layout):
    global working_table, working_ow, app

    root.remove_table(working_table)

    Update_OW_Table_Lists(app)

    app.OWs.delete(0, 'end')

    n = root.get_table_num()

    if n == 0:
        working_table = -1

        # Correct the Buttons
        Update_OW_Menu_Buttons(0)
        Update_Sprite_Options_Buttons(0)
        Update_Table_Menu_Buttons(working_table)

        palette_cleanup()
        Update_Palette_Info(0)
        Update_Frames_Spinbox(0)
        Update_OW_Info(0)
        Update_Viewer(0)
        Update_Table_Info(0)
    else:
        app.OWList.selection_set(n - 1)
        app.OWList.selection_set(n - 1)

        ow_table_selected(app)

    layout.destroy()


def ImportSprite():
    image_loc = filedialog.askopenfilename()
    global SpriteManager, working_ow, working_table, Info

    if image_loc != "":
        sprite = Image.open(image_loc)

        # Safety measures
        ow_type = root.tables_list[working_table].ow_data_pointers[working_ow].frames.get_type()
        width, height = get_frame_dimensions(ow_type)
        frames_num = root.tables_list[working_table].ow_data_pointers[working_ow].frames.get_num()

        # Check if it needs to repoint the palette table
        free_slots = SpriteManager.get_free_slots()
        if free_slots == 0:
            SpriteManager.repoint_palette_table()
            Info.palette_table_address = SpriteManager.table_address

        recom_width = width * frames_num

        if height != sprite.height:
            message = "The height should be " + str(height) + ", yours is " + str(sprite.height)
            message += "\nThis means that your image is of different OW Type."
            messagebox.showinfo("File has wrong size", message)
        elif recom_width != sprite.width:
            message = "Your image has a different number of  frames than the OW\n"
            message += "1) Check if the type of the OW is correct.\n2) Check how many frames are in your image"
            messagebox.showinfo("Different number of Frames detected", message)
        else:

            SpriteManager.import_sprites(sprite, working_table, working_ow)
            Update_Viewer(1)
            Update_Frames_Spinbox(1)
            Update_Palette_Info(1)
            Update_OW_Info(1)


def ImportPokemon():
    image_loc = filedialog.askopenfilename()

    if image_loc != "":
        sprite = Image.open(image_loc)

        # Safety measures
        if (sprite.width != 64) or (sprite.height != 128):
            message = "The size should be 64x128, yours is " + str(sprite.width) + "x" + str(sprite.height)
            messagebox.showinfo("File has wrong size", message)
        else:

            global SpriteManager, working_table, working_ow

            free_slots = SpriteManager.get_free_slots()
            if free_slots == 0:
                SpriteManager.repoint_palette_table()
                Info.palette_table_address = SpriteManager.table_address

            ow_type = root.tables_list[working_table].ow_data_pointers[working_ow].frames.get_type()
            frames_num = root.tables_list[working_table].ow_data_pointers[working_ow].frames.get_num()

            if (ow_type != 2) or (frames_num != 9):
                root.tables_list[working_table].resize_ow(working_ow, 2, 9)
                root.__init__()

            SpriteManager.import_pokemon(sprite, working_table, working_ow)

            Update_Viewer(1)
            Update_Frames_Spinbox(1)
            Update_Palette_Info(1)
            Update_Palette_Slot_Spinbox(1)
            Update_OW_Info(1)


def ImportOW():
    image_loc = filedialog.askopenfilename()

    if image_loc != "":
        sprite = Image.open(image_loc)

        # Safety measures
        if (sprite.width != 96) or (sprite.height != 128):
            message = "The size should be 96x128, yours is " + str(sprite.width) + "x" + str(sprite.height)
            messagebox.showinfo("File has wrong size", message)
        else:

            global SpriteManager, working_table, working_ow

            free_slots = SpriteManager.get_free_slots()
            if free_slots == 0:
                SpriteManager.repoint_palette_table()
                Info.palette_table_address = SpriteManager.table_address

            ow_type = root.tables_list[working_table].ow_data_pointers[working_ow].frames.get_type()
            frames_num = root.tables_list[working_table].ow_data_pointers[working_ow].frames.get_num()

            if (ow_type != 2) or (frames_num != 9):
                root.tables_list[working_table].resize_ow(working_ow, 2, 9)
                root.__init__()

            SpriteManager.import_ow(sprite, working_table, working_ow)

            Update_Viewer(1)
            Update_Frames_Spinbox(1)
            Update_Palette_Info(1)
            Update_Palette_Slot_Spinbox(1)
            Update_OW_Info(1)


def palette_cleanup():
    global SpriteManager, working_ow, app
    SpriteManager.palette_cleanup()
    Update_Palette_Info(1)

    frame = app.Frame_Spin.get()
    if working_ow != -1 and frame != '':
        Update_Viewer(1)


def change_palette_slot():
    global app, working_ow, working_table

    slot = int(app.PaletteSlotBox.get())
    data_address = root.tables_list[working_table].ow_data_pointers[working_ow].ow_data_address

    write_palette_slot(data_address, slot)


def save_image():
    global working_ow, working_table

    image = make_image_from_rom(working_ow, working_table)

    # For the Palette
    palette_id = get_ow_palette_id(root.tables_list[working_table].ow_data_pointers[working_ow].ow_data_address)
    palette_address = SpriteManager.get_palette_address(palette_id)
    sprite_palette = create_palette_from_gba(pointer_to_address(palette_address))

    image.putpalette(sprite_palette)

    name = str(working_table) + '_' + str(working_ow)
    file_opt = options = {}
    options['filetypes'] = [('PNG', '.png'), ('BMP', '.bmp')]
    options['initialfile'] = name
    options['title'] = "Save Sprite Frames As..."
    options['defaultextension'] = 'png'

    save_path = filedialog.asksaveasfilename(**file_opt)
    if save_path != '':
        image.save(save_path)


def check_type_availability(ow_type):
    global Info

    if Info.id[:3] == 'BPR' or Info.id == 'JPAN' or Info.id[:3] == 'BPG':
        if (ow_type >= 1) and (ow_type <= 5):
            return 1
        return 0
    elif Info.id[:3] == 'BPE' or Info.id[:3] == 'AXV':
        if (ow_type >= 1) and (ow_type <= 8):
            if ow_type != 5:
                return 1
            return 0


def open_readme():
    webbrowser.open("README.txt")


def show_info():
    window = OWM_Info()
    window.attributes("-topmost", True)


# --- ------------ ---


def open_file():
    rom_name = filedialog.askopenfilename()
    global working_ow, working_table

    if rom_name != "":
        global rom_path
        rom_path = rom_name

        global file, rom, is_rom_open
        # rom.close()
        file.close()
        file = open(rom_name, 'r+b')

        rom = mmap.mmap(file.fileno(), 0)
        change_core_rom(rom)
        change_image_rom(rom)

        is_rom_open = 1

        global root, SpriteManager, Info
        Info = RomInfo()

        if Info.rom_successfully_loaded == 1:

            root = Root()
            SpriteManager = ImageManager()

            change_core_root(root)
            change_image_root(root)

            global app
            app.OWs.delete(0, "end")
            app.OWList.delete(0, "end")
            app.PaletteCleanup['state'] = 'enabled'

            if root.get_table_num() != 0:
                working_table = 0
            else:
                working_table = -1
            working_ow = -1

            Update_OW_Table_Lists(app)

            Update_OW_Menu_Buttons(0)
            Update_OW_Info(0)
            Update_Table_Info(0)
            Update_Palette_Info(0)
            Update_Table_Menu_Buttons(0)
            Update_Rom_Info()
            Update_Menu_Buttons()

            if root.get_num_of_available_table_pointers() != 0:
                app.Insert_Table_Button['state'] = 'enabled'
        else:
            working_ow = -1
            working_table = -1


def ow_selected(parent):
    global working_ow, working_table

    if working_ow != -1:
        working_ow = (parent.OWs.curselection())[0]

        Update_OW_Menu_Buttons(1)
        Update_Sprite_Options_Buttons(1)
        Update_OW_Menu_Buttons(1)
        Update_Frames_Spinbox(1)
        Update_Viewer(1)
        Update_OW_Info(1)
        Update_Palette_Info(1)
        Update_Palette_Slot_Spinbox(1)


def ow_table_selected(parent):
    global working_table, working_ow

    if working_table != -1:
        working_table = (parent.OWList.curselection())[0]
        working_ow = -1

        if working_table != 0:
            parent.Remove_Table_Button['state'] = 'ENABLED'
        else:
            parent.Remove_Table_Button['state'] = 'disabled'

        # Initialise the OWs List
        n = root.tables_list[working_table].ow_data_pointers.__len__()

        parent.OWs.delete(0, "end")
        for i in range(0, n):
            ow = "Overworld " + str(i)
            parent.OWs.insert("end", ow)
            working_ow = 0

        if n != 0:
            working_ow = 0

            parent.OWs.selection_set(working_ow)
            parent.OWs.see(working_ow)

            ow_selected(parent)
        else:
            Update_OW_Menu_Buttons(2)
            Update_Sprite_Options_Buttons(0)
            Update_OW_Info(0)
            Update_Viewer(0)
            Update_Frames_Spinbox(0)
            Update_Palette_Info(0)
            Update_Palette_Slot_Spinbox(0)

        Update_Table_Info(1)


def profile_selected(event):
    if is_rom_open == 1:
        global app, Info

        profile = app.ProfileList.get()
        Info.load_from_profile(profile)


def palette_selected(event):
    global app, working_table, working_ow

    palette_id = app.PaletteIds.get()
    palette_id = int(palette_id, 16)

    ow_data_address = root.tables_list[working_table].ow_data_pointers[working_ow].ow_data_address
    write_ow_palette_id(ow_data_address, palette_id)

    Update_Viewer(1)


def Update_OWs_List(parent):
    # Initialise the OWs List
    n = root.tables_list[working_table].ow_data_pointers.__len__()

    parent.OWs.delete(0, "end")
    for i in range(0, n):
        ow = "Overworld " + str(i)
        parent.OWs.insert("end", ow)


def Update_OW_Table_Lists(parent):
    n = root.get_table_num()

    parent.OWList.delete(0, "end")

    for i in range(0, n):
        table = "OW Table " + str(i)
        parent.OWList.insert("end", table)


def Update_OW_Info(profile):
    global app, working_ow, working_table

    if profile == 1:

        # Overworld Info
        ow_type = root.tables_list[working_table].ow_data_pointers[working_ow].frames.get_type()
        width, height = get_frame_dimensions(ow_type)

        app.Frames_Label['text'] = "Frames: " + str(
                root.tables_list[working_table].ow_data_pointers[working_ow].frames.get_num())
        app.Type_Label['text'] = "Type: " + str(ow_type) + "  [" + str(width) + 'x' + str(height) + ']'
        app.Pointer_Address_Label['text'] = "Pointer Address: " + capitalized_hex(
                root.tables_list[working_table].ow_data_pointers[working_ow].ow_pointer_address)
        app.Data_Address_Label['text'] = "Data Address: " + capitalized_hex(
                root.tables_list[working_table].ow_data_pointers[working_ow].ow_data_address)
        app.Frames_Pointers_Label['text'] = "Frames Pointers: " + capitalized_hex(
                root.tables_list[working_table].ow_data_pointers[working_ow].frames.frames_pointers_address)
        app.Frames_Address_Label['text'] = "Frames Address: " + capitalized_hex(
                root.tables_list[working_table].ow_data_pointers[working_ow].frames.frames_address)


    else:
        app.Frames_Label['text'] = "Frames: "
        app.Type_Label['text'] = "Type: "
        app.Pointer_Address_Label['text'] = "Pointer Address: "
        app.Data_Address_Label['text'] = "Data Address: "
        app.Frames_Pointers_Label['text'] = "Frames Pointers: "
        app.Frames_Address_Label['text'] = "Frames Address: "


def Update_Table_Info(val):
    global app, working_table

    if val != 0:
        app.TablePointer_Address_Label['text'] = "Table Address: " + capitalized_hex(
                root.tables_list[working_table].table_pointer_address)
        app.Table_OW_Pointer_Address_Label['text'] = "Pointers Address: " + capitalized_hex(
                root.tables_list[working_table].table_address)
        app.Table_Data_Address_Label['text'] = "Data Address: " + capitalized_hex(
                root.tables_list[working_table].ow_data_pointers_address)
        app.Table_Frames_Pointers_Address_Label['text'] = "Frames Pointers: " + capitalized_hex(
                root.tables_list[working_table].frames_pointers_address)
        app.Table_Frames_Address_Label['text'] = "Framess Address: " + capitalized_hex(
                root.tables_list[working_table].frames_address)

    else:
        app.TablePointer_Address_Label['text'] = "Table Address: "
        app.Table_OW_Pointer_Address_Label['text'] = "Pointers Address: "
        app.Table_Data_Address_Label['text'] = "Data Address: "
        app.Table_Frames_Pointers_Address_Label['text'] = "Frames Pointers: "
        app.Table_Frames_Address_Label['text'] = "Framess Address: "


def Update_Frames_Spinbox(val):
    global app, root, working_ow, working_table

    if val == 1:
        frames_num = root.tables_list[working_table].ow_data_pointers[working_ow].frames.get_num()
        app.Frame_Spin['state'] = 'normal'

        app.Frame_Spin.delete(0, 'end')
        app.Frame_Spin.insert(0, 0)
        app.Frame_Spin["from_"] = 0
        app.Frame_Spin["to"] = frames_num - 1
    else:
        app.Frame_Spin['state'] = 'disabled'


def Update_Palette_Slot_Spinbox(val):
    global app, working_ow, working_table

    if val == 1:
        app.PaletteSlotBox['state'] = 'normal'

        data_address = root.tables_list[working_table].ow_data_pointers[working_ow].ow_data_address
        slot = get_palette_slot(data_address)

        app.PaletteSlotBox.delete(0, 'end')
        app.PaletteSlotBox.insert(INSERT, str(slot))
    else:
        app.PaletteSlotBox['state'] = 'disabled'


def Update_Viewer(val):
    global working_ow, working_table, root, app, SpriteManager

    if val == 0:
        # Blank Image
        viewer = Image.new("P", (64, 64))
        viewer = ImageTk.PhotoImage(viewer)
        app.Viewer.configure(image=viewer)
        app.Viewer.image = viewer
    else:

        ow_type = root.tables_list[working_table].ow_data_pointers[working_ow].frames.get_type()
        frames_address = root.tables_list[working_table].ow_data_pointers[working_ow].frames.frames_address
        width, height = get_frame_dimensions(ow_type)
        frame = int(app.Frame_Spin.get())

        # For the palette
        palette_id = get_ow_palette_id(root.tables_list[working_table].ow_data_pointers[working_ow].ow_data_address)
        palette_address = SpriteManager.get_palette_address(palette_id)
        sprite_palette = create_palette_from_gba(pointer_to_address(palette_address))
        frame_size = get_frame_size(ow_type)

        viewer = create_image_from_address((frame * frame_size) + frames_address, width, height)
        viewer.putpalette(sprite_palette)

        viewer = viewer.resize((viewer.width * 2, viewer.height * 2))
        viewer = ImageTk.PhotoImage(viewer)
        app.Viewer.configure(image=viewer)
        app.Viewer.image = viewer


def Update_Palette_Info(val):
    global app, Info, SpriteManager, working_ow

    # Initialize the Palette IDS
    id_list = []
    for pal_id in SpriteManager.used_palettes:
        id_list.append(capitalized_hex(pal_id))
    app.PaletteIds['values'] = id_list

    if val == 1:
        # Palette info
        if working_ow != -1:
            palette_id = get_ow_palette_id(root.tables_list[working_table].ow_data_pointers[working_ow].ow_data_address)
            # app.PaletteIDLabel['text'] = "Palette ID: " + capitalized_hex(palette_id)

            app.PaletteIds['state'] = 'enabled'
            index = id_list.index(capitalized_hex(palette_id))
            app.PaletteIds.current(index)

            app.PaletteAddress['text'] = "Palette Address: " + capitalized_hex(
                    SpriteManager.get_palette_address(palette_id))

        app.PaletteTableLabel['text'] = "Palette Table: " + capitalized_hex(SpriteManager.table_address)
        app.OccupiedPaletteLabel['text'] = "Num of Palettes: " + str(SpriteManager.get_palette_num())
        app.FreePaletteLabel['text'] = "Num of free Palettes: " + str(SpriteManager.get_free_slots())

    else:
        app.PaletteIds['state'] = 'disabled'
        app.PaletteIDLabel['text'] = "Palette ID: "
        app.PaletteAddress['text'] = "Palette Address:  "
        app.PaletteTableLabel['text'] = "Palette Table: " + capitalized_hex(SpriteManager.table_address)
        app.OccupiedPaletteLabel['text'] = "Num of Palettes: " + str(SpriteManager.get_palette_num())
        app.FreePaletteLabel['text'] = "Num of free Palettes: " + str(SpriteManager.get_free_slots())


def Update_OW_Menu_Buttons(val):
    global app

    if val == 0:
        # OW Buttons
        app.Add_OW_Button.config(state='disabled')
        app.Resize_OW_Button.config(state='disabled')
        app.Insert_Pos_OW_Button.config(state='disabled')
        app.Delete_OW_Button.config(state='disabled')

    if val == 1:
        # OW Buttons
        app.Add_OW_Button['state'] = 'ENABLED'
        app.Resize_OW_Button['state'] = 'ENABLED'
        app.Insert_Pos_OW_Button['state'] = 'ENABLED'
        app.Delete_OW_Button['state'] = 'ENABLED'

    if val == 2:
        app.Insert_Pos_OW_Button.config(state='disabled')
        app.Resize_OW_Button.config(state='disabled')
        app.Delete_OW_Button.config(state='disabled')
        app.Add_OW_Button['state'] = 'ENABLED'


def Update_Table_Menu_Buttons(val):
    global app

    if val == 0:
        app.Remove_Table_Button.config(state='disabled')
        if root.get_num_of_available_table_pointers() == 0:
            app.Insert_Table_Button.config(state='disabled')
        else:
            app.Insert_Table_Button.config(state='enabled')
    else:
        app.Remove_Table_Button.config(state='enabled')
        app.Insert_Table_Button.config(state='enabled')


def Update_Sprite_Options_Buttons(val):
    global app

    if val == 0:
        app.ImportSprite.config(state='disabled')
        app.ImportPokemon.config(state='disabled')
        app.ImportOW.config(state='disabled')
        app.SaveSprite.config(state='disabled')

    if val == 1:
        app.ImportPokemon['state'] = 'ENABLED'
        app.ImportSprite['state'] = 'ENABLED'
        app.ImportOW['state'] = 'ENABLED'
        app.SaveSprite['state'] = 'ENABLED'


def Update_Rom_Info():
    global Info, app

    app.RomVer['text'] = 'ROM:  ' + Info.rom_base

    app.ProfileList['state'] = "enabled"
    app.ProfileList['values'] = Info.Profiler.default_profiles
    app.ProfileList.current(Info.Profiler.current_profile)


def Update_Menu_Buttons():
    global app, Info

    ind = app.rom_options.index("More OWs in Original Table")
    app.rom_options.entryconfig(ind, command=Info.ow_fix, state='normal')


# --- UI Initializer Functions ---


def Init_Lists_UI(app):
    # ListFrame: Contains the main OW Explorer
    # Dimensions: 10x10
    ListFrame = ttk.Frame(app.container)
    ListFrame.grid(row=0, column=0, rowspan=2, columnspan=2, sticky=N)

    # --- Initialise the Pane ---
    Pane = ttk.PanedWindow(ListFrame, orient=HORIZONTAL)
    PaneTitle = ttk.Labelframe(Pane, text="Overworld Explorer", padding=(3, 3, 3, 3))
    Pane.add(PaneTitle)
    Pane.grid(row=0, column=0)

    # --- Initialise the Labels ---
    OW_Tables_Label = ttk.Label(PaneTitle, text="OW Tables")
    OW_Tables_Label.grid(row=0, column=0, columnspan=2)

    OW_Num_Label = ttk.Label(PaneTitle, text="OW ID's")
    OW_Num_Label.grid(row=0, column=2, columnspan=2)

    # --- Initialise the Lists ---
    app.OWList = Listbox(PaneTitle, height=18, width=15, activestyle='none', exportselection=False)
    app.OWList.grid(row=1, column=0, columnspan=2, sticky="w")

    scrollbar1 = ttk.Scrollbar(PaneTitle, command=app.OWList.yview)
    scrollbar1.grid(row=1, column=2, sticky="ns")
    app.OWList.configure(yscrollcommand=scrollbar1.set)

    app.OWs = Listbox(PaneTitle, height=18, width=15, activestyle='none', exportselection=False)
    app.OWs.grid(row=1, column=3, sticky="e")

    scrollbar2 = ttk.Scrollbar(PaneTitle, command=app.OWs.yview)
    scrollbar2.grid(row=1, column=4, sticky="ns")
    app.OWs.configure(yscrollcommand=scrollbar2.set)


def Init_Control_Interface(app):
    ControlFrame = ttk.Frame(app.container, padding=(3, 0, 3, 0))
    ControlFrame.grid(row=0, column=2, sticky=N)

    # --- Initialise the Pane ---
    Pane = ttk.PanedWindow(ControlFrame, orient=HORIZONTAL)
    PaneTitle = ttk.Labelframe(Pane, text="Overworld Menu")
    Pane.add(PaneTitle)
    Pane.grid(row=0, column=1)

    # --- Initialise the Buttons Frame ---
    ButtonFrame = ttk.Frame(PaneTitle, padding=(6, 6, 6, 6))
    ButtonFrame.grid(row=0, column=0, rowspan=2, columnspan=2)

    app.Add_OW_Button = ttk.Button(ButtonFrame, text="Add OW", state=DISABLED, command=Add_OW)
    app.Add_OW_Button.grid(row=0, column=0)

    app.Insert_Pos_OW_Button = ttk.Button(ButtonFrame, text="Insert OW", state=DISABLED, command=Insert_OW)
    app.Insert_Pos_OW_Button.grid(row=0, column=1)

    app.Resize_OW_Button = ttk.Button(ButtonFrame, text="Resize", state=DISABLED, command=Resize)
    app.Resize_OW_Button.grid(row=1, column=0)

    app.Delete_OW_Button = ttk.Button(ButtonFrame, text="Remove", state=DISABLED, command=Remove_OW)
    app.Delete_OW_Button.grid(row=1, column=1)

    # --- Initialise the OW Info ---
    InfoFrame = ttk.Frame(PaneTitle, padding=(8, 8, 8, 8))
    InfoFrame.grid(row=2, column=0)

    app.Type_Label = ttk.Label(InfoFrame, text="Type: ", width=25)
    app.Type_Label.grid(row=0, column=0, sticky=W)

    app.Frames_Label = ttk.Label(InfoFrame, text="Frames: ")
    app.Frames_Label.grid(row=1, column=0, sticky=W)

    app.Pointer_Address_Label = ttk.Label(InfoFrame, text="Pointer Address: ")
    app.Pointer_Address_Label.grid(row=2, column=0, sticky=W)

    app.Data_Address_Label = ttk.Label(InfoFrame, text="Data Address: ")
    app.Data_Address_Label.grid(row=3, column=0, sticky=W)

    app.Frames_Pointers_Label = ttk.Label(InfoFrame, text="Frames Pointers: ")
    app.Frames_Pointers_Label.grid(row=4, column=0, sticky=W)

    app.Frames_Address_Label = ttk.Label(InfoFrame, text="Frames Address: ")
    app.Frames_Address_Label.grid(row=5, column=0, sticky=W)


def Init_Table_Control(app):
    # --- TABLE MENU---
    # --- Initialise the Table Pane ---
    ControlFrame = ttk.Frame(app.container)
    ControlFrame.grid(row=1, column=2, sticky=N)  # , rowspan=10, columnspan=4

    Pane2 = ttk.PanedWindow(ControlFrame, orient=HORIZONTAL)
    PaneTitle2 = ttk.Labelframe(Pane2, text="Table Menu", padding=(3, 3, 3, 3))
    Pane2.add(PaneTitle2)
    Pane2.grid(row=1, column=1)

    # === Initialise the Table Button Frame ===
    Table_Button_Frame = ttk.Frame(PaneTitle2, padding=(3, 3, 3, 3))
    Table_Button_Frame.grid(row=0, column=0)

    app.Insert_Table_Button = ttk.Button(Table_Button_Frame, text="Insert Table", state=DISABLED, command=Insert_Table)
    app.Insert_Table_Button.grid(row=0, column=0)

    app.Remove_Table_Button = ttk.Button(Table_Button_Frame, text="Remove Table", state=DISABLED, command=remove_table)
    app.Remove_Table_Button.grid(row=0, column=1)

    # === Initialise Table Info ===
    Table_Info_Frame = ttk.Frame(PaneTitle2, padding=(3, 3, 3, 3))
    Table_Info_Frame.grid(row=1, column=0, columnspan=2)

    app.TablePointer_Address_Label = ttk.Label(Table_Info_Frame, text="Table Address: ", width=24)
    app.TablePointer_Address_Label.grid(row=0, column=0, sticky='w')

    app.Table_OW_Pointer_Address_Label = ttk.Label(Table_Info_Frame, text="Pointers Address: ")
    app.Table_OW_Pointer_Address_Label.grid(row=1, column=0, sticky='w')

    app.Table_Data_Address_Label = ttk.Label(Table_Info_Frame, text="Data Address: ")
    app.Table_Data_Address_Label.grid(row=2, column=0, sticky='w')

    app.Table_Frames_Pointers_Address_Label = ttk.Label(Table_Info_Frame, text="Frames Pointers: ")
    app.Table_Frames_Pointers_Address_Label.grid(row=3, column=0, sticky='w')

    app.Table_Frames_Address_Label = ttk.Label(Table_Info_Frame, text="Frames Address: ")
    app.Table_Frames_Address_Label.grid(row=4, column=0, sticky='w')


def Init_Sprite_Interface(app):
    SpriteFrame = ttk.Frame(app.container, padding=(3, 0, 3, 0))
    SpriteFrame.grid(row=0, column=3, rowspan=2, columnspan=2, sticky=N)

    # --- Initialise the Pane ---
    Pane = ttk.PanedWindow(SpriteFrame, orient=HORIZONTAL)
    PaneTitle = ttk.Labelframe(Pane, text="Sprite Viewer", padding=(3, 3, 3, 3))
    Pane.add(PaneTitle)
    Pane.grid(row=0, column=0)

    # === Initialise the Sprite Viewer Frame ===
    SpriteViewerFrame = ttk.Frame(PaneTitle, padding=(6, 6, 6, 6))
    SpriteViewerFrame.grid(row=0, column=0, rowspan=2)

    app.sizer = Label(SpriteViewerFrame, image='', height=10, width=46)
    app.sizer.grid(row=0, column=0)

    app.Viewer = Label(SpriteViewerFrame, image='')
    app.Viewer.grid(row=0, column=0)

    app.Frame_Spin = Spinbox(SpriteViewerFrame, from_=0, to=0, state=DISABLED, command=lambda: Update_Viewer(1))
    app.Frame_Spin.grid(row=1, column=0)


def Init_Sprite_Insert_Interface(app):
    InsertFrame = ttk.Frame(app.container)
    InsertFrame.grid(row=1, column=4, sticky=N)

    # --- Initialise the Pane ---
    Pane = ttk.PanedWindow(InsertFrame, orient=HORIZONTAL)
    PaneTitle = ttk.Labelframe(Pane, text="Sprite Options")
    Pane.add(PaneTitle)
    Pane.grid(row=0, column=0)

    # === Initialise the Sprite Viewer Frame ===
    InsertButtonsFrame = ttk.Frame(PaneTitle, padding=(6, 6, 6, 6))
    InsertButtonsFrame.grid(row=0, column=0, rowspan=2, columnspan=2)

    app.ImportSprite = ttk.Button(InsertButtonsFrame, text="Import Frames Sheet", state=DISABLED, width=24,
                                  command=ImportSprite)
    app.ImportSprite.grid(row=0, column=0)

    app.ImportOW = ttk.Button(InsertButtonsFrame, text="Import OW (Spr.Res)", state=DISABLED, width=24,
                              command=ImportOW)
    app.ImportOW.grid(row=1, column=0)

    app.ImportPokemon = ttk.Button(InsertButtonsFrame, text="Import Pokemon (Spr.Res)", state=DISABLED, width=24,
                                   command=ImportPokemon)
    app.ImportPokemon.grid(row=2, column=0)

    app.SaveSprite = ttk.Button(InsertButtonsFrame, text='Export Frames Sheet', state=DISABLED, command=save_image,
                                width=24)
    app.SaveSprite.grid(row=3, column=0)

    app.PaletteCleanup = ttk.Button(InsertButtonsFrame, text='Palette Cleanup', state=DISABLED, width=24,
                                    command=palette_cleanup)
    app.PaletteCleanup.grid(row=4, column=0)


def Init_Palette_Info_Interface(app):
    PaletteFrame = ttk.Frame(app.container)
    PaletteFrame.grid(row=1, column=3, sticky=N)  # 2

    # --- Initialise the Pane ---
    Pane = ttk.PanedWindow(PaletteFrame, orient=HORIZONTAL)
    PaneTitle = ttk.Labelframe(Pane, text="Palette Info", padding=(3, 3, 3, 3))
    Pane.add(PaneTitle)
    Pane.grid(row=0, column=0)

    # === Initialise the Sprite Viewer Frame ===
    PaletteInfoFrame = ttk.Frame(PaneTitle)
    PaletteInfoFrame.grid(row=0, column=0, rowspan=4, columnspan=4, sticky=E)

    # === Initialise the Labels ===
    app.PaletteSlotLabel = ttk.Label(PaletteInfoFrame, text="Palette slot: ", padding=(0, 8, 6, 9))
    app.PaletteSlotLabel.grid(row=0, column=0, sticky=W)

    app.PaletteSlotBox = Spinbox(PaletteInfoFrame, from_=0, to=15, state=DISABLED, width=3, command=change_palette_slot)
    app.PaletteSlotBox.grid(row=0, column=1)

    app.PaletteIDLabel = ttk.Label(PaletteInfoFrame, text="OW Palette ID: ")
    app.PaletteIDLabel.grid(row=1, column=0, columnspan=2, sticky=W)

    app.PaletteIds = ttk.Combobox(PaletteInfoFrame, width=6, state=DISABLED)
    app.PaletteIds.bind("<<ComboboxSelected>>", palette_selected)
    app.PaletteIds.grid(row=1, column=1)

    app.PaletteAddress = ttk.Label(PaletteInfoFrame, text="Palette Address:", width=25)
    app.PaletteAddress.grid(row=2, column=0, columnspan=2, sticky=W)

    app.PaletteTableLabel = ttk.Label(PaletteInfoFrame, text="Palette Table: ")
    app.PaletteTableLabel.grid(row=3, column=0, columnspan=2, sticky=W)

    app.OccupiedPaletteLabel = ttk.Label(PaletteInfoFrame, text="Num of Palettes: ")
    app.OccupiedPaletteLabel.grid(row=4, column=0, columnspan=2, sticky=W)

    app.FreePaletteLabel = ttk.Label(PaletteInfoFrame, text="Num of free Palettes: ")
    app.FreePaletteLabel.grid(row=5, column=0, columnspan=2, sticky=W)


def Init_Info_Section(app):
    # === Initialise the Sprite Viewer Frame ===
    RomInfoFrame = ttk.Frame(app.container, padding=(6, 0, 6, 6))
    RomInfoFrame.grid(row=1, column=0, sticky=S)

    app.RomVer = ttk.Label(RomInfoFrame, text="ROM: ", state=DISABLED, width=13)
    app.RomVer.grid(row=0, column=0, sticky='w')

    profile = ttk.Label(RomInfoFrame, text='Profile:', state=DISABLED)
    profile.grid(row=0, column=1)

    app.ProfileList = ttk.Combobox(RomInfoFrame, width=13, state=DISABLED)
    app.ProfileList.bind("<<ComboboxSelected>>", profile_selected)
    app.ProfileList.grid(row=0, column=2)


def init_menu(base):
    base.menu = Menu(base)
    base.config(menu=base.menu)

    base.filemenu = Menu(base.menu, tearoff=False)
    base.rom_options = Menu(base.menu, tearoff=False)
    base.info = Menu(base.menu, tearoff=False)

    base.menu.add_cascade(label="File", menu=base.filemenu)
    base.menu.add_cascade(label="Options", menu=base.rom_options)
    base.menu.add_cascade(label="Info", menu=base.info)

    base.filemenu.add_command(label="Open ROM...", command=open_file)
    base.filemenu.add_separator()
    base.filemenu.add_command(label="Exit", command=lambda: close(base))

    base.rom_options.add_command(label="Fixes", state=DISABLED)
    base.rom_options.add_command(label="More OWs in Original Table", state=DISABLED)
    base.rom_options.add_separator()

    base.info.add_command(label="Readme", command=open_readme)
    base.info.add_separator()
    base.info.add_command(label="About", command=show_info)


# --- ------------------------ ---

# --- Windows Functions ---

def close_window():
    quit()


def close(window):
    window.destroy()


# --- ----------------- ---

# --- Windows Classes ---

class SelectColor(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.title("Select your Color")
        # self.iconbitmap(r'Files/App.ico')

        self.container = ttk.Frame(self, padding=(12, 12, 12, 12))
        self.container.grid(row=0, column=0, columnspan=4)

        # Label
        sure = ttk.Label(self.container, text="OWM: OverWorld Manager 1.2.1",
                         padding=(12, 12, 12, 12))
        sure.grid(row=0, column=0, columnspan=4)

        message = "Credits/Special Thanks:\n\n"
        message += "Karatekid and Darthron for their tutorials and research in OWs Structure.\n"
        message += "Metapd23 for his tutorial on adding OWs with JPAN's engine.\n"
        message += "JPAN for his beautiful engine and documentation on OWs and Palettes.\n"
        message += "link12552 for his NSE, and the creator of OW RE. \n"
        message += "FBI for his hex to ASCII converter script and answering all my questions.\n\n"
        message += "Created by: Kimonas\n"
        blah = ttk.Label(self.container, text=message)
        blah.grid(row=1, column=0, columnspan=4)

        OK = ttk.Button(self.container, text="OK", command=lambda: close(self))
        OK.grid(row=20, column=2, sticky=E)

        Cancel = ttk.Button(self.container, text="Cancel", command=lambda: close(self))
        Cancel.grid(row=20, column=3, sticky=W)


class OWM_Info(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.title("About OWM")
        # self.iconbitmap(r'Files/App.ico')

        self.container = ttk.Frame(self, padding=(12, 12, 12, 12))
        self.container.grid(row=0, column=0, columnspan=4)

        # Label
        sure = ttk.Label(self.container, text="OWM: OverWorld Manager 1.2.1",
                         padding=(12, 12, 12, 12))
        sure.grid(row=0, column=0, columnspan=4)

        message = "Credits/Special Thanks:\n\n"
        message += "Karatekid and Darthron for their tutorials and research in OWs Structure.\n"
        message += "Metapd23 for his tutorial on adding OWs with JPAN's engine.\n"
        message += "JPAN for his beautiful engine and documentation on OWs and Palettes.\n"
        message += "link12552 for his NSE, and the creator of OW RE. \n"
        message += "FBI for his hex to ASCII converter script and answering all my questions.\n\n"
        message += "Created by: Kimonas\n"
        blah = ttk.Label(self.container, text=message)
        blah.grid(row=1, column=0, columnspan=4)

        OK = ttk.Button(self.container, text="OK", command=lambda: close(self))
        OK.grid(row=20, column=2, sticky=E)

        Cancel = ttk.Button(self.container, text="Cancel", command=lambda: close(self))
        Cancel.grid(row=20, column=3, sticky=W)


class RemoveTable(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.title("Remove Table")
        # self.iconbitmap(r'Files/App.ico')

        self.container = ttk.Frame(self, padding=(12, 12, 12, 12))
        self.container.grid()

        # Label
        sure = ttk.Label(self.container, text="Are you sure you want to delete the entire table?",
                         padding=(12, 12, 12, 12))
        sure.grid(row=0, column=0, columnspan=2)

        OK = ttk.Button(self.container, text="OK", command=lambda: yes_remove_table(self))
        OK.grid(row=3, column=0)

        Cancel = ttk.Button(self.container, text="Cancel", command=lambda: close(self))
        Cancel.grid(row=3, column=1)


class TableInsert(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.title("Table Settings")
        # self.iconbitmap(r'Files/App.ico')

        self.container = ttk.Frame(self, padding=(12, 12, 12, 12))
        self.container.grid()

        # General Label
        self.general = ttk.Label(self.container, text="Table Settings")
        self.general.grid(columnspan=2)

        # Pointers Address
        Table_Pointers = ttk.Label(self.container, text="OW Pointers Address: 0x", padding=(0, 6, 0, 6))
        Table_Pointers.grid(row=1, column=0, sticky=E)
        self.Table_pointers_Entr = ttk.Entry(self.container)
        self.Table_pointers_Entr.grid(row=1, column=1)

        # Data Address
        Table_Data_Address = ttk.Label(self.container, text="Table Data Address: 0x", padding=(0, 6, 0, 6))
        Table_Data_Address.grid(row=2, column=0, sticky=E)
        self.Table_Dt_Address_Entr = ttk.Entry(self.container)
        self.Table_Dt_Address_Entr.grid(row=2, column=1)

        # Frames Pointers Layout
        Table_Frames_Pointers = ttk.Label(self.container, text="Frames Pointers: 0x", padding=(0, 6, 0, 6))
        Table_Frames_Pointers.grid(row=3, column=0, sticky=E)
        self.Table_Fr_Ptr_Entry = ttk.Entry(self.container)
        self.Table_Fr_Ptr_Entry.grid(row=3, column=1)

        # Frames Address
        Table_Frames = ttk.Label(self.container, text="Frames Address: 0x", padding=(0, 6, 0, 6))
        Table_Frames.grid(row=4, column=0, sticky=E)
        self.Table_Frames_Entry = ttk.Entry(self.container)
        self.Table_Frames_Entry.grid(row=4, column=1)

        # OK-Cancel Buttons
        OK = ttk.Button(self.container, text="OK", command=lambda: create_table(self))
        OK.grid(row=5, column=0)

        Cancel = ttk.Button(self.container, text="Cancel", command=lambda: close(self))
        Cancel.grid(row=5, column=1)


class OWInsertSettings(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.title("OW Settings")
        # self.iconbitmap(r'Files/App.ico')

        self.container = ttk.Frame(self, padding=(12, 12, 12, 12))
        self.container.grid()

        # General Label
        self.general = ttk.Label(self.container, text="OW Settings")
        self.general.grid(columnspan=2)

        # Type Layout
        OW_Type = ttk.Label(self.container, text="OW Type (1-6):", padding=(0, 6, 0, 6))
        OW_Type.grid(row=1, column=0, sticky=E)
        self.OW_Type_Entry = ttk.Entry(self.container)
        self.OW_Type_Entry.grid(row=1, column=1)

        # Frames Layout
        OW_Frames = ttk.Label(self.container, text="Number of Frames:", padding=(0, 6, 0, 6))
        OW_Frames.grid(row=2, column=0)
        self.OW_Frames_Entry = ttk.Entry(self.container)
        self.OW_Frames_Entry.grid(row=2, column=1)

        # Num of OWs Layout
        OW_Num_Add = ttk.Label(self.container, text="Number of OWs:", padding=(0, 6, 0, 6))
        OW_Num_Add.grid(row=3, column=0)
        self.OW_Num_Insert_Entry = ttk.Entry(self.container)
        self.OW_Num_Insert_Entry.grid(row=3, column=1)

        # OK-Cancel Buttons
        OK = ttk.Button(self.container, text="OK", command=lambda: Insert_OW_fun(self))
        OK.grid(row=4, column=0)

        Cancel = ttk.Button(self.container, text="Cancel", command=lambda: close(self))
        Cancel.grid(row=4, column=1)


class OWResizeSettings(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.title("OW Resize Settings")
        # self.iconbitmap(r'Files/App.ico')

        self.container = ttk.Frame(self, padding=(12, 12, 12, 12))
        self.container.grid()

        # General Label
        self.general = ttk.Label(self.container, text="Resized OW Settings")
        self.general.grid(columnspan=2)

        # Type Layout
        OW_Type = ttk.Label(self.container, text="OW Type (1-6):", padding=(0, 6, 0, 6))
        OW_Type.grid(row=1, column=0, sticky=E)
        self.OW_Type_Entry = ttk.Entry(self.container)
        self.OW_Type_Entry.grid(row=1, column=1)

        # Frames Layout
        OW_Frames = ttk.Label(self.container, text="Number of Frames:", padding=(0, 6, 0, 6))
        OW_Frames.grid(row=2, column=0)
        self.OW_Frames_Entry = ttk.Entry(self.container)
        self.OW_Frames_Entry.grid(row=2, column=1)

        # OK-Cancel Buttons
        OK = ttk.Button(self.container, text="OK", command=lambda: resize_ow(self))
        OK.grid(row=3, column=0)

        Cancel = ttk.Button(self.container, text="Cancel", command=lambda: close(self))
        Cancel.grid(row=3, column=1)


class OWSettings(Tk):
    def __init__(self):
        Tk.__init__(self)

        self.attributes("-topmost", True)
        self.title("OW Settings")
        # self.iconbitmap(r'Files/App.ico')

        self.container = ttk.Frame(self, padding=(12, 12, 12, 12))
        self.container.grid()

        # General Label
        self.general = ttk.Label(self.container, text="OW Settings")
        self.general.grid(columnspan=2)

        # Type Layout
        OW_Type = ttk.Label(self.container, text="OW Type (1-6):", padding=(0, 6, 0, 6))
        OW_Type.grid(row=1, column=0, sticky=E)
        self.OW_Type_Entry = ttk.Entry(self.container)
        self.OW_Type_Entry.grid(row=1, column=1)

        # Frames Layout
        OW_Frames = ttk.Label(self.container, text="Number of Frames:", padding=(0, 6, 0, 6))
        OW_Frames.grid(row=2, column=0)
        self.OW_Frames_Entry = ttk.Entry(self.container)
        self.OW_Frames_Entry.grid(row=2, column=1)

        # Num of OWs Layout
        OW_Num_Add = ttk.Label(self.container, text="Number of OWs:", padding=(0, 6, 0, 6))
        OW_Num_Add.grid(row=3, column=0)
        self.OW_Num_Add_Entry = ttk.Entry(self.container)
        self.OW_Num_Add_Entry.grid(row=3, column=1)

        # OK-Cancel Buttons
        OK = ttk.Button(self.container, text="OK", command=lambda: create_ow(self))
        OK.grid(row=4, column=0)

        Cancel = ttk.Button(self.container, text="Cancel", command=lambda: close(self))
        Cancel.grid(row=4, column=1)


class OWEditor(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.title("OWM: OverWorld Manager")
        self.container = ttk.Frame(self)
        self.container.grid()
        # self.iconbitmap(r'Files/App.ico')

        Init_Lists_UI(self)

        Init_Control_Interface(self)

        Init_Table_Control(self)

        Init_Sprite_Interface(self)

        Init_Sprite_Insert_Interface(self)

        Init_Palette_Info_Interface(self)

        Init_Info_Section(self)

        init_menu(self)

        self.OWList.bind('<<ListboxSelect>>', lambda event: ow_table_selected(self))
        self.OWs.bind('<<ListboxSelect>>', lambda event: ow_selected(self))


app = OWEditor()
app.resizable(width=FALSE, height=FALSE)
app.mainloop()
