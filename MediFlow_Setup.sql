-- ===============================
-- MEDIFLOW CLEAN SETUP (RUN ONCE)
-- ===============================

USE DATABASE SNOWFLAKE_LEARNING_DB;

CREATE SCHEMA IF NOT EXISTS INVENTORY_SCHEMA;
USE SCHEMA INVENTORY_SCHEMA;

-- ===============================
-- HOSPITALS
-- ===============================
CREATE OR REPLACE TABLE hospitals (
    hospital_id STRING,
    hospital_name STRING,
    location STRING
);

INSERT INTO hospitals VALUES
('H1','City Hospital','Delhi'),
('H2','Green Life Hospital','Noida'),
('H3','Care Plus Hospital','Ghaziabad'),
('N1','Health NGO Trust','Delhi'),
('N2','Helping Hands NGO','Noida');

-- ===============================
-- INVENTORY
-- ===============================
CREATE OR REPLACE TABLE inventory (
    hospital_id STRING,
    medicine_name STRING,
    stock_available INTEGER,
    daily_usage INTEGER,
    lead_time_days INTEGER
);

INSERT INTO inventory VALUES
-- H1
('H1','Paracetamol',120,30,3),
('H1','Insulin',50,10,7),
('H1','Amoxicillin',80,20,3),
('H1','ORS Sachet',100,25,3),
('H1','Cough Syrup',60,15,3),

-- H2
('H2','Paracetamol',60,20,3),
('H2','Oxygen Cylinder',15,5,5),
('H2','Insulin',40,8,7),
('H2','IV Fluids',70,14,3),
('H2','ORS Sachet',90,18,3),

-- H3
('H3','Paracetamol',200,25,3),
('H3','Antibiotic Injection',30,6,3),
('H3','Insulin',45,9,7),
('H3','IV Fluids',60,12,3),
('H3','Cough Syrup',55,11,3),

-- N1
('N1','Paracetamol',40,15,3),
('N1','ORS Sachet',120,30,3),
('N1','Amoxicillin',50,10,3),
('N1','IV Fluids',40,8,3),
('N1','Cough Syrup',35,7,3),

-- N2
('N2','Insulin',20,8,7),
('N2','ORS Sachet',60,20,3),
('N2','Oxygen Cylinder',10,3,5),
('N2','Amoxicillin',30,6,3),
('N2','Paracetamol',50,12,3);

-- ===============================
-- BILLING
-- ===============================
CREATE OR REPLACE TABLE billing (
    hospital_id STRING,
    medicine_name STRING,
    quantity_sold INTEGER,
    bill_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- GOODS REQUESTS
-- ===============================
CREATE OR REPLACE TABLE goods_requests (
    request_id INTEGER AUTOINCREMENT,
    hospital_id STRING,
    medicine_name STRING,
    requested_quantity INTEGER,
    request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status STRING DEFAULT 'PENDING'
);

-- ===============================
-- INVENTORY STATUS VIEW
-- ===============================
CREATE OR REPLACE VIEW inventory_status AS
SELECT
    hospital_id,
    medicine_name,
    stock_available,
    daily_usage,
    lead_time_days,
    CAST(stock_available / daily_usage AS INTEGER) AS days_left,
    CASE
        WHEN stock_available / daily_usage > 7 THEN 'GREEN'
        WHEN stock_available / daily_usage BETWEEN 3 AND 7 THEN 'YELLOW'
        ELSE 'RED'
    END AS stock_status
FROM inventory;

-- ===============================
-- REORDER RECOMMENDATIONS
-- ===============================
CREATE OR REPLACE VIEW reorder_recommendations AS
SELECT
    hospital_id,
    medicine_name,
    stock_available,
    daily_usage,
    lead_time_days,
    CAST(stock_available / daily_usage AS INTEGER) AS days_left,
    GREATEST((daily_usage * lead_time_days) - stock_available,0) AS recommended_reorder_qty,
    CASE
        WHEN stock_available / daily_usage <= lead_time_days THEN 'HIGH'
        WHEN stock_available / daily_usage <= lead_time_days + 3 THEN 'MEDIUM'
        ELSE 'LOW'
    END AS priority
FROM inventory;
-- ===============================
-- RE-INSERT INVENTORY DATA
-- ===============================

INSERT INTO inventory VALUES
-- H1
('H1','Paracetamol',120,30,3),
('H1','Insulin',50,10,7),
('H1','Amoxicillin',80,20,3),
('H1','ORS Sachet',100,25,3),
('H1','Cough Syrup',60,15,3),

-- H2
('H2','Paracetamol',60,20,3),
('H2','Oxygen Cylinder',15,5,5),
('H2','Insulin',40,8,7),
('H2','IV Fluids',70,14,3),
('H2','ORS Sachet',90,18,3),

-- H3
('H3','Paracetamol',200,25,3),
('H3','Antibiotic Injection',30,6,3),
('H3','Insulin',45,9,7),
('H3','IV Fluids',60,12,3),
('H3','Cough Syrup',55,11,3),

-- N1
('N1','Paracetamol',40,15,3),
('N1','ORS Sachet',120,30,3),
('N1','Amoxicillin',50,10,3),
('N1','IV Fluids',40,8,3),
('N1','Cough Syrup',35,7,3),

-- N2
('N2','Insulin',20,8,7),
('N2','ORS Sachet',60,20,3),
('N2','Oxygen Cylinder',10,3,5),
('N2','Amoxicillin',30,6,3),
('N2','Paracetamol',50,12,3);

SELECT hospital_id, COUNT(*) 
FROM inventory 
GROUP BY hospital_id 
ORDER BY hospital_id;
SELECT * FROM inventory_status;
