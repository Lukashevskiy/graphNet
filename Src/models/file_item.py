from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class FileItem:
    """Модель элемента файловой системы"""
    path: Path
    name: str
    is_directory: bool
    size: Optional[int] = None
    modified_date: Optional[datetime] = None
    extension: Optional[str] = None
    
    @classmethod
    def from_path(cls, path: Path) -> 'FileItem':
        """Создает FileItem из Path объекта"""
        try:
            stat = path.stat()
            size = stat.st_size if not path.is_dir() else None
            modified_date = datetime.fromtimestamp(stat.st_mtime)
            extension = path.suffix if not path.is_dir() else None
        except:
            size = None
            modified_date = None
            extension = None
            
        return cls(
            path=path,
            name=path.name,
            is_directory=path.is_dir(),
            size=size,
            modified_date=modified_date,
            extension=extension
        )
    
    def get_formatted_size(self) -> str:
        """Возвращает отформатированный размер файла"""
        if self.size is None:
            return ""
        if self.is_directory:
            return ""
        
        size_names = ["B", "KB", "MB", "GB"]
        size_bytes = float(self.size)
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def get_formatted_date(self) -> str:
        """Возвращает отформатированную дату"""
        if self.modified_date is None:
            return "N/A"
        return self.modified_date.strftime("%d.%m.%Y %H:%M")