# models/file_tree.py
from .file_item import FileItem
from dataclasses import dataclass
from typing import List, Optional, Dict, Set
from pathlib import Path


@dataclass
class FileTreeNode:
    """Узел файлового дерева"""
    id: int
    file_item: FileItem
    children: List['FileTreeNode']
    parent: Optional['FileTreeNode']
    is_expanded: bool = False
    is_loaded: bool = False
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
    
    def add_child(self, child: 'FileTreeNode') -> None:
        """Добавляет дочерний узел"""
        child.parent = self
        self.children.append(child)
    
    def remove_child(self, child: 'FileTreeNode') -> None:
        """Удаляет дочерний узел"""
        if child in self.children:
            self.children.remove(child)
            child.parent = None
    
    def get_path(self) -> Path:
        """Возвращает путь к этому узлу"""
        return self.file_item.path
    
    def is_directory(self) -> bool:
        """Проверяет, является ли узел директорией"""
        return self.file_item.is_directory
    
    def has_children(self) -> bool:
        """Проверяет, есть ли дочерние элементы"""
        return len(self.children) > 0
    
    def find_child_by_path(self, path: Path) -> Optional['FileTreeNode']:
        """Ищет дочерний узел по пути"""
        for child in self.children:
            if child.file_item.path == path:
                return child
        return None
    
    def get_all_descendants(self) -> List['FileTreeNode']:
        """Возвращает все дочерние узлы рекурсивно"""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants


@dataclass
class FileTree:
    """Файловое дерево"""
    root_nodes: List[FileTreeNode]
    node_map: Dict[Path, FileTreeNode]  # Быстрый доступ к узлам по пути
    next_id: int = 0
    
    def __post_init__(self):
        if self.root_nodes is None:
            self.root_nodes = []
        if self.node_map is None:
            self.node_map = {}
    
    def generate_id(self) -> int:
        """Генерирует уникальный ID для узла"""
        self.next_id += 1
        return self.next_id
    
    def add_root_node(self, file_item: FileItem) -> FileTreeNode:
        """Добавляет корневой узел"""
        node = FileTreeNode(
            id=self.generate_id(),
            file_item=file_item,
            children=[],
            parent=None
        )
        self.root_nodes.append(node)
        self.node_map[file_item.path] = node
        return node
    
    def remove_root_node(self, node: FileTreeNode) -> None:
        """Удаляет корневой узел"""
        if node in self.root_nodes:
            self.root_nodes.remove(node)
            # Удаляем узел и всех его потомков из карты
            self._remove_node_from_map(node)
    
    def _remove_node_from_map(self, node: FileTreeNode) -> None:
        """Рекурсивно удаляет узел из карты"""
        del self.node_map[node.file_item.path]
        for child in node.children:
            self._remove_node_from_map(child)
    
    def find_node_by_path(self, path: Path) -> Optional[FileTreeNode]:
        """Ищет узел по пути"""
        return self.node_map.get(path)
    
    def get_node_by_id(self, node_id: int) -> Optional[FileTreeNode]:
        """Ищет узел по ID"""
        for node in self.node_map.values():
            if node.id == node_id:
                return node
        return None
    
    def expand_node(self, node: FileTreeNode) -> None:
        """Раскрывает узел"""
        node.is_expanded = True
    
    def collapse_node(self, node: FileTreeNode) -> None:
        """Сворачивает узел"""
        node.is_expanded = False
    
    def is_node_expanded(self, node: FileTreeNode) -> bool:
        """Проверяет, раскрыт ли узел"""
        return node.is_expanded
    
    def load_node_children(self, node: FileTreeNode) -> None:
        """Загружает дочерние элементы узла"""
        # Эта функция будет реализована в сервисе
        node.is_loaded = True
    
    def get_visible_nodes(self) -> List[FileTreeNode]:
        """Возвращает все видимые узлы (с учетом раскрытых родителей)"""
        visible_nodes = []
        
        def add_visible_children(parent_node: FileTreeNode):
            for child in parent_node.children:
                visible_nodes.append(child)
                if child.is_expanded and child.is_loaded:
                    add_visible_children(child)
        
        for root_node in self.root_nodes:
            visible_nodes.append(root_node)
            if root_node.is_expanded and root_node.is_loaded:
                add_visible_children(root_node)
        
        return visible_nodes
    
    def clear(self) -> None:
        """Очищает дерево"""
        self.root_nodes.clear()
        self.node_map.clear()
        self.next_id = 0
    
    def get_all_nodes(self) -> List[FileTreeNode]:
        """Возвращает все узлы дерева"""
        return list(self.node_map.values())
    
    def get_depth(self, node: FileTreeNode) -> int:
        """Возвращает глубину узла в дереве"""
        depth = 0
        current = node.parent
        while current is not None:
            depth += 1
            current = current.parent
        return depth