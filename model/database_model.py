import psycopg2
from config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

class DataModel:
    def get_db_connection(self):
        try:
            conn = psycopg2.connect(
                dbname=DB_NAME,
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD
            )
            return conn
        except psycopg2.Error as e:
            print(f"Error connecting to the database: {e}")
            return None

    def add_user(self, username, email, password_hash):
        conn = self.get_db_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    sql = "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING user_id;"
                    cursor.execute(sql, (username, email, password_hash))
                    user_id = cursor.fetchone()[0]
                    conn.commit()
                    return user_id
            except psycopg2.Error as e:
                print(f"Error adding user: {e}")
                conn.rollback()
            finally:
                conn.close()

        return None
