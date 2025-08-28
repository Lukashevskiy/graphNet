import dearpygui.dearpygui as dpg
from pathlib import Path
from typing import List, Callable
from Src.services.file_system_service import FileSystemService

class NavigationPanel:
    """Компонент навигационной панели"""
    
    def __init__(self, on_navigate_callback: Callable[[Path], None]):
        self.on_navigate_callback = on_navigate_callback
        self.container_tag = "navigation_panel"
        self.tree_group_tag = "nav_tree_group"
    
    def create(self, parent: str = None) -> str:
        """Создает компонент навигационной панели"""
        with dpg.child_window(width=250, height=-150, parent=parent, tag=self.container_tag):
            dpg.add_text("Навигация:")
            dpg.add_button(label="🏠 Домой", tag="nav_home_btn")
            dpg.add_button(label="🔄 Обновить", tag="nav_refresh_btn")
            
            dpg.add_separator()
            dpg.add_text("Дерево папок:")
            
            with dpg.group(tag=self.tree_group_tag):
                pass  # Будет заполнено позже
        
        # Настраиваем callback'и
        dpg.set_item_callback("nav_home_btn", lambda: self.on_navigate_callback(Path.home()))
        dpg.set_item_callback("nav_refresh_btn", self.refresh)
        
        return self.container_tag
    
    def refresh(self) -> None:
        """Обновляет навигационное дерево"""
        self.load_navigation_tree()
    
    def load_navigation_tree(self) -> None:
        """Загружает дерево навигации"""
        try:
            # Очищаем содержимое
            dpg.delete_item(self.tree_group_tag, children_only=True)
            
            # Получаем диски/корневые папки
            drives = FileSystemService.get_available_drives()
            
            for i, drive_path in enumerate(drives):
                node_tag = f"nav_node_{i}"
                
                # Определяем метку
                if drive_path.parts and len(drive_path.parts) > 0:
                    if sys.platform == "win32":
                        label = f"💾 {drive_path.parts[0]}"
                    else:
                        label = f"📁 {drive_path.name}" if drive_path.name else "📁 /"
                else:
                    label = f"📁 {drive_path}"
                
                # Создаем узел дерева
                dpg.add_tree_node(
                    label=label,
                    parent=self.tree_group_tag,
                    tag=node_tag,
                    callback=lambda p=drive_path: self.on_navigate_callback(p)
                )
                
        except Exception as e:
            print(f"Ошибка загрузки навигации: {e}")