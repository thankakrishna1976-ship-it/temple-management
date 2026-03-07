import streamlit as st
import bcrypt
from datetime import datetime, date, timedelta
from supabase import create_client, Client
import json
import base64
import os

# ============================================================
# PAGE CONFIG
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
TEMPLE_FULL_ADDRESS = f"{TEMPLE_NAME}, {TEMPLE_TRUST} - {TEMPLE_REG}, {TEMPLE_PLACE}, {TEMPLE_DISTRICT}"

NATCHATHIRAM_LIST = [
    'அசுவினி (Ashwini)', 'பரணி (Bharani)', 'கார்த்திகை (Krittika)',
    'ரோகிணி (Rohini)', 'மிருகசீரிடம் (Mrigashira)', 'திருவாதிரை (Ardra)',
    'புனர்பூசம் (Punarvasu)', 'பூசம் (Pushya)', 'ஆயில்யம் (Ashlesha)',
    'மகம் (Magha)', 'பூரம் (Purva Phalguni)', 'உத்திரம் (Uttara Phalguni)',
    'ஹஸ்தம் (Hasta)', 'சித்திரை (Chitra)', 'சுவாதி (Swati)',
    'விசாகம் (Vishakha)', 'அனுஷம் (Anuradha)', 'கேட்டை (Jyeshtha)',
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
# SUPABASE CONNECTION
# ============================================================
@st.cache_resource
def get_supabase_client():
    """Create and cache Supabase client"""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def get_db():
    """Get Supabase client"""
    return get_supabase_client()


# ============================================================
# PASSWORD HELPERS
# ============================================================
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def check_password(password: str, hashed: str) -> bool:
    """Check password against hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


# ============================================================
# DATABASE HELPER FUNCTIONS
# ============================================================
def init_default_data():
    """Initialize default data if tables are empty"""
    db = get_db()

    # Check if admin exists
    result = db.table('users').select('id').eq('username', 'admin').execute()
    if not result.data:
        admin_hash = hash_password('admin123')
        db.table('users').insert({
            'username': 'admin',
            'password_hash': admin_hash,
            'full_name': 'Administrator',
            'role': 'admin',
            'is_active_user': True
        }).execute()

    # Check pooja types
    result = db.table('pooja_type').select('id').execute()
    if not result.data:
        poojas = [
            {'name': 'அபிஷேகம் (Abhishekam)', 'amount': 100},
            {'name': 'அர்ச்ச���ை (Archanai)', 'amount': 50},
            {'name': 'சஹஸ்ரநாம அர்ச்சனை (Sahasranamam)', 'amount': 200},
            {'name': 'திரு���ிளக்கு பூஜை (Thiruvilakku)', 'amount': 150},
            {'name': 'கணபதி ஹோமம் (Ganapathi Homam)', 'amount': 500},
            {'name': 'நவக்கிரக பூஜை (Navagraha Pooja)', 'amount': 300},
            {'name': 'சந்தன கவசம் (Chandana Kavasam)', 'amount': 250},
            {'name': 'அன்னதானம் (Annadhanam)', 'amount': 1000},
        ]
        db.table('pooja_type').insert(poojas).execute()

    # Check expense types
    result = db.table('expense_type').select('id').execute()
    if not result.data:
        expenses = [
            {'name': 'பூ (Flowers)'}, {'name': 'எண்ணெய் (Oil)'},
            {'name': 'கற்பூரம் (Camphor)'}, {'name': 'மின்சாரம் (Electricity)'},
            {'name': 'நிர்வாகம் (Admin)'}, {'name': 'பராமரிப்பு (Maintenance)'},
            {'name': '��ம்பளம் (Salary)'}, {'name': 'இதர (Others)'},
        ]
        db.table('expense_type').insert(expenses).execute()

    # Check daily poojas
    result = db.table('daily_pooja').select('id').execute()
    if not result.data:
        daily = [
            {'pooja_name': 'சுப்ரபாதம்', 'pooja_time': '5:30 AM', 'description': 'Morning prayer'},
            {'pooja_name': 'காலை அபிஷேகம்', 'pooja_time': '6:00 AM', 'description': 'Morning bath'},
            {'pooja_name': 'காலை பூஜை', 'pooja_time': '7:00 AM', 'description': 'Morning worship'},
            {'pooja_name': 'உச்சிக்கால பூஜை', 'pooja_time': '12:00 PM', 'description': 'Noon'},
            {'pooja_name': 'சாயரக்ஷை', 'pooja_time': '6:00 PM', 'description': 'Evening'},
            {'pooja_name': 'அர்��்த ஜாம பூஜை', 'pooja_time': '8:00 PM', 'description': 'Night'},
        ]
        db.table('daily_pooja').insert(daily).execute()


# ============================================================
# CUSTOM CSS
# ============================================================
def apply_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Tamil:wght@400;600;700&display=swap');

        :root { --td: #8B0000; --tg: #FFD700; --tl: #FFF8DC; }

        .stApp {
            background: linear-gradient(135deg, #FFF8DC 0%, #FFEFD5 50%, #FFE4B5 100%);
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #8B0000 0%, #B22222 50%, #DC143C 100%) !important;
        }
        [data-testid="stSidebar"] * {
            color: #FFF8DC !important;
        }
        [data-testid="stSidebar"] .stSelectbox label,
        [data-testid="stSidebar"] .stRadio label {
            color: #FFD700 !important;
            font-weight: 600;
        }

        /* Header */
        .temple-header {
            background: linear-gradient(135deg, #8B0000, #DC143C);
            color: #FFD700;
            padding: 15px 25px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(139, 0, 0, 0.3);
        }
        .temple-header h1 { font-size: 1.5em; margin: 0; color: #FFD700; }
        .temple-header p { font-size: 0.85em; margin: 2px 0; color: #FFF8DC; opacity: 0.9; }

        /* Stat cards */
        .stat-card {
            border-radius: 15px;
            padding: 20px;
            color: white;
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
            text-align: center;
            margin-bottom: 15px;
        }
        .stat-income { background: linear-gradient(135deg, #228B22, #32CD32); }
        .stat-expense { background: linear-gradient(135deg, #DC143C, #FF4500); }
        .stat-devotees { background: linear-gradient(135deg, #4169E1, #6495ED); }
        .stat-bills { background: linear-gradient(135deg, #FF8C00, #FFD700); }
        .stat-card h3 { font-size: 1.8em; font-weight: 700; margin: 5px 0; }
        .stat-card p { font-size: 0.85em; opacity: 0.9; margin: 0; }

        /* Content card */
        .content-card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 15px rgba(0,0,0,0.08);
            padding: 20px;
            margin-bottom: 15px;
        }
        .content-card h3 {
            color: #8B0000;
            border-bottom: 2px solid #FFD700;
            padding-bottom: 8px;
            margin-bottom: 15px;
        }

        /* Pooja card */
        .pooja-card {
            background: linear-gradient(135deg, #FFF8DC, #FFEFD5);
            border: 1px solid #FFD700;
            border-radius: 10px;
            padding: 12px 15px;
            margin-bottom: 8px;
            border-left: 4px solid #8B0000;
        }
        .pooja-card strong { color: #8B0000; }
        .pooja-time { color: #8B0000; font-weight: 700; float: right; }

        /* Birthday card */
        .birthday-card {
            background: #FFF8DC;
            border-radius: 8px;
            padding: 10px 15px;
            margin-bottom: 8px;
            border-left: 3px solid #DC143C;
        }

        /* Bill header */
        .bill-header {
            text-align: center;
            border-bottom: 3px double #8B0000;
            padding-bottom: 15px;
            margin-bottom: 15px;
        }
        .bill-header h2 { color: #8B0000; font-size: 1.3em; margin: 0; }
        .bill-header h4 { color: #DC143C; font-size: 0.95em; margin: 2px 0; }
        .bill-header p { color: #555; font-size: 0.8em; margin: 1px 0; }

        /* Login card */
        .login-container {
            max-width: 450px;
            margin: 50px auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.15);
            text-align: center;
        }
        .login-container h2 { color: #8B0000; font-weight: 700; }
        .login-container p { color: #DC143C; font-size: 0.85em; }

        /* Button styles */
        .stButton > button {
            border-radius: 8px;
            font-weight: 600;
        }

        /* Table styling */
        .dataframe { border-radius: 8px; overflow: hidden; }
        .dataframe thead tr { background: linear-gradient(135deg, #8B0000, #DC143C) !important; }
        .dataframe thead th { color: white !important; font-weight: 600; }

        /* Badge */
        .badge-temple {
            background: #8B0000;
            color: #FFD700;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: 600;
        }

        /* News ticker */
        .ticker-container {
            background: linear-gradient(90deg, #8B0000, #DC143C, #8B0000);
            border-radius: 10px;
            padding: 10px 15px;
            overflow: hidden;
            margin-bottom: 20px;
        }
        .ticker-text {
            color: #FFD700;
            font-weight: 500;
            animation: ticker 20s linear infinite;
            white-space: nowrap;
        }
        @keyframes ticker {
            0% { transform: translateX(100%); }
            100% { transform: translateX(-100%); }
        }

        .deleted-badge {
            background: #DC143C;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.75em;
        }

        /* Hide Streamlit defaults */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
def init_session_state():
    """Initialize session state variables"""
    defaults = {
        'logged_in': False,
        'user_id': None,
        'username': None,
        'full_name': None,
        'role': None,
        'current_page': 'dashboard',
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ============================================================
# LOGIN PAGE
# ============================================================
def login_page():
    """Display login page"""
    st.markdown("""
    <div style="text-align:center; padding:20px;">
        <h1 style="color:#8B0000; font-size:2em;">🕉️</h1>
        <h2 style="color:#8B0000; margin:5px 0;">""" + TEMPLE_NAME + """</h2>
        <p style="color:#DC143C; font-weight:600;">""" + TEMPLE_TRUST + """ - """ + TEMPLE_REG + """</p>
        <p style="color:#888; font-size:0.85em;">""" + TEMPLE_PLACE + """, """ + TEMPLE_DISTRICT + """</p>
        <hr style="border-color:#FFD700; margin:15px auto; width:50%;">
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown("### 🔐 Please Login")

        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter password")
            submitted = st.form_submit_button("🕉️ Login", use_container_width=True)

            if submitted:
                if username and password:
                    db = get_db()
                    result = db.table('users').select('*').eq('username', username).eq('is_active_user', True).execute()
                    if result.data:
                        user = result.data[0]
                        if check_password(password, user['password_hash']):
                            st.session_state['logged_in'] = True
                            st.session_state['user_id'] = user['id']
                            st.session_state['username'] = user['username']
                            st.session_state['full_name'] = user['full_name'] or user['username']
                            st.session_state['role'] = user['role']
                            st.success("✅ Welcome back!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid credentials!")
                    else:
                        st.error("❌ Invalid credentials!")
                else:
                    st.warning("⚠️ Please enter username and password")

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('<p style="text-align:center;color:#aaa;font-size:0.8em;">🕉️ Temple Management System</p>', unsafe_allow_html=True)


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================
def sidebar_navigation():
    """Display sidebar with navigation"""
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center; padding:10px 0; border-bottom:2px solid rgba(255,215,0,0.3);">
            <h3 style="font-size:1.8em; margin:0;">🕉️</h3>
            <h4 style="color:#FFD700; font-size:0.85em; margin:5px 0;">{TEMPLE_NAME}</h4>
            <p style="color:rgba(255,215,0,0.7); font-size:0.7em;">{TEMPLE_TRUST}</p>
            <p style="color:rgba(255,215,0,0.7); font-size:0.65em;">{TEMPLE_PLACE}, {TEMPLE_DISTRICT}</p>
            <p style="color:#FFD700; font-size:0.75em; margin-top:8px;">
                👤 {st.session_state['full_name']}
                {'🔑 ADMIN' if st.session_state['role'] == 'admin' else ''}
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        menu_items = {
            "🏠 Dashboard": "dashboard",
            "👥 Devotees": "devotees",
            "🧾 Billing": "billing",
            "💰 Expenses": "expenses",
            "📊 Reports": "reports",
            "🎓 Samaya Vakuppu": "samaya",
            "🏛️ Thirumana Mandapam": "mandapam",
            "🙏 Daily Pooja": "daily_pooja",
            "⚙️ Settings": "settings",
        }

        if st.session_state['role'] == 'admin':
            menu_items["👤 User Management"] = "users"
            menu_items["🗑️ Deleted Bills"] = "deleted_bills"

        for label, page in menu_items.items():
            if st.button(label, key=f"nav_{page}", use_container_width=True):
                st.session_state['current_page'] = page
                st.rerun()

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.markdown(f"""
        <div style="text-align:center; padding-top:10px; font-size:0.7em; color:rgba(255,215,0,0.5);">
            📅 {datetime.now().strftime('%d %B %Y, %A')}
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# DASHBOARD PAGE
# ============================================================
def dashboard_page():
    db = get_db()

    # Temple Header
    st.markdown(f"""
    <div class="temple-header">
        <h1>🕉️ {TEMPLE_NAME}</h1>
        <p>{TEMPLE_TRUST} - {TEMPLE_REG}</p>
        <p>{TEMPLE_PLACE}, {TEMPLE_DISTRICT}</p>
    </div>
    """, unsafe_allow_html=True)

    # Period selection
    period = st.radio("📅 Select Period", ["Daily", "Weekly", "Monthly", "Yearly"],
                      horizontal=True, index=0)

    today_d = date.today()
    if period == "Daily":
        sd, ed = today_d, today_d
    elif period == "Weekly":
        sd = today_d - timedelta(days=today_d.weekday())
        ed = today_d
    elif period == "Monthly":
        sd = today_d.replace(day=1)
        ed = today_d
    else:
        sd = today_d.replace(month=1, day=1)
        ed = today_d

    # Get statistics
    bills_result = db.table('bill').select('amount').eq('is_deleted', False)\
        .gte('bill_date', sd.isoformat()).lte('bill_date', ed.isoformat() + 'T23:59:59').execute()
    total_income = sum(b['amount'] for b in bills_result.data) if bills_result.data else 0

    expenses_result = db.table('expense').select('amount')\
        .gte('expense_date', sd.isoformat()).lte('expense_date', ed.isoformat()).execute()
    total_expenses = sum(e['amount'] for e in expenses_result.data) if expenses_result.data else 0

    devotees_result = db.table('devotee').select('id', count='exact')\
        .eq('is_family_head', True).eq('is_active', True).execute()
    total_devotees = devotees_result.count or 0

    total_bills = len(bills_result.data) if bills_result.data else 0

    # Stat cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="stat-card stat-income">
            <p>📈 {period} Income</p>
            <h3>₹{total_income:,.2f}</h3>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-card stat-expense">
            <p>📉 {period} Expenses</p>
            <h3>₹{total_expenses:,.2f}</h3>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stat-card stat-devotees">
            <p>👥 Total Devotees</p>
            <h3>{total_devotees}</h3>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="stat-card stat-bills">
            <p>🧾 {period} Bills</p>
            <h3>{total_bills}</h3>
        </div>""", unsafe_allow_html=True)

    # Today's birthdays and pooja schedule
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("### 🙏 Today's Pooja Schedule")
        dp_result = db.table('daily_pooja').select('*').eq('is_active', True)\
            .order('pooja_time').execute()
        if dp_result.data:
            for p in dp_result.data:
                st.markdown(f"""
                <div class="pooja-card">
                    <strong>{p['pooja_name']}</strong>
                    <span class="pooja-time">{p.get('pooja_time', 'TBD')}</span>
                    <br><small style="color:#666;">{p.get('description', '')}</small>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No pooja scheduled")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("### 🎂 Today's Birthdays")

        # Get birthdays - query all devotees and filter in Python
        all_devotees = db.table('devotee').select('name, dob, mobile_no')\
            .eq('is_active', True).not_.is_('dob', 'null').execute()
        birthdays = []
        if all_devotees.data:
            for d in all_devotees.data:
                if d.get('dob'):
                    try:
                        dob = datetime.strptime(d['dob'], '%Y-%m-%d').date()
                        if dob.month == today_d.month and dob.day == today_d.day:
                            birthdays.append(d)
                    except (ValueError, TypeError):
                        pass

        if birthdays:
            # Ticker
            ticker_text = " 🎂 ".join([f"Happy Birthday {d['name']}!" for d in birthdays])
            st.markdown(f"""
            <div class="ticker-container">
                <div class="ticker-text">🎂 {ticker_text} 🎂</div>
            </div>""", unsafe_allow_html=True)
            for d in birthdays:
                st.markdown(f"""
                <div class="birthday-card">
                    🎂 <strong>{d['name']}</strong> - {d.get('mobile_no', '')}
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No birthdays today")
        st.markdown('</div>', unsafe_allow_html=True)

    # Recent bills
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown("### 🧾 Recent Bills")
    recent_bills = db.table('bill').select('*, devotee(name), pooja_type(name)')\
        .eq('is_deleted', False).order('bill_date', desc=True).limit(10).execute()
    if recent_bills.data:
        import pandas as pd
        bill_data = []
        for b in recent_bills.data:
            bill_data.append({
                'Bill No': b.get('bill_number', '-'),
                'Date': b.get('bill_date', '-')[:10] if b.get('bill_date') else '-',
                'Name': b.get('devotee', {}).get('name', '') if b.get('devotee') else b.get('guest_name', '-'),
                'Pooja': b.get('pooja_type', {}).get('name', '-') if b.get('pooja_type') else '-',
                'Amount': f"₹{b.get('amount', 0):,.2f}"
            })
        st.dataframe(pd.DataFrame(bill_data), use_container_width=True, hide_index=True)
    else:
        st.info("No bills yet")
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# DEVOTEES PAGE
# ============================================================
def devotees_page():
    db = get_db()

    st.markdown("### 👥 Enrolled Devotees")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ Add New Devotee", use_container_width=True):
            st.session_state['current_page'] = 'add_devotee'
            st.session_state['edit_devotee_id'] = None
            st.rerun()

    with col1:
        search = st.text_input("🔍 Search devotees", placeholder="Search by name, mobile...")

    # Fetch devotees
    query = db.table('devotee').select('*').eq('is_family_head', True).eq('is_active', True)\
        .order('name')
    if search:
        query = query.or_(f"name.ilike.%{search}%,mobile_no.ilike.%{search}%")
    result = query.execute()

    if result.data:
        import pandas as pd
        for d in result.data:
            # Count family members
            fm_count = db.table('devotee').select('id', count='exact')\
                .eq('family_head_id', d['id']).execute()
            family_count = fm_count.count or 0

            with st.expander(f"**{d['name']}** | 📱 {d.get('mobile_no', '-')} | ⭐ {d.get('natchathiram', '-')} | 👨‍👩‍👧‍👦 Family: {family_count}"):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"**DOB:** {d.get('dob', '-')}")
                    st.write(f"**Mobile:** {d.get('mobile_no', '-')}")
                    st.write(f"**WhatsApp:** {d.get('whatsapp_no', '-')}")
                with col2:
                    st.write(f"**Natchathiram:** {d.get('natchathiram', '-')}")
                    st.write(f"**Wedding Day:** {d.get('wedding_day', '-')}")
                    st.write(f"**Address:** {d.get('address', '-')}")
                with col3:
                    if st.button("✏️ Edit", key=f"edit_{d['id']}"):
                        st.session_state['current_page'] = 'add_devotee'
                        st.session_state['edit_devotee_id'] = d['id']
                        st.rerun()
                    if st.button("👁️ View", key=f"view_{d['id']}"):
                        st.session_state['current_page'] = 'view_devotee'
                        st.session_state['view_devotee_id'] = d['id']
                        st.rerun()
                    if st.button("🗑️ Delete", key=f"del_{d['id']}"):
                        # Delete family members first
                        db.table('devotee').delete().eq('family_head_id', d['id']).execute()
                        db.table('devotee_yearly_pooja').delete().eq('devotee_id', d['id']).execute()
                        db.table('devotee').delete().eq('id', d['id']).execute()
                        st.success("Deleted!")
                        st.rerun()

                # Show family members
                fm_result = db.table('devotee').select('*').eq('family_head_id', d['id']).execute()
                if fm_result.data:
                    st.markdown("**👨‍👩‍👧‍👦 Family Members:**")
                    fm_data = []
                    for fm in fm_result.data:
                        fm_data.append({
                            'Name': fm['name'],
                            'Relation': fm.get('relation_type', '-'),
                            'DOB': fm.get('dob', '-'),
                            'Star': fm.get('natchathiram', '-'),
                            'Mobile': fm.get('mobile_no', '-')
                        })
                    st.dataframe(pd.DataFrame(fm_data), use_container_width=True, hide_index=True)

                # Show yearly poojas
                yp_result = db.table('devotee_yearly_pooja').select('*, pooja_type(name)')\
                    .eq('devotee_id', d['id']).execute()
                if yp_result.data:
                    st.markdown("**🙏 Yearly Poojas:**")
                    for yp in yp_result.data:
                        pooja_name = yp.get('pooja_type', {}).get('name', '') if yp.get('pooja_type') else yp.get('pooja_name', '-')
                        st.write(f"  - {pooja_name} | Date: {yp.get('pooja_date', '-')} | {yp.get('notes', '')}")
    else:
        st.info("No devotees found. Click 'Add New Devotee' to get started.")


# ============================================================
# ADD/EDIT DEVOTEE PAGE
# ============================================================
def add_devotee_page():
    db = get_db()
    edit_id = st.session_state.get('edit_devotee_id')
    devotee_data = None

    if edit_id:
        result = db.table('devotee').select('*').eq('id', edit_id).execute()
        if result.data:
            devotee_data = result.data[0]
        st.markdown(f"### ✏️ Edit Devotee (ID: {edit_id})")
    else:
        st.markdown("### ➕ Add New Devotee")

    # Back button
    if st.button("⬅️ Back to Devotees"):
        st.session_state['current_page'] = 'devotees'
        st.rerun()

    with st.form("devotee_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name *", value=devotee_data.get('name', '') if devotee_data else '')
            dob = st.date_input("Date of Birth",
                value=datetime.strptime(devotee_data['dob'], '%Y-%m-%d').date() if devotee_data and devotee_data.get('dob') else None,
                min_value=date(1900, 1, 1), max_value=date.today(), value=None if not devotee_data or not devotee_data.get('dob') else None)
            mobile = st.text_input("Mobile", value=devotee_data.get('mobile_no', '') if devotee_data else '')
            relation = st.selectbox("Relation", [''] + RELATION_TYPES,
                index=RELATION_TYPES.index(devotee_data['relation_type'])+1 if devotee_data and devotee_data.get('relation_type') in RELATION_TYPES else 0)

        with col2:
            whatsapp = st.text_input("WhatsApp", value=devotee_data.get('whatsapp_no', '') if devotee_data else '')
            wedding = st.date_input("Wedding Day",
                value=datetime.strptime(devotee_data['wedding_day'], '%Y-%m-%d').date() if devotee_data and devotee_data.get('wedding_day') else None,
                min_value=date(1900, 1, 1), value=None if not devotee_data or not devotee_data.get('wedding_day') else None)
            natchathiram = st.selectbox("Natchathiram", [''] + NATCHATHIRAM_LIST,
                index=NATCHATHIRAM_LIST.index(devotee_data['natchathiram'])+1 if devotee_data and devotee_data.get('natchathiram') in NATCHATHIRAM_LIST else 0)
            address = st.text_area("Address", value=devotee_data.get('address', '') if devotee_data else '')

        st.markdown("---")
        st.markdown("#### 👨‍👩‍👧‍👦 Family Members")
        st.markdown("*Add family members below (up to 10)*")

        # Get existing family members if editing
        existing_fm = []
        if edit_id:
            fm_result = db.table('devotee').select('*').eq('family_head_id', edit_id).execute()
            if fm_result.data:
                existing_fm = fm_result.data

        num_family = st.number_input("Number of family members", min_value=0, max_value=10,
            value=len(existing_fm) if existing_fm else 0)

        family_members = []
        for i in range(int(num_family)):
            st.markdown(f"**Family Member {i+1}**")
            fc1, fc2, fc3, fc4, fc5 = st.columns(5)
            with fc1:
                fm_name = st.text_input(f"Name", key=f"fm_name_{i}",
                    value=existing_fm[i]['name'] if i < len(existing_fm) else '')
            with fc2:
                fm_dob = st.date_input(f"DOB", key=f"fm_dob_{i}",
                    value=datetime.strptime(existing_fm[i]['dob'], '%Y-%m-%d').date() if i < len(existing_fm) and existing_fm[i].get('dob') else None,
                    min_value=date(1900, 1, 1), max_value=date.today(),
                    value=None if i >= len(existing_fm) or not existing_fm[i].get('dob') else None)
            with fc3:
                fm_rel = st.selectbox(f"Relation", [''] + RELATION_TYPES, key=f"fm_rel_{i}",
                    index=RELATION_TYPES.index(existing_fm[i]['relation_type'])+1 if i < len(existing_fm) and existing_fm[i].get('relation_type') in RELATION_TYPES else 0)
            with fc4:
                fm_star = st.selectbox(f"Star", [''] + NATCHATHIRAM_LIST, key=f"fm_star_{i}",
                    index=NATCHATHIRAM_LIST.index(existing_fm[i]['natchathiram'])+1 if i < len(existing_fm) and existing_fm[i].get('natchathiram') in NATCHATHIRAM_LIST else 0)
            with fc5:
                fm_mobile = st.text_input(f"Mobile", key=f"fm_mobile_{i}",
                    value=existing_fm[i].get('mobile_no', '') if i < len(existing_fm) else '')

            if fm_name.strip():
                family_members.append({
                    'name': fm_name,
                    'dob': fm_dob.isoformat() if fm_dob else None,
                    'relation_type': fm_rel if fm_rel else None,
                    'natchathiram': fm_star if fm_star else None,
                    'mobile_no': fm_mobile if fm_mobile else None,
                    'existing_id': existing_fm[i]['id'] if i < len(existing_fm) else None
                })

        st.markdown("---")
        st.markdown("#### 🙏 Yearly Poojas")

        # Get pooja types
        pt_result = db.table('pooja_type').select('*').eq('is_active', True).execute()
        pooja_types = pt_result.data if pt_result.data else []
        pt_names = [''] + [pt['name'] for pt in pooja_types]
        pt_map = {pt['name']: pt['id'] for pt in pooja_types}

        # Get existing yearly poojas
        existing_yp = []
        if edit_id:
            yp_result = db.table('devotee_yearly_pooja').select('*, pooja_type(name)')\
                .eq('devotee_id', edit_id).execute()
            if yp_result.data:
                existing_yp = yp_result.data

        num_yp = st.number_input("Number of yearly poojas", min_value=0, max_value=20,
            value=len(existing_yp) if existing_yp else 0)

        yearly_poojas = []
        for i in range(int(num_yp)):
            yc1, yc2, yc3 = st.columns(3)
            with yc1:
                existing_pt_name = existing_yp[i].get('pooja_type', {}).get('name', '') if i < len(existing_yp) and existing_yp[i].get('pooja_type') else ''
                yp_type = st.selectbox(f"Pooja Type {i+1}", pt_names, key=f"yp_type_{i}",
                    index=pt_names.index(existing_pt_name) if existing_pt_name in pt_names else 0)
            with yc2:
                yp_date = st.date_input(f"Date {i+1}", key=f"yp_date_{i}",
                    value=datetime.strptime(existing_yp[i]['pooja_date'], '%Y-%m-%d').date() if i < len(existing_yp) and existing_yp[i].get('pooja_date') else None,
                    value=None if i >= len(existing_yp) or not existing_yp[i].get('pooja_date') else None)
            with yc3:
                yp_notes = st.text_input(f"Notes {i+1}", key=f"yp_notes_{i}",
                    value=existing_yp[i].get('notes', '') if i < len(existing_yp) else '')

            if yp_type:
                yearly_poojas.append({
                    'pooja_type_id': pt_map.get(yp_type),
                    'pooja_name': yp_type,
                    'pooja_date': yp_date.isoformat() if yp_date else None,
                    'notes': yp_notes if yp_notes else None
                })

        submitted = st.form_submit_button("💾 Save Devotee", use_container_width=True)

        if submitted:
            if not name.strip():
                st.error("❌ Name is required!")
            else:
                devotee_record = {
                    'name': name.strip(),
                    'dob': dob.isoformat() if dob else None,
                    'relation_type': relation if relation else None,
                    'mobile_no': mobile if mobile else None,
                    'whatsapp_no': whatsapp if whatsapp else None,
                    'wedding_day': wedding.isoformat() if wedding else None,
                    'natchathiram': natchathiram if natchathiram else None,
                    'address': address if address else None,
                    'is_family_head': True,
                    'is_active': True
                }

                if edit_id:
                    db.table('devotee').update(devotee_record).eq('id', edit_id).execute()
                    devotee_id = edit_id

                    # Delete old family members and re-add
                    db.table('devotee').delete().eq('family_head_id', edit_id).execute()
                    # Delete old yearly poojas
                    db.table('devotee_yearly_pooja').delete().eq('devotee_id', edit_id).execute()
                else:
                    result = db.table('devotee').insert(devotee_record).execute()
                    devotee_id = result.data[0]['id']

                # Add family members
                for fm in family_members:
                    fm_record = {
                        'name': fm['name'],
                        'dob': fm['dob'],
                        'relation_type': fm['relation_type'],
                        'natchathiram': fm['natchathiram'],
                        'mobile_no': fm['mobile_no'],
                        'is_family_head': False,
                        'family_head_id': devotee_id,
                        'address': address if address else None,
                        'is_active': True
                    }
                    db.table('devotee').insert(fm_record).execute()

                # Add yearly poojas
                for yp in yearly_poojas:
                    yp_record = {
                        'devotee_id': devotee_id,
                        'pooja_type_id': yp['pooja_type_id'],
                        'pooja_name': yp['pooja_name'],
                        'pooja_date': yp['pooja_date'],
                        'notes': yp['notes']
                    }
                    db.table('devotee_yearly_pooja').insert(yp_record).execute()

                st.success(f"✅ Devotee {'updated' if edit_id else 'added'} successfully!")
                st.session_state['current_page'] = 'devotees'
                st.session_state['edit_devotee_id'] = None
                st.rerun()


# ============================================================
# VIEW DEVOTEE PAGE
# ============================================================
def view_devotee_page():
    db = get_db()
    devotee_id = st.session_state.get('view_devotee_id')

    if not devotee_id:
        st.session_state['current_page'] = 'devotees'
        st.rerun()
        return

    result = db.table('devotee').select('*').eq('id', devotee_id).execute()
    if not result.data:
        st.error("Devotee not found!")
        return

    d = result.data[0]

    if st.button("⬅️ Back to Devotees"):
        st.session_state['current_page'] = 'devotees'
        st.rerun()

    st.markdown(f"""
    <div class="content-card">
        <h3>👤 {d['name']}</h3>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**📅 DOB:** {d.get('dob', '-')}")
        st.write(f"**📱 Mobile:** {d.get('mobile_no', '-')}")
        st.write(f"**💬 WhatsApp:** {d.get('whatsapp_no', '-')}")
        st.write(f"**👤 Relation:** {d.get('relation_type', '-')}")
    with col2:
        st.write(f"**⭐ Natchathiram:** {d.get('natchathiram', '-')}")
        st.write(f"**💍 Wedding Day:** {d.get('wedding_day', '-')}")
        st.write(f"**📍 Address:** {d.get('address', '-')}")

    # Family members
    st.markdown("---")
    st.markdown("### 👨‍👩���👧‍👦 Family Members")
    fm_result = db.table('devotee').select('*').eq('family_head_id', devotee_id).execute()
    if fm_result.data:
        import pandas as pd
        fm_data = [{'Name': fm['name'], 'Relation': fm.get('relation_type', '-'),
                     'DOB': fm.get('dob', '-'), 'Star': fm.get('natchathiram', '-'),
                     'Mobile': fm.get('mobile_no', '-')} for fm in fm_result.data]
        st.dataframe(pd.DataFrame(fm_data), use_container_width=True, hide_index=True)
    else:
        st.info("No family members")

    # Yearly poojas
    st.markdown("### 🙏 Yearly Poojas")
    yp_result = db.table('devotee_yearly_pooja').select('*, pooja_type(name)')\
        .eq('devotee_id', devotee_id).execute()
    if yp_result.data:
        for yp in yp_result.data:
            pooja_name = yp.get('pooja_type', {}).get('name', '') if yp.get('pooja_type') else yp.get('pooja_name', '-')
            st.markdown(f"""
            <div class="pooja-card">
                <strong>{pooja_name}</strong>
                <span class="pooja-time">{yp.get('pooja_date', '-')}</span>
                <br><small>{yp.get('notes', '')}</small>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("No yearly poojas")

    # Bills
    st.markdown("### 🧾 Bills")
    bills_result = db.table('bill').select('*, pooja_type(name)')\
        .eq('devotee_id', devotee_id).eq('is_deleted', False).order('bill_date', desc=True).execute()
    if bills_result.data:
        import pandas as pd
        bill_data = [{'Bill No': b.get('bill_number', '-'),
                       'Date': b.get('bill_date', '-')[:10] if b.get('bill_date') else '-',
                       'Pooja': b.get('pooja_type', {}).get('name', '-') if b.get('pooja_type') else '-',
                       'Amount': f"₹{b.get('amount', 0):,.2f}"} for b in bills_result.data]
        st.dataframe(pd.DataFrame(bill_data), use_container_width=True, hide_index=True)
    else:
        st.info("No bills")


# ============================================================
# BILLING PAGE
# ============================================================
def billing_page():
    db = get_db()

    st.markdown("### 🧾 Bills")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ New Bill", use_container_width=True):
            st.session_state['current_page'] = 'new_bill'
            st.rerun()

    # Date filter
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        from_date = st.date_input("From Date", value=date.today())
    with col2:
        to_date = st.date_input("To Date", value=date.today())

    # Fetch bills
    bills = db.table('bill').select('*, devotee(name), pooja_type(name)')\
        .gte('bill_date', from_date.isoformat())\
        .lte('bill_date', to_date.isoformat() + 'T23:59:59')\
        .order('bill_date', desc=True).execute()

    if bills.data:
        import pandas as pd
        total_amount = 0
        for b in bills.data:
            is_deleted = b.get('is_deleted', False)
            status = "🗑️ Deleted" if is_deleted else "✅ Active"
            devotee_name = b.get('devotee', {}).get('name', '') if b.get('devotee') else b.get('guest_name', '-')
            pooja_name = b.get('pooja_type', {}).get('name', '-') if b.get('pooja_type') else '-'
            amount = b.get('amount', 0)

            if not is_deleted:
                total_amount += amount

            with st.expander(f"{'~~' if is_deleted else ''}{b.get('bill_number', '-')} | {devotee_name} | {pooja_name} | ₹{amount:,.2f} | {status}{'~~' if is_deleted else ''}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Bill No:** {b.get('bill_number', '-')}")
                    st.write(f"**Manual Bill:** {b.get('manual_bill_no', '-')}")
                    st.write(f"**Date:** {b.get('bill_date', '-')[:16] if b.get('bill_date') else '-'}")
                    st.write(f"**Type:** {'Enrolled' if b.get('devotee_type') == 'enrolled' else 'Guest'}")
                with col2:
                    st.write(f"**Name:** {devotee_name}")
                    st.write(f"**Pooja:** {pooja_name}")
                    st.write(f"**Amount:** ₹{amount:,.2f}")
                    st.write(f"**Notes:** {b.get('notes', '-')}")

                if not is_deleted:
                    bc1, bc2, bc3 = st.columns(3)
                    with bc1:
                        if st.button("🖨️ Print", key=f"print_{b['id']}"):
                            st.session_state['print_bill_id'] = b['id']
                            st.session_state['current_page'] = 'view_bill'
                            st.rerun()
                    with bc3:
                        if st.session_state['role'] == 'admin':
                            reason = st.text_input("Delete reason", key=f"reason_{b['id']}")
                            if st.button("🗑️ Delete Bill", key=f"delbill_{b['id']}"):
                                if reason.strip():
                                    db.table('bill').update({
                                        'is_deleted': True,
                                        'deleted_by': st.session_state['user_id'],
                                        'deleted_at': datetime.now().isoformat(),
                                        'delete_reason': reason
                                    }).eq('id', b['id']).execute()
                                    st.success("Bill deleted!")
                                    st.rerun()
                                else:
                                    st.warning("Please enter a reason!")

        st.markdown(f"""
        <div style="text-align:right; padding:10px; font-size:1.2em;">
            <strong style="color:#8B0000;">Total Active: ₹{total_amount:,.2f}</strong>
        </div>""", unsafe_allow_html=True)
    else:
        st.info("No bills found for selected date range")


# ============================================================
# NEW BILL PAGE
# ============================================================
def new_bill_page():
    db = get_db()

    st.markdown("### 🧾 New Bill")

    if st.button("⬅️ Back to Bills"):
        st.session_state['current_page'] = 'billing'
        st.rerun()

    # Get next bill number
    last_bill = db.table('bill').select('id').order('id', desc=True).limit(1).execute()
    next_id = (last_bill.data[0]['id'] + 1) if last_bill.data else 1
    next_bill_no = f"BILL-{next_id:06d}"

    with st.form("new_bill_form"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            bill_number = st.text_input("Bill Number", value=next_bill_no, disabled=True)
        with col2:
            manual_bill_no = st.text_input("Manual Bill No")
        with col3:
            bill_book_no = st.text_input("Bill Book No")
        with col4:
            bill_date = st.date_input("Date", value=date.today())
            bill_time = st.time_input("Time", value=datetime.now().time())

        st.markdown("---")

        devotee_type = st.radio("Devotee Type", ["Enrolled", "Guest"], horizontal=True)

        if devotee_type == "Enrolled":
            devotees_list = db.table('devotee').select('id, name, mobile_no, address')\
                .eq('is_family_head', True).eq('is_active', True).order('name').execute()
            if devotees_list.data:
                devotee_options = {f"{d['name']} (ID:{d['id']})": d for d in devotees_list.data}
                selected = st.selectbox("Select Devotee *", [''] + list(devotee_options.keys()))
                if selected:
                    d = devotee_options[selected]
                    st.info(f"📱 Mobile: {d.get('mobile_no', '-')} | 📍 Address: {d.get('address', '-')}")
                    devotee_id = d['id']
                else:
                    devotee_id = None
            else:
                st.warning("No enrolled devotees found")
                devotee_id = None
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

        st.markdown("---")

        # Pooja selection
        pt_result = db.table('pooja_type').select('*').eq('is_active', True).execute()
        pooja_types = pt_result.data if pt_result.data else []
        pt_options = {f"{pt['name']} (₹{pt['amount']})": pt for pt in pooja_types}

        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            selected_pooja = st.selectbox("Pooja Type *", [''] + list(pt_options.keys()))
        with pc2:
            default_amount = pt_options[selected_pooja]['amount'] if selected_pooja else 0
            amount = st.number_input("Amount *", min_value=0.0, value=float(default_amount), step=1.0)
        with pc3:
            notes = st.text_input("Notes")

        submitted = st.form_submit_button("💾 Create Bill", use_container_width=True)

        if submitted:
            if devotee_type == "Enrolled" and not devotee_id:
                st.error("❌ Please select a devotee!")
            elif devotee_type == "Guest" and not (guest_name and guest_name.strip()):
                st.error("❌ Please enter guest name!")
            elif not selected_pooja:
                st.error("❌ Please select a pooja type!")
            elif amount <= 0:
                st.error("❌ Amount must be greater than 0!")
            else:
                bill_datetime = datetime.combine(bill_date, bill_time).isoformat()
                bill_record = {
                    'bill_number': next_bill_no,
                    'manual_bill_no': manual_bill_no if manual_bill_no else None,
                    'bill_book_no': bill_book_no if bill_book_no else None,
                    'bill_date': bill_datetime,
                    'devotee_type': 'enrolled' if devotee_type == "Enrolled" else 'guest',
                    'devotee_id': devotee_id if devotee_type == "Enrolled" else None,
                    'guest_name': guest_name if devotee_type == "Guest" else None,
                    'guest_address': guest_address if devotee_type == "Guest" else None,
                    'guest_mobile': guest_mobile if devotee_type == "Guest" else None,
                    'guest_whatsapp': guest_whatsapp if devotee_type == "Guest" else None,
                    'pooja_type_id': pt_options[selected_pooja]['id'],
                    'amount': amount,
                    'notes': notes if notes else None,
                    'created_by': st.session_state['user_id'],
                    'is_deleted': False
                }
                result = db.table('bill').insert(bill_record).execute()
                st.success(f"✅ Bill {next_bill_no} created successfully!")
                st.session_state['print_bill_id'] = result.data[0]['id']
                st.session_state['current_page'] = 'view_bill'
                st.rerun()


# ============================================================
# VIEW/PRINT BILL PAGE
# ============================================================
def view_bill_page():
    db = get_db()
    bill_id = st.session_state.get('print_bill_id')

    if not bill_id:
        st.session_state['current_page'] = 'billing'
        st.rerun()
        return

    result = db.table('bill').select('*, devotee(name, mobile_no, address), pooja_type(name)')\
        .eq('id', bill_id).execute()

    if not result.data:
        st.error("Bill not found!")
        return

    b = result.data[0]

    if st.button("⬅️ Back to Bills"):
        st.session_state['current_page'] = 'billing'
        st.rerun()

    # Bill display
    devotee_name = b.get('devotee', {}).get('name', '') if b.get('devotee') else b.get('guest_name', '-')
    devotee_mobile = b.get('devotee', {}).get('mobile_no', '') if b.get('devotee') else b.get('guest_mobile', '-')
    devotee_address = b.get('devotee', {}).get('address', '') if b.get('devotee') else b.get('guest_address', '-')
    pooja_name = b.get('pooja_type', {}).get('name', '-') if b.get('pooja_type') else '-'

    bill_html = f"""
    <div style="background:white; padding:30px; border-radius:12px; box-shadow:0 2px 15px rgba(0,0,0,0.1); max-width:700px; margin:auto;">
        <div class="bill-header">
            <h2>🕉️ {TEMPLE_NAME}</h2>
            <h4>{TEMPLE_TRUST} - {TEMPLE_REG}</h4>
            <p>{TEMPLE_PLACE}, {TEMPLE_DISTRICT}</p>
            <p>📞 Temple Office | <strong>BILL RECEIPT</strong></p>
        </div>

        <table style="width:100%; margin:10px 0; font-size:0.9em;">
            <tr>
                <td><strong>Bill No:</strong> {b.get('bill_number', '-')}</td>
                <td><strong>Manual Bill:</strong> {b.get('manual_bill_no', '-')}</td>
            </tr>
            <tr>
                <td><strong>Date:</strong> {b.get('bill_date', '-')[:16] if b.get('bill_date') else '-'}</td>
                <td><strong>Bill Book:</strong> {b.get('bill_book_no', '-')}</td>
            </tr>
        </table>

        <hr style="border-color:#FFD700;">

        <table style="width:100%; margin:10px 0; font-size:0.9em;">
            <tr><td><strong>Name:</strong> {devotee_name}</td></tr>
            <tr><td><strong>Mobile:</strong> {devotee_mobile}</td></tr>
            <tr><td><strong>Address:</strong> {devotee_address}</td></tr>
        </table>

        <hr style="border-color:#FFD700;">

        <table style="width:100%; border-collapse:collapse; margin:15px 0;">
            <thead>
                <tr style="background:linear-gradient(135deg,#8B0000,#DC143C); color:white;">
                    <th style="padding:8px; text-align:left; border:1px solid #ddd;">Pooja Type</th>
                    <th style="padding:8px; text-align:left; border:1px solid #ddd;">Notes</th>
                    <th style="padding:8px; text-align:right; border:1px solid #ddd;">Amount</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="padding:8px; border:1px solid #ddd;">{pooja_name}</td>
                    <td style="padding:8px; border:1px solid #ddd;">{b.get('notes', '-')}</td>
                    <td style="padding:8px; text-align:right; border:1px solid #ddd;">��{b.get('amount', 0):,.2f}</td>
                </tr>
            </tbody>
            <tfoot>
                <tr>
                    <td colspan="2" style="padding:8px; text-align:right; border:1px solid #ddd;"><strong>Total:</strong></td>
                    <td style="padding:8px; text-align:right; border:1px solid #ddd; color:#8B0000; font-size:1.2em;"><strong>₹{b.get('amount', 0):,.2f}</strong></td>
                </tr>
            </tfoot>
        </table>

        <div style="text-align:center; margin-top:15px; padding-top:10px; border-top:1px dashed #ccc;">
            <small style="color:#888;">{TEMPLE_FULL_ADDRESS}</small><br>
            <small style="color:#888;">🕉�� Thank you for your contribution 🙏</small>
        </div>
    </div>
    """

    st.markdown(bill_html, unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("*Use your browser's print function (Ctrl+P) to print this bill*")


# ============================================================
# EXPENSES PAGE
# ============================================================
def expenses_page():
    db = get_db()

    st.markdown("### 💰 Expenses")

    # Date filter
    col1, col2 = st.columns(2)
    with col1:
        from_date = st.date_input("From", value=date.today().replace(day=1), key="exp_from")
    with col2:
        to_date = st.date_input("To", value=date.today(), key="exp_to")

    # Add expense form
    with st.expander("➕ Add New Expense"):
        et_result = db.table('expense_type').select('*').eq('is_active', True).execute()
        expense_types = et_result.data if et_result.data else []
        et_options = {et['name']: et['id'] for et in expense_types}

        with st.form("expense_form"):
            ec1, ec2, ec3 = st.columns(3)
            with ec1:
                exp_type = st.selectbox("Type *", list(et_options.keys()) if et_options else [])
            with ec2:
                exp_amount = st.number_input("Amount *", min_value=0.01, step=1.0)
            with ec3:
                exp_date = st.date_input("Date", value=date.today(), key="new_exp_date")
            exp_desc = st.text_area("Description", height=68)

            if st.form_submit_button("💾 Save Expense"):
                if exp_type and exp_amount > 0:
                    db.table('expense').insert({
                        'expense_type_id': et_options[exp_type],
                        'amount': exp_amount,
                        'description': exp_desc if exp_desc else None,
                        'expense_date': exp_date.isoformat(),
                        'created_by': st.session_state['user_id']
                    }).execute()
                    st.success("✅ Expense added!")
                    st.rerun()
                else:
                    st.error("❌ Please fill required fields!")

    # List expenses
    expenses = db.table('expense').select('*, expense_type(name)')\
        .gte('expense_date', from_date.isoformat())\
        .lte('expense_date', to_date.isoformat())\
        .order('expense_date', desc=True).execute()

    if expenses.data:
        import pandas as pd
        total = 0
        exp_data = []
        for e in expenses.data:
            total += e.get('amount', 0)
            exp_data.append({
                'ID': e['id'],
                'Date': e.get('expense_date', '-'),
                'Type': e.get('expense_type', {}).get('name', '-') if e.get('expense_type') else '-',
                'Description': e.get('description', '-'),
                'Amount': f"₹{e.get('amount', 0):,.2f}"
            })
        st.dataframe(pd.DataFrame(exp_data), use_container_width=True, hide_index=True)

        st.markdown(f"""
        <div style="text-align:right; font-size:1.2em;">
            <strong style="color:#DC143C;">Total: ₹{total:,.2f}</strong>
        </div>""", unsafe_allow_html=True)

        # Delete expense
        st.markdown("---")
        del_id = st.number_input("Enter Expense ID to delete", min_value=0, step=1)
        if st.button("🗑️ Delete Expense") and del_id > 0:
            db.table('expense').delete().eq('id', int(del_id)).execute()
            st.success("Deleted!")
            st.rerun()
    else:
        st.info("No expenses found")


# ============================================================
# REPORTS PAGE
# ============================================================
def reports_page():
    db = get_db()

    st.markdown("### 📊 Reports")

    col1, col2 = st.columns(2)
    with col1:
        from_date = st.date_input("From", value=date.today().replace(day=1), key="rpt_from")
    with col2:
        to_date = st.date_input("To", value=date.today(), key="rpt_to")

    # Income
    bills = db.table('bill').select('amount, pooja_type(name)')\
        .eq('is_deleted', False)\
        .gte('bill_date', from_date.isoformat())\
        .lte('bill_date', to_date.isoformat() + 'T23:59:59').execute()

    total_income = sum(b['amount'] for b in bills.data) if bills.data else 0

    # Expenses
    expenses = db.table('expense').select('amount, expense_type(name)')\
        .gte('expense_date', from_date.isoformat())\
        .lte('expense_date', to_date.isoformat()).execute()

    total_expenses = sum(e['amount'] for e in expenses.data) if expenses.data else 0

    # Summary cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="stat-card stat-income">
            <p>📈 Total Income</p><h3>₹{total_income:,.2f}</h3>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-card stat-expense">
            <p>📉 Total Expenses</p><h3>₹{total_expenses:,.2f}</h3>
        </div>""", unsafe_allow_html=True)
    with col3:
        net = total_income - total_expenses
        bg = "stat-income" if net >= 0 else "stat-expense"
        st.markdown(f"""
        <div class="stat-card" style="background:linear-gradient(135deg,#4B0082,#8A2BE2);">
            <p>💰 Net Balance</p><h3>₹{net:,.2f}</h3>
        </div>""", unsafe_allow_html=True)

    # Income by pooja type
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("#### 🙏 Income by Pooja Type")
        if bills.data:
            import pandas as pd
            from collections import Counter, defaultdict
            pooja_income = defaultdict(lambda: {'count': 0, 'total': 0})
            for b in bills.data:
                name = b.get('pooja_type', {}).get('name', 'Other') if b.get('pooja_type') else 'Other'
                pooja_income[name]['count'] += 1
                pooja_income[name]['total'] += b['amount']
            pi_data = [{'Pooja': k, 'Count': v['count'], 'Amount': f"₹{v['total']:,.2f}"}
                       for k, v in pooja_income.items()]
            st.dataframe(pd.DataFrame(pi_data), use_container_width=True, hide_index=True)

    with col_r:
        st.markdown("#### 💸 Expenses by Type")
        if expenses.data:
            import pandas as pd
            from collections import defaultdict
            exp_by_type = defaultdict(lambda: {'count': 0, 'total': 0})
            for e in expenses.data:
                name = e.get('expense_type', {}).get('name', 'Other') if e.get('expense_type') else 'Other'
                exp_by_type[name]['count'] += 1
                exp_by_type[name]['total'] += e['amount']
            et_data = [{'Type': k, 'Count': v['count'], 'Amount': f"₹{v['total']:,.2f}"}
                       for k, v in exp_by_type.items()]
            st.dataframe(pd.DataFrame(et_data), use_container_width=True, hide_index=True)


# ============================================================
# SAMAYA VAKUPPU PAGE
# ============================================================
def samaya_page():
    db = get_db()

    st.markdown("### 🎓 Samaya Vakuppu")

    # Add form
    with st.expander("➕ Add New Student"):
        with st.form("samaya_form"):
            sc1, sc2 = st.columns(2)
            with sc1:
                s_name = st.text_input("Student Name *")
                s_dob = st.date_input("DOB", value=None, min_value=date(1990, 1, 1), key="sam_dob")
                s_father = st.text_input("Father/Mother Name")
                s_bank = st.text_input("Bond Issuing Bank")
            with sc2:
                s_bond_no = st.text_input("Bond No")
                s_bond_date = st.date_input("Bond Issue Date", value=None, key="sam_bond")
                s_branch = st.text_input("Branch")
                s_address = st.text_area("Address", height=68)

            if st.form_submit_button("💾 Save"):
                if s_name.strip():
                    db.table('samaya_vakuppu').insert({
                        'student_name': s_name,
                        'dob': s_dob.isoformat() if s_dob else None,
                        'father_mother_name': s_father if s_father else None,
                        'bond_no': s_bond_no if s_bond_no else None,
                        'bond_issue_date': s_bond_date.isoformat() if s_bond_date else None,
                        'bond_issuing_bank': s_bank if s_bank else None,
                        'branch_of_bank': s_branch if s_branch else None,
                        'address': s_address if s_address else None,
                    }).execute()
                    st.success("✅ Student added!")
                    st.rerun()

    # List
    students = db.table('samaya_vakuppu').select('*').order('student_name').execute()
    if students.data:
        import pandas as pd
        s_data = [{'ID': s['id'], 'Name': s['student_name'],
                    'DOB': s.get('dob', '-'), 'Father/Mother': s.get('father_mother_name', '-'),
                    'Bond No': s.get('bond_no', '-'), 'Bond Date': s.get('bond_issue_date', '-'),
                    'Bank': s.get('bond_issuing_bank', '-')} for s in students.data]
        st.dataframe(pd.DataFrame(s_data), use_container_width=True, hide_index=True)

        del_id = st.number_input("Enter Student ID to delete", min_value=0, step=1, key="sam_del")
        if st.button("🗑️ Delete Student") and del_id > 0:
            db.table('samaya_vakuppu').delete().eq('id', int(del_id)).execute()
            st.success("Deleted!")
            st.rerun()
    else:
        st.info("No students found")


# ============================================================
# THIRUMANA MANDAPAM PAGE
# ============================================================
def mandapam_page():
    db = get_db()

    st.markdown("### 🏛️ Thirumana Mandapam")

    with st.expander("➕ Add New Record"):
        with st.form("mandapam_form"):
            mc1, mc2 = st.columns(2)
            with mc1:
                m_name = st.text_input("Name *")
                m_bond_no = st.text_input("Bond No")
                m_bond_date = st.date_input("Bond Issued Date", value=None, key="mand_date")
            with mc2:
                m_amount = st.number_input("Amount", min_value=0.0, step=1.0)
                m_bonds = st.number_input("No of Bonds", min_value=1, value=1)
                m_address = st.text_area("Address", height=68)

            if st.form_submit_button("💾 Save"):
                if m_name.strip():
                    db.table('thirumana_mandapam').insert({
                        'name': m_name,
                        'bond_no': m_bond_no if m_bond_no else None,
                        'bond_issued_date': m_bond_date.isoformat() if m_bond_date else None,
                        'amount': m_amount,
                        'no_of_bond': m_bonds,
                        'address': m_address if m_address else None,
                    }).execute()
                    st.success("✅ Record added!")
                    st.rerun()

    records = db.table('thirumana_mandapam').select('*').order('name').execute()
    if records.data:
        import pandas as pd
        m_data = [{'ID': m['id'], 'Name': m['name'], 'Bond No': m.get('bond_no', '-'),
                    'Date': m.get('bond_issued_date', '-'), 'Amount': f"₹{m.get('amount', 0):,.2f}",
                    'Bonds': m.get('no_of_bond', 1)} for m in records.data]
        st.dataframe(pd.DataFrame(m_data), use_container_width=True, hide_index=True)

        del_id = st.number_input("Enter Record ID to delete", min_value=0, step=1, key="mand_del")
        if st.button("🗑️ Delete Record") and del_id > 0:
            db.table('thirumana_mandapam').delete().eq('id', int(del_id)).execute()
            st.success("Deleted!")
            st.rerun()
    else:
        st.info("No records found")


# ============================================================
# DAILY POOJA PAGE
# ============================================================
def daily_pooja_page_fn():
    db = get_db()

    st.markdown("### 🙏 Daily Pooja Schedule")

    with st.expander("➕ Add Pooja"):
        with st.form("dp_form"):
            dp_name = st.text_input("Pooja Name *")
            dp_time = st.text_input("Time (e.g., 6:00 AM)")
            dp_desc = st.text_input("Description")
            if st.form_submit_button("💾 Save"):
                if dp_name.strip():
                    db.table('daily_pooja').insert({
                        'pooja_name': dp_name,
                        'pooja_time': dp_time if dp_time else None,
                        'description': dp_desc if dp_desc else None,
                        'is_active': True
                    }).execute()
                    st.success("✅ Added!")
                    st.rerun()

    poojas = db.table('daily_pooja').select('*').eq('is_active', True)\
        .order('pooja_time').execute()

    if poojas.data:
        for p in poojas.data:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"""
                <div class="pooja-card">
                    <strong>{p['pooja_name']}</strong>
                    <span class="pooja-time">{p.get('pooja_time', 'TBD')}</span>
                    <br><small style="color:#666;">{p.get('description', '')}</small>
                </div>""", unsafe_allow_html=True)
            with col2:
                if st.button("🗑️", key=f"dp_del_{p['id']}"):
                    db.table('daily_pooja').update({'is_active': False}).eq('id', p['id']).execute()
                    st.rerun()
    else:
        st.info("No poojas scheduled")


# ============================================================
# SETTINGS PAGE
# ============================================================
def settings_page():
    db = get_db()

    st.markdown("### ⚙️ Settings")

    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("#### 🙏 Pooja Types")
        with st.form("pt_form"):
            pt_name = st.text_input("Name *", key="new_pt")
            pt_amount = st.number_input("Amount", min_value=0.0, step=1.0, key="new_pt_amt")
            if st.form_submit_button("➕ Add Pooja Type"):
                if pt_name.strip():
                    db.table('pooja_type').insert({'name': pt_name, 'amount': pt_amount}).execute()
                    st.success("Added!")
                    st.rerun()

        pts = db.table('pooja_type').select('*').eq('is_active', True).execute()
        if pts.data:
            for pt in pts.data:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{pt['name']}**")
                with col2:
                    st.write(f"₹{pt['amount']}")
                with col3:
                    if st.button("🗑️", key=f"pt_del_{pt['id']}"):
                        db.table('pooja_type').update({'is_active': False}).eq('id', pt['id']).execute()
                        st.rerun()

    with col_r:
        st.markdown("#### 💰 Expense Types")
        with st.form("et_form"):
            et_name = st.text_input("Name *", key="new_et")
            if st.form_submit_button("➕ Add Expense Type"):
                if et_name.strip():
                    db.table('expense_type').insert({'name': et_name}).execute()
                    st.success("Added!")
                    st.rerun()

        ets = db.table('expense_type').select('*').eq('is_active', True).execute()
        if ets.data:
            for et in ets.data:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{et['name']}**")
                with col2:
                    if st.button("🗑️", key=f"et_del_{et['id']}"):
                        db.table('expense_type').update({'is_active': False}).eq('id', et['id']).execute()
                        st.rerun()


# ============================================================
# USER MANAGEMENT PAGE (Admin only)
# ============================================================
def user_management_page():
    db = get_db()

    if st.session_state['role'] != 'admin':
        st.error("❌ Admin access required!")
        return

    st.markdown("### 👤 User Management")

    with st.expander("➕ Add New User"):
        with st.form("user_form"):
            u_username = st.text_input("Username *")
            u_fullname = st.text_input("Full Name")
            u_password = st.text_input("Password *", type="password")
            u_role = st.selectbox("Role", ["user", "admin"])

            if st.form_submit_button("💾 Create User"):
                if u_username.strip() and u_password:
                    existing = db.table('users').select('id').eq('username', u_username).execute()
                    if existing.data:
                        st.error("❌ Username already exists!")
                    else:
                        db.table('users').insert({
                            'username': u_username,
                            'password_hash': hash_password(u_password),
                            'full_name': u_fullname if u_fullname else None,
                            'role': u_role,
                            'is_active_user': True
                        }).execute()
                        st.success("✅ User created!")
                        st.rerun()
                else:
                    st.error("❌ Username and password required!")

    users = db.table('users').select('*').execute()
    if users.data:
        import pandas as pd
        for u in users.data:
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            with col1:
                st.write(f"**{u['username']}** ({u.get('full_name', '-')})")
            with col2:
                role_badge = "🔑 Admin" if u['role'] == 'admin' else "👤 User"
                status = "✅ Active" if u['is_active_user'] else "❌ Inactive"
                st.write(f"{role_badge} | {status}")
            with col3:
                if u['id'] != st.session_state['user_id']:
                    if st.button("Toggle", key=f"toggle_{u['id']}"):
                        db.table('users').update({
                            'is_active_user': not u['is_active_user']
                        }).eq('id', u['id']).execute()
                        st.rerun()


# ============================================================
# DELETED BILLS PAGE (Admin only)
# ============================================================
def deleted_bills_page():
    db = get_db()

    if st.session_state['role'] != 'admin':
        st.error("❌ Admin access required!")
        return

    st.markdown("### 🗑️ Deleted Bills")

    bills = db.table('bill').select('*, devotee(name), pooja_type(name)')\
        .eq('is_deleted', True).order('deleted_at', desc=True).execute()

    if bills.data:
        import pandas as pd

        # Get users map
        users_result = db.table('users').select('id, username, full_name').execute()
        users_map = {u['id']: u.get('full_name') or u['username'] for u in users_result.data} if users_result.data else {}

        bill_data = []
        for b in bills.data:
            bill_data.append({
                'Bill No': b.get('bill_number', '-'),
                'Date': b.get('bill_date', '-')[:10] if b.get('bill_date') else '-',
                'Name': b.get('devotee', {}).get('name', '') if b.get('devotee') else b.get('guest_name', '-'),
                'Amount': f"���{b.get('amount', 0):,.2f}",
                'Deleted By': users_map.get(b.get('deleted_by'), '-'),
                'Deleted At': b.get('deleted_at', '-')[:16] if b.get('deleted_at') else '-',
                'Reason': b.get('delete_reason', '-')
            })
        st.dataframe(pd.DataFrame(bill_data), use_container_width=True, hide_index=True)
    else:
        st.info("No deleted bills")


# ============================================================
# MAIN APP
# ============================================================
def main():
    """Main application entry point"""
    init_session_state()
    apply_custom_css()

    # Initialize default data
    try:
        init_default_data()
    except Exception as e:
        st.error(f"Database initialization error: {e}")
        st.info("Please check your Supabase connection settings.")
        st.stop()

    # Check login
    if not st.session_state['logged_in']:
        login_page()
        return

    # Show sidebar
    sidebar_navigation()

    # Route to correct page
    page = st.session_state.get('current_page', 'dashboard')

    page_map = {
        'dashboard': dashboard_page,
        'devotees': devotees_page,
        'add_devotee': add_devotee_page,
        'view_devotee': view_devotee_page,
        'billing': billing_page,
        'new_bill': new_bill_page,
        'view_bill': view_bill_page,
        'expenses': expenses_page,
        'reports': reports_page,
        'samaya': samaya_page,
        'mandapam': mandapam_page,
        'daily_pooja': daily_pooja_page_fn,
        'settings': settings_page,
        'users': user_management_page,
        'deleted_bills': deleted_bills_page,
    }

    page_fn = page_map.get(page, dashboard_page)
    try:
        page_fn()
    except Exception as e:
        st.error(f"Error: {e}")
        st.info("Please try again or contact administrator.")
        import traceback
        st.code(traceback.format_exc())


if __name__ == "__main__":
    main()