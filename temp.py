import os
import sys
from pathlib import Path
import hashlib
from typing import List, Tuple, Optional, Callable, Any

# === Поддержка кириллицы ===
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONLEGACYWINDOWSFSENCODING"] = "1"
    if hasattr(sys, 'stdout') and sys.stdout:
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys, 'stderr') and sys.stderr:
        sys.stderr.reconfigure(encoding='utf-8')

import dearpygui.dearpygui as dpg
# with dpg.font_registry():
#     with dpg.font("notomono-regular.ttf", 18, default_font=True, tag="Default font") as f:
#         dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
# dpg.bind_font("Default font")

# ==================== MODEL ====================
class FileManagerModel:
    """Модель файлового менеджера - управляет данными"""
    
    def __init__(self):
        self.current_path = Path.home()
        self.expanded_paths = set()  # Отслеживаем раскрытые папки
        self.selected_path = None
        self.selection_mode = "both"  # "files", "folders", "both"
    
    def get_directory_contents(self, path: Path) -> Tuple[List[Path], List[Path]]:
        """Получает содержимое директории"""
        try:
            items = list(path.iterdir())
            dirs = [p for p in items if p.is_dir()]
            files = [p for p in items if p.is_file()]
            
            # Сортируем
            dirs.sort(key=lambda x: x.name.lower())
            files.sort(key=lambda x: x.name.lower())
            
            return dirs, files
        except PermissionError:
            print(f"Нет доступа: {path}")
            return [], []
        except Exception as e:
            print(f"Ошибка при чтении папки {path}: {e}")
            return [], []
    
    def set_current_path(self, path: Path):
        """Устанавливает текущий путь"""
        self.current_path = path
    
    def get_current_path(self) -> Path:
        """Возвращает текущий путь"""
        return self.current_path
    
    def is_path_expanded(self, path: Path) -> bool:
        """Проверяет, раскрыта ли папка"""
        return str(path) in self.expanded_paths
    
    def expand_path(self, path: Path):
        """Помечает папку как раскрытую"""
        self.expanded_paths.add(str(path))
    
    def collapse_path(self, path: Path):
        """Помечает папку как свёрнутую"""
        self.expanded_paths.discard(str(path))
    
    def set_selected_path(self, path: Path):
        """Устанавливает выбранный путь"""
        self.selected_path = path
    
    def get_selected_path(self) -> Optional[Path]:
        """Возвращает выбранный путь"""
        return self.selected_path
    
    def set_selection_mode(self, mode: str):
        """Устанавливает режим выбора"""
        self.selection_mode = mode
    
    def get_selection_mode(self) -> str:
        """Возвращает режим выбора"""
        return self.selection_mode


