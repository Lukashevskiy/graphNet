from typing import List, Set
from pathlib import Path
from Src.models.file_item import FileItem

class SelectionService:
    """Сервис для управления выбором файлов"""
    
    def __init__(self):
        self.selected_items: List[FileItem] = []
        self.last_selected_index: int = -1
    
    def toggle_selection(self, item: FileItem, index: int) -> None:
        """Переключает выбор элемента"""
        if item in self.selected_items:
            self.selected_items.remove(item)
        else:
            self.selected_items.append(item)
        self.last_selected_index = index
    
    def select_single(self, item: FileItem, index: int) -> None:
        """Выбирает один элемент"""
        self.selected_items = [item]
        self.last_selected_index = index
    
    def select_range(self, all_items: List[FileItem], start_index: int, end_index: int) -> None:
        """Выбирает диапазон элементов"""
        min_index = min(start_index, end_index)
        max_index = max(start_index, end_index)
        
        # Выбираем только файлы из диапазона
        self.selected_items = [
            item for i, item in enumerate(all_items)
            if min_index <= i <= max_index and not item.is_directory
        ]
        self.last_selected_index = end_index
    
    def clear_selection(self) -> None:
        """Очищает выбор"""
        self.selected_items = []
        self.last_selected_index = -1
    
    def get_selected_paths(self) -> List[Path]:
        """Возвращает список выбранных путей"""
        return [item.path for item in self.selected_items]
    
    def get_selected_names(self) -> List[str]:
        """Возвращает список имен выбранных файлов"""
        return [item.name for item in self.selected_items]
    
    def is_selected(self, item: FileItem) -> bool:
        """Проверяет, выбран ли элемент"""
        return item in self.selected_items