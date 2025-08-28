# services/file_tree_service.py
from typing import List, Optional, Set, Dict
from pathlib import Path
from ..models.file_item import FileItem
from ..models.file_tree import FileTree, FileTreeNode
from ..services.file_system_service import FileSystemService


class FileTreeService:
    """Сервис для работы с файловым деревом"""
    
    def __init__(self):
        self.file_system_service = FileSystemService()
        self._expanded_nodes: Dict[int, FileTreeNode] = {}  # Отслеживаем раскрытые узлы по ID
        self._loaded_nodes: Set[int] = set()  # Отслеживаем загруженные узлы
    
    def create_tree(self) -> FileTree:
        """Создает новое файловое дерево"""
        tree = FileTree(root_nodes=[], node_map={})
        self.load_root_nodes(tree)
        return tree
    
    def load_root_nodes(self, tree: FileTree) -> None:
        """Загружает корневые узлы дерева"""
        tree.clear()
        self._expanded_nodes.clear()
        self._loaded_nodes.clear()
        
        # Получаем доступные диски/корневые папки
        drives = self.file_system_service.get_available_drives()
        
        for drive_path in drives:
            file_item = FileItem.from_path(drive_path)
            node = FileTreeNode(
                id=tree.generate_id(),
                file_item=file_item,
                children=[],
                parent=None
            )
            tree.root_nodes.append(node)
            tree.node_map[file_item.path] = node
    
    def load_children(self, tree: FileTree, parent_node: FileTreeNode) -> List[FileTreeNode]:
        """Загружает дочерние элементы для узла (только папки)"""
        try:
            # Проверяем, может быть дети уже загружены
            if parent_node.id in self._loaded_nodes:
                return parent_node.children
            
            # Получаем содержимое директории
            directories, _ = self.file_system_service.list_directory(parent_node.file_item.path)
            
            # Создаем узлы для папок
            new_nodes = []
            for dir_item in directories:
                # Проверяем, существует ли уже такой узел
                existing_node = tree.find_node_by_path(dir_item.path)
                if existing_node is None:
                    # Создаем новый узел
                    node = FileTreeNode(
                        id=tree.generate_id(),
                        file_item=dir_item,
                        children=[],
                        parent=parent_node
                    )
                    parent_node.add_child(node)
                    tree.node_map[dir_item.path] = node
                    new_nodes.append(node)
                else:
                    # Используем существующий узел
                    if existing_node not in parent_node.children:
                        parent_node.add_child(existing_node)
                    new_nodes.append(existing_node)
            
            # Помечаем узел как загруженный
            self._loaded_nodes.add(parent_node.id)
            parent_node.is_loaded = True
            
            return new_nodes
            
        except Exception as e:
            print(f"Ошибка загрузки дочерних элементов для {parent_node.file_item.path}: {e}")
            return []
    
    def toggle_node_expansion(self, tree: FileTree, node: FileTreeNode) -> bool:
        """Переключает состояние раскрытия узла и загружает детей при раскрытии"""
        if node.is_expanded:
            # Сворачиваем узел
            node.is_expanded = False
            if node.id in self._expanded_nodes:
                del self._expanded_nodes[node.id]
            return False
        else:
            # Раскрываем узел
            node.is_expanded = True
            self._expanded_nodes[node.id] = node
            
            # Загружаем дочерние элементы, если еще не загружены
            if node.id not in self._loaded_nodes:
                self.load_children(tree, node)
            
            return True
    
    def expand_node(self, tree: FileTree, node: FileTreeNode) -> None:
        """Раскрывает узел и загружает его детей"""
        if not node.is_expanded:
            node.is_expanded = True
            self._expanded_nodes[node.id] = node
            
            # Загружаем дочерние элементы, если еще не загружены
            if node.id not in self._loaded_nodes:
                self.load_children(tree, node)
    
    def collapse_node(self, node: FileTreeNode) -> None:
        """Сворачивает узел"""
        if node.is_expanded:
            node.is_expanded = False
            if node.id in self._expanded_nodes:
                del self._expanded_nodes[node.id]
    
    def is_node_expanded(self, node: FileTreeNode) -> bool:
        """Проверяет, раскрыт ли узел"""
        return node.is_expanded
    
    def expand_to_path(self, tree: FileTree, target_path: Path) -> Optional[FileTreeNode]:
        """Раскрывает дерево до указанного пути"""
        try:
            if not target_path.exists():
                return None
            
            # Получаем все родительские директории
            path_parts = []
            current_path = target_path.resolve()
            
            # Собираем путь в обратном порядке
            while current_path != current_path.parent:
                path_parts.append(current_path)
                current_path = current_path.parent
            path_parts.append(current_path)  # Корневая директория
            path_parts.reverse()
            
            # Начинаем с корневых узлов
            current_node = None
            
            for path in path_parts:
                if current_node is None:
                    # Ищем в корневых узлах
                    for root_node in tree.root_nodes:
                        if root_node.file_item.path == path:
                            current_node = root_node
                            self.expand_node(tree, current_node)  # Раскрываем и загружаем
                            break
                    if current_node is None:
                        break
                else:
                    # Загружаем детей если нужно
                    if current_node.id not in self._loaded_nodes:
                        self.load_children(tree, current_node)
                    
                    # Ищем дочерний узел
                    found_child = False
                    for child in current_node.children:
                        if child.file_item.path == path:
                            current_node = child
                            self.expand_node(tree, current_node)  # Раскрываем и загружаем
                            found_child = True
                            break
                    
                    if not found_child:
                        # Создаем узел если не найден
                        file_item = FileItem.from_path(path)
                        child_node = FileTreeNode(
                            id=tree.generate_id(),
                            file_item=file_item,
                            children=[],
                            parent=current_node
                        )
                        current_node.add_child(child_node)
                        tree.node_map[path] = child_node
                        current_node = child_node
                        self.expand_node(tree, current_node)  # Раскрываем и загружаем
                        found_child = True
                    
                    if not found_child:
                        break
            
            return current_node
            
        except Exception as e:
            print(f"Ошибка раскрытия дерева до пути {target_path}: {e}")
            return None
    
    def build_tree_for_path(self, tree: FileTree, target_path: Path) -> Optional[FileTreeNode]:
        """Строит дерево для конкретного пути (включая все родительские узлы)"""
        try:
            if not target_path.exists():
                return None
            
            # Нормализуем путь
            target_path = target_path.resolve()
            
            # Строим путь от корня к цели
            path_stack = []
            current = target_path
            while current != current.parent:
                path_stack.append(current)
                current = current.parent
            path_stack.append(current)  # Корневая директория
            path_stack.reverse()
            
            # Убеждаемся, что все родительские узлы существуют и раскрыты
            current_node = None
            
            for i, path in enumerate(path_stack):
                if i == 0:
                    # Корневой узел
                    for root_node in tree.root_nodes:
                        if root_node.file_item.path == path:
                            current_node = root_node
                            break
                    if current_node is None:
                        # Создаем корневой узел если его нет
                        file_item = FileItem.from_path(path)
                        current_node = tree.add_root_node(file_item)
                else:
                    # Дочерний узел
                    if current_node.id not in self._loaded_nodes:
                        self.load_children(tree, current_node)
                    
                    # Ищем или создаем дочерний узел
                    child_node = None
                    for child in current_node.children:
                        if child.file_item.path == path:
                            child_node = child
                            break
                    
                    if child_node is None:
                        # Создаем новый узел
                        file_item = FileItem.from_path(path)
                        child_node = FileTreeNode(
                            id=tree.generate_id(),
                            file_item=file_item,
                            children=[],
                            parent=current_node
                        )
                        current_node.add_child(child_node)
                        tree.node_map[path] = child_node
                    
                    current_node = child_node
                
                # Раскрываем узел если это не последний элемент
                if i < len(path_stack) - 1:
                    self.expand_node(tree, current_node)
            
            return current_node
            
        except Exception as e:
            print(f"Ошибка построения дерева для пути {target_path}: {e}")
            return None
    
    def get_expanded_nodes(self) -> Dict[int, FileTreeNode]:
        """Возвращает словарь раскрытых узлов"""
        return self._expanded_nodes.copy()
    
    def get_loaded_nodes(self) -> Set[int]:
        """Возвращает множество ID загруженных узлов"""
        return self._loaded_nodes.copy()
    
    def refresh_tree(self, tree: FileTree) -> None:
        """Обновляет дерево, сохраняя состояние раскрытых узлов"""
        # Сохраняем текущие раскрытые узлы
        expanded_paths = []
        for node in self._expanded_nodes.values():
            expanded_paths.append(node.file_item.path)
        
        # Пересоздаем дерево
        self.load_root_nodes(tree)
        
        # Восстанавливаем раскрытые узлы
        for path in expanded_paths:
            self.expand_to_path(tree, path)