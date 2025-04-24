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

    def add_rated_item(self, user_id, name, item_type, status, alt_name=None, review=None):
        """
        Adds a new item basics to the database (without overall rating).
        Returns the new item_id or raises DatabaseError.
        """
        sql = """
                INSERT INTO rated_items
                    (user_id, name, alt_name, item_type, status, review, rating)
                VALUES
                    (%s, %s, %s, %s, %s, %s, NULL)
                RETURNING item_id;
              """
        params = (user_id, name, alt_name, item_type, status, review)
        try:
            result = self.execute_query(sql, params, fetch="one")
            item_id = result[0] if result else None
            if item_id:
                logger.info(f"Successfully added basic item info '{name}' with id {item_id} for user {user_id}.")
            else:
                logger.error(
                    f"Failed to add basic item info '{name}' for user {user_id} - INSERT query did not return ID.")
                raise DatabaseError("Item creation failed unexpectedly (no ID returned).")
            return item_id
        except DatabaseError as e:
            logger.error(f"Failed to add basic item info '{name}' for user_id {user_id}: {e}")
            raise

    def add_or_update_criterion_rating(self, item_id, criterion_id, rating):
        """Adds a new criterion rating or updates the existing one for an item."""
        sql = """
            INSERT INTO item_criterion_ratings (item_id, criterion_id, rating)
            VALUES (%s, %s, %s)
            ON CONFLICT (item_id, criterion_id)
            DO UPDATE SET rating = EXCLUDED.rating;
        """
        params = (item_id, criterion_id, rating)
        try:
            self.execute_query(sql, params, fetch=None)
            logger.debug(f"Successfully added/updated criterion rating for item {item_id}, criterion {criterion_id}.")
            return True
        except DatabaseError as e:
            logger.error(f"Failed to add/update criterion rating for item {item_id}, criterion {criterion_id}: {e}")
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
        """Retrieves all rated items for the user with sorting. Rating is the calculated overall rating."""
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

    def get_criterion_by_id(self, criterion_id, use_dict_cursor=True):
        """Gets criterion details by its ID."""
        sql = "SELECT criterion_id, name, description, default_for_types, is_overall FROM criteria WHERE criterion_id = %s;"
        try:
            return self.execute_query(sql, (criterion_id,), fetch="one", use_dict_cursor=use_dict_cursor)
        except DatabaseError as e:
            logger.error(f"Failed to get criterion by id {criterion_id}: {e}")
            raise

    def get_criterion_by_name(self, name, use_dict_cursor=True):
        """Gets criterion details by its name."""
        sql = "SELECT criterion_id, name, description, default_for_types, is_overall FROM criteria WHERE name = %s;"
        try:
            return self.execute_query(sql, (name,), fetch="one", use_dict_cursor=use_dict_cursor)
        except DatabaseError as e:
            logger.error(f"Failed to get criterion by name '{name}': {e}")
            raise

    def get_overall_criterion(self, use_dict_cursor=True):
        """Gets the special 'overall' criterion details."""
        sql = "SELECT criterion_id, name, description, default_for_types, is_overall FROM criteria WHERE is_overall = TRUE LIMIT 1;"
        try:
            return self.execute_query(sql, fetch="one", use_dict_cursor=use_dict_cursor)
        except DatabaseError as e:
            logger.error(f"Failed to get the overall criterion: {e}")
            raise

    def get_all_criteria(self, use_dict_cursor=True):
        """Gets all defined criteria, ordered by name."""
        sql = "SELECT criterion_id, name, description, default_for_types, is_overall FROM criteria ORDER BY name;"
        try:
            return self.execute_query(sql, fetch="all", use_dict_cursor=use_dict_cursor)
        except DatabaseError as e:
            logger.error(f"Failed to get all criteria: {e}")
            raise

    def get_suggested_criteria(self, item_type, use_dict_cursor=True):
        """Gets criteria suggested for a specific item type."""
        sql = """
            SELECT criterion_id, name, description, default_for_types, is_overall
            FROM criteria
            WHERE %s = ANY(default_for_types)
            ORDER BY name;
        """
        try:
            return self.execute_query(sql, (item_type,), fetch="all", use_dict_cursor=use_dict_cursor)
        except DatabaseError as e:
            logger.error(f"Failed to get suggested criteria for type '{item_type}': {e}")
            raise

    def get_criterion_ratings_for_item(self, item_id, use_dict_cursor=True):
        """Gets all criterion ratings for a specific item, joining with criteria names."""
        sql = """
            SELECT
                icr.rating_id, icr.item_id, icr.criterion_id, icr.rating,
                c.name as criterion_name, c.is_overall
            FROM item_criterion_ratings icr
            JOIN criteria c ON icr.criterion_id = c.criterion_id
            WHERE icr.item_id = %s
            ORDER BY c.name;
        """
        try:
            return self.execute_query(sql, (item_id,), fetch="all", use_dict_cursor=use_dict_cursor)
        except DatabaseError as e:
            logger.error(f"Failed to get criterion ratings for item {item_id}: {e}")
            raise

    def get_user_details(self, user_id):
        """Fetches user details (email, created_at) by user_id."""
        sql = "SELECT email, created_at FROM users WHERE user_id = %s;"
        try:
            return self.execute_query(sql, (user_id,), fetch="one")
        except DatabaseError as e:
            logger.error(f"Failed to get user details for user_id {user_id}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error getting user details for {user_id}: {e}")
            raise DatabaseError(f"Unexpected error getting user details: {e}") from e

    def get_user_statistics(self, user_id):
        """Calculates and returns various statistics for a user."""
        stats = {
            'total_items': 0,
            'count_by_type': {},  # {'Movie': 10, 'Game': 5, ...}
            'count_by_status': {},  # {'Completed': 15, ...}
            'average_rating': None,
            'avg_rating_by_type': {},
            'rating_distribution': {}
        }
        try:
            sql_total_avg = """
                            SELECT COUNT(*), AVG(rating)
                            FROM rated_items
                            WHERE user_id = %s; \
                            """
            result_total_avg = self.execute_query(sql_total_avg, (user_id,), fetch="one")
            if result_total_avg:
                stats['total_items'] = result_total_avg['count']
                if result_total_avg['avg'] is not None:
                    stats['average_rating'] = round(float(result_total_avg['avg']), 2)

            sql_by_type = """
                          SELECT item_type, COUNT(*) as count
                          FROM rated_items
                          WHERE user_id = %s
                          GROUP BY item_type
                          ORDER BY count DESC; \
                          """
            result_by_type = self.execute_query(sql_by_type, (user_id,), fetch="all")
            if result_by_type:
                stats['count_by_type'] = {row['item_type']: row['count'] for row in result_by_type}

            sql_by_status = """
                            SELECT status, COUNT(*) as count
                            FROM rated_items
                            WHERE user_id = %s
                            GROUP BY status
                            ORDER BY count DESC; \
                            """
            result_by_status = self.execute_query(sql_by_status, (user_id,), fetch="all")
            if result_by_status:
                stats['count_by_status'] = {row['status']: row['count'] for row in result_by_status}

            sql_avg_by_type = """
                              SELECT item_type, AVG(rating) as avg_rating
                              FROM rated_items
                              WHERE user_id = %s \
                                AND rating IS NOT NULL
                              GROUP BY item_type
                              ORDER BY item_type; \
                              """
            result_avg_by_type = self.execute_query(sql_avg_by_type, (user_id,), fetch="all")
            if result_avg_by_type:
                stats['avg_rating_by_type'] = {
                    row['item_type']: round(float(row['avg_rating']), 1)
                    for row in result_avg_by_type
                }

            sql_dist = """
                       SELECT ROUND(rating) as rating_group, COUNT(*) as count
                       FROM rated_items
                       WHERE user_id = %s AND rating IS NOT NULL
                       GROUP BY rating_group
                       ORDER BY rating_group DESC;
                       """
            result_dist = self.execute_query(sql_dist, (user_id,), fetch="all")
            if result_dist:
                stats['rating_distribution'] = {
                    int(row['rating_group']): row['count']
                    for row in result_dist if row['rating_group'] is not None
                }

            logger.info(f"Statistics calculated successfully for user_id {user_id}")
            return stats

        except DatabaseError as e:
            logger.error(f"Failed to get statistics for user_id {user_id}: {e}")
            return stats
        except Exception as e:
            logger.exception(f"Unexpected error calculating statistics for {user_id}: {e}")
            return stats

    def get_user_password_hash(self, user_id):
        """Fetches only the password hash for a user."""
        sql = "SELECT password_hash FROM users WHERE user_id = %s;"
        try:
            result = self.execute_query(sql, (user_id,), fetch="one")
            return result['password_hash'] if result else None
        except DatabaseError as e:
            logger.error(f"Failed to get password hash for user_id {user_id}: {e}")
            raise

    def update_user_password(self, user_id, new_password_hash):
        """Updates the user's password hash."""
        sql = "UPDATE users SET password_hash = %s WHERE user_id = %s;"
        params = (new_password_hash, user_id)
        try:
            self.execute_query(sql, params, fetch=None)
            logger.info(f"Password updated successfully for user_id {user_id}.")
            return True
        except DatabaseError as e:
            logger.error(f"Failed to update password for user_id {user_id}: {e}")
            raise

    def update_rated_item(self, item_id, name, alt_name, item_type, status, review):
        """Updates the basic fields of an existing rated item."""
        sql = """
            UPDATE rated_items
            SET name = %s,
                alt_name = %s,
                item_type = %s,
                status = %s,
                review = %s
            WHERE item_id = %s;
        """
        params = (name, alt_name, item_type, status, review, item_id)
        try:
            self.execute_query(sql, params, fetch=None)
            logger.info(f"Successfully updated basic info for item {item_id}.")
            return True
        except DatabaseError as e:
            logger.error(f"Failed to update basic info for item {item_id}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error updating item {item_id}: {e}")
            raise DatabaseError(f"Unexpected error updating item: {e}") from e

    def update_overall_rating(self, item_id, direct_overall_rating=None):
        """
        Calculates and updates the overall rating in rated_items.
        If direct_overall_rating is provided, uses it directly.
        Otherwise, calculates the average from item_criterion_ratings (excluding the 'overall' criterion).
        """
        final_rating = None

        try:
            if direct_overall_rating is not None:
                try:
                    final_rating = float(direct_overall_rating)
                    if not (1.0 <= final_rating <= 10.0):
                        logger.warning(
                            f"Direct overall rating {final_rating} for item {item_id} is out of range 1-10. Setting to NULL.")
                        final_rating = None
                except (ValueError, TypeError):
                    logger.error(
                        f"Invalid direct overall rating value '{direct_overall_rating}' for item {item_id}. Setting to NULL.")
                    final_rating = None
                logger.info(f"Using direct overall rating {final_rating} for item {item_id}.")

            else:
                logger.debug(f"Calculating average rating for item {item_id} from criteria...")
                overall_criterion = self.get_overall_criterion(use_dict_cursor=True)
                overall_criterion_id = overall_criterion['criterion_id'] if overall_criterion else None

                if overall_criterion_id is None:
                    logger.error("Cannot calculate average rating: 'Overall' criterion not found in DB.")
                    return False

                sql_avg = """
                    SELECT rating FROM item_criterion_ratings
                    WHERE item_id = %s AND criterion_id != %s;
                """
                params_avg = (item_id, overall_criterion_id)
                ratings_list = self.execute_query(sql_avg, params_avg, fetch="all", use_dict_cursor=False)

                if ratings_list:
                    total = sum(r[0] for r in ratings_list)
                    count = len(ratings_list)
                    average = round(total / count, 2)
                    final_rating = average
                    logger.info(f"Calculated average rating {final_rating} from {count} criteria for item {item_id}.")
                else:
                    logger.info(f"No specific criteria rated for item {item_id}. Overall rating will be NULL.")
                    final_rating = None

            sql_update = "UPDATE rated_items SET rating = %s WHERE item_id = %s;"
            params_update = (final_rating, item_id)
            self.execute_query(sql_update, params_update, fetch=None)
            logger.info(f"Updated overall rating for item {item_id} to {final_rating}.")
            return True

        except DatabaseError as e:
            logger.error(f"Failed to update overall rating for item {item_id}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error updating overall rating for item {item_id}: {e}")
            raise DatabaseError(f"Unexpected error updating overall rating: {e}") from e

    def delete_rated_item(self, item_id):
        """Deletes a rated item and its associated criteria ratings (due to CASCADE)."""
        sql = "DELETE FROM rated_items WHERE item_id = %s;"
        params = (item_id,)
        try:
            self.execute_query(sql, params, fetch=None)
            logger.info(f"Successfully deleted rated item with id {item_id}.")
            return True
        except DatabaseError as e:
            logger.error(f"Failed to delete rated item with id {item_id}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error deleting item {item_id}: {e}")
            raise DatabaseError(f"Unexpected error deleting item: {e}") from e

    def delete_criteria_ratings_except(self, item_id, criteria_ids_to_keep):
        """Deletes criterion ratings for an item that are NOT in the provided list of IDs to keep."""
        if not criteria_ids_to_keep:
            logger.warning(
                f"delete_criteria_ratings_except called with empty keep list for item {item_id}. No ratings deleted.")
            return True

        ids_tuple = tuple(criteria_ids_to_keep)

        overall_criterion = self.get_overall_criterion()
        overall_id = overall_criterion['criterion_id'] if overall_criterion else -1

        sql = """
            DELETE FROM item_criterion_ratings
            WHERE item_id = %s
              AND criterion_id != %s
              AND criterion_id NOT IN %s;
        """
        params = (item_id, overall_id, ids_tuple)

        try:
            result = self.execute_query(sql, params, fetch=None)
            logger.info(f"Executed deletion of criteria ratings for item {item_id} not in {criteria_ids_to_keep}.")
            return True
        except DatabaseError as e:
            logger.error(f"Failed to delete criteria ratings for item {item_id}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error deleting criteria ratings for item {item_id}: {e}")
            raise DatabaseError(f"Unexpected error deleting criteria ratings: {e}") from e