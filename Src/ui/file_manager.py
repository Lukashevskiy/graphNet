import dearpygui.dearpygui as dpg
from pathlib import Path
from typing import Callable, List, Optional
from .components.navigation_panel import NavigationPanel
from .components.file_list import FileList
from .components.selection_panel import SelectionPanel
from ..models.file_item import FileItem
from ..models.file_tree import FileTree
from ..services.file_tree_service import FileSystemService

class FileManagerUI:
    """Главный UI компонент файлового менеджера"""
    
    def __init__(self, 
                 on_navigate_callback: Callable[[Path], None],
                 on_file_open_callback: Callable[[Path], None],
                 on_directory_open_callback: Callable[[Path], None],
                 on_selection_change_callback: Callable[[FileItem, int, str], None],
                 on_select_callback: Callable[[], None]):
        
        self.on_navigate_callback = on_navigate_callback
        self.on_file_open_callback = on_file_open_callback
        self.on_directory_open_callback = on_directory_open_callback
        self.on_selection_change_callback = on_selection_change_callback
        self.on_select_callback = on_select_callback
        # Компоненты UI
        self.navigation_panel = NavigationPanel(
            on_navigate_callback=self._on_navigation_navigate,
            on_directory_select_callback=on_directory_open_callback
        )
        self.file_list = FileList(
            on_file_open_callback, 
            on_directory_open_callback, 
            on_selection_change_callback
        )
        self.selection_panel = SelectionPanel(on_select_callback)
        
        # Теги
        self.window_tag = "file_manager_window"
        self.breadcrumbs_tag = "breadcrumbs_text"
        self.address_input_tag = "address_input"
        self.status_text_tag = "status_text"
        self.main_content_tag = "main_content"
    
    def _on_navigation_navigate(self, path: Path) -> None:
        """Обработчик навигации из панели навигации"""
        # Раскрываем дерево до этого пути
        self.navigation_panel.expand_to_path(path)
        # Затем переходим в директорию
        self.on_navigate_callback(path)
    
    def create(self, title: str, width: int, height: int) -> str:
        """Создает главное окно файлового менеджера"""
        with dpg.window(
            label=title,
            width=width,
            height=height,
            tag=self.window_tag
        ):
            # Хлебные крошки и адресная строка
            self._create_header()
            
            dpg.add_separator()
            
            # Основная область
            with dpg.group(horizontal=True):
                self.navigation_panel.create(parent=self.window_tag)
                self.file_list.create(parent=self.window_tag)
            
            # Статус-бар
            dpg.add_text("Готов", tag=self.status_text_tag)
            
            # Панель выбора
            # self.selection_panel.create()
        
        return self.window_tag
    
    def load_navigation_tree(self, tree: FileTree) -> None:
        """Загружает дерево навигации"""
        self.navigation_panel.load_navigation_tree(tree)
    
    def expand_navigation_to_path(self, path: Path) -> None:
        """Раскрывает навигацию до указанного пути"""
        self.navigation_panel.expand_to_path(path)
            
    def _create_header(self) -> None:
        """Создает верхнюю часть интерфейса"""
        dpg.add_text("Путь: ", tag=self.breadcrumbs_tag)
        
        dpg.add_input_text(
            tag=self.address_input_tag,
            width=-1,
            on_enter=True,
            callback=self._on_address_enter
        )
    
    def _on_address_enter(self, sender, app_data) -> None:
        """Обработка ввода в адресной строке"""
        path_str = dpg.get_value(self.address_input_tag)
        try:
            path = Path(path_str).resolve()
            self.on_navigate_callback(path)
        except Exception as e:
            self.show_error(f"Ошибка пути: {str(e)}")
    
    def update_breadcrumbs(self, path: Path) -> None:
        """Обновляет хлебные крошки"""
        try:
            parts = list(path.parts)
            import sys
            if sys.platform == "win32" and len(parts) > 0:
                breadcrumb_text = f"Путь: {parts[0]}"
                for part in parts[1:]:
                    breadcrumb_text += f" > {part}"
            else:
                breadcrumb_text = "Путь: " + " / ".join(parts)
            
            dpg.set_value(self.breadcrumbs_tag, breadcrumb_text)
            dpg.set_value(self.address_input_tag, str(path))
        except Exception as e:
            print(f"Ошибка обновления хлебных крошек: {e}")
    
    def update_status(self, total_items: int) -> None:
        """Обновляет статус-бар"""
        dpg.set_value(self.status_text_tag, f"Объектов: {total_items}")
    
    def show_error(self, message: str) -> None:
        """Показывает сообщение об ошибке"""
        dpg.set_value(self.status_text_tag, f"Ошибка: {message}")
        # Автоматический сброс статуса через 3 секунды
        def reset_status():
            dpg.set_value(self.status_text_tag, "Готов")
        dpg.set_frame_callback(dpg.get_frame_count() + 180, reset_status)
    
    def refresh_navigation(self) -> None:
        """Обновляет навигационную панель"""
        self.navigation_panel.refresh()
    
    def load_directory(self, path: Path) -> None:
        """Загружает содержимое директории"""
        self.file_list.load_directory(path)
    
    def update_selection_display(self, selected_names: List[str]) -> None:
        """Обновляет отображение выбранных элементов"""
        self.selection_panel.update_selection_display(selected_names)
    
    def update_selection_styles(self, selected_items: List[FileItem]) -> None:
        """Обновляет стили элементов списка"""
        self.file_list.update_selection_styles(selected_items)
        
    def load_navigation_tree(self, tree: FileTree) -> None:
        """Загружает дерево навигации"""
        self.current_tree = tree
        self.navigation_panel.load_navigation_tree(tree)
    
