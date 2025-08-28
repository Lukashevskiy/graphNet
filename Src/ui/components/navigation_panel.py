# ui/components/navigation_panel.py
import dearpygui.dearpygui as dpg
import sys
from typing import Dict, Set
from pathlib import Path
from typing import Callable, Optional
from ...models.file_tree import FileTree, FileTreeNode
from ...services.file_tree_service import FileTreeService
from ...services.file_system_service import FileSystemService
from ...models.file_item import FileItem

class NavigationPanel:
    """Компонент навигационной панели с файловым деревом"""
    
    def __init__(self, 
                 on_navigate_callback: Callable[[Path], None],
                 on_directory_select_callback: Callable[[Path], None]):
        self.on_navigate_callback = on_navigate_callback
        self.on_directory_select_callback = on_directory_select_callback
        self.container_tag = "navigation_panel"
        self.tree_group_tag = "nav_tree_group"
        self.tree_nodes_map: Dict[int, str] = {}
        self.current_tree: Optional[FileTree] = None
        self.file_tree_service = FileTreeService()

    def create(self, parent: str) -> str:
        """Создает компонент навигационной панели"""
        with dpg.child_window(width=250, height=-150, parent=parent, tag=self.container_tag, resizable_x=True):
            dpg.add_text("Навигация:")
            dpg.add_button(label="🏠 Домой", tag="nav_home_btn")
            dpg.add_button(label="🔄 Обновить", tag="nav_refresh_btn")
            
            dpg.add_separator()
            dpg.add_text("Дерево папок:")
            
            with dpg.group(tag=self.tree_group_tag):
                dpg.add_text("Загрузка...")
        
        dpg.set_item_callback("nav_home_btn", lambda: self.on_navigate_callback(Path.home()))
        dpg.set_item_callback("nav_refresh_btn", self._on_refresh)
        
        return self.container_tag
    
    def _on_refresh(self) -> None:
        """Обработчик обновления"""
        if self.current_tree:
            self.load_navigation_tree(self.current_tree)
    
    def load_navigation_tree(self, navigation_tree: FileTree) -> None:
        """Загружает дерево навигации"""
        try:
            self.current_tree = navigation_tree
            dpg.delete_item(self.tree_group_tag, children_only=True)
            self.tree_nodes_map.clear()
            
            # Создаем корневые узлы
            for root_node in navigation_tree.root_nodes:
                self._create_tree_node(root_node, self.tree_group_tag)
                
        except Exception as e:
            print(f"Ошибка загрузки навигации: {e}")
            dpg.add_text(f"Ошибка: {e}", parent=self.tree_group_tag)
    
    def _create_tree_node(self, file_tree_node: FileTreeNode, parent_tag: str, is_leaf: bool = False) -> str:
        """Создает узел дерева DPG для FileTreeNode"""
        node_tag = f"tree_node_{file_tree_node.id}"
        
        # Определяем метку узла
        if sys.platform == "win32" and len(file_tree_node.file_item.path.parts) == 1:
            label = f"💾 {file_tree_node.file_item.path.parts[0]}"
        elif file_tree_node.file_item.path.name:
            label = f"📁 {file_tree_node.file_item.name}"
        else:
            label = f"📁 {file_tree_node.file_item.path}"
        # Создаем узел дерева в DPG
        dpg_tree_node = dpg.add_tree_node(
            label=label,
            parent=parent_tag,
            tag=node_tag,
            leaf=is_leaf
        )
        
        self.tree_nodes_map[file_tree_node.id] = node_tag
        
        # Добавляем обработчики
        self._add_node_handlers(node_tag, file_tree_node)
        
        # Добавляем placeholder для lazy loading
        placeholder_tag = f"placeholder_{file_tree_node.id}"
        dpg.add_text("...", parent=node_tag, tag=placeholder_tag)
        
        return node_tag
    
    # ui/components/navigation_panel.py (обновленный фрагмент)
    def _add_node_handlers(self, node_tag: str, file_tree_node: FileTreeNode) -> None:
        """Добавляет обработчики событий для узла дерева"""
        
        # Обработчик клика по узлу (для выбора директории)
        def on_node_clicked(sender):
            node = dpg.get_item_user_data(sender)
            if node and node.is_directory():
                self.on_directory_select_callback(node.get_path())
        
        # Обработчик раскрытия узла (здесь происходит ленивая загрузка!)
        def on_node_toggled(sender, app_data):
            print(sender)
            
            node = dpg.get_item_user_data(sender)
            if node is None:
                raise ValueError("Node empty")
            
            if node and node.is_directory():
                # Переключаем состояние раскрытия через сервис
                was_expanded = self.file_tree_service.toggle_node_expansion(self.current_tree, node)
                
                if was_expanded:
                    # Узел был раскрыт - обновляем визуальное отображение
                    self._update_node_children(node)
        # Создаем обработчики
        with dpg.item_handler_registry() as node_handler:
            dpg.add_item_clicked_handler(parent=node_handler, callback=on_node_clicked)
            dpg.add_item_toggled_open_handler(parent=node_handler, callback=on_node_toggled, user_data=file_tree_node)
            dpg.bind_item_handler_registry(node_tag, node_handler)

    def _update_node_children(self, file_tree_node: FileTreeNode) -> None:
        """Обновляет визуальное отображение дочерних элементов узла"""
        if self.current_tree is None:
            return
            
        try:
            node_tag = self.tree_nodes_map.get(file_tree_node.id)
            if not node_tag or not dpg.does_item_exist(node_tag):
                return
            
            # Удаляем placeholder если он есть
            placeholder_tag = f"placeholder_{file_tree_node.id}"
            if dpg.does_item_exist(placeholder_tag):
                dpg.delete_item(placeholder_tag)
            
            # Создаем визуальные узлы для детей
            for child in file_tree_node.children:
                child_node_tag = self.tree_nodes_map.get(child.id)
                if not child_node_tag:
                    self._create_tree_node(child, node_tag)
                    
        except Exception as e:
            print(f"Ошибка обновления детей узла: {e}")

    def _load_children_on_expand(self, file_tree_node: FileTreeNode) -> None:
        """Ленивая загрузка дочерних элементов при раскрытии узла"""
        if self.current_tree is None:
            return
            
        try:
            node_tag = self.tree_nodes_map.get(file_tree_node.id)
            if not node_tag or not dpg.does_item_exist(node_tag):
                return
            
            # Проверяем, загружены ли уже дети
            if file_tree_node.is_loaded:
                # Дети уже загружены, просто создаем узлы
                self._create_children_nodes(file_tree_node, node_tag)
                return
            
            # Удаляем placeholder
            placeholder_tag = f"placeholder_{file_tree_node.id}"
            if dpg.does_item_exist(placeholder_tag):
                dpg.delete_item(placeholder_tag)
            
            # Загружаем содержимое директории
            try:
                directories, files = FileSystemService.list_directory(file_tree_node.file_item.path)
                
                # Создаем узлы для папок
                for dir_item in directories:
                    # Создаем новый узел
                    child_node = FileTreeNode(
                        id=self.current_tree.generate_id(),
                        file_item=dir_item,
                        children=[],
                        parent=file_tree_node
                    )
                    file_tree_node.add_child(child_node)
                    self.current_tree.node_map[dir_item.path] = child_node
                    
                    # Создаем визуальный узел
                    self._create_tree_node(child_node, node_tag)
                
                # Создаем узлы для папок
                for file_item in files:
                    # Создаем новый узел
                    child_node = FileTreeNode(
                        id=self.current_tree.generate_id(),
                        file_item=file_item,
                        children=[],
                        parent=file_tree_node
                    )
                    file_tree_node.add_child(child_node)
                    self.current_tree.node_map[dir_item.path] = child_node
                    
                    # Создаем визуальный узел
                    self._create_tree_node(child_node, node_tag, is_leaf=True)
                
                
                # Помечаем узел как загруженный
                file_tree_node.is_loaded = True
                
            except PermissionError:
                dpg.add_text("Нет доступа", parent=node_tag)
            except Exception as e:
                dpg.add_text(f"Ошибка: {str(e)}", parent=node_tag)
                
        except Exception as e:
            print(f"Ошибка при загрузке детей: {e}")
    
    def _create_children_nodes(self, file_tree_node: FileTreeNode, parent_tag: str) -> None:
        """Создает визуальные узлы для уже загруженных детей"""
        try:
            # Удаляем placeholder если он есть
            placeholder_tag = f"placeholder_{file_tree_node.id}"
            if dpg.does_item_exist(placeholder_tag):
                dpg.delete_item(placeholder_tag)
            
            # Создаем узлы для детей
            for child in file_tree_node.children:
                self._create_tree_node(child, parent_tag)
                
        except Exception as e:
            print(f"Ошибка создания узлов детей: {e}")
    
    def expand_to_path(self, path: Path) -> None:
        """Раскрывает дерево до указанного пути"""
        if self.current_tree is None:
            return
            
        try:
            # Строим путь от корня к цели
            path_parts = []
            current_path = path.resolve()
            
            while current_path != current_path.parent:
                path_parts.append(current_path)
                current_path = current_path.parent
            path_parts.append(current_path)
            path_parts.reverse()
            
            # Для каждого уровня пути создаем узлы и загружаем детей
            current_parent_tag = self.tree_group_tag
            
            for i, path_part in enumerate(path_parts):
                # Находим или создаем узел для этого пути
                node = self.current_tree.find_node_by_path(path_part)
                if node is None:
                    # Создаем временный FileItem для этого пути
                    temp_file_item = FileItem.from_path(path_part)
                    node = FileTreeNode(
                        id=self.current_tree.generate_id(),
                        file_item=temp_file_item,
                        children=[],
                        parent=None
                    )
                    self.current_tree.node_map[path_part] = node
                    if i == 0:
                        self.current_tree.root_nodes.append(node)
                
                # Создаем визуальный узел если его нет
                node_tag = self.tree_nodes_map.get(node.id)
                if not node_tag:
                    node_tag = self._create_tree_node(node, current_parent_tag)
                
                # Если это не последний элемент, загружаем его детей
                if i < len(path_parts) - 1:
                    # Загружаем детей если нужно
                    if not node.is_loaded:
                        self._load_children_on_expand(node)
                
                current_parent_tag = node_tag
                
        except Exception as e:
            print(f"Ошибка раскрытия до пути {path}: {e}")