"""Oracle database connection utilities."""

import oracledb
from typing import Optional
import os
from pathlib import Path

def find_oracle_client_lib_dir() -> Optional[str]:
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

    # Check Homebrew paths (Apple Silicon and Intel)
    homebrew_paths = [
        "/opt/homebrew/opt/instantclient-basic/lib",  # Apple Silicon
        "/usr/local/opt/instantclient-basic/lib",  # Intel Mac
    ]

    for path in homebrew_paths:
        path_obj = Path(path)
        if path_obj.exists() and has_oracle_lib(path_obj):
            return path

    # Check common installation paths
    common_paths = [
        os.path.expanduser("~/Downloads/instantclient_23_3"),
        os.path.expanduser("~/Downloads/instantclient_21_8"),
        os.path.expanduser("~/Downloads/instantclient_19_8"),
        os.path.expanduser("~/oracle/instantclient_23_3"),
        os.path.expanduser("~/oracle/instantclient_21_8"),
        os.path.expanduser("~/oracle/instantclient_19_8"),
        "/usr/lib/oracle/23.3/client64/lib",
        "/usr/lib/oracle/21.8/client64/lib",
        "/usr/lib/oracle/19.8/client64/lib",
        "/opt/oracle/instantclient_23_3",
        "/opt/oracle/instantclient_21_8",
        "/opt/oracle/instantclient_19_8",
        "/opt/oracle/instantclient_21_9",
        "/opt/oracle/instantclient",
    ]

    for path in common_paths:
        lib_path = Path(path)
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
    lib_dir: Optional[str] = None,
    mode: Optional[int] = None,
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
        lib_dir: Optional path to Oracle Client libraries directory.
                 If not provided, will auto-detect from common locations.
    Returns:
        Oracle database connection object

    Example:
        >>> # Auto-detect Oracle Client
        >>> conn = connect_to_oracle(
        ...     username="myuser",
        ...     password="mypassword",
        ...     dsn="localhost:1521/XEPDB1"
        ... )
        >>>
        >>> # Specify Oracle Client location
        >>> conn = connect_to_oracle(
        ...     username="myuser",
        ...     password="mypassword",
        ...     dsn="localhost:1521/XEPDB1",
        ...     lib_dir="/path/to/instantclient"
        ... )
        >>> cursor = conn.cursor()
        >>> cursor.execute("SELECT * FROM my_table")
        >>> rows = cursor.fetchall()
        >>> conn.close()
    """
    # Auto-detect lib_dir if not provided
    if not lib_dir:
        detected_lib_dir = find_oracle_client_lib_dir()
        if detected_lib_dir:
            lib_dir = detected_lib_dir
            print(f"Auto-detected Oracle Client at: {lib_dir}")
        else:
            print("Warning: Oracle Client library not found. Attempting to use default locations...")

    # Initialize Oracle Client
    try:
        if lib_dir:
            oracledb.init_oracle_client(lib_dir=lib_dir)
            print(f"Oracle Client initialized from: {lib_dir}")
        else:
            # Last resort - let python-oracledb search default locations
            oracledb.init_oracle_client()
            print("Oracle Client initialized from default locations")
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

def delete_all(connection: oracledb.Connection):
    """
    Delete all records from the database.

    Args:
        connection: Oracle database connection
    """
    cursor = connection.cursor()
    try:
        cursor.execute("DROP TABLE bookings_services")
        cursor.execute("DROP TABLE payments")
        cursor.execute("DROP TABLE room_types")
        cursor.execute("DROP TABLE rooms")
        cursor.execute("DROP TABLE bookings")
        cursor.execute("DROP TABLE positions")
        cursor.execute("DROP TABLE staff")
        cursor.execute("DROP TABLE services")
        cursor.execute("DROP TABLE guests")
        connection.commit()
        print("All tables deleted successfully")
    except oracledb.Error as e:
        connection.rollback()
        (error,) = e.args
        print(f"Error deleting all records: {error.message}")
        raise
    finally:
        cursor.close()

def create_tables(connection: oracledb.Connection):
    """
    Create the tables in the database.

    Args:
        connection: Oracle database connection

        CREATE TABLE guests (id INTEGER PRIMARY KEY,
email VARCHAR2(255),
phone_num VARCHAR2(255),
first_name VARCHAR2(255) NOT NULL,
last_name VARCHAR2(255) NOT NULL);
CREATE TABLE services (id INTEGER PRIMARY KEY,
service_type VARCHAR2(255) NOT NULL,
price NUMBER NOT NULL);

