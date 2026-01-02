import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / "mediflow.db"

def init_db(db_path):
    """Initialize the SQLite database with required tables and seed demo data."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create hospitals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hospitals (
            hospital_id TEXT PRIMARY KEY,
            hospital_name TEXT NOT NULL,
            location TEXT
        )
    ''')

    # Create inventory table - with daily_usage and lead_time_days columns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            hospital_id TEXT NOT NULL,
            medicine_name TEXT NOT NULL,
            stock_available INTEGER,
            daily_usage INTEGER,
            lead_time_days INTEGER,
            PRIMARY KEY (hospital_id, medicine_name),
            FOREIGN KEY(hospital_id) REFERENCES hospitals(hospital_id)
        )
    ''')

    # Create billing table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS billing (
            hospital_id TEXT NOT NULL,
            medicine_name TEXT NOT NULL,
            quantity_sold INTEGER,
            bill_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(hospital_id) REFERENCES hospitals(hospital_id)
        )
    ''')

    # Create goods_requests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goods_requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_id TEXT NOT NULL,
            medicine_name TEXT NOT NULL,
            requested_quantity INTEGER,
            request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'PENDING',
            FOREIGN KEY(hospital_id) REFERENCES hospitals(hospital_id)
        )
    ''')

    conn.commit()
    conn.close()

    # Auto-seed database with demo data if not already populated
    try:
        from seed_db import seed_database
        seed_database()
    except Exception as e:
        print(f"[INIT] Warning: Could not auto-seed database: {e}")

if __name__ == "__main__":
    init_db(DB_PATH)
    print(f"Database initialized at {DB_PATH}")
