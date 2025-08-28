# filemanager.py
import os
import sys
from pathlib import Path
import dearpygui.dearpygui as dpg
from typing import List, Tuple, Callable
from datetime import datetime


class FileManager:
    """Файловый менеджер с древовидной структурой и списком файлов"""
    
    def __init__(self, 
                 callback: Callable[[Path, str], None], 
                 title: str = "Файловый менеджер",
                 width: int = 900,
                 height: int = 600):
        self.callback = callback
        self.title = title
        self.width = width
        self.height = height
        self.window_tag = "file_manager_window"
        self.current_path = Path.cwd()
        self.selected_items = []  # Список выбранных элементов
        self.last_selected_index = -1  # Для Shift-выбора
        self.file_items = []  # Список всех элементов для индексации
        
    def show(self):
        """Показывает файловый менеджер"""
        with dpg.window(
            label=self.title,
            width=self.width,
            height=self.height,
            tag=self.window_tag,
            on_close=self._on_close
        ):
            self._create_gui()
            # Откладываем загрузку до следующего кадра
            dpg.set_frame_callback(dpg.get_frame_count() + 1, lambda: self._load_sidebar())
    
    def _create_gui(self):
        """Создаёт интерфейс"""
        # Хлебные крошки
        dpg.add_text("Путь: ", tag="breadcrumbs_text")
        
        # Адресная строка
        dpg.add_input_text(
            tag="address_input",
            width=-1,
            on_enter=True,
            callback=self._on_address_enter
        )
        
        dpg.add_separator()
        
        # Панель быстрого доступа (слева) и основная область
        with dpg.group(horizontal=True):
            # Боковая панель с древовидной структурой
            with dpg.child_window(width=250, height=-150, tag="sidebar_container"):
                dpg.add_text("Навигация:")
                dpg.add_button(label="🏠 Домой", tag="home_btn")
                dpg.add_button(label="🔄 Обновить", tag="refresh_btn")
                
                dpg.add_separator()
                dpg.add_text("Дерево папок:")
                
                # Группа для дерева (будем очищать её)
                with dpg.group(tag="tree_group"):
                    pass  # Пустая группа, содержимое добавим позже
            
            # Основная область - список файлов
            with dpg.child_window(height=-150, tag="main_content"):
                # Заголовки колонок
                with dpg.group(horizontal=True):
                    dpg.add_text("Имя")
                    dpg.add_text("Тип")
                    dpg.add_text("Размер")
                    dpg.add_text("Дата")
                
                dpg.add_separator()
                
                # Список файлов
                with dpg.group(tag="files_list"):
                    dpg.add_text("Загрузка...")
        
        # Статус-бар
        dpg.add_text("Готов", tag="status_text")
        
        # Область выбора файлов
        dpg.add_separator()
        dpg.add_text("Выбранные элементы:")
        dpg.add_input_text(
            tag="selected_items_text",
            width=-1,
            height=30,
            multiline=True,
            readonly=True
        )
        
        # Кнопка выбора
        dpg.add_button(
            label="Выбрать", 
            tag="select_btn",
            width=120,
            height=30
        )
        
        # Настраиваем callback'и
        dpg.set_item_callback("home_btn", self._go_home)
        dpg.set_item_callback("refresh_btn", self._refresh_sidebar)
        dpg.set_item_callback("select_btn", self._select_and_close)
    
    def _load_sidebar(self):
        """Загружает боковую панель с древовидной структурой"""
        try:
            # Очищаем содержимое дерева
            dpg.delete_item("tree_group", children_only=True)
            
            if sys.platform == "win32":
                # Для Windows показываем диски
                import string
                drives = [f"{d}:\\\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\\\")]
                for drive in drives:
                    drive_path = Path(drive)
                    # Простая замена символов для тега
                    drive_letter = drive.replace(":\\\\", "").replace(":", "")
                    node_tag = f"node_{drive_letter}"
                    
                    # Создаем узел дерева напрямую в группе
                    dpg.add_tree_node(
                        label=f"💾 {drive}",
                        parent="tree_group",
                        tag=node_tag,
                        callback=lambda p=drive_path: self._on_tree_node_click(p)
                    )
            else:
                # Для Linux/macOS показываем корневые директории
                # Корневая директория
                dpg.add_tree_node(
                    label="📁 /",
                    parent="tree_group",
                    tag="node_root",
                    callback=lambda: self._on_tree_node_click(Path("/"))
                )
                # Домашняя директория
                dpg.add_tree_node(
                    label="🏠 /home",
                    parent="tree_group",
                    tag="node_home",
                    callback=lambda: self._on_tree_node_click(Path.home())
                )
                    
        except Exception as e:
            self._show_simple_error(f"Ошибка загрузки навигации: {str(e)}")
    
    def _on_tree_node_click(self, path: Path):
        """Обработка клика по узлу дерева"""
        # Загружаем содержимое директории в основную область
        self._clear_selection()
        self._load_directory(path)
    
    def _update_breadcrumbs(self, path: Path):
        """Обновляет хлебные крошки"""
        try:
            parts = list(path.parts)
            if sys.platform == "win32" and len(parts) > 0:
                breadcrumb_text = f"Путь: {parts[0]}"
                for part in parts[1:]:
                    breadcrumb_text += f" > {part}"
            else:
                breadcrumb_text = "Путь: " + " / ".join(parts)
            
            dpg.set_value("breadcrumbs_text", breadcrumb_text)
            dpg.set_value("address_input", str(path))
        except Exception as e:
            print(f"Ошибка обновления хлебных крошек: {e}")
    
    def _load_directory(self, path: Path):
        """Загружает содержимое директории"""
        try:
            if not path.exists():
                self._show_simple_error("Путь не существует")
                return
                
            if not path.is_dir():
                self._show_simple_error("Выбранный путь не является директорией")
                return
            
            self.current_path = path
            self._update_breadcrumbs(path)
            
            # Очищаем списки
            self.file_items = []
            dpg.delete_item("files_list", children_only=True)
            
            # Получаем содержимое
            dirs, files = self._safe_listdir(path)
            
            # Добавляем родительскую директорию
            if path.parent != path:  # Не корневая директория
                with dpg.group(horizontal=True, parent="files_list"):
                    dpg.add_button(
                        label="..",
                        width=300,
                        callback=lambda: self._load_directory(path.parent)
                    )
                    dpg.add_text("Папка")
                    dpg.add_text("")
                    dpg.add_text("")
            
            # Добавляем папки
            for i, d in enumerate(dirs):
                self._add_file_item(d, is_dir=True, index=i)
            
            # Добавляем файлы
            for i, f in enumerate(files):
                self._add_file_item(f, is_dir=False, index=len(dirs) + i)
            
            # Обновляем статус
            total_items = len(dirs) + len(files)
            dpg.set_value("status_text", f"Объектов: {total_items}")
            
        except PermissionError:
            self._show_simple_error("Нет доступа к директории")
        except Exception as e:
            self._show_simple_error(f"Ошибка загрузки директории: {str(e)}")
    
    def _safe_listdir(self, path: Path) -> Tuple[List[Path], List[Path]]:
        """Безопасное чтение содержимого папки"""
        try:
            items = list(path.iterdir())
            dirs = [p for p in items if p.is_dir()]
            files = [p for p in items if p.is_file()]
            dirs.sort(key=lambda x: x.name.lower())
            files.sort(key=lambda x: x.name.lower())
            return dirs, files
        except Exception as e:
            print(f"Ошибка при чтении папки {path}: {e}")
            return [], []
    
    def _add_file_item(self, item_path: Path, is_dir: bool, index: int):
        """Добавляет элемент в список файлов"""
        try:
            stat = item_path.stat()
            size = self._format_size(stat.st_size) if not is_dir else ""
            mtime = self._format_date(stat.st_mtime)
        except:
            size = "N/A"
            mtime = "N/A"
        
        item_type = "Папка" if is_dir else "Файл"
        
        with dpg.group(horizontal=True, parent="files_list"):
            # Кнопка для выбора/открытия
            btn = dpg.add_button(
                label=item_path.name,
                width=300,
                callback=lambda: self._on_item_click(item_path, is_dir, index)
            )
            dpg.add_text(item_type)
            dpg.add_text(size)
            dpg.add_text(mtime)
            
            # Сохраняем данные в user_data для возможности выбора
            dpg.set_item_user_data(btn, {
                "path": item_path, 
                "is_dir": is_dir, 
                "button": btn,
                "index": index
            })
            
            # Сохраняем элемент для индексации
            if not is_dir:  # Только файлы для выбора
                self.file_items.append({
                    "path": item_path,
                    "is_dir": is_dir,
                    "button": btn,
                    "index": index
                })
    
    def _on_item_click(self, path: Path, is_dir: bool, index: int):
        """Обработка клика по элементу"""
        # Получаем модификаторы клавиш
        key_shift = dpg.is_key_down(dpg.mvKey_Shift)
        key_ctrl = dpg.is_key_down(dpg.mvKey_Control)
        
        if is_dir:
            # Переход в папку
            self._clear_selection()
            self._load_directory(path)
        else:
            # Работа с файлами - выбор
            if key_ctrl:
                # Ctrl + клик - переключить выбор
                self._toggle_selection(path, index)
            elif key_shift and self.last_selected_index >= 0:
                # Shift + клик - выбор диапазона
                self._select_range(self.last_selected_index, index)
            else:
                # Простой клик - выбрать только этот элемент
                self._select_single(path, index)
    
    def _toggle_selection(self, path: Path, index: int):
        """Переключает выбор элемента"""
        if path in [item["path"] for item in self.selected_items]:
            # Удаляем из выбранных
            self.selected_items = [item for item in self.selected_items if item["path"] != path]
        else:
            # Добавляем в выбранные
            self.selected_items.append({"path": path, "index": index})
        
        self.last_selected_index = index
        self._update_selection_display()
        self._update_button_styles()
    
    def _select_single(self, path: Path, index: int):
        """Выбирает только один элемент"""
        self.selected_items = [{"path": path, "index": index}]
        self.last_selected_index = index
        self._update_selection_display()
        self._update_button_styles()
    
    def _select_range(self, start_index: int, end_index: int):
        """Выбирает диапазон элементов"""
        # Определяем границы диапазона
        min_index = min(start_index, end_index)
        max_index = max(start_index, end_index)
        
        # Очищаем текущий выбор и добавляем диапазон
        self.selected_items = []
        
        for i in range(min_index, max_index + 1):
            if i < len(self.file_items):
                item = self.file_items[i]
                if not item["is_dir"]:  # Только файлы
                    self.selected_items.append({"path": item["path"], "index": i})
        
        self.last_selected_index = end_index
        self._update_selection_display()
        self._update_button_styles()
    
    def _clear_selection(self):
        """Очищает выбор"""
        self.selected_items = []
        self.last_selected_index = -1
        self._update_selection_display()
        self._update_button_styles()
    
    def _update_selection_display(self):
        """Обновляет отображение выбранных элементов"""
        if self.selected_items:
            names = [item["path"].name for item in self.selected_items]
            display_text = "\n".join(names)
            dpg.set_value("selected_items_text", display_text)
        else:
            dpg.set_value("selected_items_text", "")
    
    def _update_button_styles(self):
        """Обновляет стили кнопок в соответствии с выбором"""
        selected_paths = [item["path"] for item in self.selected_items]
        
        # Сбрасываем все стили
        for item in self.file_items:
            if not item["is_dir"]:  # Только файлы
                if item["path"] in selected_paths:
                    # Выбранный элемент - подсвечиваем
                    dpg.configure_item(item["button"], color=(255, 255, 0))  # Желтый текст
                else:
                    # Не выбранный элемент - обычный стиль
                    dpg.configure_item(item["button"], color=(255, 255, 255))  # Белый текст
    
    def _on_address_enter(self, sender, app_data):
        """Обработка ввода в адресной строке"""
        path_str = dpg.get_value("address_input")
        try:
            path = Path(path_str).resolve()
            if path.exists() and path.is_dir():
                self._clear_selection()
                self._load_directory(path)
            else:
                self._show_simple_error("Неверный путь или путь не является директорией")
        except Exception as e:
            self._show_simple_error(f"Ошибка пути: {str(e)}")
    
    def _go_home(self):
        """Переход в домашнюю директорию"""
        self._clear_selection()
        self._load_directory(Path.home())
    
    def _refresh_sidebar(self):
        """Обновление боковой панели"""
        self._load_sidebar()
    
    def _refresh(self):
        """Обновление текущей директории"""
        self._load_directory(self.current_path)
    
    def _select_and_close(self):
        """Выбирает выбранные элементы и закрывает менеджер"""
        if self.callback:
            # Если есть выбранные элементы, передаем их
            if self.selected_items:
                # Передаем первый выбранный элемент
                first_item = self.selected_items[0]["path"]
                item_type = "file" if first_item.is_file() else "folder"
                self.callback(first_item, item_type)
            else:
                # Если ничего не выбрано, передаем текущую директорию
                self.callback(self.current_path, "folder")
        self._close()
    
    def _show_simple_error(self, message: str):
        """Показывает простое сообщение об ошибке в статус-баре"""
        dpg.set_value("status_text", f"Ошибка: {message}")
        # Через 3 секунды возвращаем нормальный статус
        def reset_status():
            dpg.set_value("status_text", "Готов")
        dpg.set_frame_callback(dpg.get_frame_count() + 180, reset_status)  # ~3 секунды при 60 FPS
    
    def _format_size(self, size_bytes: int) -> str:
        """Форматирует размер файла"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def _format_date(self, timestamp: float) -> str:
        """Форматирует дату"""
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%d.%m.%Y %H:%M")
        except:
            return "N/A"
    
    def _on_close(self):
        """Обработка закрытия окна"""
        self._close()
    
    def _close(self):
        """Закрывает окно"""
        try:
            dpg.delete_item(self.window_tag)
        except:
            pass


def show_file_manager(callback: Callable[[Path, str], None], 
                     title: str = "Файловый менеджер",
                     width: int = 900,
                     height: int = 600):
    """
    Показывает файловый менеджер
    
    Args:
        callback: функция callback(selected_path: Path, item_type: str)
        title: заголовок окна
        width: ширина окна
        height: высота окна
    """
    manager = FileManager(callback, title, width, height)
    manager.show()