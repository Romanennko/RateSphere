# mvc_multiscreen_app/model/session_model.py

class SessionModel:
    """Хранит информацию о текущей сессии (залогиненном пользователе)."""
    def __init__(self):
        self._logged_in_username = None

    def login(self, username):
        """Сохраняет имя пользователя при входе."""
        self._logged_in_username = username
        print(f"SessionModel: Пользователь '{username}' вошел в систему.")

    def logout(self):
        """Сбрасывает имя пользователя при выходе."""
        print(f"SessionModel: Пользователь '{self._logged_in_username}' вышел.")
        self._logged_in_username = None

    def get_logged_in_username(self):
        """Возвращает имя текущего пользователя или None."""
        return self._logged_in_username