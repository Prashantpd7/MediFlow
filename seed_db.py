import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "mediflow.db"

def seed_db(db_path):
    """Add sample data to the specified SQLite database.

    This function accepts a path (Path or str) so callers can seed a
    database at any location (useful for Streamlit Cloud ephemeral FS).
    """
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Add hospitals data (INSERT OR IGNORE prevents duplicates on reruns)
    hospitals = [
        ('H1', 'City Hospital', 'Delhi'),
        ('H2', 'Green Life Hospital', 'Noida'),
        ('H3', 'Care Plus Hospital', 'Ghaziabad'),
        ('N1', 'Health NGO Trust', 'Delhi'),
        ('N2', 'Helping Hands NGO', 'Noida'),
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO hospitals (hospital_id, hospital_name, location)
        VALUES (?, ?, ?)
    ''', hospitals)

    # Add inventory data
    inventory_data = [
        ('H1', 'Paracetamol', 120, 30, 3),
        ('H1', 'Insulin', 50, 10, 7),
        ('H1', 'Amoxicillin', 80, 20, 3),
        ('H1', 'ORS Sachet', 100, 25, 3),
        ('H1', 'Cough Syrup', 60, 15, 3),
        ('H2', 'Paracetamol', 60, 20, 3),
        ('H2', 'Oxygen Cylinder', 15, 5, 5),
        ('H2', 'Insulin', 40, 8, 7),
        ('H2', 'IV Fluids', 70, 14, 3),
        ('H2', 'ORS Sachet', 90, 18, 3),
        ('H3', 'Paracetamol', 200, 25, 3),
        ('H3', 'Antibiotic Injection', 30, 6, 3),
        ('H3', 'Insulin', 45, 9, 7),
        ('H3', 'IV Fluids', 60, 12, 3),
        ('H3', 'Cough Syrup', 55, 11, 3),
        ('N1', 'Paracetamol', 40, 15, 3),
        ('N1', 'ORS Sachet', 120, 30, 3),
        ('N1', 'Amoxicillin', 50, 10, 3),
        ('N1', 'IV Fluids', 40, 8, 3),
        ('N1', 'Cough Syrup', 35, 7, 3),
        ('N2', 'Insulin', 20, 8, 7),
        ('N2', 'ORS Sachet', 60, 20, 3),
        ('N2', 'Oxygen Cylinder', 10, 3, 5),
        ('N2', 'Amoxicillin', 30, 6, 3),
        ('N2', 'Paracetamol', 50, 12, 3),
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO inventory (hospital_id, medicine_name, stock_available, daily_usage, lead_time_days)
        VALUES (?, ?, ?, ?, ?)
    ''', inventory_data)

    conn.commit()
    conn.close()
    print("[SEED] Database seeded with demo data successfully!")

# Backwards-compatible alias used by older code
def seed_database(db_path=DB_PATH):
    return seed_db(db_path)

if __name__ == "__main__":
    seed_db(DB_PATH)