CREATE TABLE staff (id INTEGER PRIMARY KEY,
first_name VARCHAR2(255) NOT NULL,
last_name VARCHAR2(255) NOT NULL,
email VARCHAR2(255),
staff_dept VARCHAR2(20) CHECK (staff_dept IN ('KITCHEN',
'RECEPTION', 'HOUSEKEEPING')),
position VARCHAR2(255) NOT NULL,
pay_type VARCHAR2(20) CHECK (pay_type IN ('HOURLY',
'ANNUALLY')),
staff_pay NUMBER NOT NULL,
status VARCHAR2(20) CHECK(status in ('ACTIVE', 'INACTIVE'))
NOT NULL, service_id INTEGER REFERENCES services(id));
CREATE TABLE bookings (id INTEGER PRIMARY KEY,
check_in_date DATE NOT NULL,
check_out_date DATE,
status VARCHAR2(20) DEFAULT 'ONGOING'
CHECK(status in ('ONGOING', 'CANCELLED',
'CHECKED_OUT')),
guest_id INTEGER NOT NULL REFERENCES guests(id),
staff_id INTEGER NOT NULL REFERENCES staff(id));
CREATE TABLE rooms (id INTEGER PRIMARY KEY,
floor_num INTEGER NOT NULL,
room_type VARCHAR2(20) DEFAULT 'REGULAR'
CHECK(room_type in ('REGULAR', 'SUITE')),
room_price NUMBER NOT NULL,
booking_id INTEGER REFERENCES bookings(id));

CREATE TABLE payments (id INTEGER PRIMARY KEY,
booking_id INTEGER NOT NULL REFERENCES
bookings(id),
amount NUMERIC(6,2) NOT NULL,
payment_date DATE,
payment_method VARCHAR2(20) DEFAULT 'NONE'
CHECK(payment_method IN ('CASH', 'CREDIT',
'BANK_TRANSFER', 'NONE')));
CREATE TABLE bookings_services (id INTEGER PRIMARY KEY,
booking_id INTEGER NOT NULL REFERENCES
bookings(id),
service_id INTEGER NOT NULL REFERENCES
services(id));

CREATE TABLE room_types (room_type VARCHAR2(20) NOT NULL,
room_price NUMBER NOT NULL,
PRIMARY KEY (room_type));

