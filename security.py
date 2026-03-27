import os

try:
    # Most common library for SQLCipher with Python 3
    from pysqlcipher3 import dbapi2 as sqlite3
except ImportError:
    # A standard SQLite import fallback for development systems without SQLCipher compiled.
    import sqlite3  

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

DB_PATH = 'attendance_payroll.db'
ADMIN_HASH = None  

ph = PasswordHasher()

def _initialize_admin_hash():
    """Helper to ensure an admin hash exists for demo/first-run purposes."""
    global ADMIN_HASH
    # In a real app, this hash would be read from a secure config file.
    # The default password for this MVP is 'admin'
    ADMIN_HASH = ph.hash("admin")

def init_db(password: str):
    """
    Initializes the database, sets the encryption key and creates tables if they don't exist.
    """
    conn = sqlite3.connect(DB_PATH)
    
    # Apply SQLCipher encryption key
    # Ensure there is no whitespace after PRAGMA key!
    conn.execute(f"PRAGMA key = '{password}';")
    
    # Verify if encryption works / DB is valid by making an access
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, base_salary REAL NOT NULL, designation TEXT, vehicle_number TEXT, vehicle_type TEXT, license_number TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id INTEGER NOT NULL, date TEXT NOT NULL, status TEXT NOT NULL, FOREIGN KEY(employee_id) REFERENCES employees(id))")
        
        # Add columns to existing DB if upgrading from older version
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(employees)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'designation' not in columns:
            conn.execute("ALTER TABLE employees ADD COLUMN designation TEXT DEFAULT ''")
        if 'vehicle_number' not in columns:
            conn.execute("ALTER TABLE employees ADD COLUMN vehicle_number TEXT DEFAULT ''")
        if 'vehicle_type' not in columns:
            conn.execute("ALTER TABLE employees ADD COLUMN vehicle_type TEXT DEFAULT ''")
        if 'license_number' not in columns:
            conn.execute("ALTER TABLE employees ADD COLUMN license_number TEXT DEFAULT ''")
            
        conn.commit()
    except sqlite3.DatabaseError:
        conn.close()
        raise ValueError("Invalid database payload or incorrect password.")
    
    return conn

def verify_and_unlock(password: str):
    """
    Verifies the admin password using Argon2.
    If successful, unlocks the SQLCipher DB and returns the connection.
    """
    if ADMIN_HASH is None:
        _initialize_admin_hash()
        
    try:
        # Verify password matches the stored admin hash
        ph.verify(ADMIN_HASH, password)
        # If valid, unlock DB and return connection
        return init_db(password)
    except VerifyMismatchError:
        return None
