import streamlit as st
import psycopg2
import psycopg2.extras
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import base64
import io
import os
import json

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="🕉️ Temple Management System",
    page_icon="🕉️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# TEMPLE CONFIGURATION
# ============================================================
TEMPLE_NAME = "Arulmigu Bhadreshwari Amman Kovil"
TEMPLE_TRUST = "Samrakshana Seva Trust"
TEMPLE_REG = "179/2004"
TEMPLE_PLACE = "Kanjampuram"
TEMPLE_DISTRICT = "Kanniyakumari Dist- 629154"
TEMPLE_ADDRESS_LINE1 = f"{TEMPLE_NAME}"
TEMPLE_ADDRESS_LINE2 = f"{TEMPLE_TRUST} - {TEMPLE_REG}"
TEMPLE_ADDRESS_LINE3 = f"{TEMPLE_PLACE}, {TEMPLE_DISTRICT}"
TEMPLE_FULL_ADDRESS = f"{TEMPLE_ADDRESS_LINE1}, {TEMPLE_ADDRESS_LINE2}, {TEMPLE_ADDRESS_LINE3}"

NATCHATHIRAM_LIST = [
    'அசுவினி (Ashwini)', 'பரணி (Bharani)', 'கார்த்திகை (Krittika)',
    'ரோகிணி (Rohini)', 'மிருகசீரிடம் (Mrigashira)', 'திருவாதிரை (Ardra)',
    'புனர்பூசம் (Punarvasu)', 'பூசம் (Pushya)', 'ஆயில்யம் (Ashlesha)',
    'மகம் (Magha)', 'பூரம் (Purva Phalguni)', 'உத்திரம் (Uttara Phalguni)',
    'ஹஸ்தம் (Hasta)', 'சித்திரை (Chitra)', 'சுவாதி (Swati)',
    '��ிசாகம் (Vishakha)', 'அனுஷம் (Anuradha)', 'கேட்டை (Jyeshtha)',
    'மூலம் (Mula)', 'பூராடம் (Purva Ashadha)', 'உத்திராடம் (Uttara Ashadha)',
    'திருவோணம் (Shravana)', 'அவிட்டம் (Dhanishta)', 'சதயம் (Shatabhisha)',
    'பூரட்டாதி (Purva Bhadrapada)', 'உத்திரட்டாதி (Uttara Bhadrapada)',
    'ரேவதி (Revati)'
]
RELATION_TYPES = [
    'Self', 'Spouse', 'Son', 'Daughter', 'Father', 'Mother', 'Brother', 'Sister',
    'Grandfather', 'Grandmother', 'Father-in-law', 'Mother-in-law',
    'Son-in-law', 'Daughter-in-law', 'Uncle', 'Aunt', 'Nephew', 'Niece', 'Cousin', 'Other'
]