CREATE TABLE departments (position VARCHAR2(20) NOT NULL,
dept VARCHAR2(20) NOT NULL,
pay_type VARCHAR2(20) NOT NULL,
PRIMARY KEY (position));
    """
    cursor = connection.cursor()
    try:
        cursor.execute("""CREATE TABLE guests (id INTEGER PRIMARY KEY,
email VARCHAR2(255),
phone_num VARCHAR2(255),
first_name VARCHAR2(255) NOT NULL,
last_name VARCHAR2(255) NOT NULL)""")

        cursor.execute("""CREATE TABLE services (id INTEGER PRIMARY KEY,
service_type VARCHAR2(255) NOT NULL,
price NUMBER NOT NULL)""")

        cursor.execute("""CREATE TABLE staff (id INTEGER PRIMARY KEY,
first_name VARCHAR2(255) NOT NULL,
last_name VARCHAR2(255) NOT NULL,
email VARCHAR2(255),
staff_dept VARCHAR2(20) CHECK (staff_dept IN ('KITCHEN',
'RECEPTION', 'HOUSEKEEPING')),
position VARCHAR2(255) NOT NULL,
pay_type VARCHAR2(20) CHECK (pay_type IN ('HOURLY',
'ANNUALLY')),
staff_pay NUMBER NOT NULL,
status VARCHAR2(20) CHECK(status in ('ACTIVE', 'INACTIVE'))
NOT NULL, service_id INTEGER REFERENCES services(id))""")

        cursor.execute("""CREATE TABLE bookings (id INTEGER PRIMARY KEY,
check_in_date DATE NOT NULL,
check_out_date DATE,
status VARCHAR2(20) DEFAULT 'ONGOING'
CHECK(status in ('ONGOING', 'CANCELLED',
'CHECKED_OUT')),
guest_id INTEGER NOT NULL REFERENCES guests(id),
staff_id INTEGER NOT NULL REFERENCES staff(id))""")

        cursor.execute("""CREATE TABLE rooms (id INTEGER PRIMARY KEY,
floor_num INTEGER NOT NULL,
room_type VARCHAR2(20) DEFAULT 'REGULAR'
CHECK(room_type in ('REGULAR', 'SUITE')),
booking_id INTEGER REFERENCES bookings(id))""")

        cursor.execute("""CREATE TABLE payments (id INTEGER PRIMARY KEY,
booking_id INTEGER NOT NULL REFERENCES
bookings(id),
amount NUMERIC(6,2) NOT NULL,
payment_date DATE,
payment_method VARCHAR2(20) DEFAULT 'NONE'
CHECK(payment_method IN ('CASH', 'CREDIT',
'BANK_TRANSFER', 'NONE')))""")

        cursor.execute("""CREATE TABLE bookings_services (id INTEGER PRIMARY KEY,
booking_id INTEGER NOT NULL REFERENCES
bookings(id),
service_id INTEGER NOT NULL REFERENCES
services(id))""")

        cursor.execute("""CREATE TABLE room_types (room_type VARCHAR2(20) NOT NULL,
room_price NUMBER NOT NULL,
PRIMARY KEY (room_type))""")

        cursor.execute("""CREATE TABLE positions (position VARCHAR2(40) NOT NULL,
staff_dept VARCHAR2(30) NOT NULL,
pay_type VARCHAR2(20) NOT NULL,
PRIMARY KEY (position))""")

        connection.commit()
        print("Tables created successfully")

    except oracledb.Error as e:
        connection.rollback()
        (error,) = e.args
        print(f"Error inserting sample data: {error.message}")
        raise
    finally:
        cursor.close()

def populate(connection: oracledb.Connection):
    """
    Populate the database with sample data.

    Args:
        connection: Oracle database connection
    """
    print("Populating database with sample data...")
    cursor = connection.cursor()
    try:
        cursor.execute("INSERT INTO guests (id, email, phone_num, first_name, last_name) VALUES (1, 'rousseau@gmail.com', '123-456', 'Jean-Jacques', 'Rousseau')")
        cursor.execute("INSERT INTO guests (id, email, phone_num, first_name, last_name) VALUES (2, 'fdostoevsky@gmail.com', '456-789', 'Fyodor', 'Dostoevsky')")
        cursor.execute("INSERT INTO guests (id, email, phone_num, first_name, last_name) VALUES (3, 'alexandre.dumas@gmail.com', '789-123', 'Alexandre', 'Dumas')")
        cursor.execute("INSERT INTO guests (id, email, phone_num, first_name, last_name) VALUES (4, 'julius.caesar@gmail.com', '135-790', 'Julius', 'Caesar')")
        cursor.execute("INSERT INTO guests (id, email, phone_num, first_name, last_name) VALUES (5, 'shakespeare@gmail.com', '246-802', 'William', 'Shakespeare')")
        cursor.execute("INSERT INTO services (id, service_type, price) VALUES (1, 'Room Service', 25.00)")
        cursor.execute("INSERT INTO services (id, service_type, price) VALUES (2, 'Spa Treatment', 120.00)")
        cursor.execute("INSERT INTO services (id, service_type, price) VALUES (3, 'Laundry Service', 15.00)")
        cursor.execute("INSERT INTO services (id, service_type, price) VALUES (4, 'Airport Shuttle', 35.00)")
        cursor.execute("INSERT INTO services (id, service_type, price) VALUES (5, 'Breakfast Buffet', 18.00)")
        cursor.execute("INSERT INTO services (id, service_type, price) VALUES (6, 'Valet Parking', 20.00)")
        cursor.execute("INSERT INTO services (id, service_type, price) VALUES (7, 'Gym Access', 10.00)")

        cursor.execute("INSERT INTO room_types (room_type, room_price) VALUES ('REGULAR', 120.00)")
        cursor.execute("INSERT INTO room_types (room_type, room_price) VALUES ('SUITE', 250.00)")
        
        cursor.execute("INSERT INTO positions (position, staff_dept, pay_type) VALUES ('Hotel Manager', 'RECEPTION', 'ANNUALLY')")
        cursor.execute("INSERT INTO positions (position, staff_dept, pay_type) VALUES ('Receptionist', 'RECEPTION', 'HOURLY')")
        cursor.execute("INSERT INTO positions (position, staff_dept, pay_type) VALUES ('Housekeeping Supervisor', 'HOUSEKEEPING', 'ANNUALLY')")
        cursor.execute("INSERT INTO positions (position, staff_dept, pay_type) VALUES ('Head Chef', 'KITCHEN', 'ANNUALLY')")

        cursor.execute("INSERT INTO staff (id, first_name, last_name, email, position, staff_pay, status, service_id) VALUES (1, 'Caesar', 'Augustus', 'caesar.augustus@hotel.com', 'Hotel Manager', 200000, 'ACTIVE', NULL)")
        cursor.execute("INSERT INTO staff (id, first_name, last_name, email, position, staff_pay, status, service_id) VALUES (2, 'Marcus', 'Cicero', 'marcus.cicero@hotel.com', 'Receptionist', 21.50, 'ACTIVE', NULL)")
        cursor.execute("INSERT INTO staff (id, first_name, last_name, email, position, staff_pay, status, service_id) VALUES (3, 'Haruki', 'Murakami', 'haruki.murakami@hotel.com', 'Housekeeping Supervisor', 37000, 'ACTIVE', 1)")
        cursor.execute("INSERT INTO staff (id, first_name, last_name, email, position, staff_pay, status, service_id) VALUES (4, 'Leo', 'Tolstoy', 'leo.tolstoy@hotel.com', 'Head Chef', 75000, 'ACTIVE', 5)")

        cursor.execute("INSERT INTO rooms (id, floor_num, room_type, booking_id) VALUES (101, 1, 'REGULAR', NULL)")
        cursor.execute("INSERT INTO rooms (id, floor_num, room_type, booking_id) VALUES (102, 1, 'REGULAR', NULL)")
        cursor.execute("INSERT INTO rooms (id, floor_num, room_type, booking_id) VALUES (103, 1, 'SUITE', NULL)")
        cursor.execute("INSERT INTO rooms (id, floor_num, room_type, booking_id) VALUES (201, 2, 'REGULAR', NULL)")
        cursor.execute("INSERT INTO rooms (id, floor_num, room_type, booking_id) VALUES (202, 2, 'REGULAR', NULL)")
        cursor.execute("INSERT INTO rooms (id, floor_num, room_type, booking_id) VALUES (203, 2, 'SUITE', NULL)")
        cursor.execute("INSERT INTO rooms (id, floor_num, room_type, booking_id) VALUES (301, 3, 'REGULAR', NULL)")
        cursor.execute("INSERT INTO rooms (id, floor_num, room_type, booking_id) VALUES (302, 3, 'REGULAR', NULL)")
        cursor.execute("INSERT INTO rooms (id, floor_num, room_type, booking_id) VALUES (303, 3, 'SUITE', NULL)")
        cursor.execute("INSERT INTO rooms (id, floor_num, room_type, booking_id) VALUES (401, 4, 'SUITE', NULL)")

        cursor.execute("INSERT INTO bookings (id, check_in_date, check_out_date, status, guest_id, staff_id) VALUES (1, DATE '2025-09-16', NULL, 'ONGOING', 1, 1)")
        cursor.execute("INSERT INTO bookings (id, check_in_date, check_out_date, status, guest_id, staff_id) VALUES (2, DATE '2025-08-20', DATE '2025-08-22', 'CHECKED_OUT', 2, 2)")
        cursor.execute("INSERT INTO bookings (id, check_in_date, check_out_date, status, guest_id, staff_id) VALUES (4, DATE '2025-09-10', DATE '2025-09-15', 'CHECKED_OUT', 3, 3)")
        cursor.execute("INSERT INTO bookings (id, check_in_date, check_out_date, status, guest_id, staff_id) VALUES (8, DATE '2025-09-20', NULL, 'ONGOING', 4, 4)")

        cursor.execute("INSERT INTO payments (id, booking_id, amount, payment_date, payment_method) VALUES (1, 1, 2100.00, DATE '2025-09-17', 'BANK_TRANSFER')")
        cursor.execute("INSERT INTO payments (id, booking_id, amount, payment_date, payment_method) VALUES (2, 2, 600.00, DATE '2025-08-21', 'CASH')")
        cursor.execute("INSERT INTO payments (id, booking_id, amount, payment_date, payment_method) VALUES (3, 4, 1500.00, DATE '2025-09-14', 'CREDIT')")
        cursor.execute("INSERT INTO payments (id, booking_id, amount, payment_date, payment_method) VALUES (4, 8, 900.00, DATE '2024-09-20', 'BANK_TRANSFER')")

        cursor.execute("UPDATE rooms SET booking_id = 1 WHERE id = 302")
        cursor.execute("UPDATE rooms SET booking_id = 8 WHERE id = 401")

        cursor.execute("INSERT INTO bookings_services (id, booking_id, service_id) VALUES (1, 2, 1)")
        cursor.execute("INSERT INTO bookings_services (id, booking_id, service_id) VALUES (2, 4, 3)")
        cursor.execute("INSERT INTO bookings_services (id, booking_id, service_id) VALUES (3, 8, 6)")
        connection.commit()
        print("Sample data inserted successfully")
    except oracledb.Error as e:
        connection.rollback()
        (error,) = e.args
        print(f"Error populating database: {error.message}")
        raise
    finally:
        cursor.close()

def q1(connection: oracledb.Connection):
    """
    Query 1: Get all guests.

    Args:
        connection: Oracle database connection
    """
    cursor = connection.cursor()
    try:
        cursor.execute("""
        SELECT 
    r.id AS room_number,
    rt.room_type,
    b.status AS booking_status,
    b.Check_In_Date,
    b.Check_Out_Date,
    g.first_name || ' ' || g.last_name AS guest_name,
    p.amount