# ==================== VIEW ====================
class FileManagerView:
    """Представление файлового менеджера - отвечает за GUI"""
    
    def __init__(self, controller, width=900, height=700, title="Файловый менеджер"):
        self.controller = controller
        self.width = width
        self.height = height
        self.title = title
        self.tag_generator = self._create_tag_generator()
        
    def _create_tag_generator(self):
        """Генератор уникальных тегов"""
        counter = 0
        while True:
            yield f"fm_tag_{counter}"
            counter += 1
    
    def make_tag(self) -> str:
        """Создаёт уникальный тег"""
        return next(self.tag_generator)
    
    def make_path_tag(self, path: Path) -> str:
        """Создаёт тег для пути"""
        return "tag_" + hashlib.md5(str(path).encode()).hexdigest()
    
    def create_gui(self):
        """Создаёт графический интерфейс"""
        dpg.create_context()
        with dpg.font_registry():
            with dpg.font("notomono-regular.ttf", 18, default_font=True, tag="Default font") as f:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
        dpg.bind_font("Default font")

        # Создаём окно
        with dpg.window(label=self.title, width=self.width, height=self.height, tag="main_window"):
            self._create_toolbar()
            self._create_status_bar()
            self._create_content_area()
    
    def _create_toolbar(self):
        """Создаёт панель инструментов"""
        dpg.add_text("Выберите путь:")
        
        with dpg.group(horizontal=True):
            dpg.add_input_text(
                tag="input_path",
                width=400,
                default_value=str(Path.home()),
                on_enter=True,
                callback=self.controller.on_path_enter
            )
            dpg.add_button(label="[*] Обновить", callback=self.controller.on_refresh)
            dpg.add_button(label="[~] Домой", callback=self.controller.on_go_home)
            
            # Выбор режима
            dpg.add_combo(
                items=["Файлы", "Папки", "Всё"],
                default_value="Всё",
                callback=self.controller.on_mode_change,
                tag="mode_combo",
                width=100
            )
    
    def _create_status_bar(self):
        """Создаёт статусную строку"""
        dpg.add_text("", tag="status")
        dpg.add_input_text(
            tag="selected_path", 
            label="Выбранный путь", 
            width=-1, 
            readonly=True
        )
    
    def _create_content_area(self):
        """Создаёт область содержимого"""
        dpg.add_separator()
        dpg.add_text("Содержимое папки:")
        
        with dpg.child_window(height=-1, tag="content_window"):
            with dpg.tree_node(label="Корень", tag="tree_root"):
                dpg.add_text("Загрузка...")
    
    def update_path_input(self, path: Path):
        """Обновляет поле ввода пути"""
        dpg.set_value("input_path", str(path))
    
    def update_status(self, message: str):
        """Обновляет статусную строку"""
        dpg.set_value("status", message)
    
    def update_selected_path(self, path: Path):
        """Обновляет поле выбранного пути"""
        dpg.set_value("selected_path", str(path))
    
    def clear_tree(self):
        """Очищает дерево"""
        try:
            dpg.delete_item("tree_root", children_only=True)
        except:
            pass
    
    def add_folder_node(self, parent_tag: str, folder_path: Path, is_root: bool = False) -> str:
        """Добавляет узел папки"""
        folder_name = folder_path.name or folder_path.drive
        node_tag = self.make_path_tag(folder_path)
        
        with dpg.tree_node(label=f"[D] {folder_name}", parent=parent_tag, tag=node_tag):
            if is_root:
                # Кнопки для корневой папки
                if self.controller.model.get_selection_mode() in ["folders", "both"]:
                    dpg.add_button(
                        label="[+] Выбрать", 
                        callback=lambda: self.controller.on_folder_select(folder_path)
                    )
                dpg.add_button(
                    label="[>] Просмотреть", 
                    callback=lambda: self.controller.on_folder_expand(folder_path, node_tag)
                )
            else:
                # Кнопки для вложенных папок
                if self.controller.model.get_selection_mode() in ["folders", "both"]:
                    dpg.add_button(
                        label="[+] Выбрать", 
                        callback=lambda: self.controller.on_folder_select(folder_path)
                    )
                dpg.add_button(
                    label="[>] Открыть", 
                    callback=lambda: self.controller.on_folder_expand(folder_path, node_tag)
                )
        
        # Сохраняем путь в user_data
        dpg.set_item_user_data(node_tag, str(folder_path))
        return node_tag
    
    def add_file_node(self, parent_tag: str, file_path: Path) -> str:
        """Добавляет узел файла"""
        node_tag = self.make_path_tag(file_path)
        
        with dpg.tree_node(label=f"[F] {file_path.name}", parent=parent_tag, tag=node_tag):
            dpg.add_button(
                label="[+] Выбрать", 
                callback=lambda: self.controller.on_file_select(file_path)
            )
        
        # Сохраняем путь в user_data
        dpg.set_item_user_data(node_tag, str(file_path))
        return node_tag
    
    def add_empty_marker(self, parent_tag: str):
        """Добавляет пометку пустой папки"""
        with dpg.group(parent=parent_tag):
            dpg.add_text("[пусто]", color=(128, 128, 128))
    
    def show_loading(self):
        """Показывает индикатор загрузки"""
        self.clear_tree()
        with dpg.tree_node(label="Корень", tag="tree_root"):
            dpg.add_text("Загрузка...")


