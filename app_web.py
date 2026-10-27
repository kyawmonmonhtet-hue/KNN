import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="ကျော်ညီနောင် ကားအပိုပစ္စည်းဆိုင် (POS System)",
    page_icon="🚗",
    layout="wide"
)

# --- Soft Pastel Custom CSS Styling ---
st.markdown("""
    <style>
    .stApp {
        background-color: #eef4f2;
    }
    div.stButton > button {
        border-radius: 20px;
        font-weight: bold;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)

# --- Database Setup ---
def create_db():
    conn = sqlite3.connect('autopart_web_system.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS spare_parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE NOT NULL,
            part_number TEXT NOT NULL,
            part_name TEXT NOT NULL,
            car_model TEXT,
            price REAL NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS store1_stock (
            part_id INTEGER PRIMARY KEY,
            stock INTEGER NOT NULL,
            FOREIGN KEY(part_id) REFERENCES spare_parts(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS store2_stock (
            part_id INTEGER PRIMARY KEY,
            stock INTEGER NOT NULL,
            FOREIGN KEY(part_id) REFERENCES spare_parts(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id INTEGER NOT NULL,
            barcode TEXT NOT NULL,
            part_name TEXT NOT NULL,
            price REAL NOT NULL,
            qty INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            sale_date TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS action_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id INTEGER NOT NULL,
            action_desc TEXT NOT NULL,
            action_time TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

create_db()

def log_action(store_id, desc):
    conn = sqlite3.connect('autopart_web_system.db')
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute("INSERT INTO action_logs (store_id, action_desc, action_time) VALUES (?, ?, ?)", (store_id, desc, timestamp))
    conn.commit()
    conn.close()

# --- Session State Management ---
if 'role' not in st.session_state:
    st.session_state.role = "Admin"
if 'store_id' not in st.session_state:
    st.session_state.store_id = 1
if 'current_view' not in st.session_state:
    st.session_state.current_view = "stock"

# --- Top Header Bar ---
col_head1, col_head2 = st.columns([2, 3])
with col_head1:
    role_text = "Admin Mode" if st.session_state.role == "Admin" else "Staff Mode"
    st.markdown(f"### 🚗 ကျော်ညီနောင် ကားအပိုပစ္စည်းဆိုင် ({role_text})")

with col_head2:
    h_col1, h_col2, h_col3 = st.columns(3)
    with h_col1:
        if st.session_state.role == "Admin":
            if st.button("👑 Admin (Staff သို့ပြောင်းရန်)", width='stretch'):
                st.session_state.role = "Staff"
                st.rerun()
        else:
            if st.button("👤 Staff (Admin သို့ပြောင်းရန်)", width='stretch'):
                # Admin သို့ပြောင်းရန် Password တောင်းခံခြင်း
                pwd = st.text_input("Admin Password ထည့်ပါ", type="password", key="admin_pwd_input")
                if pwd == "1234":
                    st.session_state.role = "Admin"
                    st.rerun()
                elif pwd:
                    st.error("Password မှားယွင်းနေပါသည်။")
    with h_col2:
        if st.button("🏪 ဆိုင် (၁)", width='stretch'):
            st.session_state.store_id = 1
            st.rerun()
    with h_col3:
        if st.button("🏪 ဆိုင် (၂)", width='stretch'):
            st.session_state.store_id = 2
            st.rerun()

store_label = "ဆိုင် (၁)" if st.session_state.store_id == 1 else "ဆိုင် (၂)"

# --- Main Layout: Left Sidebar (Forms) & Right Main Area (Search & Table) ---
main_left, main_right = st.columns([1, 2.2], gap="medium")

# --- LEFT COLUMN: Forms Container ---
with main_left:
    # 1. ပစ္စည်းအသစ်ထည့်ရန် (Admin သီးသန့် - Staff ဘက်တွင် လုံးဝ ဖျောက်ထားမည်)
    if st.session_state.role == "Admin":
        with st.container(border=True):
            st.markdown("📦 **ပစ္စည်းအသစ် ထည့်ရန် (Admin)**")
            with st.form("add_item_form"):
                new_barcode = st.text_input("Barcode", placeholder="Barcode")
                new_pnum = st.text_input("Part Number", placeholder="Part Number")
                new_pname = st.text_input("Part Name", placeholder="Part Name")
                new_cmodel = st.text_input("Car Model", placeholder="Car Model")
                new_price = st.text_input("ရောင်းဈေး (Price)", placeholder="ရောင်းဈေး (Price)")
                new_stock = st.text_input("Initial Stock", placeholder="Initial Stock")
                submit_add = st.form_submit_button("✨ ပစ္စည်းသိမ်းဆည်းမည်", width='stretch')

            if submit_add:
                if not new_barcode or not new_pnum or not new_pname or not new_price or not new_stock:
                    st.error("❌ အချက်အလက်များ အပြည့်အစုံ ဖြည့်ပါ။")
                else:
                    try:
                        conn = sqlite3.connect('autopart_web_system.db')
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO spare_parts (barcode, part_number, part_name, car_model, price) VALUES (?, ?, ?, ?, ?)",
                                       (new_barcode, new_pnum, new_pname, new_cmodel, float(new_price)))
                        p_id = cursor.lastrowid
                        cursor.execute("INSERT INTO store1_stock (part_id, stock) VALUES (?, ?)", (p_id, int(new_stock)))
                        cursor.execute("INSERT INTO store2_stock (part_id, stock) VALUES (?, ?)", (p_id, int(new_stock)))
                        conn.commit()
                        conn.close()

                        log_action(st.session_state.store_id, f"ပစ္စည်းအသစ်ထည့်သည်: {new_pname}")
                        st.success("✅ သိမ်းဆည်းပြီးပါပြီ။")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("❌ Barcode ရှိပြီးသားဖြစ်ပါသည်။")

    # 2. POS ငွေရှင်းရန် (Staff နှင့် Admin နှစ်ဦးစလုံး သုံးနိုင်သည်)
    with st.container(border=True):
        st.markdown(f"💳 **{store_label} - ငွေရှင်းရန်**")
        with st.form("pos_form"):
            sell_barcode = st.text_input("Barcode", placeholder="📷 Barcode စကင်ဖတ်ရန် (သို့ Enter)")
            sell_qty = st.text_input("Qty", placeholder="ရောင်းမည့် အရေအတွက် (Qty)")
            submit_sell = st.form_submit_button("🛍️ ရောင်းမည် & ဘေလ်ထုတ်မည်", width='stretch')

        if submit_sell and sell_barcode:
            conn = sqlite3.connect('autopart_web_system.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, part_name, price FROM spare_parts WHERE barcode = ?", (sell_barcode,))
            item = cursor.fetchone()

            if not item:
                st.error("❌ ပစ္စည်းမတွေ့ပါ။")
            else:
                p_id, p_name, p_price = item[0], item[1], item[2]
                qty = int(sell_qty) if sell_qty.isdigit() else 1
                table_name = "store1_stock" if st.session_state.store_id == 1 else "store2_stock"
                
                cursor.execute(f"SELECT stock FROM {table_name} WHERE part_id = ?", (p_id,))
                stock_res = cursor.fetchone()
                current_stock = stock_res[0] if stock_res else 0

                if qty > current_stock:
                    st.error(f"❌ စတော့မလုံလောက်ပါ။ (လက်ကျန်: {current_stock})")
                else:
                    new_stock = current_stock - qty
                    total_amt = p_price * qty
                    sale_time = datetime.now().strftime("%Y-%m-%d %H:%M")

                    cursor.execute(f"UPDATE {table_name} SET stock = ? WHERE part_id = ?", (new_stock, p_id))
                    cursor.execute('''
                        INSERT INTO sales_history (store_id, barcode, part_name, price, qty, total_amount, sale_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (st.session_state.store_id, sell_barcode, p_name, p_price, qty, total_amt, sale_time))
                    conn.commit()
                    conn.close()

                    log_action(st.session_state.store_id, f"ရောင်းချသည်: {p_name} ({qty} ခု)")
                    st.success(f"✅ အရောင်းအဝယ် အောင်မြင်သည်! ကျသင့်ငွေ: {total_amt:,.0f} ကျပ်")
                    st.balloons()

    # 3. စာရင်းစစ်ဆေးရေး & Admin Controls (Admin သီးသန့်)
    if st.session_state.role == "Admin":
        with st.container(border=True):
            st.markdown("🛡️ **စာရင်းစစ်ဆေးရေး & Admin**")
            if st.button("📈 နေ့ချုပ် ဝင်ငွေစာရင်း (Z-Report)", width='stretch'):
                today_str = datetime.now().strftime("%Y-%m-%d")
                conn = sqlite3.connect('autopart_web_system.db')
                cursor = conn.cursor()
                cursor.execute("SELECT SUM(total_amount), COUNT(id) FROM sales_history WHERE store_id = ? AND sale_date LIKE ?", (st.session_state.store_id, f"{today_str}%"))
                res = cursor.fetchone()
                conn.close()
                t_sales = res[0] if res and res[0] else 0.0
                t_count = res[1] if res and res[1] else 0
                st.info(f"ရက်စွဲ ({today_str}) ဝင်ငွေ: **{t_sales:,.0f} ကျပ်** (အကြိမ်ရေ: {t_count})")

            if st.button("🔄 အရောင်းပြန်အမ်းရန် (Void/Return)", width='stretch'):
                st.warning("အရောင်းမှတ်တမ်း ဇယားတွင် ပြန်အမ်းမှု ပြုလုပ်နိုင်ပါသည်။")

            if st.button("📋 လုပ်ဆောင်ချက် မှတ်တမ်း (Logs)", width='stretch'):
                st.session_state.current_view = "logs"
                st.rerun()

# --- RIGHT COLUMN: Search Bar & Interactive Table ---
with main_right:
    top_c1, top_c2, top_c3, top_c4 = st.columns([3, 1, 1, 1])
    with top_c1:
        search_query = st.text_input("🔍 ရှာရန်...", placeholder="Part Number သို့မဟုတ် Car Model ဖြင့် ရှာရန်...", label_visibility="collapsed")
    with top_c2:
        if st.button("ရှာမည်", width='stretch'):
            pass
    with top_c3:
        if st.button("📦 လက်ကျန်", width='stretch'):
            st.session_state.current_view = "stock"
            st.rerun()
    with top_c4:
        if st.button("📊 အရောင်း", width='stretch'):
            st.session_state.current_view = "sales"
            st.rerun()

    # Data Fetching based on current_view
    conn = sqlite3.connect('autopart_web_system.db')
    
    if st.session_state.current_view == "stock":
        if st.session_state.store_id == 1:
            df = pd.read_sql_query('''SELECT p.id AS ID, p.barcode AS Barcode, p.part_number AS "Part Number", p.part_name AS "Part Name", p.car_model AS "Car Model", p.price AS Price, s.stock AS "Stock Status" 
                                     FROM spare_parts p JOIN store1_stock s ON p.id = s.part_id''', conn)
        else:
            df = pd.read_sql_query('''SELECT p.id AS ID, p.barcode AS Barcode, p.part_number AS "Part Number", p.part_name AS "Part Name", p.car_model AS "Car Model", p.price AS Price, s.stock AS "Stock Status" 
                                     FROM spare_parts p JOIN store2_stock s ON p.id = s.part_id''', conn)
    elif st.session_state.current_view == "sales":
        df = pd.read_sql_query("SELECT id AS Trans_ID, barcode AS Barcode, part_name AS Part_Name, price AS Price, qty AS Qty, total_amount AS Total, sale_date AS Date_Time FROM sales_history WHERE store_id = ? ORDER BY id DESC", conn, params=(st.session_state.store_id,))
    else:
        df = pd.read_sql_query("SELECT id AS Log_ID, action_desc AS Description, action_time AS Time FROM action_logs WHERE store_id = ? ORDER BY id DESC", conn, params=(st.session_state.store_id,))
    
    conn.close()

    # Filtering dataframe if search_query is entered
    if search_query and not df.empty:
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
        df = df[mask]

    # Displaying Table
    with st.container(border=True):
        st.dataframe(df, width='stretch', height=550)
