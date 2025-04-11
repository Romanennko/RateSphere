# mvc_counter_app/model/counter_model.py

class CounterModel:
    """Хранит значение счетчика и логику его изменения."""
    def __init__(self):
        self._count = 0 # Начальное значение счетчика

    def get_count(self):
        """Возвращает текущее значение счетчика."""
        return self._count

    def increment(self):
        """Увеличивает счетчик на 1."""
        self._count += 1
        print(f"Model: Счетчик увеличен до {self._count}") # Для отладки

    def decrement(self):
        """Уменьшает счетчик на 1."""
        self._count -= 1
        print(f"Model: Счетчик уменьшен до {self._count}") # Для отладки