# ==================== CONTROLLER ====================
class FileManagerController:
    """Контроллер файлового менеджера - управляет логикой"""
    
    def __init__(self, width=900, height=700, title="Файловый менеджер"):
        self.model = FileManagerModel()
        self.view = FileManagerView(self, width, height, title)
        self.on_selection_callback: Optional[Callable[[Path, str], None]] = None
    
    def run(self):
        """Запускает файловый менеджер"""
        try:
            self.view.create_gui()
            self._init_app()
            dpg.start_dearpygui()
        except Exception as e:
            print(f"Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()
        finally:
            dpg.destroy_context()
    
    def _init_app(self):
        """Инициализирует приложение"""
        dpg.create_viewport(title=self.view.title, width=self.view.width, height=self.view.height)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        
        # Отложенная загрузка (после первого кадра)
        def delayed_init():
            self.load_current_directory()
        
        dpg.set_frame_callback(1, delayed_init)
    
    def load_current_directory(self):
        """Загружает текущую директорию"""
        current_path = self.model.get_current_path()
        self.view.update_path_input(current_path)
        self._load_directory_content("tree_root", current_path, is_root=True)
        self.view.update_status(f"Загружено: {current_path}")
    
    def _load_directory_content(self, parent_tag: str, directory_path: Path, is_root: bool = False):
        """Загружает содержимое директории"""
        if is_root:
            self.view.clear_tree()
        
        # Добавляем корневую папку
        root_node_tag = self.view.add_folder_node(parent_tag, directory_path, is_root)
        
        if is_root:
            # Для корневой папки не раскрываем автоматически
            return
        
        # Загружаем содержимое
        dirs, files = self.model.get_directory_contents(directory_path)
        
        # Добавляем папки
        for d in dirs:
            self.view.add_folder_node(root_node_tag, d)
        
        # Добавляем файлы (если разрешено)
        if self.model.get_selection_mode() in ["files", "both"]:
            for f in files:
                self.view.add_file_node(root_node_tag, f)
        
        # Если папка пустая - добавляем пометку
        if not dirs and not files:
            self.view.add_empty_marker(root_node_tag)
    
    def on_path_enter(self, sender, app_data):
        """Обработка ввода пути"""
        path_str = dpg.get_value("input_path")
        path = Path(path_str).resolve()
        
        if path.exists() and path.is_dir():
            self.model.set_current_path(path)
            self.load_current_directory()
        else:
            self.view.update_status("Ошибка: путь не существует или не является папкой")
    
    def on_refresh(self, sender, app_data):
        """Обработка обновления"""
        self.load_current_directory()
    
    def on_go_home(self, sender, app_data):
        """Обработка перехода домой"""
        home = Path.home()
        self.model.set_current_path(home)
        self.view.update_path_input(home)
        self.load_current_directory()
    
    def on_mode_change(self, sender, app_data):
        """Обработка изменения режима выбора"""
        mode_map = {
            "Файлы": "files",
            "Папки": "folders", 
            "Всё": "both"
        }
        mode = mode_map.get(app_data, "both")
        self.model.set_selection_mode(mode)
        self.load_current_directory()
    
    def on_folder_expand(self, folder_path: Path, node_tag: str):
        """Обработка раскрытия папки"""
        if self.model.is_path_expanded(folder_path):
            return
        
        # Загружаем содержимое папки внутрь узла
        dirs, files = self.model.get_directory_contents(folder_path)
        
        # Добавляем папки
        for d in dirs:
            self.view.add_folder_node(node_tag, d)
        
        # Добавляем файлы (если разрешено)
        if self.model.get_selection_mode() in ["files", "both"]:
            for f in files:
                self.view.add_file_node(node_tag, f)
        
        # Если папка пустая - добавляем пометку
        if not dirs and not files:
            self.view.add_empty_marker(node_tag)
        
        # Помечаем как раскрытую
        self.model.expand_path(folder_path)
        self.view.update_status(f"Открыта папка: {folder_path}")
    
    def on_folder_select(self, folder_path: Path):
        """Обработка выбора папки"""
        self.model.set_selected_path(folder_path)
        self.view.update_selected_path(folder_path)
        self.view.update_status(f"Выбрана папка: {folder_path}")
        
        if self.on_selection_callback:
            self.on_selection_callback(folder_path, "folder")
    
    def on_file_select(self, file_path: Path):
        """Обработка выбора файла"""
        self.model.set_selected_path(file_path)
        self.view.update_selected_path(file_path)
        self.view.update_status(f"Выбран файл: {file_path}")
        
        if self.on_selection_callback:
            self.on_selection_callback(file_path, "file")
    
    def set_selection_callback(self, callback: Callable[[Path, str], None]):
        """Устанавливает callback для выбора"""
        self.on_selection_callback = callback
    
    def get_selected_path(self) -> Optional[Path]:
        """Возвращает выбранный путь"""
        return self.model.get_selected_path()


# ==================== Упрощённый интерфейс ====================
class FileManager:
    """Упрощённый интерфейс для использования"""
    
    def __init__(self, width=900, height=700, title="Файловый менеджер", selection_mode="both"):
        self.controller = FileManagerController(width, height, title)
        self.controller.model.set_selection_mode(selection_mode)
    
    def set_selection_callback(self, callback: Callable[[Path, str], None]):
        """Устанавливает callback для выбора"""
        self.controller.set_selection_callback(callback)
    
    def get_selected_path(self) -> Optional[Path]:
        """Возвращает выбранный путь"""
        return self.controller.get_selected_path()
    
    def set_selection_mode(self, mode: str):
        """Устанавливает режим выбора"""
        self.controller.model.set_selection_mode(mode)
    
    def run(self):
        """Запускает файловый менеджер"""
        self.controller.run()



# === Пример использования ===
def main():
    # Создаём экземпляр файлового менеджера
        
    fm = FileManager(width=900, height=700, title="Файловый менеджер", selection_mode="both")

    # Устанавливаем callback для выбора (файл или папка)
    def on_selection(selected_path, item_type):
        print(f"Выбран {item_type}: {selected_path}")
        # Здесь можно добавить любую логику обработки
        if item_type == "folder":
            print(f"Будем работать с папкой: {selected_path}")
        elif item_type == "file":
            print(f"Будем работать с файлом: {selected_path}")
    
    fm.set_selection_callback(on_selection)
    
    # Запускаем менеджер
    fm.run()


if __name__ == "__main__":
    main()