FROM rooms r
JOIN room_type rt
    ON r.room_type = rt.room_type
JOIN bookings b 
    ON r.booking_id = b.id
JOIN guests g 
    ON b.guest_id = g.id
JOIN payments p 
    ON b.ID = p.booking_id
WHERE
    b.status = 'ONGOING'
        """)
        return cursor.fetchall()
    except oracledb.Error as e:
        (error,) = e.args
        print(f"Error executing query: {error.message}")
        raise
    finally:
        cursor.close()

def q2(connection: oracledb.Connection):
    """
    Find reception staff who are assigned services UNION kitchen staff with services.

    Args:
        connection: Oracle database connection
    """
    cursor = connection.cursor()
    try:
        cursor.execute("""
    SELECT DISTINCT 
        s.id,
        s.first_name || ' ' || s.last_name as staff_name,
        p.staff_dept,
        sv.service_type
    FROM staff s
    JOIN positions p ON s.position = p.position
    JOIN services sv ON s.service_id = sv.id
    WHERE p.staff_dept = 'RECEPTION' AND s.status = 'ACTIVE'
    UNION
    SELECT DISTINCT 
        s.id,
        s.first_name || ' ' || s.last_name as staff_name,
        d.dept,
        sv.service_type
    FROM staff s
    JOIN services sv ON s.service_id = sv.id
    WHERE p.staff_dept = 'KITCHEN' AND s.status = 'ACTIVE'
    ORDER BY p.staff_dept, s.first_name || ' ' || s.last_name
        """)
        return cursor.fetchall()
    except oracledb.Error as e:
        (error,) = e.args
        print(f"Error executing query: {error.message}")
        raise
    finally:
        cursor.close()

def q3(connection: oracledb.Connection):
    """ 
    Shows guests who spent more than average, including service usage
    """    
    cursor = connection.cursor()
    try:
        cursor.execute("""
    SELECT 
            g.first_name || ' ' || g.last_name as guest_name,
            g.email,
            COUNT(DISTINCT b.id) as num_bookings,
            SUM(p.amount) as total_spent,
            ROUND(AVG(p.amount), 2) as avg_booking_cost,
            COUNT(bs.service_id) as services_used
        FROM guests g
        JOIN bookings b ON g.id = b.guest_id
        JOIN payments p ON b.id = p.booking_id
        LEFT JOIN bookings_services bs ON b.id = bs.booking_id
        WHERE b.status = 'CHECKED_OUT'
        GROUP BY g.id, g.first_name, g.last_name, g.email
        HAVING SUM(p.amount) > (
            SELECT AVG(amount) 
            FROM payments 
            WHERE payment_method != 'NONE'
        )
        ORDER BY total_spent DESC
        """)
        return cursor.fetchall()
    except oracledb.Error as e:
        (error,) = e.args
        print(f"Error executing query: {error.message}")
        raise
    finally:
        cursor.close()

def q4(connection: oracledb.Connection):
    """
    Services used in each booking and the staff member corresponding to that service
    Args:
        connection: Oracle database connection
    """
    cursor = connection.cursor()
    try:
        cursor.execute("""
        SELECT DISTINCT st.id as staff_id, sv.id as service_id, bs.booking_id as booking_id
