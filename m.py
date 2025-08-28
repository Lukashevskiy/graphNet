# main.py
import dearpygui.dearpygui as dpg
from pathlib import Path
from file_manager import FileManager

class MyApp:
    """Пример приложения с файловым менеджером"""
    
    def __init__(self):
        self.selected_path = None
        self.selected_type = None
    
    def open_file_manager(self):
        """Открывает файловый менеджер"""
        def on_file_selected(selected_path: Path, item_type: str):
            """Callback при выборе файла/папки"""
            self.selected_path = selected_path
            self.selected_type = item_type
            
            # Обновляем отображение в основном окне
            dpg.set_value("selected_path_text", str(selected_path))
            dpg.set_value("selected_type_text", item_type)
            
            print(f"Выбран {item_type}: {selected_path}")
            print(f"Абсолютный путь: {selected_path.absolute()}")
            
            # Здесь можно добавить любую логику обработки
            if item_type == "file":
                print(f"Буду работать с файлом: {selected_path}")
                # Например: открыть файл, скопировать, переместить и т.д.
            elif item_type == "folder":
                print(f"Буду работать с папкой: {selected_path}")
                # Например: показать содержимое, создать архив и т.д.
        
        # Создаем и показываем файловый менеджер
        file_manager = FileManager(
            callback=on_file_selected,
            title="Выберите файл или папку",
            width=1000,
            height=700
        )
        file_manager.show()
    
    def create_main_window(self):
        """Создает главное окно приложения"""
        with dpg.window(
            label="Мое приложение", 
            width=600, 
            height=400,
            tag="main_window"
        ):
            dpg.add_text("Файловый менеджер Dear PyGui")
            dpg.add_separator()
            
            # Кнопка для открытия файлового менеджера
            dpg.add_button(
                label="Открыть файловый менеджер",
                callback=self.open_file_manager,
                width=250,
                height=40
            )
            
            dpg.add_spacer(height=20)
            
            # Отображение выбранного пути
            dpg.add_text("Выбранный путь:")
            dpg.add_input_text(
                tag="selected_path_text",
                width=-1,
                height=30,
                readonly=True,
                multiline=True
            )
            
            dpg.add_text("Тип:")
            dpg.add_input_text(
                tag="selected_type_text",
                width=200,
                readonly=True
            )
            
            dpg.add_spacer(height=20)
            
            # Кнопка для работы с выбранным путем
            dpg.add_button(
                label="Использовать выбранный путь",
                callback=self.use_selected_path,
                width=250
            )
    
    def use_selected_path(self):
        """Использует выбранный путь"""
        if self.selected_path:
            print(f"Использую путь: {self.selected_path}")
            print(f"Тип: {self.selected_type}")
            
            # Примеры использования:
            if self.selected_type == "file":
                print(f"Работаю с файлом: {self.selected_path.name}")
                print(f"Расширение: {self.selected_path.suffix}")
                print(f"Размер: {self.selected_path.stat().st_size} байт")
            elif self.selected_type == "folder":
                print(f"Работаю с папкой: {self.selected_path.name}")
                try:
                    items = list(self.selected_path.iterdir())
                    print(f"Содержит {len(items)} элементов")
                except:
                    print("Нет доступа к содержимому папки")
        else:
            print("Сначала выберите файл или папку!")
    
    def run(self):
        """Запускает приложение"""
        # Инициализация Dear PyGui
        dpg.create_context()
        dpg.create_viewport(
            title="Пример использования файлового менеджера", 
            width=600, 
            height=500
        )
        
        # Создание интерфейса
        self.create_main_window()
        
        # Настройка и запуск
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()

# Запуск приложения
if __name__ == "__main__":
    app = MyApp()
    app.run()