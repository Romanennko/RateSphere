# mvc_counter_app/view/screens/counter_screen.py

from kivymd.uix.screen import MDScreen

class CounterScreen(MDScreen):
    """
    Экран счетчика. Содержит минимум логики.
    Предоставляет метод для обновления метки счетчика.
    """
    def update_count_label(self, new_count):
        """
        Обновляет текст метки счетчика.
        Этот метод вызывается Контроллером.
        """
        if self.ids.count_label: # Убедимся, что id доступен
            self.ids.count_label.text = str(new_count)
            print(f"View: Метка обновлена на {new_count}") # Для отладки
        else:
            print("View Error: Не найден count_label в ids")