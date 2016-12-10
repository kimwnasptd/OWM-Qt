from ui_functions.treeViewClasses import *


def update_ow_menu_buttons(ui):

    if ui.selected_ow is None and ui.selected_table is not None:
        # A Table was selected
        ui.addOwButton.setEnabled(True)
        ui.insertOwButton.setEnabled(True)
        ui.resizeOwButton.setEnabled(False)
        ui.removeOwButton.setEnabled(False)
        return

    if ui.selected_ow is not None and ui.selected_table is not None:
        # An OW was selected
        ui.addOwButton.setEnabled(True)
        ui.insertOwButton.setEnabled(True)
        ui.resizeOwButton.setEnabled(True)
        ui.removeOwButton.setEnabled(True)
        return


def update_ow_text_menu(ui):

    if ui.selected_ow is None and ui.selected_table is not None:
        # Table selected
        ui.typeLabel.setText("")
        ui.framesLabel.setText("")
        ui.pointerAddressLabel.setText("")
        ui.dataAddressLabel.setText("")
        ui.framesPointersLabel.setText("")
        ui.framesAddressLabel.setText("")

    if ui.selected_ow is not None and ui.selected_table is not None:
        # OW selected
        ow_type = root.tables_list[ui.selected_table].ow_data_pointers[ui.selected_ow].frames.get_type()
        width, height = get_frame_dimensions(ow_type)

        ui.typeLabel.setText("Type: " + str(ow_type) + "  [" + str(width) + 'x' + str(height) + ']')
        ui.framesLabel.setText(str(ui.OWTreeView.selectionModel().currentIndex().internalPointer().frames))
        ui.pointerAddressLabel.setText(capitalized_hex(
            root.tables_list[ui.selected_table].ow_data_pointers[ui.selected_ow].ow_pointer_address))
        ui.dataAddressLabel.setText(capitalized_hex(
            root.tables_list[ui.selected_table].ow_data_pointers[ui.selected_ow].ow_data_address))
        ui.framesPointersLabel.setText(capitalized_hex(
            root.tables_list[ui.selected_table].ow_data_pointers[ui.selected_ow].frames.frames_pointers_address))
        ui.framesAddressLabel.setText(capitalized_hex(
            root.tables_list[ui.selected_table].ow_data_pointers[ui.selected_ow].frames.frames_address))


def update_tables_menu_buttons(ui):
    # They are actually always open
    ui.addTableButton.setEnabled(True)
    ui.removeTableButton.setEnabled(True)

    if ui.selected_table is None:
        ui.removeTableButton.setEnabled(False)
    return


def update_tables_text_menu(ui):

    if ui.selected_ow is None and ui.selected_table is not None:
        # A Table was selected
        ui.tableAddressLabel.setText(capitalized_hex(root.tables_list[ui.selected_table].table_pointer_address))
        ui.pointersAddressTableLabel.setText(capitalized_hex(root.tables_list[ui.selected_table].table_address))
        ui.dataAddressTableLabel.setText(capitalized_hex(root.tables_list[ui.selected_table].ow_data_pointers_address))
        ui.framesPointersTableLabel.setText(capitalized_hex(root.tables_list[ui.selected_table].frames_pointers_address))
        ui.framesAddressTableLabel.setText(capitalized_hex(root.tables_list[ui.selected_table].frames_address))

    if ui.selected_ow is None and ui.selected_table is None:
        ui.tableAddressLabel.setText("")
        ui.pointersAddressTableLabel.setText("")
        ui.dataAddressTableLabel.setText("")
        ui.framesPointersTableLabel.setText("")
        ui.framesAddressTableLabel.setText("")


def update_palette_info(ui):

    if ui.selected_table is not None:
        ui.paletteIDComboBox.setEnabled(False)

        if ui.selected_ow is not None:
            ui.paletteIDComboBox.setEnabled(True)
            # Create the list with the palette IDs
            id_list = []
            ui.paletteIDComboBox.clear()
            for pal_id in ui.sprite_manager.used_palettes:
                id_list.append(capitalized_hex(pal_id))
                ui.paletteIDComboBox.addItem(id_list[-1])

            palette_id = get_ow_palette_id(root.tables_list[ui.selected_table].ow_data_pointers[ui.selected_ow].ow_data_address)
            index = id_list.index(capitalized_hex(palette_id))
            ui.paletteIDComboBox.setCurrentIndex(index)
            ui.paletteAddressLabel.setText(capitalized_hex(ui.sprite_manager.get_palette_address(palette_id)))
        else:
            ui.paletteAddressLabel.setText("")

        ui.paletteTableAddressLabel.setText(capitalized_hex(ui.sprite_manager.table_address))
        ui.usedPalettesLabel.setText(str(ui.sprite_manager.get_palette_num()))
        ui.availablePalettesLabel.setText(str(ui.sprite_manager.get_free_slots()))


def update_menu_actions(ui):
    ui.menuFrames_Sheet.setEnabled(False)
    ui.menuSpriters_Resource.setEnabled(False)
    ui.actionImport_Frames_Sheet.setEnabled(False)
    ui.actionExport_Frames_Sheet.setEnabled(False)

    if ui.selected_ow is not None:
        ui.menuFrames_Sheet.setEnabled(True)
        ui.menuSpriters_Resource.setEnabled(True)
        ui.actionImport_Frames_Sheet.setEnabled(True)
        ui.actionExport_Frames_Sheet.setEnabled(True)


def update_gui(ui):

    update_ow_menu_buttons(ui)
    update_ow_text_menu(ui)
    update_tables_menu_buttons(ui)
    update_tables_text_menu(ui)
    update_palette_info(ui)
    update_menu_actions(ui)