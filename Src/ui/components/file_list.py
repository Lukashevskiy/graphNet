import dearpygui.dearpygui as dpg
from pathlib import Path
from typing import List, Callable, Tuple
from ...models.file_item import FileItem
from ...services.file_system_service import FileSystemService

class FileList:
    """Компонент списка файлов"""
    
    def __init__(self, 
                 on_file_open_callback: Callable[[Path], None],
                 on_directory_open_callback: Callable[[Path], None],
                 on_selection_change_callback: Callable[[FileItem, int, str], None]):
        self.on_file_open_callback = on_file_open_callback
        self.on_directory_open_callback = on_directory_open_callback
        self.on_selection_change_callback = on_selection_change_callback
        self.container_tag = "file_list_container"
        self.files_list_tag = "files_list"
        self.all_items: List[FileItem] = []  # Все отображаемые элементы
    
    def create(self, parent: str = None) -> str:
        """Создает компонент списка файлов"""
        with dpg.child_window(height=-150, parent=parent, tag=self.container_tag):
            # Заголовки колонок
            with dpg.group(horizontal=True):
                dpg.add_text("Имя")
                dpg.add_text("Тип")
                dpg.add_text("Размер")
                dpg.add_text("Дата")
            
            dpg.add_separator()
            
            # Список файлов
            with dpg.group(tag=self.files_list_tag):
                dpg.add_text("Загрузка...")
        
        return self.container_tag
    
    def load_directory(self, path: Path) -> None:
        """Загружает содержимое директории"""
        try:
            # Очищаем список
            dpg.delete_item(self.files_list_tag, children_only=True)
            
            # Получаем содержимое
            directories, files = FileSystemService.list_directory(path)
            self.all_items = directories + files
            
            # Добавляем родительскую директорию
            parent_dir = FileSystemService.get_parent_directory(path)
            if parent_dir:
                self._add_parent_directory_item(parent_dir)
            
            # Добавляем папки
            for i, dir_item in enumerate(directories):
                self._add_file_item(dir_item, len(self.all_items) + i if parent_dir else i)
            
            # Добавляем файлы
            start_index = len(directories) + (1 if parent_dir else 0)
            for i, file_item in enumerate(files):
                self._add_file_item(file_item, start_index + i)
                
        except Exception as e:
            dpg.add_text(f"Ошибка загрузки директории: {str(e)}", parent=self.files_list_tag)
    
    def _add_parent_directory_item(self, parent_path: Path) -> None:
        """Добавляет элемент родительской директории"""
        with dpg.group(horizontal=True, parent=self.files_list_tag):
            dpg.add_button(
                label="..",
                width=300,
                callback=lambda: self.on_directory_open_callback(parent_path)
            )
            dpg.add_text("Папка")
            dpg.add_text("")
            dpg.add_text("")
    
    def _add_file_item(self, item: FileItem, index: int) -> None:
        """Добавляет элемент в список"""
        with dpg.group(horizontal=True, parent=self.files_list_tag):
            btn = dpg.add_button(
                label=item.name,
                width=300,
                callback=lambda: self._on_item_click(item, index)
            )
            dpg.add_text("Папка" if item.is_directory else "Файл")
            dpg.add_text(item.get_formatted_size())
            dpg.add_text(item.get_formatted_date())
            
            # Сохраняем данные в user_data
            dpg.set_item_user_data(btn, {"item": item, "index": index})
    
    def _on_item_click(self, item: FileItem, index: int) -> None:
        """Обработка клика по элементу"""
        # Получаем модификаторы клавиш
        key_shift = dpg.is_key_down(dpg.mvKey_Shift)
        key_ctrl = dpg.is_key_down(dpg.mvKey_Control)
        
        if item.is_directory:
            # Переход в папку
            self.on_directory_open_callback(item.path)
        else:
            # Работа с файлами - выбор или открытие
            if key_ctrl or key_shift:
                # Для выбора вызываем callback
                key_type = "ctrl" if key_ctrl else "shift"
                self.on_selection_change_callback(item, index, key_type)
            else:
                # Простой клик - открытие файла
                self.on_file_open_callback(item.path)
    
    def update_selection_styles(self, selected_items: List[FileItem]) -> None:
        """Обновляет стили элементов в соответствии с выбором"""
        # Получаем все кнопки в списке
        children = dpg.get_item_children(self.files_list_tag, 1)
        
        for child_group in children:
            # Получаем кнопки из каждой группы
            group_children = dpg.get_item_children(child_group, 1)
            for btn in group_children:
                if dpg.get_item_type(btn) == "mvAppItemType::mvButton":
                    user_data = dpg.get_item_user_data(btn)
                    if user_data and "item" in user_data:
                        item = user_data["item"]
                        if item in selected_items:
                            dpg.configure_item(btn, color=(255, 255, 0))  # Желтый
                        else:
                            dpg.configure_item(btn, color=(255, 255, 255))  # Белый