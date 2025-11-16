"""Oracle database connection utilities."""

import oracledb
from typing import Optional
import os
from pathlib import Path

def find_oracle_client_lib_dir(path: str) -> Optional[str]:
    """
    Automatically find Oracle Client library directory in common locations.

    Checks:
    - Homebrew installation paths (/opt/homebrew/opt/instantclient-basic/lib, /usr/local/opt/instantclient-basic/lib)
    - ORACLE_HOME environment variable
    - Common installation paths (macOS and Linux)

    Returns:
        Path to Oracle Client lib directory if found, None otherwise
    """

    def has_oracle_lib(path: Path) -> bool:
        """Check if path contains Oracle Client library (supports both macOS .dylib and Linux .so)"""
        return (path / "libclntsh.dylib").exists() or (path / "libclntsh.so").exists()

    # Check ORACLE_HOME environment variable
    oracle_home = os.getenv("ORACLE_HOME")
    if oracle_home:
        lib_path = Path(oracle_home)
        # Check if ORACLE_HOME points to lib directory or parent directory
        if lib_path.name == "lib":
            if lib_path.exists() and has_oracle_lib(lib_path):
                return str(lib_path)
        else:
            # Prioritize ORACLE_HOME itself (Docker case - libraries are directly in ORACLE_HOME)
            if lib_path.exists() and has_oracle_lib(lib_path):
                return str(lib_path)
            # Fall back to lib subdirectory if libraries aren't in ORACLE_HOME directly
            lib_subdir = lib_path / "lib"
            if lib_subdir.exists() and has_oracle_lib(lib_subdir):
                return str(lib_subdir)

    lib_path = Path(os.path.expanduser("~/Downloads/instantclient_23_3"))
    if lib_path.exists() and has_oracle_lib(lib_path):
        return str(lib_path)

    return None

def init_oracle_client(lib_dir: Optional[str] = None):
    """
    Initialize Oracle Client for thick mode.

    This is required when connecting to older Oracle database versions
    that are not supported by python-oracledb in thin mode.

    Args:
        lib_dir: Optional path to Oracle Client libraries directory.
                 If not provided, python-oracledb will search for Oracle Client
                 in common installation locations.

    Note:
        This only needs to be called once per application.
        If Oracle Client is not found, you may need to:
        1. Install Oracle Instant Client from Oracle's website
        2. Set the ORACLE_HOME environment variable
        3. Or provide the lib_dir parameter

    Example:
        >>> init_oracle_client()  # Auto-detect Oracle Client
        >>> # or
        >>> init_oracle_client(lib_dir="/path/to/instantclient_21_8")
    """
    try:
        if lib_dir:
            oracledb.init_oracle_client(lib_dir=lib_dir)
        else:
            oracledb.init_oracle_client()
        print("Oracle Client initialized successfully (thick mode)")
    except Exception as e:
        print(f"Warning: Could not initialize Oracle Client: {e}")
        print(
            "Attempting to continue with thin mode (may not work for older Oracle versions)"
        )
        raise

def connect_to_oracle(
    username: str,
    password: str,
    dsn: str,
    lib_dir: str,
    mode: Optional[int] = None,
    use_thick_mode: bool = True,
) -> oracledb.Connection:
    """
    Connect to an Oracle database.

    Args:
        username: Database username
        password: Database password
        dsn: Data Source Name (connection string)
              Format: "hostname:port/service_name" or "hostname:port:SID"
              Example: "localhost:1521/XEPDB1"
        mode: Optional connection mode (default: oracledb.default)
        use_thick_mode: If True, use thick mode (requires Oracle Client libraries).
                       Set to True if you get DPY-3010 error.
        lib_dir: Optional path to Oracle Client libraries directory.
                Only used if use_thick_mode is True.

    Returns:
        Oracle database connection object

    Example:
        >>> # Thin mode (default, no Oracle Client needed)
        >>> conn = connect_to_oracle(
        ...     username="myuser",
        ...     password="mypassword",
        ...     dsn="localhost:1521/XEPDB1"
        ... )
        >>>
        >>> # Thick mode (for older Oracle versions)
        >>> conn = connect_to_oracle(
        ...     username="myuser",
        ...     password="mypassword",
        ...     dsn="localhost:1521/XEPDB1",
        ...     use_thick_mode=True
        ... )
        >>> cursor = conn.cursor()
        >>> cursor.execute("SELECT * FROM my_table")
        >>> rows = cursor.fetchall()
        >>> conn.close()
    """
    # Initialize thick mode if requested
    if use_thick_mode:
        # initialized = False
        # If ORACLE_HOME is set, use it as lib_dir directly
        oracle_home = os.getenv("ORACLE_HOME")
        if oracle_home:
            # When ORACLE_HOME is set, libraries are directly in that directory
            # NOT in ORACLE_HOME/lib (Docker Instant Client structure)
            lib_dir = oracle_home
            print(f"Using ORACLE_HOME as lib_dir: {lib_dir}")

        try:
            oracledb.init_oracle_client(lib_dir=lib_dir)
            print(f"Oracle Client initialized from: {lib_dir}")
        except Exception as e:
            error_msg = str(e).lower()
            if (
                "already initialized" not in error_msg
                and "already been called" not in error_msg
            ):
                raise

        # Connect to the database
        try:
            connection = oracledb.connect(
                user=username, password=password, dsn=dsn, mode=mode
            )
            print(f"Successfully connected to Oracle database: {dsn}")
            return connection
        except oracledb.Error as e:
            (error,) = e.args
            print(f"Error connecting to Oracle database: {error.message}")
            raise

def execute_select(
    connection: oracledb.Connection, query: str, params: Optional[dict] = None
):
    """
    Execute a SELECT query and return results.

    Args:
        connection: Oracle database connection
        query: SQL query string
        params: Optional dictionary of parameters for parameterized queries

    Returns:
        List of tuples containing query results

    Example:
        >>> conn = connect_to_oracle(...)
        >>> results = execute_query(conn, "SELECT * FROM employees WHERE dept_id = :dept_id", {"dept_id": 10})
    """
    print(f"Executing query: {query}")
    cursor = connection.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        print(f"Query executed successfully. Rows fetched: {cursor.rowcount}")
        return cursor.fetchall()
    except oracledb.Error as e:
        (error,) = e.args
        print(f"Error executing query: {error.message}")
        raise
    finally:
        cursor.close()


def execute_dml(
    connection: oracledb.Connection, statement: str, params: Optional[dict] = None
):
    """
    Execute a DML statement (INSERT, UPDATE, DELETE) and commit.

    Args:
        connection: Oracle database connection
        statement: SQL DML statement
        params: Optional dictionary of parameters for parameterized queries

    Example:
        >>> conn = connect_to_oracle(...)
        >>> execute_dml(conn, "INSERT INTO employees (id, name) VALUES (:id, :name)", {"id": 1, "name": "John"})
    """
    cursor = connection.cursor()
    try:
        if params:
            cursor.execute(statement, params)
        else:
            cursor.execute(statement)
        connection.commit()
        print(f"Statement executed successfully. Rows affected: {cursor.rowcount}")
    except oracledb.Error as e:
        connection.rollback()
        (error,) = e.args
        print(f"Error executing statement: {error.message}")
        raise
    finally:
        cursor.close()