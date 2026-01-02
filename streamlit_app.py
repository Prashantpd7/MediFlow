import sys
import os
from pathlib import Path

# Ensure the repository/app directory and current working directory are on sys.path
# so local modules like `init_db.py` can be imported on Streamlit Community Cloud.
try:
    ROOT_DIR = Path(__file__).resolve().parent
except NameError:
    # When __file__ is not available, fall back to the current working directory
    ROOT_DIR = Path(os.getcwd()).resolve()

# Insert at the front so these paths take precedence over other entries
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

cwd = Path.cwd().resolve()
if str(cwd) not in sys.path:
    sys.path.insert(0, str(cwd))

import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
import importlib.util


def get_active_session():
    # Lazy import of init_db to ensure ROOT_DIR and sys.path are set up first
    global init_db, DB_PATH
    
    # Import `init_db` from the local file. On some hosting environments
    # (Streamlit Community Cloud) the normal import may fail due to import
    # path / package semantics; if so, fall back to loading the module
    # directly from the repository file path.
    try:
        from init_db import init_db as init_db_func, DB_PATH as db_path
        init_db = init_db_func
        DB_PATH = db_path
        print(f"[DEBUG] Successfully imported init_db using standard import")
    except Exception as e:
        print(f"[DEBUG] Standard import failed: {type(e).__name__}: {e}")
        print(f"[DEBUG] ROOT_DIR = {ROOT_DIR}")
        print(f"[DEBUG] sys.path = {sys.path}")
        init_db_path = Path(ROOT_DIR) / "init_db.py"
        print(f"[DEBUG] Attempting fallback import from: {init_db_path}")
        print(f"[DEBUG] File exists? {init_db_path.exists()}")
        try:
            spec = importlib.util.spec_from_file_location("init_db", str(init_db_path))
            print(f"[DEBUG] spec = {spec}")
            init_db_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(init_db_mod)
            init_db = getattr(init_db_mod, "init_db")
            DB_PATH = getattr(init_db_mod, "DB_PATH", str(Path(ROOT_DIR) / "mediflow.db"))
            print(f"[DEBUG] Fallback import successful. DB_PATH = {DB_PATH}")
        except Exception as e2:
            print(f"[DEBUG] Fallback import also failed: {type(e2).__name__}: {e2}")
            raise
    
    # Ensure DB exists
    init_db(DB_PATH)
    
    # Auto-seed database if it's empty (inline to avoid import issues)
    conn_seed = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor_seed = conn_seed.cursor()
    try:
        cursor_seed.execute("SELECT COUNT(*) FROM hospitals")
        count = cursor_seed.fetchone()[0]
        
        if count == 0:
            print("[DEBUG] Hospitals table empty. Seeding with sample data...")
            
            # Seed hospitals
            hospitals = [
                ('H1', 'City Hospital', 'Delhi'),
                ('H2', 'Green Life Hospital', 'Noida'),
                ('H3', 'Care Plus Hospital', 'Ghaziabad'),
                ('N1', 'Health NGO Trust', 'Delhi'),
                ('N2', 'Helping Hands NGO', 'Noida'),
            ]
            cursor_seed.executemany('''
                INSERT INTO hospitals (hospital_id, hospital_name, location)
                VALUES (?, ?, ?)
            ''', hospitals)
            
            # Seed inventory
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
            cursor_seed.executemany('''
                INSERT INTO inventory (hospital_id, medicine_name, stock_available, daily_usage, lead_time_days)
                VALUES (?, ?, ?, ?, ?)
            ''', inventory_data)
            
            conn_seed.commit()
            print("[DEBUG] Database seeded successfully!")
    except Exception as e:
        print(f"[DEBUG] Seed error: {e}")
    finally:
        conn_seed.close()
    
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)

    class Result:
        def __init__(self, df=None):
            self._df = df if df is not None else pd.DataFrame()

        def to_pandas(self):
            # normalize columns to upper-case to match app expectations
            df = self._df.copy()
            df.columns = [c.upper() for c in df.columns]
            return df

        def collect(self):
            return self

    class SQLiteSession:
        def __init__(self, conn):
            self.conn = conn
            self._create_views()

        def _create_views(self):
            """Create computed views based on inventory data."""
            try:
                cur = self.conn.cursor()
                # Drop existing views if they exist
                cur.execute('DROP VIEW IF EXISTS inventory_status')
                cur.execute('DROP VIEW IF EXISTS reorder_recommendations')
                
                # Create inventory_status view
                cur.execute('''
                    CREATE VIEW inventory_status AS
                    SELECT
                        hospital_id,
                        medicine_name,
                        stock_available,
                        daily_usage,
                        lead_time_days,
                        CAST(stock_available / CASE WHEN daily_usage = 0 THEN 1 ELSE daily_usage END AS INTEGER) AS days_left,
                        CASE
                            WHEN CAST(stock_available / CASE WHEN daily_usage = 0 THEN 1 ELSE daily_usage END AS INTEGER) > 7 THEN 'GREEN'
                            WHEN CAST(stock_available / CASE WHEN daily_usage = 0 THEN 1 ELSE daily_usage END AS INTEGER) BETWEEN 3 AND 7 THEN 'YELLOW'
                            ELSE 'RED'
                        END AS stock_status
                    FROM inventory
                ''')
                
                # Create reorder_recommendations view
                cur.execute('''
                    CREATE VIEW reorder_recommendations AS
                    SELECT
                        hospital_id,
                        medicine_name,
                        stock_available,
                        daily_usage,
                        lead_time_days,
                        CAST(stock_available / CASE WHEN daily_usage = 0 THEN 1 ELSE daily_usage END AS INTEGER) AS days_left,
                        GREATEST((daily_usage * lead_time_days) - stock_available, 0) AS recommended_reorder_qty,
                        CASE
                            WHEN CAST(stock_available / CASE WHEN daily_usage = 0 THEN 1 ELSE daily_usage END AS INTEGER) <= lead_time_days THEN 'HIGH'
                            WHEN CAST(stock_available / CASE WHEN daily_usage = 0 THEN 1 ELSE daily_usage END AS INTEGER) <= lead_time_days + 3 THEN 'MEDIUM'
                            ELSE 'LOW'
                        END AS priority
                    FROM inventory
                ''')
                self.conn.commit()
            except Exception as e:
                print(f"Error creating views: {e}")

        def sql(self, query):
            q = query
            # adapt Snowflake ::INT cast to SQLite CAST(... AS INTEGER)
            q = q.replace('::INT', '')
            q = q.replace('AVG(days_left)::INT', 'CAST(AVG(days_left) AS INTEGER)')

            try:
                if q.strip().lower().startswith('select'):
                    df = pd.read_sql_query(q, self.conn)
                    return Result(df)
                else:
                    cur = self.conn.cursor()
                    cur.executescript(q)
                    self.conn.commit()
                    return Result(pd.DataFrame())
            except Exception:
                # On error, return empty result to avoid crashing the UI
                return Result(pd.DataFrame())

    return SQLiteSession(conn)

