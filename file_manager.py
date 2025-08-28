import dearpygui.dearpygui as dpg
from pathlib import Path
from typing import Callable, List
from Src.services.file_system_service import FileSystemService
from Src.services.selection_service import SelectionService
from Src.ui.file_manager import FileManagerUI
from Src.models.file_item import FileItem

class FileManager:
    """Главный класс файлового менеджера"""
    
    def __init__(self, 
                 callback: Callable[[Path, str], None],
                 title: str = "Файловый менеджер",
                 width: int = 900,
                 height: int = 600):
        
        self.callback = callback
        self.title = title
        self.width = width
        self.height = height
        
        # Сервисы
        self.file_system_service = FileSystemService()
        self.selection_service = SelectionService()
        
        # Текущее состояние
        self.current_path = Path.cwd()
        
        # UI
        self.ui = FileManagerUI(
            on_navigate_callback=self._on_navigate,
            on_file_open_callback=self._on_file_open,
            on_directory_open_callback=self._on_directory_open,
            on_selection_change_callback=self._on_selection_change,
            on_select_callback=self._on_select
        )
    
    def show(self) -> None:
        """Показывает файловый менеджер"""
        window_tag = self.ui.create(self.title, self.width, self.height)
        # Откладываем загрузку до следующего кадра
        # dpg.set_frame_callback(dpg.get_frame_count() + 1, lambda: self._load_current_directory())
    
    def _on_navigate(self, path: Path) -> None:
        """Обработка навигации"""
        self._load_directory(path)
    
    def _on_file_open(self, path: Path) -> None:
        """Обработка открытия файла"""
        FileSystemService.open_file(path)
    
    def _on_directory_open(self, path: Path) -> None:
        """Обработка открытия директории"""
        self._clear_selection()
        self._load_directory(path)
    
    def _on_selection_change(self, item: FileItem, index: int, key_type: str) -> None:
        """Обработка изменения выбора"""
        if key_type == "ctrl":
            self.selection_service.toggle_selection(item, index)
        elif key_type == "shift" and self.selection_service.last_selected_index >= 0:
            # Для упрощения передаем все элементы (в реальной реализации нужно передавать видимые)
            self.selection_service.select_range([], self.selection_service.last_selected_index, index)
        
        self._update_selection_ui()
    
    def _on_select(self) -> None:
        """Обработка выбора"""
        if self.callback:
            selected_paths = self.selection_service.get_selected_paths()
            if selected_paths:
                # Передаем первый выбранный элемент
                first_path = selected_paths[0]
                item_type = "file" if first_path.is_file() else "folder"
                self.callback(first_path, item_type)
            else:
                # Если ничего не выбрано, передаем текущую директорию
                self.callback(self.current_path, "folder")
        self._close()
    
    def _load_current_directory(self) -> None:
        """Загружает текущую директорию"""
        self._load_directory(self.current_path)
    
    def _load_directory(self, path: Path) -> None:
        """Загружает указанную директорию"""
        try:
            if not path.exists():
                self.ui.show_error("Путь не существует")
                return
            
            if not path.is_dir():
                self.ui.show_error("Выбранный путь не является директорией")
                return
            
            self.current_path = path
            self.ui.update_breadcrumbs(path)
            self.ui.load_directory(path)
            self.ui.refresh_navigation()
            
            # Обновляем статус
            try:
                dirs, files = FileSystemService.list_directory(path)
                total_items = len(dirs) + len(files)
                self.ui.update_status(total_items)
            except:
                self.ui.update_status(0)
                
        except PermissionError:
            self.ui.show_error("Нет доступа к директории")
        except Exception as e:
            self.ui.show_error(f"Ошибка загрузки директории: {str(e)}")
    
    def _clear_selection(self) -> None:
        """Очищает выбор"""
        self.selection_service.clear_selection()
        self._update_selection_ui()
    
    def _update_selection_ui(self) -> None:
        """Обновляет UI в соответствии с выбором"""
        selected_names = self.selection_service.get_selected_names()
        selected_items = self.selection_service.selected_items
        
        self.ui.update_selection_display(selected_names)
        self.ui.update_selection_styles(selected_items)
    
    def _close(self) -> None:
        """Закрывает окно"""
        try:
            dpg.delete_item(self.ui.window_tag)
        except:
            pass