"""
Interface for executing sql instruction on local SQLite3 database. 

This moudule allow for the sharing of one database connection to be 
used across the the whole project.

    Typical usage example:

    import core.database as db

    db.connect("example.db")
    query = db.execute("SELECT * FROM table WHERE id=?",(id,))
    db.execute_and_commit("INSERT INTO table VALUE (...)"
"""
import json
import atexit
import sqlite3

_connection = None


def setup(config_path: str) -> None:
    """
    Connect to database using a config file

    Args:
        config_path: path to a JSON config file 

    Returns:
        None

    Raises:
        IOError: Config file cannot be read
        json.JSONDecodeError: Invaild JSON
        KeyError: The keys: ["database"]["DB_PATH"] does not exist
        sqlite3.OperationalError: Failed to create a connection to database
    """

    with open(config_path) as f:
        path = json.load(f)["database"]["DB_PATH"]

    connect(path)


def connect(db_path: str) -> None:
    """
    Connect to database

    Args:
        db_path: path to database

    Returns:
        None

    Raises:
        sqlite3.OperationalError: Database cannot be opened
        sqlite3.OperationalError: Database is already connected
    """
    global _connection

    if _connection is not None:
        raise sqlite3.OperationalError(
            "Database is already connected, run disconnect() before connecting")

    _connection = sqlite3.connect(f'file:{str(db_path)}?mode=rw', uri=True)


@atexit.register
def disconnect() -> None:
    """Disconnect from database"""
    global _connection

    if _connection is None:
        return

    conn = get_connection()
    conn.commit()
    conn.close()
    _connection = None


def get_connection() -> sqlite3.Connection:
    """
    Get connection object of database

    Returns: 
        sqlite3.Connection

    Raises:
        sqlite3.OperationalError: Database not connected

    """
    global _connection
    if not _connection:
        raise sqlite3.OperationalError(
            "Database is Not Connected: Run db.connect() first")

    return _connection


def get_cursor():
    """
    Get connection cursor object of database

    Returns:
        sqlite3.Cursor objects

    Raises:
        sqlite3.OperationalError: Database not connected
    """

    global _connection

    if not _connection:
        raise sqlite3.OperationalError(
            "Database is Not Connected: Run db.connect() first")

    return _connection.cursor()


def execute(sql: str, format=None) -> list[tuple]:
    """
    Execute a SQL command to database

    Args:
        sql: SQL
        format (optional): tuple/dict as used in sqlite3.Cursor.execute(sql,format) 

    Returns:
        Return rows of a query result as a list of tuples. 
        Return an empty list if no rows are available.

    Raises:
        sqlite3.OperationalError: Database not connected
        sqlite3.OperationalError: Invaild SQL syntax / format
    """
    cur = get_cursor()

    if format is not None:
        return cur.execute(sql, format).fetchall()
    else:
        return cur.execute(sql).fetchall()


def commit() -> None:
    """
    Commit changes to database

    Raises:
        sqlite3.OperationalError: Database is not connected
    """

    get_connection().commit()


def execute_and_commit(sql: str, format=None) -> list[tuple]:
    """
    Execute and commit SQL command to database

    Args:
        sql: SQL
        format (optional): tuple/dict as used in sqlite3.Cursor.execute(sql,format) 

    Returns:
        Return rows of a query result as a list of tuples. 
        Return an empty list if no rows are available.

    Raises:
        sqlite3.OperationalError: Database not connected
        sqlite3.OperationalError: Invaild SQL syntax
    """

    cur = get_cursor()
    if format is not None:
        cur = cur.execute(sql, format).fetchall()
    else:
        cur = cur.execute(sql).fetchall()

    commit()
    return cur
