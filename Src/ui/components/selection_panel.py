import dearpygui.dearpygui as dpg
from typing import List, Callable
from pathlib import Path

class SelectionPanel:
    """Компонент панели выбора"""
    
    def __init__(self, on_select_callback: Callable[[], None]):
        self.on_select_callback = on_select_callback
        self.container_tag = "selection_panel"
        self.selected_text_tag = "selected_items_text"
    
    def create(self, parent: str = None) -> str:
        """Создает компонент панели выбора"""
        with dpg.group(parent=parent, tag=self.container_tag):
            dpg.add_separator()
            dpg.add_text("Выбранные элементы:")
            dpg.add_input_text(
                tag=self.selected_text_tag,
                width=-1,
                height=30,
                multiline=True,
                readonly=True
            )
            
            dpg.add_button(
                label="Выбрать",
                tag="select_btn",
                width=120,
                height=30
            )
        
        # Настраиваем callback
        dpg.set_item_callback("select_btn", self.on_select_callback)
        
        return self.container_tag
    
    def update_selection_display(self, selected_names: List[str]) -> None:
        """Обновляет отображение выбранных элементов"""
        if selected_names:
            display_text = "\n".join(selected_names)
            dpg.set_value(self.selected_text_tag, display_text)
        else:
            dpg.set_value(self.selected_text_tag, "")