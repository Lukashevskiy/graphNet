# main.py
import dearpygui.dearpygui as dpg
from pathlib import Path
from filemanager import show_file_dialog

def on_file_selected(selected_path: Path, item_type: str):
    """Callback для обработки выбора"""
    print(f"Выбран {item_type}: {selected_path}")
    dpg.set_value("selected_path_text", str(selected_path))

def open_file_dialog():
    """Открывает диалог выбора"""
    show_file_dialog(
        callback=on_file_selected,
        selection_mode="both",  # files, folders, both
        title="Выберите файл или папку"
    )

# Создаём основной интерфейс
dpg.create_context()

with dpg.font_registry():
    with dpg.font("notomono-regular.ttf", 18, default_font=True, tag="Default font") as f:
        dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
dpg.bind_font("Default font")

dpg.create_viewport(title="Тест", width=600, height=300)

with dpg.window(label="Тестовое окно", width=600, height=300):
    dpg.add_button(label="Выбрать файл/папку", callback=open_file_dialog)
    dpg.add_input_text(tag="selected_path_text", width=400, readonly=True)

dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()