# PAGE CONFIG
st.set_page_config(
    page_title="MediFlow",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
st.markdown("""
<style>
[data-testid="stHeader"] {background: transparent !important; height: 0px !important;}
header {background: transparent !important;}
.block-container {padding-top: 1rem !important;}

.stApp {background: linear-gradient(180deg, #1f3a4d, #2b5876);}
[data-testid="stSidebar"] {background: linear-gradient(180deg, #0f2027, #203a43);}

h1,h2,h3,h4,h5,p,label,span {color: white !important;}

.kpi {border-radius:22px; padding:28px; text-align:center; font-weight:600;}
.kpi h2 {font-size:42px; margin-top:8px;}
.blue {background:#22d3ee;}
.red {background:#fb7185;}
.green {background:#34d399;}

.stButton>button {
    width:100%; height:46px;
    background:linear-gradient(135deg,#20c997,#17a2b8);
    color:white; border-radius:14px; font-weight:600;
}

[data-testid="stDownloadButton"] button {
    background:rgba(255,255,255,0.18)!important;
    border:1px solid rgba(255,255,255,0.45)!important;
    color:white!important;
}

thead tr th {background:#203a43 !important; color:white !important;}
tbody tr td {background:#f8fafc !important; color:#0f172a !important;}
</style>
""", unsafe_allow_html=True)

# SESSION STATE
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "role" not in st.session_state:
    st.session_state.role = "Hospital"
if "hospital_id" not in st.session_state:
    st.session_state.hospital_id = None

# SIDEBAR
with st.sidebar:
    st.markdown("## 🏥 MediFlow")

    st.session_state.role = st.selectbox(
        "Switch Role",
        ["Hospital", "Distribution Center"]
    )

    if st.button("🏠 Dashboard"):
        st.session_state.page = "Dashboard"
        st.rerun()

    if st.button("📦 Inventory"):
        st.session_state.page = "Inventory"
        st.rerun()

    if st.button("📩 Requests"):
        st.session_state.page = "Requests"
        st.rerun()

    if st.session_state.role == "Distribution Center":
        if st.button("📊 Reorder"):
            st.session_state.page = "Reorder"
            st.rerun()

# SNOWFLAKE SESSION
session = get_active_session()

# DASHBOARD
if st.session_state.page == "Dashboard":

    st.markdown("## 📊 System Dashboard")

    hospitals_df = session.sql(
        "SELECT hospital_id FROM hospitals"
    ).to_pandas()

    # KPIs
    if st.session_state.role == "Hospital":
        st.session_state.hospital_id = st.selectbox(
            "Hospital ID",
            hospitals_df["HOSPITAL_ID"]
        )
        hid = st.session_state.hospital_id

        metrics = session.sql(f"""
            SELECT
                COUNT(*) medicines,
                SUM(CASE WHEN stock_status='RED' THEN 1 ELSE 0 END) critical,
                AVG(days_left)::INT avg_days
            FROM inventory_status
            WHERE hospital_id='{hid}'
        """).to_pandas().iloc[0]
    else:
        metrics = session.sql("""
            SELECT
                COUNT(DISTINCT medicine_name) medicines,
                SUM(CASE WHEN stock_status='RED' THEN 1 ELSE 0 END) critical,
                AVG(days_left)::INT avg_days
            FROM inventory_status
        """).to_pandas().iloc[0]

    c1, c2, c3 = st.columns(3)
    try:
        med_val = int(metrics['MEDICINES'])
    except Exception:
        med_val = 0
    try:
        crit_val = int(metrics['CRITICAL'])
    except Exception:
        crit_val = 0
    try:
        avg_val = int(metrics['AVG_DAYS'])
    except Exception:
        avg_val = 0

    c1.markdown(f"<div class='kpi blue'>Medicines<h2>{med_val}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi red'>Critical<h2>{crit_val}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi green'>Avg Days<h2>{avg_val}</h2></div>", unsafe_allow_html=True)

    # HOSPITAL
    if st.session_state.role == "Hospital":

        st.divider()
        st.markdown("## 🧾 Issue Medicine")

        meds_df = session.sql(
            f"SELECT medicine_name FROM inventory WHERE hospital_id='{hid}'"
        ).to_pandas()

        med = st.selectbox("Medicine", meds_df["MEDICINE_NAME"])
        qty = st.number_input("Quantity", min_value=1)

        if st.button("Generate Bill"):
            session.sql(f"""
                INSERT INTO billing (hospital_id, medicine_name, quantity_sold)
                VALUES ('{hid}','{med}',{qty})
            """).collect()

            session.sql(f"""
                UPDATE inventory
                SET stock_available = stock_available - {qty}
                WHERE hospital_id='{hid}' AND medicine_name='{med}'
            """).collect()

            st.success("Bill generated")

    #  DISTRIBUTION CENTER
    if st.session_state.role == "Distribution Center":

        # HEATMAP
        st.divider()
        st.markdown("## 🌍 Inventory Heatmap")

        heat_df = session.sql("""
            SELECT hospital_id, medicine_name, stock_status
            FROM inventory_status
        """).to_pandas()

        pivot_df = heat_df.pivot(
            index="HOSPITAL_ID",
            columns="MEDICINE_NAME",
            values="STOCK_STATUS"
        )

        def color(val):
            if val == "RED": return "background-color:#fecaca;color:black"
            if val == "YELLOW": return "background-color:#fef08a;color:black"
            if val == "GREEN": return "background-color:#bbf7d0;color:black"
            return ""

        st.dataframe(pivot_df.style.applymap(color), use_container_width=True)

        # RESTOCK
        st.divider()
        st.markdown("## 🚚 Restock Inventory")

        restock_hid = st.selectbox("Hospital", hospitals_df["HOSPITAL_ID"])

        meds_df = session.sql(
            f"SELECT medicine_name FROM inventory WHERE hospital_id='{restock_hid}'"
        ).to_pandas()

        restock_med = st.selectbox("Medicine", meds_df["MEDICINE_NAME"])
        restock_qty = st.number_input("Quantity", min_value=1)

        if st.button("🚛 Restock Inventory"):
            session.sql(f"""
                UPDATE inventory
                SET stock_available = stock_available + {restock_qty}
                WHERE hospital_id='{restock_hid}'
                AND medicine_name='{restock_med}'
            """).collect()
            st.success("Inventory restocked")

        # EXPORT
        st.divider()
        st.markdown("## 📤 Export Data")

        critical_df = session.sql(
            "SELECT * FROM inventory_status WHERE stock_status='RED'"
        ).to_pandas()

        reorder_df = session.sql(
            "SELECT * FROM reorder_recommendations"
        ).to_pandas()

        heat_export_df = session.sql("""
            SELECT hospital_id, medicine_name, stock_status
            FROM inventory_status
        """).to_pandas()

        st.download_button(
            "⬇️ Download Critical Stock (CSV)",
            critical_df.to_csv(index=False),
            "critical_stock.csv"
        )

        st.download_button(
            "⬇️ Download Reorder Recommendations (CSV)",
            reorder_df.to_csv(index=False),
            "reorder_recommendations.csv"
        )

        st.download_button(
            "⬇️ Download Heatmap Data (CSV)",
            heat_export_df.to_csv(index=False),
            "inventory_heatmap.csv"
        )

# INVENTORY
if st.session_state.page == "Inventory":

    st.markdown("## 📦 Inventory Overview")

    if st.session_state.role == "Hospital":
        hid = st.session_state.hospital_id
        df = session.sql(
            f"SELECT * FROM inventory_status WHERE hospital_id='{hid}'"
        ).to_pandas()
    else:
        df = session.sql("SELECT * FROM inventory_status").to_pandas()

    st.dataframe(df, use_container_width=True)

# REQUESTS
if st.session_state.page == "Requests":

    st.markdown("## 📩 Requests")

    if st.session_state.role == "Hospital":

        hid = st.session_state.hospital_id
        meds_df = session.sql(
            f"SELECT medicine_name FROM inventory WHERE hospital_id='{hid}'"
        ).to_pandas()

        med = st.selectbox("Medicine", meds_df["MEDICINE_NAME"])
        qty = st.number_input("Quantity", min_value=1)

        if st.button("Send Request"):
            session.sql(f"""
                INSERT INTO goods_requests (hospital_id, medicine_name, requested_quantity)
                VALUES ('{hid}','{med}',{qty})
            """).collect()
            st.success("Request sent")

    else:
        reqs_df = session.sql(
            "SELECT * FROM goods_requests ORDER BY request_time DESC"
        ).to_pandas()

        for _, r in reqs_df.iterrows():
            st.markdown(
                f"""**Hospital:** {r['HOSPITAL_ID']}  
**Medicine:** {r['MEDICINE_NAME']}  
**Qty:** {r['REQUESTED_QUANTITY']}  
**Status:** {r['STATUS']}"""
            )

            if r["STATUS"] == "PENDING":
                c1, c2 = st.columns(2)

                with c1:
                    if st.button("✅ Approve", key=f"a{r['REQUEST_ID']}"):
                        session.sql(
                            f"UPDATE goods_requests SET status='APPROVED' WHERE request_id={r['REQUEST_ID']}"
                        ).collect()
                        st.rerun()

                with c2:
                    if st.button("❌ Reject", key=f"r{r['REQUEST_ID']}"):
                        session.sql(
                            f"UPDATE goods_requests SET status='REJECTED' WHERE request_id={r['REQUEST_ID']}"
                        ).collect()
                        st.rerun()

            st.divider()

# REORDER
if st.session_state.page == "Reorder" and st.session_state.role == "Distribution Center":

    st.markdown("## 📊 Reorder Insights")

    reorder_df = session.sql(
        "SELECT * FROM reorder_recommendations ORDER BY priority"
    ).to_pandas()

    st.dataframe(reorder_df, use_container_width=True)