# ============================================================
# AMMAN SVG PLACEHOLDER
# ============================================================
AMMAN_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">
<defs><radialGradient id="g1" cx="50%" cy="50%" r="50%">
<stop offset="0%" style="stop-color:#FFD700;stop-opacity:0.4"/>
<stop offset="100%" style="stop-color:#FF6600;stop-opacity:0"/>
</radialGradient></defs>
<circle cx="100" cy="100" r="98" fill="#FFF8DC" stroke="#FFD700" stroke-width="3"/>
<circle cx="100" cy="100" r="92" fill="url(#g1)" stroke="#8B0000" stroke-width="1.5"/>
<text x="100" y="65" text-anchor="middle" font-size="35">🙏</text>
<text x="100" y="95" text-anchor="middle" font-size="11" fill="#8B0000" font-weight="bold">ஸ்ரீ பத்ரேஸ்வரி</text>
<text x="100" y="112" text-anchor="middle" font-size="11" fill="#8B0000" font-weight="bold">அம்மன்</text>
<text x="100" y="135" text-anchor="middle" font-size="9" fill="#DC143C">Bhadreshwari</text>
<text x="100" y="148" text-anchor="middle" font-size="9" fill="#DC143C">Amman</text>
<text x="100" y="175" text-anchor="middle" font-size="22">🪷</text>
</svg>'''


# ============================================================
# DATABASE CONNECTION
# ============================================================
def get_db_connection():
    """Get database connection using Streamlit secrets"""
    try:
        conn = psycopg2.connect(
            host=st.secrets["database"]["host"],
            database=st.secrets["database"]["database"],
            user=st.secrets["database"]["user"],
            password=st.secrets["database"]["password"],
            port=st.secrets["database"]["port"],
            sslmode="require"
        )
        return conn
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None


def run_query(query, params=None, fetch=True):
    """Run a database query and return results"""
    conn = get_db_connection()
    if not conn:
        return [] if fetch else None
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            if fetch:
                result = cur.fetchall()
                conn.close()
                return result
            else:
                conn.commit()
                conn.close()
                return True
    except Exception as e:
        conn.rollback()
        conn.close()
        st.error(f"Query error: {e}")
        return [] if fetch else None


def run_query_single(query, params=None):
    """Run query and return single row"""
    result = run_query(query, params)
    return result[0] if result else None


def run_insert_returning(query, params=None):
    """Run insert and return the new ID"""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            result = cur.fetchone()
            conn.commit()
            conn.close()
            return result[0] if result else None
    except Exception as e:
        conn.rollback()
        conn.close()
        st.error(f"Insert error: {e}")
        return None


# ============================================================
# CUSTOM CSS
# ============================================================
def load_css():
    st.markdown("""
    <style>
        /* Main styling */
        .main-header {
            background: linear-gradient(135deg, #8B0000 0%, #DC143C 100%);
            color: #FFD700;
            padding: 15px 25px;
            border-radius: 12px;
            margin-bottom: 20px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(139,0,0,0.3);
        }
        .main-header h1 { color: #FFD700; font-size: 1.5em; margin: 0; }
        .main-header h3 { color: rgba(255,215,0,0.8); font-size: 0.9em; margin: 2px 0; }
        .main-header p { color: rgba(255,248,220,0.8); font-size: 0.75em; margin: 0; }

        .stat-card {
            border-radius: 15px;
            padding: 20px;
            color: white;
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
            margin-bottom: 15px;
            position: relative;
            overflow: hidden;
        }
        .stat-card.income { background: linear-gradient(135deg, #228B22, #32CD32); }
        .stat-card.expense { background: linear-gradient(135deg, #DC143C, #FF4500); }
        .stat-card.devotees { background: linear-gradient(135deg, #4169E1, #6495ED); }
        .stat-card.bills { background: linear-gradient(135deg, #FF8C00, #FFD700); }
        .stat-card h4 { font-size: 0.85em; opacity: 0.9; margin-bottom: 5px; }
        .stat-card h2 { font-size: 1.8em; font-weight: 700; margin: 0; }

        .pooja-card {
            background: linear-gradient(135deg, #FFF8DC, #FFEFD5);
            border: 1px solid #FFD700;
            border-radius: 10px;
            padding: 12px;
            margin-bottom: 8px;
            border-left: 4px solid #8B0000;
        }

        .content-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 15px rgba(0,0,0,0.08);
            margin-bottom: 15px;
        }

        .news-ticker {
            background: linear-gradient(90deg, #8B0000, #DC143C, #8B0000);
            color: #FFD700;
            padding: 10px 20px;
            border-radius: 10px;
            margin-bottom: 15px;
            text-align: center;
            font-weight: 500;
        }

        .badge-temple {
            background: #8B0000;
            color: #FFD700;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.8em;
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #8B0000 0%, #B22222 50%, #DC143C 100%);
        }
        [data-testid="stSidebar"] .stMarkdown { color: #FFF8DC; }
        [data-testid="stSidebar"] .stSelectbox label { color: #FFD700 !important; }
        [data-testid="stSidebar"] hr { border-color: rgba(255,215,0,0.3); }

        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, #8B0000, #DC143C);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 500;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #DC143C, #FF4500);
            color: white;
        }

        /* Table styling */
        .stDataFrame thead tr th {
            background: linear-gradient(135deg, #8B0000, #DC143C) !important;
            color: white !important;
        }

        /* Bill print area */
        .bill-header {
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 12px;
            padding-bottom: 12px;
            border-bottom: 3px double #8B0000;
        }
        .bill-header-info { text-align: center; flex: 1; }
        .bill-header-info h3 { color: #8B0000; margin: 0; font-size: 1.15em; }
        .bill-header-info h5 { color: #DC143C; margin: 2px 0; font-size: 0.88em; }
        .bill-header-info p { margin: 1px 0; color: #555; font-size: 0.78em; }

        .family-card {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 10px;
            padding: 12px;
            margin-bottom: 8px;
        }

        .yearly-pooja-card {
            background: #FFF8DC;
            border: 1px solid #FFD700;
            border-radius: 8px;
            padding: 8px 12px;
            margin-bottom: 6px;
        }

        /* Hide default streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
def init_session_state():
    defaults = {
        'logged_in': False,
        'user_id': None,
        'username': None,
        'full_name': None,
        'role': None,
        'current_page': 'dashboard',
        'edit_devotee_id': None,
        'view_devotee_id': None,
        'view_bill_id': None,
        'edit_samaya_id': None,
        'edit_mandapam_id': None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ============================================================
# AUTHENTICATION
# ============================================================
def login_page():
    st.markdown("""
    <div style="text-align:center; padding:30px;">
        <div style="font-size:80px;">🕉️</div>
        <h1 style="color:#8B0000;">""" + TEMPLE_NAME + """</h1>
        <h3 style="color:#DC143C;">""" + TEMPLE_TRUST + """</h3>
        <p style="color:#666;">""" + TEMPLE_ADDRESS_LINE3 + """</p>
        <hr style="border-color:#FFD700; width:50%; margin:15px auto;">
        <p style="color:#888;">Please login to continue</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter password")
            submitted = st.form_submit_button("🔑 Login", use_container_width=True)

            if submitted:
                if username and password:
                    user = run_query_single(
                        "SELECT * FROM users WHERE username = %s AND is_active_user = TRUE",
                        (username,)
                    )
                    if user and check_password_hash(user['password_hash'], password):
                        st.session_state['logged_in'] = True
                        st.session_state['user_id'] = user['id']
                        st.session_state['username'] = user['username']
                        st.session_state['full_name'] = user['full_name'] or user['username']
                        st.session_state['role'] = user['role']
                        st.success("Welcome back! 🙏")
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials!")
                else:
                    st.warning("Please enter both username and password")

        st.markdown("<div style='text-align:center;'><small style='color:#aaa;'>🕉️ Temple Management System</small></div>", unsafe_allow_html=True)


def check_admin():
    return st.session_state.get('role') == 'admin'


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================
def render_sidebar():
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center; padding:10px; border-bottom:2px solid rgba(255,215,0,0.3);">
            <div style="font-size:50px;">🕉️</div>
            <h4 style="color:#FFD700; font-size:0.9em; margin:5px 0;">{TEMPLE_NAME}</h4>
            <p style="color:rgba(255,215,0,0.7); font-size:0.7em;">{TEMPLE_TRUST}</p>
            <p style="color:rgba(255,215,0,0.6); font-size:0.65em;">{TEMPLE_ADDRESS_LINE3}</p>
            <p style="color:#FFD700; font-size:0.75em;">👤 {st.session_state['full_name']}
            {"🔴 ADMIN" if check_admin() else ""}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        menu_items = [
            ("📊 Dashboard", "dashboard"),
            ("👥 Devotees", "devotees"),
            ("🧾 Billing", "billing"),
            ("💸 Expenses", "expenses"),
            ("📈 Reports", "reports"),
            ("---", "---"),
            ("🎓 Samaya Vakuppu", "samaya"),
            ("🏛️ Thirumana Mandapam", "mandapam"),
            ("---", "---"),
            ("🙏 Daily Pooja", "daily_pooja"),
            ("⚙️ Settings", "settings"),
        ]

        if check_admin():
            menu_items.append(("👤 User Management", "users"))
            menu_items.append(("🗑️ Deleted Bills", "deleted_bills"))

        menu_items.append(("---", "---"))
        menu_items.append(("🚪 Logout", "logout"))

        for label, page in menu_items:
            if label == "---":
                st.markdown("---")
            elif page == "logout":
                if st.button(label, key="logout_btn", use_container_width=True):
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()
            else:
                if st.button(label, key=f"nav_{page}", use_container_width=True):
                    st.session_state['current_page'] = page
                    st.rerun()


# ============================================================
# DASHBOARD
# ============================================================
def page_dashboard():
    st.markdown(f"""
    <div class="main-header">
        <h1>🕉️ {TEMPLE_NAME}</h1>
        <h3>{TEMPLE_TRUST}</h3>
        <p>{TEMPLE_ADDRESS_LINE3}</p>
    </div>
    """, unsafe_allow_html=True)

    # Period selection
    col1, col2, col3, col4 = st.columns(4)
    period = 'daily'
    with col1:
        if st.button("📅 Daily", use_container_width=True):
            period = 'daily'
    with col2:
        if st.button("📆 Weekly", use_container_width=True):
            period = 'weekly'
    with col3:
        if st.button("🗓️ Monthly", use_container_width=True):
            period = 'monthly'
    with col4:
        if st.button("📊 Yearly", use_container_width=True):
            period = 'yearly'

    # Use session state for period
    if 'dashboard_period' not in st.session_state:
        st.session_state['dashboard_period'] = 'daily'

    period = st.session_state.get('dashboard_period', 'daily')

    period_select = st.radio("Select Period:", ['Daily', 'Weekly', 'Monthly', 'Yearly'],
                              horizontal=True, label_visibility="collapsed")
    period = period_select.lower()
    st.session_state['dashboard_period'] = period

    today_d = date.today()
    if period == 'daily':
        sd, ed = today_d, today_d
    elif period == 'weekly':
        sd = today_d - timedelta(days=today_d.weekday())
        ed = today_d
    elif period == 'monthly':
        sd = today_d.replace(day=1)
        ed = today_d
    else:
        sd = today_d.replace(month=1, day=1)
        ed = today_d

    # Statistics
    income_result = run_query_single(
        "SELECT COALESCE(SUM(amount),0) as total FROM bill WHERE is_deleted=FALSE AND bill_date >= %s AND bill_date <= %s",
        (datetime.combine(sd, datetime.min.time()), datetime.combine(ed, datetime.max.time()))
    )
    total_income = float(income_result['total']) if income_result else 0

    expense_result = run_query_single(
        "SELECT COALESCE(SUM(amount),0) as total FROM expense WHERE expense_date >= %s AND expense_date <= %s",
        (sd, ed)
    )
    total_expenses = float(expense_result['total']) if expense_result else 0

    devotee_result = run_query_single(
        "SELECT COUNT(*) as total FROM devotee WHERE is_family_head=TRUE AND is_active=TRUE"
    )
    total_devotees = devotee_result['total'] if devotee_result else 0

    bill_result = run_query_single(
        "SELECT COUNT(*) as total FROM bill WHERE is_deleted=FALSE AND bill_date >= %s AND bill_date <= %s",
        (datetime.combine(sd, datetime.min.time()), datetime.combine(ed, datetime.max.time()))
    )
    total_bills = bill_result['total'] if bill_result else 0

    # Stat cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="stat-card income">
            <h4>⬆️ {period.title()} Income</h4><h2>₹{total_income:,.2f}</h2></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="stat-card expense">
            <h4>⬇️ {period.title()} Expenses</h4><h2>₹{total_expenses:,.2f}</h2></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="stat-card devotees">
            <h4>👥 Total Devotees</h4><h2>{total_devotees}</h2></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="stat-card bills">
            <h4>🧾 {period.title()} Bills</h4><h2>{total_bills}</h2></div>""", unsafe_allow_html=True)

    # Birthday ticker
    birthdays = run_query(
        "SELECT name, mobile_no FROM devotee WHERE is_active=TRUE AND EXTRACT(MONTH FROM dob) = %s AND EXTRACT(DAY FROM dob) = %s",
        (today_d.month, today_d.day)
    )
    if birthdays:
        bday_msg = " | ".join([f"🎂 Happy Birthday {b['name']}!" for b in birthdays])
        st.markdown(f'<div class="news-ticker">{bday_msg}</div>', unsafe_allow_html=True)

    # Two columns: Pooja + Birthdays
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### 🙏 Today's Pooja Schedule")
        poojas = run_query("SELECT * FROM daily_pooja WHERE is_active=TRUE ORDER BY pooja_time")
        for p in poojas:
            st.markdown(f"""<div class="pooja-card">
                <strong>{p['pooja_name']}</strong> — <span style="color:#8B0000;font-weight:700;">{p['pooja_time'] or 'TBD'}</span>
                <br><small style="color:#666;">{p['description'] or ''}</small>
            </div>""", unsafe_allow_html=True)
        if not poojas:
            st.info("No pooja scheduled")

    with col_right:
        st.markdown("### 🎂 Today's Birthdays")
        if birthdays:
            for b in birthdays:
                st.markdown(f"""<div style="background:#FFF8DC;padding:10px;border-radius:8px;margin-bottom:5px;">
                    🎂 <strong>{b['name']}</strong> — {b['mobile_no'] or '-'}</div>""", unsafe_allow_html=True)
        else:
            st.info("No birthdays today")

    # Recent bills
    st.markdown("### 🧾 Recent Bills")
    recent = run_query(
        """SELECT b.bill_number, b.bill_date, b.amount, b.guest_name,
           d.name as devotee_name, pt.name as pooja_name
           FROM bill b LEFT JOIN devotee d ON b.devotee_id=d.id
           LEFT JOIN pooja_type pt ON b.pooja_type_id=pt.id
           WHERE b.is_deleted=FALSE ORDER BY b.bill_date DESC LIMIT 10"""
    )
    if recent:
        import pandas as pd
        df = pd.DataFrame(recent)
        df['Name'] = df.apply(lambda r: r['devotee_name'] if r['devotee_name'] else r['guest_name'], axis=1)
        df['Date'] = df['bill_date'].apply(lambda x: x.strftime('%d/%m/%Y') if x else '-')
        df['Amount'] = df['amount'].apply(lambda x: f"₹{x:,.2f}")
        st.dataframe(
            df[['bill_number', 'Date', 'Name', 'pooja_name', 'Amount']].rename(
                columns={'bill_number': 'Bill No', 'pooja_name': 'Pooja'}
            ),
            use_container_width=True, hide_index=True
        )


# ============================================================
# DEVOTEES PAGE
# ============================================================
def page_devotees():
    st.markdown("## 👥 Enrolled Devotees")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ Add Devotee", use_container_width=True):
            st.session_state['current_page'] = 'add_devotee'
            st.session_state['edit_devotee_id'] = None
            st.rerun()

    search = st.text_input("🔍 Search devotees...", placeholder="Type name, mobile...")

    query = """SELECT id, name, mobile_no, whatsapp_no, natchathiram, photo_filename,
               (SELECT COUNT(*) FROM devotee fm WHERE fm.family_head_id = devotee.id) as family_count
               FROM devotee WHERE is_family_head=TRUE AND is_active=TRUE"""
    params = []
    if search:
        query += " AND (name ILIKE %s OR mobile_no ILIKE %s)"
        params = [f"%{search}%", f"%{search}%"]
    query += " ORDER BY name"

    devotees = run_query(query, params if params else None)

    if devotees:
        for d in devotees:
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([1, 3, 2, 1, 2])
                with c1:
                    st.markdown(f"**#{d['id']}**")
                with c2:
                    st.markdown(f"**{d['name']}**")
                with c3:
                    st.markdown(f"📱 {d['mobile_no'] or '-'}")
                with c4:
                    st.markdown(f"👨‍👩‍👧‍👦 {d['family_count']}")
                with c5:
                    bc1, bc2, bc3 = st.columns(3)
                    with bc1:
                        if st.button("👁", key=f"view_{d['id']}"):
                            st.session_state['current_page'] = 'view_devotee'
                            st.session_state['view_devotee_id'] = d['id']
                            st.rerun()
                    with bc2:
                        if st.button("✏️", key=f"edit_{d['id']}"):
                            st.session_state['current_page'] = 'add_devotee'
                            st.session_state['edit_devotee_id'] = d['id']
                            st.rerun()
                    with bc3:
                        if st.button("🗑", key=f"del_{d['id']}"):
                            run_query("DELETE FROM devotee WHERE family_head_id = %s", (d['id'],), fetch=False)
                            run_query("DELETE FROM devotee WHERE id = %s", (d['id'],), fetch=False)
                            st.success("Deleted!")
                            st.rerun()
                st.markdown("---")
    else:
        st.info("No devotees found")


def page_add_devotee():
    edit_id = st.session_state.get('edit_devotee_id')
    devotee = None
    if edit_id:
        devotee = run_query_single("SELECT * FROM devotee WHERE id=%s", (edit_id,))

    st.markdown(f"## {'✏️ Edit' if devotee else '➕ Add New'} Devotee")

    pooja_types = run_query("SELECT * FROM pooja_type WHERE is_active=TRUE ORDER BY name")

    with st.form("devotee_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name *", value=devotee['name'] if devotee else "")
            dob = st.date_input("Date of Birth", value=devotee['dob'] if devotee and devotee['dob'] else None,
                                min_value=date(1920, 1, 1), max_value=date.today(), format="DD/MM/YYYY")
            relation = st.selectbox("Relation", [''] + RELATION_TYPES,
                                    index=RELATION_TYPES.index(devotee['relation_type']) + 1 if devotee and devotee['relation_type'] in RELATION_TYPES else 0)
            mobile = st.text_input("Mobile", value=devotee['mobile_no'] if devotee else "")

        with col2:
            whatsapp = st.text_input("WhatsApp", value=devotee['whatsapp_no'] if devotee else "")
            wedding = st.date_input("Wedding Day", value=devotee['wedding_day'] if devotee and devotee['wedding_day'] else None,
                                    min_value=date(1920, 1, 1), format="DD/MM/YYYY")
            natch_idx = NATCHATHIRAM_LIST.index(devotee['natchathiram']) + 1 if devotee and devotee['natchathiram'] in NATCHATHIRAM_LIST else 0
            natchathiram = st.selectbox("Natchathiram", [''] + NATCHATHIRAM_LIST, index=natch_idx)
            address = st.text_area("Address", value=devotee['address'] if devotee else "", height=80)

        submitted = st.form_submit_button("💾 Save Devotee", use_container_width=True)

        if submitted:
            if not name.strip():
                st.error("Name is required!")
            else:
                if edit_id and devotee:
                    run_query("""UPDATE devotee SET name=%s, dob=%s, relation_type=%s,
                              mobile_no=%s, whatsapp_no=%s, wedding_day=%s,
                              natchathiram=%s, address=%s WHERE id=%s""",
                              (name, dob, relation or None, mobile, whatsapp,
                               wedding, natchathiram or None, address, edit_id), fetch=False)
                    st.success("Devotee updated! ✅")
                else:
                    new_id = run_insert_returning(
                        """INSERT INTO devotee (name, dob, relation_type, mobile_no, whatsapp_no,
                           wedding_day, natchathiram, address, is_family_head, is_active)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,TRUE,TRUE) RETURNING id""",
                        (name, dob, relation or None, mobile, whatsapp,
                         wedding, natchathiram or None, address)
                    )
                    if new_id:
                        st.session_state['edit_devotee_id'] = new_id
                        st.success(f"Devotee added with ID: {new_id} ✅")

    # Family Members Section
    st.markdown("---")
    st.markdown("### 👨‍👩‍👧‍👦 Family Members")

    current_id = edit_id or st.session_state.get('edit_devotee_id')
    if current_id:
        family = run_query("SELECT * FROM devotee WHERE family_head_id=%s ORDER BY name", (current_id,))
        for fm in family:
            with st.expander(f"👤 {fm['name']} ({fm['relation_type'] or '-'})"):
                fc1, fc2, fc3 = st.columns([2, 1, 1])
                with fc1:
                    st.write(f"**DOB:** {fm['dob'].strftime('%d/%m/%Y') if fm['dob'] else '-'}")
                    st.write(f"**Star:** {fm['natchathiram'] or '-'}")
                with fc2:
                    st.write(f"**Mobile:** {fm['mobile_no'] or '-'}")
                with fc3:
                    if st.button("🗑 Remove", key=f"rmfm_{fm['id']}"):
                        run_query("DELETE FROM devotee WHERE id=%s", (fm['id'],), fetch=False)
                        st.rerun()

        st.markdown("#### Add Family Member")
        with st.form("add_family_form"):
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                fm_name = st.text_input("Name", key="fm_name")
                fm_dob = st.date_input("DOB", key="fm_dob", value=None, min_value=date(1920, 1, 1), format="DD/MM/YYYY")
            with fc2:
                fm_rel = st.selectbox("Relation", [''] + RELATION_TYPES, key="fm_rel")
                fm_natch = st.selectbox("Star", [''] + NATCHATHIRAM_LIST, key="fm_natch")
            with fc3:
                fm_mobile = st.text_input("Mobile", key="fm_mobile")

            if st.form_submit_button("➕ Add Family Member"):
                if fm_name.strip():
                    run_query(
                        """INSERT INTO devotee (name, dob, relation_type, natchathiram, mobile_no,
                           family_head_id, is_family_head, is_active, address)
                           VALUES (%s,%s,%s,%s,%s,%s,FALSE,TRUE,
                           (SELECT address FROM devotee WHERE id=%s))""",
                        (fm_name, fm_dob, fm_rel or None, fm_natch or None, fm_mobile,
                         current_id, current_id), fetch=False
                    )
                    st.success("Family member added!")
                    st.rerun()

        # Yearly Pooja Section
        st.markdown("---")
        st.markdown("### 🕉️ Yearly Poojas")

        yearly = run_query(
            """SELECT yp.*, pt.name as pooja_type_name FROM devotee_yearly_pooja yp
               LEFT JOIN pooja_type pt ON yp.pooja_type_id=pt.id
               WHERE yp.devotee_id=%s ORDER BY yp.pooja_date""", (current_id,))
        for yp in yearly:
            c1, c2, c3, c4 = st.columns([3, 2, 3, 1])
            with c1:
                st.write(f"**{yp['pooja_type_name'] or yp['pooja_name'] or '-'}**")
            with c2:
                st.write(yp['pooja_date'].strftime('%d/%m/%Y') if yp['pooja_date'] else '-')
            with c3:
                st.write(yp['notes'] or '-')
            with c4:
                if st.button("🗑", key=f"rmyp_{yp['id']}"):
                    run_query("DELETE FROM devotee_yearly_pooja WHERE id=%s", (yp['id'],), fetch=False)
                    st.rerun()

        with st.form("add_yearly_form"):
            yc1, yc2, yc3 = st.columns(3)
            with yc1:
                pt_options = {f"{pt['name']} (₹{pt['amount']})": pt['id'] for pt in pooja_types}
                yp_type = st.selectbox("Pooja Type", [''] + list(pt_options.keys()), key="yp_type")
            with yc2:
                yp_date = st.date_input("Pooja Date", key="yp_date", format="DD/MM/YYYY")
            with yc3:
                yp_notes = st.text_input("Notes", key="yp_notes")

            if st.form_submit_button("➕ Add Yearly Pooja"):
                pt_id = pt_options.get(yp_type) if yp_type else None
                pt_name_val = yp_type.split(' (')[0] if yp_type else None
                run_query(
                    """INSERT INTO devotee_yearly_pooja (devotee_id, pooja_type_id, pooja_name, pooja_date, notes)
                       VALUES (%s,%s,%s,%s,%s)""",
                    (current_id, pt_id, pt_name_val, yp_date, yp_notes), fetch=False
                )
                st.success("Yearly pooja added!")
                st.rerun()
    else:
        st.info("Save the devotee first, then add family members and yearly poojas.")

    if st.button("⬅️ Back to Devotees"):
        st.session_state['current_page'] = 'devotees'
        st.session_state['edit_devotee_id'] = None
        st.rerun()


def page_view_devotee():
    did = st.session_state.get('view_devotee_id')
    if not did:
        st.session_state['current_page'] = 'devotees'
        st.rerun()
        return

    d = run_query_single("SELECT * FROM devotee WHERE id=%s", (did,))
    if not d:
        st.error("Devotee not found!")
        return

    st.markdown(f"## 👤 {d['name']}")

    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown(f"""<div style="width:120px;height:120px;background:#8B0000;color:#FFD700;
            border-radius:50%;display:flex;align-items:center;justify-content:center;
            font-size:3em;font-weight:bold;margin:auto;">{d['name'][0]}</div>""", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center;'><span class='badge-temple'>ID: {d['id']}</span></p>", unsafe_allow_html=True)

    with col2:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.write(f"**DOB:** {d['dob'].strftime('%d/%m/%Y') if d['dob'] else '-'}")
            st.write(f"**Relation:** {d['relation_type'] or '-'}")
        with c2:
            st.write(f"**Mobile:** {d['mobile_no'] or '-'}")
            st.write(f"**WhatsApp:** {d['whatsapp_no'] or '-'}")
        with c3:
            st.write(f"**Wedding:** {d['wedding_day'].strftime('%d/%m/%Y') if d['wedding_day'] else '-'}")
            st.write(f"**Star:** {d['natchathiram'] or '-'}")
        st.write(f"**Address:** {d['address'] or '-'}")

    # Family
    st.markdown("### 👨‍👩‍👧‍👦 Family Members")
    family = run_query("SELECT * FROM devotee WHERE family_head_id=%s ORDER BY name", (did,))
    if family:
        for fm in family:
            st.markdown(f"""<div class="family-card">
                <strong>{fm['name']}</strong> | {fm['relation_type'] or '-'} |
                DOB: {fm['dob'].strftime('%d/%m/%Y') if fm['dob'] else '-'} |
                Star: {fm['natchathiram'] or '-'} | Mobile: {fm['mobile_no'] or '-'}
            </div>""", unsafe_allow_html=True)
    else:
        st.info("No family members")

    # Yearly Poojas
    st.markdown("### 🕉️ Yearly Poojas")
    yearly = run_query(
        """SELECT yp.*, pt.name as pt_name FROM devotee_yearly_pooja yp
           LEFT JOIN pooja_type pt ON yp.pooja_type_id=pt.id
           WHERE yp.devotee_id=%s""", (did,))
    for yp in yearly:
        st.markdown(f"""<div class="yearly-pooja-card">
            <strong>{yp['pt_name'] or yp['pooja_name'] or '-'}</strong> |
            Date: {yp['pooja_date'].strftime('%d/%m/%Y') if yp['pooja_date'] else '-'} |
            {yp['notes'] or '-'}
        </div>""", unsafe_allow_html=True)

    # Bills
    st.markdown("### 🧾 Bills")
    bills = run_query(
        """SELECT b.*, pt.name as pooja_name FROM bill b
           LEFT JOIN pooja_type pt ON b.pooja_type_id=pt.id
           WHERE b.devotee_id=%s AND b.is_deleted=FALSE ORDER BY b.bill_date DESC""", (did,))
    if bills:
        import pandas as pd
        df = pd.DataFrame(bills)
        df['Date'] = df['bill_date'].apply(lambda x: x.strftime('%d/%m/%Y') if x else '-')
        df['Amount'] = df['amount'].apply(lambda x: f"₹{x:,.2f}")
        st.dataframe(df[['bill_number', 'Date', 'pooja_name', 'Amount']].rename(
            columns={'bill_number': 'Bill No', 'pooja_name': 'Pooja'}),
            use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("✏️ Edit Devotee"):
            st.session_state['current_page'] = 'add_devotee'
            st.session_state['edit_devotee_id'] = did
            st.rerun()
    with c2:
        if st.button("⬅️ Back"):
            st.session_state['current_page'] = 'devotees'
            st.rerun()


# ============================================================
# BILLING PAGE
# ============================================================
def page_billing():
    st.markdown("## 🧾 Bills")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ New Bill", use_container_width=True):
            st.session_state['current_page'] = 'new_bill'
            st.rerun()

    fc1, fc2, fc3 = st.columns([2, 2, 1])
    with fc1:
        from_date = st.date_input("From", value=date.today(), format="DD/MM/YYYY", key="bill_from")
    with fc2:
        to_date = st.date_input("To", value=date.today(), format="DD/MM/YYYY", key="bill_to")

    bills = run_query(
        """SELECT b.*, d.name as devotee_name, pt.name as pooja_name
           FROM bill b LEFT JOIN devotee d ON b.devotee_id=d.id
           LEFT JOIN pooja_type pt ON b.pooja_type_id=pt.id
           WHERE b.bill_date >= %s AND b.bill_date <= %s
           ORDER BY b.bill_date DESC""",
        (datetime.combine(from_date, datetime.min.time()),
         datetime.combine(to_date, datetime.max.time()))
    )

    if bills:
        for b in bills:
            if b['is_deleted']:
                st.markdown(f"""<div style="background:#ffe0e0;padding:8px;border-radius:8px;margin-bottom:5px;opacity:0.5;text-decoration:line-through;">
                    {b['bill_number']} | {b['devotee_name'] or b['guest_name']} | ₹{b['amount']:,.2f} | DELETED
                </div>""", unsafe_allow_html=True)
                continue

            with st.container():
                c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1.5, 1, 2, 1.5, 2])
                with c1:
                    st.write(f"**{b['bill_number']}**")
                with c2:
                    st.write(b['bill_date'].strftime('%d/%m/%Y') if b['bill_date'] else '-')
                with c3:
                    dtype = "✅ Enrolled" if b['devotee_type'] == 'enrolled' else "👤 Guest"
                    st.write(dtype)
                with c4:
                    st.write(b['devotee_name'] or b['guest_name'] or '-')
                with c5:
                    st.write(f"**₹{b['amount']:,.2f}**")
                with c6:
                    bc1, bc2, bc3 = st.columns(3)
                    with bc1:
                        if st.button("👁", key=f"vb_{b['id']}"):
                            st.session_state['current_page'] = 'view_bill'
                            st.session_state['view_bill_id'] = b['id']
                            st.rerun()
                    with bc2:
                        if st.button("🖨", key=f"pb_{b['id']}"):
                            st.session_state['current_page'] = 'print_bill'
                            st.session_state['view_bill_id'] = b['id']
                            st.rerun()
                    with bc3:
                        if check_admin():
                            if st.button("🗑", key=f"db_{b['id']}"):
                                st.session_state[f'confirm_delete_bill_{b["id"]}'] = True
                                st.rerun()

                    # Delete confirmation
                    if st.session_state.get(f'confirm_delete_bill_{b["id"]}'):
                        reason = st.text_input("Reason for deletion:", key=f"dr_{b['id']}")
                        if st.button("Confirm Delete", key=f"cd_{b['id']}"):
                            run_query(
                                """UPDATE bill SET is_deleted=TRUE, deleted_by=%s,
                                   deleted_at=NOW(), delete_reason=%s WHERE id=%s""",
                                (st.session_state['user_id'], reason, b['id']), fetch=False
                            )
                            del st.session_state[f'confirm_delete_bill_{b["id"]}']
                            st.success("Bill deleted!")
                            st.rerun()
                st.markdown("---")
    else:
        st.info("No bills found for selected period")


def page_new_bill():
    st.markdown("## 🧾 New Bill")

    pooja_types = run_query("SELECT * FROM pooja_type WHERE is_active=TRUE ORDER BY name")
    devotees_list = run_query(
        "SELECT id, name, mobile_no, address FROM devotee WHERE is_family_head=TRUE AND is_active=TRUE ORDER BY name"
    )

    last_bill = run_query_single("SELECT id FROM bill ORDER BY id DESC LIMIT 1")
    next_no = f"BILL-{(last_bill['id'] + 1) if last_bill else 1:06d}"

    with st.form("new_bill_form"):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            bill_no = st.text_input("Bill Number", value=next_no, disabled=True)
        with c2:
            manual_no = st.text_input("Manual Bill No")
        with c3:
            book_no = st.text_input("Bill Book No")
        with c4:
            bill_date = st.date_input("Date", value=date.today(), format="DD/MM/YYYY")
            bill_time = st.time_input("Time", value=datetime.now().time())

        devotee_type = st.radio("Devotee Type:", ["Enrolled", "Guest"], horizontal=True)

        if devotee_type == "Enrolled":
            dev_options = {f"{d['name']} (ID:{d['id']})": d['id'] for d in devotees_list}
            selected_dev = st.selectbox("Select Devotee *", [''] + list(dev_options.keys()))
            devotee_id = dev_options.get(selected_dev) if selected_dev else None
            guest_name = guest_address = guest_mobile = guest_whatsapp = None
        else:
            devotee_id = None
            gc1, gc2 = st.columns(2)
            with gc1:
                guest_name = st.text_input("Guest Name *")
                guest_mobile = st.text_input("Guest Mobile")
            with gc2:
                guest_address = st.text_area("Guest Address", height=68)
                guest_whatsapp = st.text_input("Guest WhatsApp")

        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            pt_options = {f"{pt['name']} (₹{pt['amount']})": (pt['id'], pt['amount']) for pt in pooja_types}
            sel_pt = st.selectbox("Pooja Type *", [''] + list(pt_options.keys()))
            pt_id = pt_options[sel_pt][0] if sel_pt else None
            default_amt = pt_options[sel_pt][1] if sel_pt else 0.0
        with pc2:
            amount = st.number_input("Amount *", value=float(default_amt), step=10.0, min_value=0.0)
        with pc3:
            notes = st.text_input("Notes")

        submitted = st.form_submit_button("💾 Create Bill", use_container_width=True)

        if submitted:
            if not pt_id:
                st.error("Please select a pooja type!")
            elif devotee_type == "Enrolled" and not devotee_id:
                st.error("Please select a devotee!")
            elif devotee_type == "Guest" and not guest_name:
                st.error("Please enter guest name!")
            else:
                bill_datetime = datetime.combine(bill_date, bill_time)
                new_id = run_insert_returning(
                    """INSERT INTO bill (bill_number, manual_bill_no, bill_book_no, bill_date,
                       devotee_type, devotee_id, guest_name, guest_address, guest_mobile,
                       guest_whatsapp, pooja_type_id, amount, notes, created_by)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                    (next_no, manual_no, book_no, bill_datetime,
                     devotee_type.lower(), devotee_id, guest_name, guest_address,
                     guest_mobile, guest_whatsapp, pt_id, amount, notes,
                     st.session_state['user_id'])
                )
                if new_id:
                    st.success(f"Bill {next_no} created! ✅")
                    st.session_state['view_bill_id'] = new_id
                    st.session_state['current_page'] = 'view_bill'
                    st.rerun()

    if st.button("⬅️ Back to Bills"):
        st.session_state['current_page'] = 'billing'
        st.rerun()


def page_view_bill():
    bid = st.session_state.get('view_bill_id')
    if not bid:
        st.session_state['current_page'] = 'billing'
        st.rerun()
        return

    b = run_query_single(
        """SELECT b.*, d.name as devotee_name, d.mobile_no as dev_mobile, d.address as dev_address,
           pt.name as pooja_name FROM bill b
           LEFT JOIN devotee d ON b.devotee_id=d.id
           LEFT JOIN pooja_type pt ON b.pooja_type_id=pt.id WHERE b.id=%s""", (bid,))

    if not b:
        st.error("Bill not found!")
        return

    # Printable bill
    st.markdown(f"""
    <div style="background:white;padding:25px;border-radius:12px;box-shadow:0 2px 15px rgba(0,0,0,0.08);">
        <div style="text-align:center;border-bottom:3px double #8B0000;padding-bottom:12px;margin-bottom:15px;">
            <h2 style="color:#8B0000;margin:0;">🕉️ {TEMPLE_NAME}</h2>
            <h4 style="color:#DC143C;margin:3px 0;">{TEMPLE_TRUST}</h4>
            <p style="color:#555;font-size:0.85em;">{TEMPLE_ADDRESS_LINE3}</p>
            <p style="color:#666;font-size:0.8em;">📜 BILL RECEIPT</p>
        </div>
        <div style="display:flex;justify-content:space-between;margin-bottom:15px;">
            <div>
                <p><strong>Bill No:</strong> {b['bill_number']}</p>
                <p><strong>Manual Bill:</strong> {b['manual_bill_no'] or '-'}</p>
                <p><strong>Bill Book:</strong> {b['bill_book_no'] or '-'}</p>
            </div>
            <div style="text-align:right;">
                <p><strong>Date:</strong> {b['bill_date'].strftime('%d/%m/%Y %I:%M %p') if b['bill_date'] else '-'}</p>
                <p><strong>{"Devotee" if b['devotee_type']=="enrolled" else "Guest"}:</strong>
                    {b['devotee_name'] if b['devotee_type']=='enrolled' else b['guest_name']}</p>
                <p><strong>Mobile:</strong> {b['dev_mobile'] if b['devotee_type']=='enrolled' else (b['guest_mobile'] or '-')}</p>
            </div>
        </div>
        <table style="width:100%;border-collapse:collapse;margin:10px 0;">
            <thead><tr style="background:#8B0000;color:white;">
                <th style="padding:8px;text-align:left;">Pooja Type</th>
                <th style="padding:8px;text-align:left;">Notes</th>
                <th style="padding:8px;text-align:right;">Amount</th>
            </tr></thead>
            <tbody><tr style="border-bottom:1px solid #ddd;">
                <td style="padding:8px;">{b['pooja_name'] or '-'}</td>
                <td style="padding:8px;">{b['notes'] or '-'}</td>
                <td style="padding:8px;text-align:right;"><strong>₹{b['amount']:,.2f}</strong></td>
            </tr></tbody>
            <tfoot><tr style="border-top:2px solid #8B0000;">
                <td colspan="2" style="padding:8px;text-align:right;"><strong>Total:</strong></td>
                <td style="padding:8px;text-align:right;"><strong style="color:#8B0000;font-size:1.3em;">₹{b['amount']:,.2f}</strong></td>
            </tr></tfoot>
        </table>
        <div style="text-align:center;margin-top:15px;padding-top:10px;border-top:1px dashed #ccc;">
            <small style="color:#888;">{TEMPLE_FULL_ADDRESS}</small><br>
            <small style="color:#aaa;">🕉️ Thank you for your contribution 🙏</small>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🖨️ Print (Ctrl+P)"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    with c2:
        if st.button("⬅️ Back to Bills"):
            st.session_state['current_page'] = 'billing'
            st.rerun()


# ============================================================
# EXPENSES PAGE
# ============================================================
def page_expenses():
    st.markdown("## 💸 Expenses")

    fc1, fc2 = st.columns(2)
    with fc1:
        from_date = st.date_input("From", value=date.today().replace(day=1), format="DD/MM/YYYY", key="exp_from")
    with fc2:
        to_date = st.date_input("To", value=date.today(), format="DD/MM/YYYY", key="exp_to")

    expenses = run_query(
        """SELECT e.*, et.name as type_name FROM expense e
           LEFT JOIN expense_type et ON e.expense_type_id=et.id
           WHERE e.expense_date >= %s AND e.expense_date <= %s
           ORDER BY e.expense_date DESC""",
        (from_date, to_date)
    )

    total = sum(e['amount'] for e in expenses) if expenses else 0
    st.markdown(f"**Total Expenses: ₹{total:,.2f}**")

    if expenses:
        import pandas as pd
        df = pd.DataFrame(expenses)
        df['Date'] = df['expense_date'].apply(lambda x: x.strftime('%d/%m/%Y') if x else '-')
        df['Amount'] = df['amount'].apply(lambda x: f"₹{x:,.2f}")
        st.dataframe(
            df[['id', 'Date', 'type_name', 'description', 'Amount']].rename(
                columns={'id': 'ID', 'type_name': 'Type', 'description': 'Description'}),
            use_container_width=True, hide_index=True
        )

        # Delete expense
        del_id = st.number_input("Delete Expense ID:", min_value=0, step=1, value=0, key="del_exp")
        if del_id > 0 and st.button("🗑 Delete Expense"):
            run_query("DELETE FROM expense WHERE id=%s", (del_id,), fetch=False)
            st.success("Deleted!")
            st.rerun()

    # Add expense
    st.markdown("### ➕ Add Expense")
    expense_types = run_query("SELECT * FROM expense_type WHERE is_active=TRUE ORDER BY name")

    with st.form("add_expense_form"):
        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            et_options = {et['name']: et['id'] for et in expense_types}
            sel_et = st.selectbox("Expense Type *", list(et_options.keys()))
        with ec2:
            exp_amount = st.number_input("Amount *", min_value=0.0, step=10.0)
        with ec3:
            exp_date = st.date_input("Date", value=date.today(), format="DD/MM/YYYY")
        description = st.text_input("Description")

        if st.form_submit_button("💾 Save Expense", use_container_width=True):
            if exp_amount > 0:
                run_query(
                    """INSERT INTO expense (expense_type_id, amount, description, expense_date, created_by)
                       VALUES (%s,%s,%s,%s,%s)""",
                    (et_options[sel_et], exp_amount, description, exp_date, st.session_state['user_id']),
                    fetch=False
                )
                st.success("Expense added! ✅")
                st.rerun()


# ============================================================
# REPORTS PAGE
# ============================================================
def page_reports():
    st.markdown("## 📈 Reports")

    fc1, fc2 = st.columns(2)
    with fc1:
        from_date = st.date_input("From", value=date.today().replace(day=1), format="DD/MM/YYYY", key="rep_from")
    with fc2:
        to_date = st.date_input("To", value=date.today(), format="DD/MM/YYYY", key="rep_to")

    sdt = datetime.combine(from_date, datetime.min.time())
    edt = datetime.combine(to_date, datetime.max.time())

    income_r = run_query_single(
        "SELECT COALESCE(SUM(amount),0) as total FROM bill WHERE is_deleted=FALSE AND bill_date>=%s AND bill_date<=%s",
        (sdt, edt))
    expense_r = run_query_single(
        "SELECT COALESCE(SUM(amount),0) as total FROM expense WHERE expense_date>=%s AND expense_date<=%s",
        (from_date, to_date))

    ti = float(income_r['total']) if income_r else 0
    te = float(expense_r['total']) if expense_r else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="stat-card income"><h4>Total Income</h4><h2>₹{ti:,.2f}</h2></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-card expense"><h4>Total Expenses</h4><h2>₹{te:,.2f}</h2></div>', unsafe_allow_html=True)
    with c3:
        net = ti - te
        color = "income" if net >= 0 else "expense"
        st.markdown(f'<div class="stat-card {color}"><h4>Net Balance</h4><h2>₹{net:,.2f}</h2></div>', unsafe_allow_html=True)

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("### Income by Pooja Type")
        ibp = run_query(
            """SELECT pt.name, COUNT(b.id) as cnt, COALESCE(SUM(b.amount),0) as total
               FROM pooja_type pt JOIN bill b ON b.pooja_type_id=pt.id
               WHERE b.is_deleted=FALSE AND b.bill_date>=%s AND b.bill_date<=%s
               GROUP BY pt.name ORDER BY total DESC""", (sdt, edt))
        if ibp:
            import pandas as pd
            df = pd.DataFrame(ibp)
            df['Amount'] = df['total'].apply(lambda x: f"₹{x:,.2f}")
            st.dataframe(df[['name', 'cnt', 'Amount']].rename(
                columns={'name': 'Pooja', 'cnt': 'Count'}), use_container_width=True, hide_index=True)

    with col_r:
        st.markdown("### Expenses by Type")
        ebt = run_query(
            """SELECT et.name, COUNT(e.id) as cnt, COALESCE(SUM(e.amount),0) as total
               FROM expense_type et JOIN expense e ON e.expense_type_id=et.id
               WHERE e.expense_date>=%s AND e.expense_date<=%s
               GROUP BY et.name ORDER BY total DESC""", (from_date, to_date))
        if ebt:
            import pandas as pd
            df = pd.DataFrame(ebt)
            df['Amount'] = df['total'].apply(lambda x: f"₹{x:,.2f}")
            st.dataframe(df[['name', 'cnt', 'Amount']].rename(
                columns={'name': 'Type', 'cnt': 'Count'}), use_container_width=True, hide_index=True)


# ============================================================
# SAMAYA VAKUPPU
# ============================================================
def page_samaya():
    st.markdown("## 🎓 Samaya Vakuppu")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ Add Student", use_container_width=True):
            st.session_state['current_page'] = 'add_samaya'
            st.session_state['edit_samaya_id'] = None
            st.rerun()

    students = run_query("SELECT * FROM samaya_vakuppu ORDER BY student_name")
    if students:
        for s in students:
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
                with c1:
                    st.write(f"**{s['student_name']}**")
                with c2:
                    st.write(f"DOB: {s['dob'].strftime('%d/%m/%Y') if s['dob'] else '-'}")
                with c3:
                    st.write(f"Parent: {s['father_mother_name'] or '-'}")
                with c4:
                    st.write(f"Bond: {s['bond_no'] or '-'}")
                with c5:
                    bc1, bc2 = st.columns(2)
                    with bc1:
                        if st.button("✏️", key=f"es_{s['id']}"):
                            st.session_state['current_page'] = 'add_samaya'
                            st.session_state['edit_samaya_id'] = s['id']
                            st.rerun()
                    with bc2:
                        if st.button("🗑", key=f"ds_{s['id']}"):
                            run_query("DELETE FROM samaya_vakuppu WHERE id=%s", (s['id'],), fetch=False)
                            st.rerun()
                st.markdown("---")
    else:
        st.info("No students found")


def page_add_samaya():
    edit_id = st.session_state.get('edit_samaya_id')
    student = run_query_single("SELECT * FROM samaya_vakuppu WHERE id=%s", (edit_id,)) if edit_id else None

    st.markdown(f"## {'✏️ Edit' if student else '➕ Add'} Student")

    with st.form("samaya_form"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Student Name *", value=student['student_name'] if student else "")
            dob = st.date_input("DOB", value=student['dob'] if student and student['dob'] else None,
                                min_value=date(1920, 1, 1), format="DD/MM/YYYY")
            parent = st.text_input("Father/Mother Name", value=student['father_mother_name'] if student else "")
            bond_no = st.text_input("Bond No", value=student['bond_no'] if student else "")
        with c2:
            bond_date = st.date_input("Bond Issue Date",
                                       value=student['bond_issue_date'] if student and student['bond_issue_date'] else None,
                                       min_value=date(1990, 1, 1), format="DD/MM/YYYY")
            bank = st.text_input("Issuing Bank", value=student['bond_issuing_bank'] if student else "")
            branch = st.text_input("Branch", value=student['branch_of_bank'] if student else "")
        address = st.text_area("Address", value=student['address'] if student else "", height=80)

        if st.form_submit_button("💾 Save", use_container_width=True):
            if name.strip():
                if edit_id and student:
                    run_query(
                        """UPDATE samaya_vakuppu SET student_name=%s, dob=%s, address=%s,
                           father_mother_name=%s, bond_no=%s, bond_issue_date=%s,
                           bond_issuing_bank=%s, branch_of_bank=%s WHERE id=%s""",
                        (name, dob, address, parent, bond_no, bond_date, bank, branch, edit_id), fetch=False)
                else:
                    run_query(
                        """INSERT INTO samaya_vakuppu (student_name, dob, address, father_mother_name,
                           bond_no, bond_issue_date, bond_issuing_bank, branch_of_bank)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (name, dob, address, parent, bond_no, bond_date, bank, branch), fetch=False)
                st.success("Saved! ✅")
                st.session_state['current_page'] = 'samaya'
                st.rerun()

    if st.button("⬅️ Back"):
        st.session_state['current_page'] = 'samaya'
        st.rerun()


# ============================================================
# THIRUMANA MANDAPAM
# ============================================================
def page_mandapam():
    st.markdown("## 🏛️ Thirumana Mandapam")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ Add Record", use_container_width=True):
            st.session_state['current_page'] = 'add_mandapam'
            st.session_state['edit_mandapam_id'] = None
            st.rerun()

    records = run_query("SELECT * FROM thirumana_mandapam ORDER BY name")
    if records:
        for m in records:
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([2, 1.5, 1.5, 1, 1])
                with c1:
                    st.write(f"**{m['name']}**")
                with c2:
                    st.write(f"Bond: {m['bond_no'] or '-'}")
                with c3:
                    st.write(f"₹{m['amount']:,.2f}")
                with c4:
                    st.write(f"Bonds: {m['no_of_bond']}")
                with c5:
                    bc1, bc2 = st.columns(2)
                    with bc1:
                        if st.button("✏️", key=f"em_{m['id']}"):
                            st.session_state['current_page'] = 'add_mandapam'
                            st.session_state['edit_mandapam_id'] = m['id']
                            st.rerun()
                    with bc2:
                        if st.button("🗑", key=f"dm_{m['id']}"):
                            run_query("DELETE FROM thirumana_mandapam WHERE id=%s", (m['id'],), fetch=False)
                            st.rerun()
                st.markdown("---")
    else:
        st.info("No records found")


def page_add_mandapam():
    edit_id = st.session_state.get('edit_mandapam_id')
    record = run_query_single("SELECT * FROM thirumana_mandapam WHERE id=%s", (edit_id,)) if edit_id else None

    st.markdown(f"## {'✏️ Edit' if record else '➕ Add'} Record")

    with st.form("mandapam_form"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Name *", value=record['name'] if record else "")
            bond_no = st.text_input("Bond No", value=record['bond_no'] if record else "")
            bond_date = st.date_input("Bond Date",
                                       value=record['bond_issued_date'] if record and record['bond_issued_date'] else None,
                                       format="DD/MM/YYYY")
        with c2:
            amount = st.number_input("Amount", value=float(record['amount']) if record else 0.0, step=100.0)
            no_bond = st.number_input("No of Bonds", value=int(record['no_of_bond']) if record else 1, min_value=1)
        address = st.text_area("Address", value=record['address'] if record else "", height=80)

        if st.form_submit_button("💾 Save", use_container_width=True):
            if name.strip():
                if edit_id and record:
                    run_query(
                        """UPDATE thirumana_mandapam SET name=%s, bond_no=%s, bond_issued_date=%s,
                           amount=%s, no_of_bond=%s, address=%s WHERE id=%s""",
                        (name, bond_no, bond_date, amount, no_bond, address, edit_id), fetch=False)
                else:
                    run_query(
                        """INSERT INTO thirumana_mandapam (name, bond_no, bond_issued_date, amount, no_of_bond, address)
                           VALUES (%s,%s,%s,%s,%s,%s)""",
                        (name, bond_no, bond_date, amount, no_bond, address), fetch=False)
                st.success("Saved! ✅")
                st.session_state['current_page'] = 'mandapam'
                st.rerun()

    if st.button("⬅️ Back"):
        st.session_state['current_page'] = 'mandapam'
        st.rerun()


# ============================================================
# DAILY POOJA
# ============================================================
def page_daily_pooja():
    st.markdown("## 🙏 Daily Pooja Schedule")

    poojas = run_query("SELECT * FROM daily_pooja WHERE is_active=TRUE ORDER BY pooja_time")
    for p in poojas:
        c1, c2, c3, c4 = st.columns([3, 2, 3, 1])
        with c1:
            st.markdown(f"**{p['pooja_name']}**")
        with c2:
            st.markdown(f"🕐 **{p['pooja_time'] or 'TBD'}**")
        with c3:
            st.write(p['description'] or '-')
        with c4:
            if st.button("🗑", key=f"ddp_{p['id']}"):
                run_query("UPDATE daily_pooja SET is_active=FALSE WHERE id=%s", (p['id'],), fetch=False)
                st.rerun()

    st.markdown("### ➕ Add Pooja")
    with st.form("add_pooja_form"):
        c1, c2 = st.columns(2)
        with c1:
            pname = st.text_input("Pooja Name *")
            ptime = st.text_input("Time (e.g. 6:00 AM)")
        with c2:
            pdesc = st.text_input("Description")

        if st.form_submit_button("💾 Add Pooja"):
            if pname.strip():
                run_query("INSERT INTO daily_pooja (pooja_name, pooja_time, description) VALUES (%s,%s,%s)",
                          (pname, ptime, pdesc), fetch=False)
                st.success("Added!")
                st.rerun()


# ============================================================
# SETTINGS
# ============================================================
def page_settings():
    st.markdown("## ⚙️ Settings")

    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("### 🕉️ Pooja Types")
        pts = run_query("SELECT * FROM pooja_type WHERE is_active=TRUE ORDER BY name")
        for pt in pts:
            c1, c2, c3 = st.columns([3, 1.5, 1])
            with c1:
                st.write(pt['name'])
            with c2:
                st.write(f"₹{pt['amount']}")
            with c3:
                if st.button("🗑", key=f"dpt_{pt['id']}"):
                    run_query("UPDATE pooja_type SET is_active=FALSE WHERE id=%s", (pt['id'],), fetch=False)
                    st.rerun()

        st.markdown("#### ➕ Add Pooja Type")
        with st.form("add_pt_form"):
            pt_name = st.text_input("Name *", key="new_pt_name")
            pt_amt = st.number_input("Amount", value=0.0, step=10.0, key="new_pt_amt")
            if st.form_submit_button("Add"):
                if pt_name.strip():
                    run_query("INSERT INTO pooja_type (name, amount) VALUES (%s,%s)",
                              (pt_name, pt_amt), fetch=False)
                    st.rerun()

    with col_r:
        st.markdown("### 🏷️ Expense Types")
        ets = run_query("SELECT * FROM expense_type WHERE is_active=TRUE ORDER BY name")
        for et in ets:
            c1, c2 = st.columns([4, 1])
            with c1:
                st.write(et['name'])
            with c2:
                if st.button("🗑", key=f"det_{et['id']}"):
                    run_query("UPDATE expense_type SET is_active=FALSE WHERE id=%s", (et['id'],), fetch=False)
                    st.rerun()

        st.markdown("#### ➕ Add Expense Type")
        with st.form("add_et_form"):
            et_name = st.text_input("Name *", key="new_et_name")
            if st.form_submit_button("Add"):
                if et_name.strip():
                    run_query("INSERT INTO expense_type (name) VALUES (%s)", (et_name,), fetch=False)
                    st.rerun()


# ============================================================
# USER MANAGEMENT
# ============================================================
def page_users():
    if not check_admin():
        st.error("Admin access required!")
        return

    st.markdown("## 👤 User Management")

    users = run_query("SELECT * FROM users ORDER BY id")
    if users:
        for u in users:
            c1, c2, c3, c4, c5 = st.columns([1, 2, 2, 1, 1])
            with c1:
                st.write(f"#{u['id']}")
            with c2:
                st.write(f"**{u['username']}** ({u['full_name'] or '-'})")
            with c3:
                role_badge = "🔴 ADMIN" if u['role'] == 'admin' else "🔵 User"
                st.write(role_badge)
            with c4:
                status = "✅ Active" if u['is_active_user'] else "⛔ Inactive"
                st.write(status)
            with c5:
                if u['id'] != st.session_state['user_id']:
                    label = "Deactivate" if u['is_active_user'] else "Activate"
                    if st.button(label, key=f"tu_{u['id']}"):
                        run_query("UPDATE users SET is_active_user = NOT is_active_user WHERE id=%s",
                                  (u['id'],), fetch=False)
                        st.rerun()
            st.markdown("---")

    st.markdown("### ➕ Add User")
    with st.form("add_user_form"):
        c1, c2 = st.columns(2)
        with c1:
            new_un = st.text_input("Username *")
            new_fn = st.text_input("Full Name")
        with c2:
            new_pw = st.text_input("Password *", type="password")
            new_role = st.selectbox("Role", ['user', 'admin'])

        if st.form_submit_button("👤 Create User", use_container_width=True):
            if new_un and new_pw:
                existing = run_query_single("SELECT id FROM users WHERE username=%s", (new_un,))
                if existing:
                    st.error("Username already exists!")
                else:
                    pw_hash = generate_password_hash(new_pw)
                    run_query(
                        "INSERT INTO users (username, password_hash, full_name, role) VALUES (%s,%s,%s,%s)",
                        (new_un, pw_hash, new_fn, new_role), fetch=False)
                    st.success("User created! ✅")
                    st.rerun()


# ============================================================
# DELETED BILLS
# ============================================================
def page_deleted_bills():
    if not check_admin():
        st.error("Admin access required!")
        return

    st.markdown("## 🗑️ Deleted Bills")

    bills = run_query(
        """SELECT b.*, d.name as devotee_name, u.full_name as deleted_by_name
           FROM bill b LEFT JOIN devotee d ON b.devotee_id=d.id
           LEFT JOIN users u ON b.deleted_by=u.id
           WHERE b.is_deleted=TRUE ORDER BY b.deleted_at DESC""")

    if bills:
        import pandas as pd
        df = pd.DataFrame(bills)
        df['Date'] = df['bill_date'].apply(lambda x: x.strftime('%d/%m/%Y') if x else '-')
        df['Del Date'] = df['deleted_at'].apply(lambda x: x.strftime('%d/%m/%Y %I:%M %p') if x else '-')
        df['Name'] = df.apply(lambda r: r['devotee_name'] or r['guest_name'] or '-', axis=1)
        df['Amount'] = df['amount'].apply(lambda x: f"₹{x:,.2f}")
        st.dataframe(
            df[['bill_number', 'Date', 'Name', 'Amount', 'deleted_by_name', 'Del Date', 'delete_reason']].rename(
                columns={'bill_number': 'Bill No', 'deleted_by_name': 'Deleted By',
                         'Del Date': 'Deleted At', 'delete_reason': 'Reason'}),
            use_container_width=True, hide_index=True)
    else:
        st.info("No deleted bills")


# ============================================================
# MAIN APP ROUTER
# ============================================================
def main():
    init_session_state()
    load_css()

    if not st.session_state['logged_in']:
        login_page()
        return

    render_sidebar()

    page = st.session_state.get('current_page', 'dashboard')

    page_map = {
        'dashboard': page_dashboard,
        'devotees': page_devotees,
        'add_devotee': page_add_devotee,
        'view_devotee': page_view_devotee,
        'billing': page_billing,
        'new_bill': page_new_bill,
        'view_bill': page_view_bill,
        'print_bill': page_view_bill,
        'expenses': page_expenses,
        'reports': page_reports,
        'samaya': page_samaya,
        'add_samaya': page_add_samaya,
        'mandapam': page_mandapam,
        'add_mandapam': page_add_mandapam,
        'daily_pooja': page_daily_pooja,
        'settings': page_settings,
        'users': page_users,
        'deleted_bills': page_deleted_bills,
    }

    page_func = page_map.get(page, page_dashboard)
    page_func()


if __name__ == "__main__":
    main()