FROM staff st
JOIN services sv on st.service_id = sv.id
JOIN bookings_services  bs on bs.service_id = sv.id
        """)
        return cursor.fetchall()
    except oracledb.Error as e:
        (error,) = e.args
        print(f"Error executing query: {error.message}")
        raise
    finally:
        cursor.close()

def q5(connection: oracledb.Connection):
    """
    Find active staff who have processed bookings MINUS those with cancelled bookings
    Args:
        connection: Oracle database connection
    """
    cursor = connection.cursor()
    try:
        cursor.execute("""
        SELECT 
        s.id,
        s.first_name || ' ' || s.last_name as staff_name,
        s.position,
        COUNT(b.id) as total_bookings,
        SUM(p.amount) as revenue_generated
    FROM staff s
    JOIN bookings b ON s.id = b.staff_id
    JOIN payments p ON b.id = p.booking_id
    WHERE s.status = 'ACTIVE' AND b.status = 'CANCELLED'
    GROUP BY s.id, s.first_name, s.last_name, s.position
    ORDER BY revenue_generated DESC
        """)
        return cursor.fetchall()
    except oracledb.Error as e:
        (error,) = e.args
        print(f"Error executing query: {error.message}")
        raise
    finally:
        cursor.close()

def generate_q1_dml(connection: oracledb.Connection):
    """
    Generate DML queries to add rows that satisfy q1() query.
    q1() returns rooms with ONGOING bookings, so we need:
    - A guest
    - An ONGOING booking for that guest
    - A room linked to that booking
    - A matching room_type record (if not exists)
    - A payment for that booking
    
    Args:
        connection: Oracle database connection
        
    Returns:
        List of SQL INSERT statements as strings
    """
    cursor = connection.cursor()
    try:
        # Check if room_types exist, if not create them
        cursor.execute("SELECT COUNT(*) FROM room_types WHERE room_type = 'REGULAR'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO room_types (room_type, room_price) VALUES ('REGULAR', 120.00)")
        
        cursor.execute("SELECT COUNT(*) FROM room_types WHERE room_type = 'SUITE'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO room_types (room_type, room_price) VALUES ('SUITE', 250.00)")
        
        # Get next available IDs
        cursor.execute("SELECT NVL(MAX(id), 0) + 1 FROM guests")
        guest_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT NVL(MAX(id), 0) + 1 FROM bookings")
        booking_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT NVL(MAX(id), 0) + 1 FROM rooms")
        room_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT NVL(MAX(id), 0) + 1 FROM payments")
        payment_id = cursor.fetchone()[0]
        
        # Get an available staff member for the booking
        cursor.execute("SELECT id FROM staff WHERE status = 'ACTIVE' AND ROWNUM = 1")
        staff_result = cursor.fetchone()
        if not staff_result:
            raise ValueError("No active staff members found. Please add staff first.")
        staff_id = staff_result[0]
        
        # Generate DML queries
        dml_queries = []
        
        # 1. Insert guest
        guest_query = f"""INSERT INTO guests (id, email, phone_num, first_name, last_name) 
