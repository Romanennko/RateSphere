import psycopg2
from psycopg2 import pool

from config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

connection_pool = None

def initialize_pool():
    global connection_pool

    if connection_pool is None:
        print("Creating database connection pool...")
        try:
            connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            print("Connection pool created successfully")
        except psycopg2.OperationalError as e:
            print(f"Error creating connection pool: {e}")
            connection_pool = None

def close_pool():
    global connection_pool
    if connection_pool:
        print("Closing connection pool...")
        connection_pool.closeall()
        connection_pool = None
        print("Connection pool closed")


class DatabaseModel:
    def execute_query(self, sql, params=None, fetch=None):
        """
        An auxiliary method for executing queries using a pool.
        fetch: None (for INSERT/UPDATE/DELETE), 'one' (for fetchone), 'all' (for fetchall)
        """
        global connection_pool
        if not connection_pool:
            print("Attempting to initialize pool before query...")
            initialize_pool()
            if not connection_pool:
                print("Cannot execute query: Connection pool is not available.")

                raise ConnectionError("Database connection pool is not available.")

        conn = None
        try:
            conn = connection_pool.getconn()
            if conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)

                    result = None
                    if fetch == "one":
                        result = cur.fetchone()
                    elif fetch == "all":
                        result = cur.fetchall()


                    conn.commit()
                    return result
            else:
                print("Error: Failed to get connection from pool (returned None).")
                return None

        except psycopg2.Error as e:
            print(f"Database error: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                connection_pool.putconn(conn)

    def add_user(self, username, email, password_hash):
        sql = "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING user_id;"
        result = self.execute_query(sql, (username, email, password_hash), fetch="one")
        return result[0] if result else None

    def get_user_by_username(self, username):
        sql = "SELECT user_id, username, email, password_hash FROM users WHERE username = %s;"
        return self.execute_query(sql, (username,), fetch="one")

    def get_user_by_email(self, email):
        sql = "SELECT user_id, username, email, password_hash FROM users WHERE email = %s;"
        return self.execute_query(sql, (email,), fetch="one")

    def get_user_items(self, user_id):
        sql = """
            SELECT item_id, name, alt_name, item_type, status, rating, review, created_at
            FROM rated_items
            WHERE user_id = %s
            ORDER BY created_at DESC;
        """
        return self.execute_query(sql, (user_id,), fetch="all")