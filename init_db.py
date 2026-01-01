import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_suffix('.db')


def init_db(db_path=DB_PATH):
    if db_path.exists():
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Create tables
    cur.executescript('''
    CREATE TABLE hospitals (
        hospital_id TEXT PRIMARY KEY,
        hospital_name TEXT,
        location TEXT
    );

    CREATE TABLE inventory (
        hospital_id TEXT,
        medicine_name TEXT,
        stock_available INTEGER,
        daily_usage INTEGER,
        lead_time_days INTEGER
    );

    CREATE TABLE billing (
        hospital_id TEXT,
        medicine_name TEXT,
        quantity_sold INTEGER,
        bill_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE goods_requests (
        request_id INTEGER PRIMARY KEY AUTOINCREMENT,
        hospital_id TEXT,
        medicine_name TEXT,
        requested_quantity INTEGER,
        request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'PENDING'
    );
    ''')

    # Insert hospitals
    hospitals = [
        ('H1','City Hospital','Delhi'),
        ('H2','Green Life Hospital','Noida'),
        ('H3','Care Plus Hospital','Ghaziabad'),
        ('N1','Health NGO Trust','Delhi'),
        ('N2','Helping Hands NGO','Noida'),
    ]
    cur.executemany('INSERT INTO hospitals VALUES (?,?,?)', hospitals)

    # Insert inventory (mirrors setup file)
    inventory_rows = [
        ('H1','Paracetamol',120,30,3),
        ('H1','Insulin',50,10,7),
        ('H1','Amoxicillin',80,20,3),
        ('H1','ORS Sachet',100,25,3),
        ('H1','Cough Syrup',60,15,3),

        ('H2','Paracetamol',60,20,3),
        ('H2','Oxygen Cylinder',15,5,5),
        ('H2','Insulin',40,8,7),
        ('H2','IV Fluids',70,14,3),
        ('H2','ORS Sachet',90,18,3),

        ('H3','Paracetamol',200,25,3),
        ('H3','Antibiotic Injection',30,6,3),
        ('H3','Insulin',45,9,7),
        ('H3','IV Fluids',60,12,3),
        ('H3','Cough Syrup',55,11,3),

        ('N1','Paracetamol',40,15,3),
        ('N1','ORS Sachet',120,30,3),
        ('N1','Amoxicillin',50,10,3),
        ('N1','IV Fluids',40,8,3),
        ('N1','Cough Syrup',35,7,3),

        ('N2','Insulin',20,8,7),
        ('N2','ORS Sachet',60,20,3),
        ('N2','Oxygen Cylinder',10,3,5),
        ('N2','Amoxicillin',30,6,3),
        ('N2','Paracetamol',50,12,3),
    ]
    cur.executemany('INSERT INTO inventory VALUES (?,?,?,?,?)', inventory_rows)

    conn.commit()

    # Create views using SQLite-compatible SQL
    cur.executescript('''
    DROP VIEW IF EXISTS inventory_status;
    CREATE VIEW inventory_status AS
    SELECT
        hospital_id,
        medicine_name,
        stock_available,
        daily_usage,
        lead_time_days,
        CAST((stock_available / CAST(daily_usage AS FLOAT)) AS INTEGER) AS days_left,
        CASE
            WHEN (stock_available / CAST(daily_usage AS FLOAT)) > 7 THEN 'GREEN'
            WHEN (stock_available / CAST(daily_usage AS FLOAT)) BETWEEN 3 AND 7 THEN 'YELLOW'
            ELSE 'RED'
        END AS stock_status
    FROM inventory;

    DROP VIEW IF EXISTS reorder_recommendations;
    CREATE VIEW reorder_recommendations AS
    SELECT
        hospital_id,
        medicine_name,
        stock_available,
        daily_usage,
        lead_time_days,
        CAST((stock_available / CAST(daily_usage AS FLOAT)) AS INTEGER) AS days_left,
        CASE WHEN ((daily_usage * lead_time_days) - stock_available) > 0 THEN ((daily_usage * lead_time_days) - stock_available) ELSE 0 END AS recommended_reorder_qty,
        CASE
            WHEN (stock_available / CAST(daily_usage AS FLOAT)) <= lead_time_days THEN 'HIGH'
            WHEN (stock_available / CAST(daily_usage AS FLOAT)) <= (lead_time_days + 3) THEN 'MEDIUM'
            ELSE 'LOW'
        END AS priority
    FROM inventory;
    ''')

    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
    print(f"Initialized DB at {DB_PATH}")
