import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional
from Src.models.file_item import FileItem

class FileSystemService:
    """Сервис для работы с файловой системой"""
    
    @staticmethod
    def get_available_drives() -> List[Path]:
        """Получает список доступных дисков"""
        if sys.platform == "win32":
            import string
            drives = []
            for letter in string.ascii_uppercase:
                drive_path = Path(f"{letter}:\\")
                if drive_path.exists():
                    drives.append(drive_path)
            return drives
        else:
            return [Path("/"), Path.home()]
    
    @staticmethod
    def list_directory(path: Path) -> Tuple[List[FileItem], List[FileItem]]:
        """Получает содержимое директории"""
        try:
            items = list(path.iterdir())
            directories = []
            files = []
            
            for item_path in items:
                file_item = FileItem.from_path(item_path)
                if file_item.is_directory:
                    directories.append(file_item)
                else:
                    files.append(file_item)
            
            # Сортировка
            directories.sort(key=lambda x: x.name.lower())
            files.sort(key=lambda x: x.name.lower())
            
            return directories, files
        except PermissionError:
            raise PermissionError(f"Нет доступа к директории: {path}")
        except Exception as e:
            raise Exception(f"Ошибка чтения директории {path}: {str(e)}")
    
    @staticmethod
    def get_parent_directory(path: Path) -> Optional[Path]:
        """Получает родительскую директорию"""
        if path.parent != path:  # Не корневая директория
            return path.parent
        return None
    
    @staticmethod
    def open_file(path: Path) -> bool:
        """Открывает файл системным приложением"""
        try:
            if sys.platform == "win32":
                os.startfile(path)
            else:
                import subprocess
                if sys.platform == "darwin":  # macOS
                    subprocess.run(["open", str(path)])
                else:  # Linux
                    subprocess.run(["xdg-open", str(path)])
            return True
        except Exception as e:
            print(f"Ошибка открытия файла {path}: {e}")
            return False