import sqlite3
from init_db import DB_PATH

def seed_database():
    """Add sample data from MediFlow_Setup.sql to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Clear existing data
    cursor.execute('DELETE FROM goods_requests')
    cursor.execute('DELETE FROM billing')
    cursor.execute('DELETE FROM inventory')
    cursor.execute('DELETE FROM hospitals')

    # Add hospitals data from MediFlow_Setup.sql
    hospitals = [
        ('H1', 'City Hospital', 'Delhi'),
        ('H2', 'Green Life Hospital', 'Noida'),
        ('H3', 'Care Plus Hospital', 'Ghaziabad'),
        ('N1', 'Health NGO Trust', 'Delhi'),
        ('N2', 'Helping Hands NGO', 'Noida'),
    ]
    
    cursor.executemany('''
        INSERT INTO hospitals (hospital_id, hospital_name, location)
        VALUES (?, ?, ?)
    ''', hospitals)

    # Add inventory data from MediFlow_Setup.sql
    inventory_data = [
        # H1
        ('H1', 'Paracetamol', 120, 30, 3),
        ('H1', 'Insulin', 50, 10, 7),
        ('H1', 'Amoxicillin', 80, 20, 3),
        ('H1', 'ORS Sachet', 100, 25, 3),
        ('H1', 'Cough Syrup', 60, 15, 3),
        # H2
        ('H2', 'Paracetamol', 60, 20, 3),
        ('H2', 'Oxygen Cylinder', 15, 5, 5),
        ('H2', 'Insulin', 40, 8, 7),
        ('H2', 'IV Fluids', 70, 14, 3),
        ('H2', 'ORS Sachet', 90, 18, 3),
        # H3
        ('H3', 'Paracetamol', 200, 25, 3),
        ('H3', 'Antibiotic Injection', 30, 6, 3),
        ('H3', 'Insulin', 45, 9, 7),
        ('H3', 'IV Fluids', 60, 12, 3),
        ('H3', 'Cough Syrup', 55, 11, 3),
        # N1
        ('N1', 'Paracetamol', 40, 15, 3),
        ('N1', 'ORS Sachet', 120, 30, 3),
        ('N1', 'Amoxicillin', 50, 10, 3),
        ('N1', 'IV Fluids', 40, 8, 3),
        ('N1', 'Cough Syrup', 35, 7, 3),
        # N2
        ('N2', 'Insulin', 20, 8, 7),
        ('N2', 'ORS Sachet', 60, 20, 3),
        ('N2', 'Oxygen Cylinder', 10, 3, 5),
        ('N2', 'Amoxicillin', 30, 6, 3),
        ('N2', 'Paracetamol', 50, 12, 3),
    ]
    
    cursor.executemany('''
        INSERT INTO inventory (hospital_id, medicine_name, stock_available, daily_usage, lead_time_days)
        VALUES (?, ?, ?, ?, ?)
    ''', inventory_data)

    conn.commit()
    conn.close()
    print("Database seeded with MediFlow data successfully!")

if __name__ == "__main__":
    seed_database()
