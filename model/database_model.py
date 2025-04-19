import psycopg2
from psycopg2 import pool, extras
import logging

from config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

logger = logging.getLogger(__name__)
connection_pool = None

class DatabaseError(Exception):
    """Custom exception for database operation errors."""
    pass

def initialize_pool():
    global connection_pool
    if connection_pool is None:
        logger.info("Creating database connection pool...")
        try:
            connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                cursor_factory = extras.DictCursor
            )
            conn = connection_pool.getconn()
            logger.info(f"Successfully connected to database '{DB_NAME}' on {DB_HOST}:{DB_PORT}")
            connection_pool.putconn(conn)
            logger.info("Connection pool created successfully.")
        except psycopg2.OperationalError as e:
            logger.critical(f"FATAL: Error creating connection pool: {e}", exc_info=True)
            connection_pool = None
            raise DatabaseError(f"Could not connect to the database: {e}") from e
        except Exception as e:
            logger.critical(f"FATAL: An unexpected error occurred during pool initialization: {e}", exc_info=True)
            connection_pool = None
            raise DatabaseError(f"Unexpected error initializing database connection: {e}") from e

def close_pool():
    global connection_pool
    if connection_pool:
        logger.info("Closing connection pool...")
        connection_pool.closeall()
        connection_pool = None
    else:
        logger.warning("Attempted to close connection pool, but it was not initialized.")

class DatabaseModel:
    def execute_query(self, sql, params=None, fetch=None, use_dict_cursor=False):
        """
        Executes a query using the pool.
        fetch: None, 'one', 'all'
        use_dict_cursor: If True, returns results as dictionaries.
        Raises DatabaseError on failure.
        """
        global connection_pool
        if not connection_pool:
            logger.error("Cannot execute query: Connection pool is not available.")
            try:
                logger.warning("Attempting to re-initialize pool before query...")
                initialize_pool()
            except DatabaseError as init_e:
                logger.critical("Failed to re-initialize connection pool.")
                raise init_e

            if not connection_pool:
                raise DatabaseError("Database connection pool is not available after re-initialization attempt.")

        conn = None
        try:
            conn = connection_pool.getconn()
            if conn:
                cursor_factory = extras.DictCursor if use_dict_cursor else None
                with conn.cursor(cursor_factory=cursor_factory) as cur:
                    logger.debug(
                        f"Executing SQL: {cur.mogrify(sql, params).decode('utf-8') if params else sql}")
                    cur.execute(sql, params)

                    result = None
                    if fetch == "one":
                        result = cur.fetchone()
                        logger.debug(f"Query fetched one row: {result}")
                    elif fetch == "all":
                        result = cur.fetchall()
                        logger.debug(f"Query fetched {len(result) if result else 0} rows.")
                    else:
                        logger.debug(f"Query executed, row count: {cur.rowcount}")

                    conn.commit()
                    return result
            else:
                logger.error("Failed to get connection from pool (returned None).")
                raise DatabaseError("Failed to obtain a database connection from the pool.")

        except psycopg2.Error as e:
            logger.error(f"Database error executing query: {e}", exc_info=True)
            logger.error(f"Failed SQL was likely: {sql} with params {params}")
            if conn:
                try:
                    conn.rollback()
                    logger.warning("Database transaction rolled back due to error.")
                except psycopg2.Error as rb_e:
                    logger.error(f"Error during rollback: {rb_e}", exc_info=True)
            raise DatabaseError(f"A database error occurred: {e.pgcode} - {e.pgerror}. Check logs.") from e
        except Exception as e:
            logger.exception(f"An unexpected error occurred during query execution: {e}")
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            raise DatabaseError(f"An unexpected error occurred: {e}. Check logs.") from e
        finally:
            if conn:
                connection_pool.putconn(conn)
                logger.debug("Database connection returned to pool.")

    def add_user(self, username, email, password_hash):
        sql = "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING user_id;"
        try:
            result = self.execute_query(sql, (username, email, password_hash), fetch="one")
            return result[0] if result else None
        except DatabaseError as e:
             logger.error(f"Failed to add user '{username}': {e}")
             raise

    def get_user_by_username(self, username, use_dict_cursor=False):
        sql = "SELECT user_id, username, email, password_hash FROM users WHERE username = %s;"
        try:
             return self.execute_query(sql, (username,), fetch="one", use_dict_cursor=use_dict_cursor)
        except DatabaseError as e:
             logger.error(f"Failed to get user by username '{username}': {e}")
             raise

    def get_user_by_email(self, email, use_dict_cursor=False):
        sql = "SELECT user_id, username, email, password_hash FROM users WHERE email = %s;"
        try:
            return self.execute_query(sql, (email,), fetch="one", use_dict_cursor=use_dict_cursor)
        except DatabaseError as e:
             logger.error(f"Failed to get user by email: {e}")
             raise

    def get_user_items(self, user_id, sort_by='created_at', sort_order='DESC', use_dict_cursor=False):
        """Retrieves all rated items for the user with sorting."""
        allowed_sort_columns = ['name', 'item_type', 'status', 'rating', 'created_at', 'updated_at']
        if sort_by not in allowed_sort_columns:
            logger.warning(f"Invalid sort column requested: '{sort_by}'. Defaulting to 'created_at'.")
            sort_by = 'created_at'

        if sort_order.upper() not in ['ASC', 'DESC']:
            logger.warning(f"Invalid sort order requested: '{sort_order}'. Defaulting to 'DESC'.")
            sort_order = 'DESC'

        order_by_clause = f"ORDER BY {sort_by} {sort_order.upper()}"

        sql = f"""
            SELECT item_id, name, alt_name, item_type, status, rating, review, created_at, updated_at
            FROM rated_items
            WHERE user_id = %s
            {order_by_clause};
        """
        try:
            return self.execute_query(sql, (user_id,), fetch="all", use_dict_cursor=use_dict_cursor)
        except DatabaseError as e:
            logger.error(f"Failed to get items for user_id {user_id}: {e}")
            raise

    def add_rated_item(self, user_id, name, item_type, status, rating, alt_name=None, review=None):
        """Adds a new rated item. Raises DatabaseError on failure."""
        sql = """
            INSERT INTO rated_items
                (user_id, name, alt_name, item_type, status, rating, review)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s)
            RETURNING item_id;
        """
        params = (user_id, name, alt_name, item_type, status, rating, review)
        try:
            result = self.execute_query(sql, params, fetch="one")
            item_id = result[0] if result else None
            if item_id:
                 logger.info(f"Successfully added item '{name}' with id {item_id} for user {user_id}.")
            else:
                 logger.error(f"Failed to add item '{name}' for user {user_id} - INSERT query did not return ID.")
                 raise DatabaseError("Item creation failed unexpectedly (no ID returned).")
            return item_id
        except DatabaseError as e:
            logger.error(f"Failed to add item '{name}' for user_id {user_id}: {e}")
            raise