VALUES ({guest_id}, 'guest{guest_id}@example.com', '555-{1000 + guest_id}', 'Guest{guest_id}First', 'Guest{guest_id}Last')"""
        dml_queries.append(guest_query)
        
        # 2. Insert ONGOING booking
        booking_query = f"""INSERT INTO bookings (id, check_in_date, check_out_date, status, guest_id, staff_id) 
VALUES ({booking_id}, DATE '2025-10-01', NULL, 'ONGOING', {guest_id}, {staff_id})"""
        dml_queries.append(booking_query)
        
        # 3. Insert room linked to booking (using REGULAR room type)
        room_query = f"""INSERT INTO rooms (id, floor_num, room_type, booking_id) 
VALUES ({room_id}, 1, 'REGULAR', {booking_id})"""
        dml_queries.append(room_query)
        
        # 4. Insert payment for the booking
        payment_query = f"""INSERT INTO payments (id, booking_id, amount, payment_date, payment_method) 
VALUES ({payment_id}, {booking_id}, 500.00, DATE '2025-10-01', 'CREDIT')"""
        dml_queries.append(payment_query)
        
        return dml_queries
        
    except oracledb.Error as e:
        (error,) = e.args
        print(f"Error generating DML queries: {error.message}")
        raise
    finally:
        cursor.close()

def execute_q1_dml(connection: oracledb.Connection):
    """
    Execute DML queries to add rows that satisfy q1() query.
    This will add a complete set of records (guest, booking, room, payment)
    that will appear in q1() results.
    
    Args:
        connection: Oracle database connection
    """
    cursor = connection.cursor()
    try:
        # Ensure room_types exist
        cursor.execute("SELECT COUNT(*) FROM room_types WHERE room_type = 'REGULAR'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO room_types (room_type, room_price) VALUES ('REGULAR', 120.00)")
        
        cursor.execute("SELECT COUNT(*) FROM room_types WHERE room_type = 'SUITE'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO room_types (room_type, room_price) VALUES ('SUITE', 250.00)")
        
        # Get next available IDs
        cursor.execute("SELECT NVL(MAX(id), 0) + 1 FROM guests")
        guest_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT NVL(MAX(id), 0) + 1 FROM bookings")
        booking_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT NVL(MAX(id), 0) + 1 FROM rooms")
        room_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT NVL(MAX(id), 0) + 1 FROM payments")
        payment_id = cursor.fetchone()[0]
        
        # Get an available staff member
        cursor.execute("SELECT id FROM staff WHERE status = 'ACTIVE' AND ROWNUM = 1")
        staff_result = cursor.fetchone()
        if not staff_result:
            raise ValueError("No active staff members found. Please add staff first.")
        staff_id = staff_result[0]
        
        # Execute DML queries
        cursor.execute(f"""INSERT INTO guests (id, email, phone_num, first_name, last_name) 
VALUES ({guest_id}, 'guest{guest_id}@example.com', '555-{1000 + guest_id}', 'Guest{guest_id}First', 'Guest{guest_id}Last')""")
        
        cursor.execute(f"""INSERT INTO bookings (id, check_in_date, check_out_date, status, guest_id, staff_id) 
VALUES ({booking_id}, DATE '2025-10-01', NULL, 'ONGOING', {guest_id}, {staff_id})""")
        
        cursor.execute(f"""INSERT INTO rooms (id, floor_num, room_type, booking_id) 
VALUES ({room_id}, 1, 'REGULAR', {booking_id})""")
        
        cursor.execute(f"""INSERT INTO payments (id, booking_id, amount, payment_date, payment_method) 
VALUES ({payment_id}, {booking_id}, 500.00, DATE '2025-10-01', 'CREDIT')""")
        
        connection.commit()
        print(f"Successfully added data for q1(): guest_id={guest_id}, booking_id={booking_id}, room_id={room_id}, payment_id={payment_id}")
        
    except oracledb.Error as e:
        connection.rollback()
        (error,) = e.args
        print(f"Error executing DML queries: {error.message}")
        raise
    finally:
        cursor.close()