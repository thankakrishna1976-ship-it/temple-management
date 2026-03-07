import streamlit as st
import bcrypt
from datetime import datetime, date, timedelta
import traceback
import base64

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Temple Management System",
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
TEMPLE_FULL = f"{TEMPLE_NAME}, {TEMPLE_TRUST} - {TEMPLE_REG}, {TEMPLE_PLACE}, {TEMPLE_DISTRICT}"

NATCHATHIRAM_LIST = [
    'அசுவினி (Ashwini)', 'பரணி (Bharani)', 'கார்த்திகை (Krittika)',
    'ரோகிணி (Rohini)', 'மிருகசீரிடம் (Mrigashira)', 'திருவாதிரை (Ardra)',
    'பு��ர்பூசம் (Punarvasu)', 'பூசம் (Pushya)', 'ஆயில்யம் (Ashlesha)',
    'மகம் (Magha)', '��ூரம் (Purva Phalguni)', 'உத்திரம் (Uttara Phalguni)',
    'ஹஸ்தம் (Hasta)', 'சித்திரை (Chitra)', 'சுவாதி (Swati)',
    'விசாகம் (Vishakha)', 'அனுஷம் (Anuradha)', 'கேட்டை (Jyeshtha)',
    'மூலம் (Mula)', 'பூராடம் (Purva Ashadha)', 'உத்திராடம் (Uttara Ashadha)',
    'திருவோணம் (Shravana)', 'அவிட்டம் (Dhanishta)', 'சதயம் (Shatabhisha)',
    'பூரட்டாதி (Purva Bhadrapada)', 'உத்திரட்டாதி (Uttara Bhadrapada)',
    'ரேவதி (Revati)'
]

RELATION_TYPES = [
    'Self', 'Spouse', 'Son', 'Daughter', 'Father', 'Mother',
    'Brother', 'Sister', 'Grandfather', 'Grandmother',
    'Father-in-law', 'Mother-in-law', 'Son-in-law', 'Daughter-in-law',
    'Uncle', 'Aunt', 'Nephew', 'Niece', 'Cousin', 'Other'
]


# ============================================================
# SUPABASE CONNECTION
# ============================================================
def get_db():
    try:
        from supabase import create_client
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except KeyError:
        st.error("Supabase credentials not found! Add SUPABASE_URL and SUPABASE_KEY to Streamlit secrets.")
        st.stop()
    except Exception as e:
        st.error(f"Database connection error: {e}")
        st.stop()


# ============================================================
# PASSWORD HELPERS
# ============================================================
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def check_password(password, hashed):
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


# ============================================================
# DATE HELPERS
# ============================================================
def parse_date(date_str):
    if not date_str:
        return None
    try:
        if isinstance(date_str, date):
            return date_str
        return datetime.strptime(str(date_str)[:10], '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def safe_date_display(date_str):
    d = parse_date(date_str)
    return d.strftime('%d/%m/%Y') if d else '-'


# ============================================================
# IMAGE HELPERS - SUPABASE STORAGE
# ============================================================
def get_amman_image():
    """Get Amman image from Supabase storage or session state"""
    # Check session state first (cached)
    if 'amman_image_data' in st.session_state and st.session_state['amman_image_data']:
        return st.session_state['amman_image_data']

    # Try to load from Supabase storage
    try:
        db = get_db()
        # Try to download amman image
        for ext in ['png', 'jpg', 'jpeg', 'webp']:
            try:
                data = db.storage.from_('temple-images').download(f'amman.{ext}')
                if data:
                    mime = 'png' if ext == 'png' else 'jpeg' if ext in ['jpg', 'jpeg'] else ext
                    b64 = base64.b64encode(data).decode()
                    img_data = f"data:image/{mime};base64,{b64}"
                    st.session_state['amman_image_data'] = img_data
                    return img_data
            except Exception:
                continue
    except Exception:
        pass

    return None


def get_temple_bg():
    """Get temple background from Supabase storage or session state"""
    if 'temple_bg_data' in st.session_state and st.session_state['temple_bg_data']:
        return st.session_state['temple_bg_data']

    try:
        db = get_db()
        for ext in ['jpg', 'jpeg', 'png', 'webp']:
            try:
                data = db.storage.from_('temple-images').download(f'temple_bg.{ext}')
                if data:
                    mime = 'png' if ext == 'png' else 'jpeg' if ext in ['jpg', 'jpeg'] else ext
                    b64 = base64.b64encode(data).decode()
                    img_data = f"data:image/{mime};base64,{b64}"
                    st.session_state['temple_bg_data'] = img_data
                    return img_data
            except Exception:
                continue
    except Exception:
        pass

    return None


def upload_image_to_storage(file_data, filename):
    """Upload image to Supabase storage"""
    try:
        db = get_db()
        # Delete existing file first
        try:
            db.storage.from_('temple-images').remove([filename])
        except Exception:
            pass
        # Upload new file
        db.storage.from_('temple-images').upload(filename, file_data)
        return True
    except Exception as e:
        st.error(f"Upload error: {e}")
        return False


# ============================================================
# INITIALIZE DEFAULT DATA
# ============================================================
def init_default_data():
    try:
        db = get_db()

        result = db.table('users').select('id').eq('username', 'admin').execute()
        if not result.data:
            db.table('users').insert({
                'username': 'admin',
                'password_hash': hash_password('admin123'),
                'full_name': 'Administrator',
                'role': 'admin',
                'is_active_user': True
            }).execute()

        result = db.table('pooja_type').select('id').limit(1).execute()
        if not result.data:
            db.table('pooja_type').insert([
                {'name': 'Abhishekam', 'amount': 100, 'is_active': True},
                {'name': 'Archanai', 'amount': 50, 'is_active': True},
                {'name': 'Sahasranamam', 'amount': 200, 'is_active': True},
                {'name': 'Thiruvilakku Pooja', 'amount': 150, 'is_active': True},
                {'name': 'Ganapathi Homam', 'amount': 500, 'is_active': True},
                {'name': 'Navagraha Pooja', 'amount': 300, 'is_active': True},
                {'name': 'Chandana Kavasam', 'amount': 250, 'is_active': True},
                {'name': 'Annadhanam', 'amount': 1000, 'is_active': True},
            ]).execute()

        result = db.table('expense_type').select('id').limit(1).execute()
        if not result.data:
            db.table('expense_type').insert([
                {'name': 'Flowers', 'is_active': True},
                {'name': 'Oil', 'is_active': True},
                {'name': 'Camphor', 'is_active': True},
                {'name': 'Electricity', 'is_active': True},
                {'name': 'Admin', 'is_active': True},
                {'name': 'Maintenance', 'is_active': True},
                {'name': 'Salary', 'is_active': True},
                {'name': 'Others', 'is_active': True},
            ]).execute()

        result = db.table('daily_pooja').select('id').limit(1).execute()
        if not result.data:
            db.table('daily_pooja').insert([
                {'pooja_name': 'Suprabhatam', 'pooja_time': '5:30 AM', 'description': 'Morning prayer', 'is_active': True},
                {'pooja_name': 'Kalai Abhishekam', 'pooja_time': '6:00 AM', 'description': 'Morning bath', 'is_active': True},
                {'pooja_name': 'Kalai Pooja', 'pooja_time': '7:00 AM', 'description': 'Morning worship', 'is_active': True},
                {'pooja_name': 'Uchikala Pooja', 'pooja_time': '12:00 PM', 'description': 'Noon', 'is_active': True},
                {'pooja_name': 'Sayarakshai', 'pooja_time': '6:00 PM', 'description': 'Evening', 'is_active': True},
                {'pooja_name': 'Artha Jama Pooja', 'pooja_time': '8:00 PM', 'description': 'Night', 'is_active': True},
            ]).execute()

    except Exception as e:
        st.warning(f"Init note: {e}")


# ============================================================
# CUSTOM CSS
# ============================================================
def apply_css():
    st.markdown("""
    <style>
        :root { --td: #8B0000; --tg: #FFD700; --tl: #FFF8DC; }
        .stApp { background: linear-gradient(135deg, #FFF8DC 0%, #FFEFD5 50%, #FFE4B5 100%); }

        /* Sidebar - Full width with visible text */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #8B0000 0%, #B22222 50%, #DC143C 100%) !important;
            min-width: 280px !important;
            width: 280px !important;
        }
        section[data-testid="stSidebar"] > div {
            padding-top: 0 !important;
        }
        section[data-testid="stSidebar"] .stButton > button {
            background: transparent !important;
            color: #FFF8DC !important;
            border: none !important;
            border-left: 3px solid transparent !important;
            text-align: left !important;
            padding: 12px 20px !important;
            font-size: 1em !important;
            font-weight: 500 !important;
            border-radius: 0 !important;
            width: 100% !important;
            display: flex !important;
            justify-content: flex-start !important;
            transition: all 0.3s !important;
        }
        section[data-testid="stSidebar"] .stButton > button:hover {
            background: rgba(255, 215, 0, 0.15) !important;
            border-left: 3px solid #FFD700 !important;
            color: #FFD700 !important;
        }
        section[data-testid="stSidebar"] hr {
            border-color: rgba(255, 215, 0, 0.2) !important;
            margin: 5px 15px !important;
        }
        section[data-testid="stSidebar"] .stMarkdown {
            color: #FFF8DC !important;
        }
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] div {
            color: #FFF8DC !important;
        }

        .temple-hdr {
            background: linear-gradient(135deg, #8B0000, #DC143C);
            color: #FFD700; padding: 15px 25px; border-radius: 12px;
            text-align: center; margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(139,0,0,0.3);
        }
        .temple-hdr h1 { font-size: 1.5em; margin: 0; color: #FFD700; }
        .temple-hdr p { font-size: 0.85em; margin: 2px 0; color: #FFF8DC; }

        .stat-card {
            border-radius: 15px; padding: 20px; color: white;
            box-shadow: 0 5px 20px rgba(0,0,0,0.15); text-align: center; margin-bottom: 10px;
        }
        .stat-income { background: linear-gradient(135deg, #228B22, #32CD32); }
        .stat-expense { background: linear-gradient(135deg, #DC143C, #FF4500); }
        .stat-devotees { background: linear-gradient(135deg, #4169E1, #6495ED); }
        .stat-bills { background: linear-gradient(135deg, #FF8C00, #FFD700); }
        .stat-card h3 { font-size: 1.8em; font-weight: 700; margin: 5px 0; }
        .stat-card p { font-size: 0.85em; opacity: 0.9; margin: 0; }

        .ccard {
            background: white; border-radius: 12px;
            box-shadow: 0 2px 15px rgba(0,0,0,0.08); padding: 20px; margin-bottom: 15px;
        }

        .pooja-card {
            background: linear-gradient(135deg, #FFF8DC, #FFEFD5);
            border: 1px solid #FFD700; border-radius: 10px; padding: 12px 15px;
            margin-bottom: 8px; border-left: 4px solid #8B0000;
        }
        .pooja-card strong { color: #8B0000; }

        .bday-card {
            background: #FFF8DC; border-radius: 8px; padding: 10px 15px;
            margin-bottom: 8px; border-left: 3px solid #DC143C;
        }

        .bill-hdr {
            text-align: center; border-bottom: 3px double #8B0000;
            padding-bottom: 15px; margin-bottom: 15px;
        }
        .bill-hdr h2 { color: #8B0000; font-size: 1.3em; margin: 0; }
        .bill-hdr h4 { color: #DC143C; font-size: 0.95em; margin: 2px 0; }
        .bill-hdr p { color: #555; font-size: 0.8em; margin: 1px 0; }

        /* Amman round image */
        .amman-round {
            width: 100px; height: 100px; border-radius: 50%;
            border: 4px solid #FFD700; object-fit: cover;
            box-shadow: 0 0 25px rgba(255,215,0,0.5);
            display: block; margin: 0 auto 10px;
        }
        .amman-round-sm {
            width: 60px; height: 60px; border-radius: 50%;
            border: 3px solid #FFD700; object-fit: cover;
            box-shadow: 0 0 15px rgba(255,215,0,0.4);
            display: block; margin: 0 auto 8px;
        }
        .amman-placeholder {
            width: 100px; height: 100px; border-radius: 50%;
            border: 4px solid #FFD700; display: flex;
            align-items: center; justify-content: center;
            font-size: 3em; margin: 0 auto 10px;
            background: linear-gradient(135deg, #FFF8DC, #FFEFD5);
            box-shadow: 0 0 25px rgba(255,215,0,0.5);
        }
        .amman-placeholder-sm {
            width: 60px; height: 60px; border-radius: 50%;
            border: 3px solid #FFD700; display: flex;
            align-items: center; justify-content: center;
            font-size: 1.8em; margin: 0 auto 8px;
            background: linear-gradient(135deg, #FFF8DC, #FFEFD5);
        }

        /* Login page */
        .login-bg {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background-size: cover; background-position: center;
            z-index: -2; filter: brightness(0.35) saturate(1.2);
        }
        .login-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: linear-gradient(135deg, rgba(139,0,0,0.6), rgba(220,20,60,0.5));
            z-index: -1;
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================
def init_session():
    defaults = {
        'logged_in': False, 'user_id': None, 'username': None,
        'full_name': None, 'role': None, 'page': 'dashboard',
        'edit_devotee_id': None, 'view_devotee_id': None,
        'print_bill_id': None, 'amman_image_data': None,
        'temple_bg_data': None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ============================================================
# LOGIN PAGE - WITH AMMAN IMAGE & TEMPLE BG
# ============================================================
def login_page():
    # Get images
    amman_img = get_amman_image()
    temple_bg = get_temple_bg()

    # Temple background
    if temple_bg:
        st.markdown(f"""
        <div class="login-bg" style="background-image:url('{temple_bg}');"></div>
        <div class="login-overlay"></div>
        """, unsafe_allow_html=True)

    # Main login content
    st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.96); border-radius:20px; padding:35px;
                    box-shadow:0 20px 60px rgba(0,0,0,0.3); text-align:center;
                    backdrop-filter:blur(10px);">
        """, unsafe_allow_html=True)

        # Amman Image - Round
        if amman_img:
            st.markdown(f'<img src="{amman_img}" class="amman-round">', unsafe_allow_html=True)
        else:
            st.markdown('<div class="amman-placeholder">🙏</div>', unsafe_allow_html=True)

        st.markdown(f"""
            <h2 style="color:#8B0000; margin:5px 0; font-weight:700;">{TEMPLE_NAME}</h2>
            <p style="color:#DC143C; font-weight:600; font-size:0.9em;">{TEMPLE_TRUST} - {TEMPLE_REG}</p>
            <p style="color:#888; font-size:0.82em;">{TEMPLE_PLACE}, {TEMPLE_DISTRICT}</p>
            <hr style="border-color:#FFD700; margin:12px auto; width:60%;">
        """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Login form
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter password")
            submitted = st.form_submit_button("🕉️ Login", use_container_width=True)

            if submitted and username and password:
                try:
                    db = get_db()
                    result = db.table('users').select('*').eq('username', username).eq('is_active_user', True).execute()
                    if result.data:
                        user = result.data[0]
                        if check_password(password, user['password_hash']):
                            st.session_state['logged_in'] = True
                            st.session_state['user_id'] = user['id']
                            st.session_state['username'] = user['username']
                            st.session_state['full_name'] = user.get('full_name') or user['username']
                            st.session_state['role'] = user['role']
                            st.success("✅ Welcome!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid credentials!")
                    else:
                        st.error("❌ Invalid credentials!")
                except Exception as e:
                    st.error(f"Login error: {e}")
            elif submitted:
                st.warning("Please enter username and password")

        st.markdown('<p style="text-align:center;color:#aaa;font-size:0.8em;">🕉️ Temple Management System v2.0</p>', unsafe_allow_html=True)


# ============================================================
# SIDEBAR - FULL MENU NAMES (NOT ICONS ONLY)
# ============================================================
def sidebar():
    with st.sidebar:
        # Amman image in sidebar
        amman_img = get_amman_image()

        st.markdown("<div style='text-align:center; padding:15px 0; border-bottom:2px solid rgba(255,215,0,0.3);'>", unsafe_allow_html=True)

        if amman_img:
            st.markdown(f'<img src="{amman_img}" class="amman-round-sm">', unsafe_allow_html=True)
        else:
            st.markdown('<div class="amman-placeholder-sm">🙏</div>', unsafe_allow_html=True)

        st.markdown(f"""
            <h4 style="color:#FFD700; font-size:0.85em; margin:5px 0; text-align:center;">{TEMPLE_NAME}</h4>
            <p style="color:rgba(255,215,0,0.7); font-size:0.7em; text-align:center;">{TEMPLE_TRUST}</p>
            <p style="color:rgba(255,215,0,0.7); font-size:0.65em; text-align:center;">{TEMPLE_PLACE}, {TEMPLE_DISTRICT}</p>
            <p style="color:#FFD700; font-size:0.78em; margin-top:6px; text-align:center;">
                👤 {st.session_state['full_name']}
                {'  🔑 ADMIN' if st.session_state['role'] == 'admin' else ''}
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # ===== MENU WITH FULL NAMES =====
        # Main Navigation
        st.markdown("<p style='color:#FFD700; font-size:0.75em; font-weight:700; padding:0 20px; margin-bottom:5px;'>MAIN MENU</p>", unsafe_allow_html=True)

        if st.button("🏠  Dashboard", key="nav_dashboard", use_container_width=True):
            st.session_state['page'] = 'dashboard'
            st.rerun()

        if st.button("👥  Devotees", key="nav_devotees", use_container_width=True):
            st.session_state['page'] = 'devotees'
            st.rerun()

        if st.button("🧾  Billing", key="nav_billing", use_container_width=True):
            st.session_state['page'] = 'billing'
            st.rerun()

        if st.button("💰  Expenses", key="nav_expenses", use_container_width=True):
            st.session_state['page'] = 'expenses'
            st.rerun()

        if st.button("📊  Reports", key="nav_reports", use_container_width=True):
            st.session_state['page'] = 'reports'
            st.rerun()

        st.markdown("---")

        # Special Sections
        st.markdown("<p style='color:#FFD700; font-size:0.75em; font-weight:700; padding:0 20px; margin-bottom:5px;'>SPECIAL</p>", unsafe_allow_html=True)

        if st.button("🎓  Samaya Vakuppu", key="nav_samaya", use_container_width=True):
            st.session_state['page'] = 'samaya'
            st.rerun()

        if st.button("🏛️  Thirumana Mandapam", key="nav_mandapam", use_container_width=True):
            st.session_state['page'] = 'mandapam'
            st.rerun()

        if st.button("🙏  Daily Pooja Schedule", key="nav_daily_pooja", use_container_width=True):
            st.session_state['page'] = 'daily_pooja'
            st.rerun()

        st.markdown("---")

        # Settings
        st.markdown("<p style='color:#FFD700; font-size:0.75em; font-weight:700; padding:0 20px; margin-bottom:5px;'>SETTINGS</p>", unsafe_allow_html=True)

        if st.button("⚙️  Pooja & Expense Types", key="nav_settings", use_container_width=True):
            st.session_state['page'] = 'settings'
            st.rerun()

        if st.button("🖼️  Temple Images", key="nav_images", use_container_width=True):
            st.session_state['page'] = 'temple_images'
            st.rerun()

        # Admin only menus
        if st.session_state['role'] == 'admin':
            st.markdown("---")
            st.markdown("<p style='color:#FFD700; font-size:0.75em; font-weight:700; padding:0 20px; margin-bottom:5px;'>ADMIN</p>", unsafe_allow_html=True)

            if st.button("👤  User Management", key="nav_users", use_container_width=True):
                st.session_state['page'] = 'users'
                st.rerun()

            if st.button("🗑️  Deleted Bills", key="nav_deleted_bills", use_container_width=True):
                st.session_state['page'] = 'deleted_bills'
                st.rerun()

        st.markdown("---")

        if st.button("🚪  Logout", key="nav_logout", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

        st.markdown(f"""
        <div style="text-align:center; padding-top:10px; font-size:0.7em; color:rgba(255,215,0,0.5);">
            📅 {datetime.now().strftime('%d %B %Y, %A')}
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# TEMPLE IMAGES UPLOAD PAGE
# ============================================================
def pg_temple_images():
    st.markdown("### 🖼️ Temple Images")
    st.markdown("Upload Amman image (shown as round icon) and Temple background (shown on login page)")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background:white; border-radius:12px; padding:20px; box-shadow:0 2px 10px rgba(0,0,0,0.1);">
            <h4 style="color:#8B0000; border-bottom:2px solid #FFD700; padding-bottom:8px;">
                🙏 Amman Image (Round Icon)
            </h4>
        </div>
        """, unsafe_allow_html=True)

        # Show current image
        amman_img = get_amman_image()
        if amman_img:
            st.markdown(f'<div style="text-align:center;"><img src="{amman_img}" class="amman-round"></div>', unsafe_allow_html=True)
            st.success("✅ Amman image is set")
        else:
            st.markdown('<div style="text-align:center;"><div class="amman-placeholder">🙏</div></div>', unsafe_allow_html=True)
            st.info("No Amman image uploaded yet. Using default icon.")

        st.markdown("---")
        st.markdown("**Upload New Amman Image:**")
        st.markdown("*Best: Square image (e.g., 500x500px), PNG or JPG*")

        amman_file = st.file_uploader("Choose Amman image", type=['png', 'jpg', 'jpeg', 'webp'],
                                        key="amman_upload")

        if amman_file:
            # Preview
            st.image(amman_file, caption="Preview", width=150)

            if st.button("📤 Upload Amman Image", key="btn_upload_amman"):
                ext = amman_file.name.rsplit('.', 1)[-1].lower()
                filename = f"amman.{ext}"
                file_data = amman_file.read()

                # Remove old files
                db = get_db()
                for old_ext in ['png', 'jpg', 'jpeg', 'webp']:
                    try:
                        db.storage.from_('temple-images').remove([f'amman.{old_ext}'])
                    except Exception:
                        pass

                if upload_image_to_storage(file_data, filename):
                    # Clear cache
                    st.session_state['amman_image_data'] = None
                    st.success("✅ Amman image uploaded successfully!")
                    st.rerun()

    with col2:
        st.markdown("""
        <div style="background:white; border-radius:12px; padding:20px; box-shadow:0 2px 10px rgba(0,0,0,0.1);">
            <h4 style="color:#8B0000; border-bottom:2px solid #FFD700; padding-bottom:8px;">
                🏛️ Temple Background (Login Page)
            </h4>
        </div>
        """, unsafe_allow_html=True)

        # Show current background
        temple_bg = get_temple_bg()
        if temple_bg:
            st.markdown(f"""
            <div style="text-align:center;">
                <img src="{temple_bg}" style="width:250px; height:150px; border-radius:10px;
                     object-fit:cover; border:2px solid #FFD700; box-shadow:0 2px 10px rgba(0,0,0,0.2);">
            </div>
            """, unsafe_allow_html=True)
            st.success("✅ Temple background is set")
        else:
            st.markdown("""
            <div style="text-align:center;">
                <div style="width:250px; height:150px; background:#ddd; border-radius:10px;
                     display:flex; align-items:center; justify-content:center; margin:0 auto;
                     border:2px dashed #ccc;">
                    <span style="color:#999; font-size:2em;">🏛️</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.info("No temple background uploaded yet.")

        st.markdown("---")
        st.markdown("**Upload New Temple Background:**")
        st.markdown("*Best: Wide image (e.g., 1920x1080px), JPG*")

        bg_file = st.file_uploader("Choose temple background", type=['png', 'jpg', 'jpeg', 'webp'],
                                     key="bg_upload")

        if bg_file:
            # Preview
            st.image(bg_file, caption="Preview", width=250)

            if st.button("📤 Upload Temple Background", key="btn_upload_bg"):
                ext = bg_file.name.rsplit('.', 1)[-1].lower()
                filename = f"temple_bg.{ext}"
                file_data = bg_file.read()

                # Remove old files
                db = get_db()
                for old_ext in ['png', 'jpg', 'jpeg', 'webp']:
                    try:
                        db.storage.from_('temple-images').remove([f'temple_bg.{old_ext}'])
                    except Exception:
                        pass

                if upload_image_to_storage(file_data, filename):
                    st.session_state['temple_bg_data'] = None
                    st.success("✅ Temple background uploaded successfully!")
                    st.rerun()

    # Instructions
    st.markdown("---")
    st.markdown("""
    <div style="background:white; border-radius:12px; padding:20px; box-shadow:0 2px 10px rgba(0,0,0,0.1);">
        <h4 style="color:#8B0000;">📌 Instructions</h4>
        <ul style="color:#555;">
            <li><strong>Amman Image:</strong> This will appear as a round icon in the sidebar, login page, and bill headers.</li>
            <li><strong>Temple Background:</strong> This will appear as the background image on the login page.</li>
            <li><strong>Image Size:</strong> Keep images under 5MB for best performance.</li>
            <li><strong>Format:</strong> PNG or JPG recommended.</li>
            <li>After uploading, you may need to <strong>reload the page</strong> to see changes everywhere.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Clear cache button
    if st.button("🔄 Refresh Images (Clear Cache)"):
        st.session_state['amman_image_data'] = None
        st.session_state['temple_bg_data'] = None
        st.rerun()


# ============================================================
# DASHBOARD
# ============================================================
def pg_dashboard():
    db = get_db()
    amman_img = get_amman_image()

    # Header with amman image
    if amman_img:
        st.markdown(f"""
        <div class="temple-hdr">
            <img src="{amman_img}" style="width:70px;height:70px;border-radius:50%;border:3px solid #FFD700;object-fit:cover;display:block;margin:0 auto 8px;">
            <h1>{TEMPLE_NAME}</h1>
            <p>{TEMPLE_TRUST} - {TEMPLE_REG}</p>
            <p>{TEMPLE_PLACE}, {TEMPLE_DISTRICT}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="temple-hdr">
            <h1>🕉️ {TEMPLE_NAME}</h1>
            <p>{TEMPLE_TRUST} - {TEMPLE_REG}</p>
            <p>{TEMPLE_PLACE}, {TEMPLE_DISTRICT}</p>
        </div>
        """, unsafe_allow_html=True)

    period = st.radio("📅 Period", ["Daily", "Weekly", "Monthly", "Yearly"], horizontal=True)

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

    try:
        bills_r = db.table('bill').select('amount').eq('is_deleted', False).gte('bill_date', sd.isoformat()).lte('bill_date', ed.isoformat() + 'T23:59:59').execute()
        total_income = sum(b['amount'] or 0 for b in (bills_r.data or []))
        total_bills = len(bills_r.data or [])

        exp_r = db.table('expense').select('amount').gte('expense_date', sd.isoformat()).lte('expense_date', ed.isoformat()).execute()
        total_expenses = sum(e['amount'] or 0 for e in (exp_r.data or []))

        dev_r = db.table('devotee').select('id', count='exact').eq('is_family_head', True).eq('is_active', True).execute()
        total_devotees = dev_r.count or 0
    except Exception as e:
        total_income = total_expenses = total_bills = total_devotees = 0
        st.warning(f"Stats error: {e}")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="stat-card stat-income"><p>📈 {period} Income</p><h3>₹{total_income:,.2f}</h3></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-card stat-expense"><p>📉 {period} Expenses</p><h3>₹{total_expenses:,.2f}</h3></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat-card stat-devotees"><p>👥 Total Devotees</p><h3>{total_devotees}</h3></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="stat-card stat-bills"><p>🧾 {period} Bills</p><h3>{total_bills}</h3></div>', unsafe_allow_html=True)

    cl, cr = st.columns(2)

    with cl:
        st.markdown("### 🙏 Today's Pooja Schedule")
        try:
            dp_r = db.table('daily_pooja').select('*').eq('is_active', True).order('pooja_time').execute()
            for p in (dp_r.data or []):
                st.markdown(f"""<div class="pooja-card">
                    <strong>{p['pooja_name']}</strong> -
                    <span style="color:#8B0000;font-weight:700;">{p.get('pooja_time','TBD')}</span>
                    <br><small style="color:#666;">{p.get('description','')}</small>
                </div>""", unsafe_allow_html=True)
            if not dp_r.data:
                st.info("No pooja scheduled")
        except Exception as e:
            st.warning(f"Error: {e}")

    with cr:
        st.markdown("### 🎂 Today's Birthdays")
        try:
            all_dev = db.table('devotee').select('name, dob, mobile_no').eq('is_active', True).not_.is_('dob', 'null').execute()
            birthdays = []
            for d in (all_dev.data or []):
                dd = parse_date(d.get('dob'))
                if dd and dd.month == today_d.month and dd.day == today_d.day:
                    birthdays.append(d)
            for b in birthdays:
                st.markdown(f'<div class="bday-card">🎂 <strong>{b["name"]}</strong> - {b.get("mobile_no","")}</div>', unsafe_allow_html=True)
            if not birthdays:
                st.info("No birthdays today")
        except Exception as e:
            st.warning(f"Error: {e}")

    st.markdown("### 🧾 Recent Bills")
    try:
        import pandas as pd
        rb = db.table('bill').select('bill_number, bill_date, amount, guest_name, devotee(name), pooja_type(name)').eq('is_deleted', False).order('bill_date', desc=True).limit(10).execute()
        if rb.data:
            rows = []
            for b in rb.data:
                name = (b.get('devotee') or {}).get('name', '') or b.get('guest_name', '-')
                pooja = (b.get('pooja_type') or {}).get('name', '-')
                rows.append({'Bill': b.get('bill_number', '-'), 'Date': str(b.get('bill_date', '-'))[:10],
                             'Name': name, 'Pooja': pooja, 'Amount': f"₹{b.get('amount',0):,.2f}"})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("No bills yet")
    except Exception as e:
        st.warning(f"Error: {e}")


# ============================================================
# DEVOTEES
# ============================================================
def pg_devotees():
    db = get_db()
    st.markdown("### 👥 Enrolled Devotees")

    c1, c2 = st.columns([3, 1])
    with c2:
        if st.button("��� Add Devotee", use_container_width=True):
            st.session_state['page'] = 'add_devotee'
            st.session_state['edit_devotee_id'] = None
            st.rerun()
    with c1:
        search = st.text_input("🔍 Search", placeholder="Name or mobile...")

    try:
        if search:
            result = db.table('devotee').select('*').eq('is_family_head', True).eq('is_active', True).ilike('name', f'%{search}%').order('name').execute()
        else:
            result = db.table('devotee').select('*').eq('is_family_head', True).eq('is_active', True).order('name').execute()

        if result.data:
            for d in result.data:
                fm_r = db.table('devotee').select('id', count='exact').eq('family_head_id', d['id']).execute()
                fm_count = fm_r.count or 0

                with st.expander(f"**{d['name']}** | 📱 {d.get('mobile_no','-')} | ⭐ {d.get('natchathiram','-')} | 👨‍👩‍👧‍👦 {fm_count}"):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    with c1:
                        st.write(f"**DOB:** {safe_date_display(d.get('dob'))}")
                        st.write(f"**Mobile:** {d.get('mobile_no', '-')}")
                        st.write(f"**WhatsApp:** {d.get('whatsapp_no', '-')}")
                    with c2:
                        st.write(f"**Star:** {d.get('natchathiram', '-')}")
                        st.write(f"**Wedding:** {safe_date_display(d.get('wedding_day'))}")
                        st.write(f"**Address:** {d.get('address', '-')}")
                    with c3:
                        if st.button("✏️ Edit", key=f"e_{d['id']}"):
                            st.session_state['page'] = 'add_devotee'
                            st.session_state['edit_devotee_id'] = d['id']
                            st.rerun()
                        if st.button("🗑️ Delete", key=f"d_{d['id']}"):
                            db.table('devotee_yearly_pooja').delete().eq('devotee_id', d['id']).execute()
                            db.table('devotee').delete().eq('family_head_id', d['id']).execute()
                            db.table('devotee').delete().eq('id', d['id']).execute()
                            st.success("Deleted!")
                            st.rerun()

                    fm_result = db.table('devotee').select('*').eq('family_head_id', d['id']).execute()
                    if fm_result.data:
                        import pandas as pd
                        st.markdown("**👨‍👩‍👧‍👦 Family:**")
                        fm_rows = [{'Name': f['name'], 'Relation': f.get('relation_type', '-'),
                                     'DOB': safe_date_display(f.get('dob')), 'Star': f.get('natchathiram', '-'),
                                     'Mobile': f.get('mobile_no', '-')} for f in fm_result.data]
                        st.dataframe(pd.DataFrame(fm_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No devotees found.")
    except Exception as e:
        st.error(f"Error: {e}")


# ============================================================
# ADD/EDIT DEVOTEE
# ============================================================
def pg_add_devotee():
    db = get_db()
    edit_id = st.session_state.get('edit_devotee_id')
    dd = None

    if edit_id:
        r = db.table('devotee').select('*').eq('id', edit_id).execute()
        if r.data:
            dd = r.data[0]
        st.markdown(f"### ✏️ Edit Devotee (ID: {edit_id})")
    else:
        st.markdown("### ➕ Add New Devotee")

    if st.button("⬅️ Back to Devotees"):
        st.session_state['page'] = 'devotees'
        st.rerun()

    with st.form("dev_form"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Name *", value=dd.get('name', '') if dd else '')
            dob_val = parse_date(dd.get('dob')) if dd else None
            dob = st.date_input("DOB", value=dob_val)
            mobile = st.text_input("Mobile", value=dd.get('mobile_no', '') if dd else '')
            rel_idx = (RELATION_TYPES.index(dd['relation_type']) + 1) if dd and dd.get('relation_type') in RELATION_TYPES else 0
            relation = st.selectbox("Relation", [''] + RELATION_TYPES, index=rel_idx)
        with c2:
            whatsapp = st.text_input("WhatsApp", value=dd.get('whatsapp_no', '') if dd else '')
            wed_val = parse_date(dd.get('wedding_day')) if dd else None
            wedding = st.date_input("Wedding Day", value=wed_val)
            star_idx = (NATCHATHIRAM_LIST.index(dd['natchathiram']) + 1) if dd and dd.get('natchathiram') in NATCHATHIRAM_LIST else 0
            natchathiram = st.selectbox("Natchathiram", [''] + NATCHATHIRAM_LIST, index=star_idx)
            address = st.text_area("Address", value=dd.get('address', '') if dd else '')

        st.markdown("---")
        st.markdown("#### 👨‍👩‍👧‍👦 Family Members")

        existing_fm = []
        if edit_id:
            fm_r = db.table('devotee').select('*').eq('family_head_id', edit_id).execute()
            existing_fm = fm_r.data or []

        num_fm = st.number_input("Number of family members", 0, 15, len(existing_fm))

        family_data = []
        for i in range(int(num_fm)):
            st.markdown(f"**Member {i+1}**")
            fc1, fc2, fc3, fc4, fc5 = st.columns(5)
            efm = existing_fm[i] if i < len(existing_fm) else {}
            with fc1:
                fn = st.text_input("Name", key=f"fn_{i}", value=efm.get('name', ''))
            with fc2:
                fd = st.date_input("DOB", key=f"fd_{i}", value=parse_date(efm.get('dob')))
            with fc3:
                fr_idx = (RELATION_TYPES.index(efm['relation_type']) + 1) if efm.get('relation_type') in RELATION_TYPES else 0
                fr = st.selectbox("Relation", [''] + RELATION_TYPES, key=f"fr_{i}", index=fr_idx)
            with fc4:
                fs_idx = (NATCHATHIRAM_LIST.index(efm['natchathiram']) + 1) if efm.get('natchathiram') in NATCHATHIRAM_LIST else 0
                fs = st.selectbox("Star", [''] + NATCHATHIRAM_LIST, key=f"fs_{i}", index=fs_idx)
            with fc5:
                fmob = st.text_input("Mobile", key=f"fm_{i}", value=efm.get('mobile_no', ''))
            if fn.strip():
                family_data.append({'name': fn, 'dob': fd.isoformat() if fd else None,
                    'relation_type': fr or None, 'natchathiram': fs or None, 'mobile_no': fmob or None})

        st.markdown("---")
        st.markdown("#### 🙏 Yearly Poojas")

        pt_r = db.table('pooja_type').select('*').eq('is_active', True).execute()
        pooja_types = pt_r.data or []
        pt_names = [''] + [p['name'] for p in pooja_types]
        pt_map = {p['name']: p['id'] for p in pooja_types}

        existing_yp = []
        if edit_id:
            yp_r = db.table('devotee_yearly_pooja').select('*, pooja_type(name)').eq('devotee_id', edit_id).execute()
            existing_yp = yp_r.data or []

        num_yp = st.number_input("Number of yearly poojas", 0, 20, len(existing_yp))

        yp_data = []
        for i in range(int(num_yp)):
            yc1, yc2, yc3 = st.columns(3)
            eyp = existing_yp[i] if i < len(existing_yp) else {}
            ept_name = (eyp.get('pooja_type') or {}).get('name', '') if eyp.get('pooja_type') else ''
            with yc1:
                yp_idx = pt_names.index(ept_name) if ept_name in pt_names else 0
                ypt = st.selectbox(f"Pooja {i+1}", pt_names, key=f"ypt_{i}", index=yp_idx)
            with yc2:
                ypd = st.date_input(f"Date {i+1}", key=f"ypd_{i}", value=parse_date(eyp.get('pooja_date')))
            with yc3:
                ypn = st.text_input(f"Notes {i+1}", key=f"ypn_{i}", value=eyp.get('notes', ''))
            if ypt:
                yp_data.append({'pooja_type_id': pt_map.get(ypt), 'pooja_name': ypt,
                    'pooja_date': ypd.isoformat() if ypd else None, 'notes': ypn or None})

        submitted = st.form_submit_button("💾 Save Devotee", use_container_width=True)

        if submitted:
            if not name.strip():
                st.error("Name is required!")
            else:
                rec = {
                    'name': name.strip(), 'dob': dob.isoformat() if dob else None,
                    'relation_type': relation or None, 'mobile_no': mobile or None,
                    'whatsapp_no': whatsapp or None, 'wedding_day': wedding.isoformat() if wedding else None,
                    'natchathiram': natchathiram or None, 'address': address or None,
                    'is_family_head': True, 'is_active': True
                }
                try:
                    if edit_id:
                        db.table('devotee').update(rec).eq('id', edit_id).execute()
                        dev_id = edit_id
                        db.table('devotee').delete().eq('family_head_id', edit_id).execute()
                        db.table('devotee_yearly_pooja').delete().eq('devotee_id', edit_id).execute()
                    else:
                        r = db.table('devotee').insert(rec).execute()
                        dev_id = r.data[0]['id']

                    for fm in family_data:
                        fm_rec = {**fm, 'is_family_head': False, 'family_head_id': dev_id,
                                   'address': address or None, 'is_active': True}
                        db.table('devotee').insert(fm_rec).execute()

                    for yp in yp_data:
                        db.table('devotee_yearly_pooja').insert({**yp, 'devotee_id': dev_id}).execute()

                    st.success(f"✅ Devotee {'updated' if edit_id else 'added'}!")
                    st.session_state['page'] = 'devotees'
                    st.session_state['edit_devotee_id'] = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


# ============================================================
# BILLING
# ============================================================
def pg_billing():
    db = get_db()
    st.markdown("### 🧾 Bills")

    c1, c2 = st.columns([3, 1])
    with c2:
        if st.button("➕ New Bill", use_container_width=True):
            st.session_state['page'] = 'new_bill'
            st.rerun()

    fc1, fc2 = st.columns(2)
    with fc1:
        from_d = st.date_input("From", value=date.today(), key="bf")
    with fc2:
        to_d = st.date_input("To", value=date.today(), key="bt")

    try:
        bills = db.table('bill').select('*, devotee(name), pooja_type(name)').gte('bill_date', from_d.isoformat()).lte('bill_date', to_d.isoformat() + 'T23:59:59').order('bill_date', desc=True).execute()

        total_active = 0
        if bills.data:
            for b in bills.data:
                deleted = b.get('is_deleted', False)
                name = (b.get('devotee') or {}).get('name', '') or b.get('guest_name', '-')
                pooja = (b.get('pooja_type') or {}).get('name', '-')
                amt = b.get('amount', 0) or 0
                status = "🗑️ DELETED" if deleted else "✅"
                if not deleted:
                    total_active += amt

                with st.expander(f"{status} {b.get('bill_number','-')} | {name} | {pooja} | ₹{amt:,.2f}"):
                    st.write(f"**Bill:** {b.get('bill_number','-')} | **Manual:** {b.get('manual_bill_no','-')}")
                    st.write(f"**Date:** {str(b.get('bill_date','-'))[:16]} | **Name:** {name}")
                    st.write(f"**Pooja:** {pooja} | **Amount:** ₹{amt:,.2f}")
                    st.write(f"**Notes:** {b.get('notes','-')}")

                    if not deleted:
                        bc1, bc2 = st.columns(2)
                        with bc1:
                            if st.button("🖨️ View/Print", key=f"pb_{b['id']}"):
                                st.session_state['print_bill_id'] = b['id']
                                st.session_state['page'] = 'view_bill'
                                st.rerun()
                        with bc2:
                            if st.session_state['role'] == 'admin':
                                reason = st.text_input("Reason", key=f"dr_{b['id']}")
                                if st.button("🗑️ Delete", key=f"db_{b['id']}"):
                                    if reason.strip():
                                        db.table('bill').update({
                                            'is_deleted': True, 'deleted_by': st.session_state['user_id'],
                                            'deleted_at': datetime.now().isoformat(), 'delete_reason': reason
                                        }).eq('id', b['id']).execute()
                                        st.success("Deleted!")
                                        st.rerun()
                                    else:
                                        st.warning("Enter reason!")

            st.markdown(f"**Total Active: ₹{total_active:,.2f}**")
        else:
            st.info("No bills found")
    except Exception as e:
        st.error(f"Error: {e}")


# ============================================================
# NEW BILL
# ============================================================
def pg_new_bill():
    db = get_db()
    st.markdown("### 🧾 New Bill")

    if st.button("⬅️ Back"):
        st.session_state['page'] = 'billing'
        st.rerun()

    try:
        last_b = db.table('bill').select('id').order('id', desc=True).limit(1).execute()
        nid = (last_b.data[0]['id'] + 1) if last_b.data else 1
    except:
        nid = 1
    next_no = f"BILL-{nid:06d}"

    with st.form("bill_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            bill_no = st.text_input("Bill Number", value=next_no, disabled=True)
        with c2:
            manual_no = st.text_input("Manual Bill No")
        with c3:
            book_no = st.text_input("Bill Book No")

        bill_date = st.date_input("Date", value=date.today())
        dev_type = st.radio("Type", ["Enrolled", "Guest"], horizontal=True)

        devotee_id = None
        guest_name = guest_addr = guest_mob = guest_wa = None

        if dev_type == "Enrolled":
            try:
                devs = db.table('devotee').select('id, name, mobile_no, address').eq('is_family_head', True).eq('is_active', True).order('name').execute()
                if devs.data:
                    opts = {f"{d['name']} (ID:{d['id']})": d for d in devs.data}
                    sel = st.selectbox("Select Devotee *", [''] + list(opts.keys()))
                    if sel:
                        devotee_id = opts[sel]['id']
                        st.info(f"📱 {opts[sel].get('mobile_no','-')} | 📍 {opts[sel].get('address','-')}")
                else:
                    st.warning("No devotees found")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            gc1, gc2 = st.columns(2)
            with gc1:
                guest_name = st.text_input("Guest Name *")
                guest_mob = st.text_input("Guest Mobile")
            with gc2:
                guest_addr = st.text_area("Guest Address", height=68)
                guest_wa = st.text_input("Guest WhatsApp")

        st.markdown("---")

        try:
            pts = db.table('pooja_type').select('*').eq('is_active', True).execute()
            pt_list = pts.data or []
        except:
            pt_list = []

        pt_opts = {f"{p['name']} (₹{p['amount']})": p for p in pt_list}
        sel_pooja = st.selectbox("Pooja *", [''] + list(pt_opts.keys()))
        def_amt = pt_opts[sel_pooja]['amount'] if sel_pooja else 0
        amount = st.number_input("Amount *", min_value=0.0, value=float(def_amt), step=1.0)
        notes = st.text_input("Notes")

        if st.form_submit_button("💾 Create Bill", use_container_width=True):
            if dev_type == "Enrolled" and not devotee_id:
                st.error("Select a devotee!")
            elif dev_type == "Guest" and not (guest_name and guest_name.strip()):
                st.error("Enter guest name!")
            elif not sel_pooja:
                st.error("Select pooja!")
            elif amount <= 0:
                st.error("Amount must be > 0!")
            else:
                try:
                    rec = {
                        'bill_number': next_no, 'manual_bill_no': manual_no or None,
                        'bill_book_no': book_no or None,
                        'bill_date': bill_date.isoformat() + 'T' + datetime.now().strftime('%H:%M:%S'),
                        'devotee_type': 'enrolled' if dev_type == "Enrolled" else 'guest',
                        'devotee_id': devotee_id if dev_type == "Enrolled" else None,
                        'guest_name': guest_name if dev_type == "Guest" else None,
                        'guest_address': guest_addr if dev_type == "Guest" else None,
                        'guest_mobile': guest_mob if dev_type == "Guest" else None,
                        'guest_whatsapp': guest_wa if dev_type == "Guest" else None,
                        'pooja_type_id': pt_opts[sel_pooja]['id'], 'amount': amount,
                        'notes': notes or None, 'created_by': st.session_state['user_id'],
                        'is_deleted': False
                    }
                    r = db.table('bill').insert(rec).execute()
                    st.success(f"✅ Bill {next_no} created!")
                    st.session_state['print_bill_id'] = r.data[0]['id']
                    st.session_state['page'] = 'view_bill'
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


# ============================================================
# VIEW/PRINT BILL
# ============================================================
def pg_view_bill():
    db = get_db()
    bid = st.session_state.get('print_bill_id')

    if not bid:
        st.session_state['page'] = 'billing'
        st.rerun()
        return

    if st.button("⬅️ Back to Bills"):
        st.session_state['page'] = 'billing'
        st.rerun()

    try:
        r = db.table('bill').select('*, devotee(name, mobile_no, address), pooja_type(name)').eq('id', bid).execute()
        if not r.data:
            st.error("Bill not found!")
            return

        b = r.data[0]
        name = (b.get('devotee') or {}).get('name', '') or b.get('guest_name', '-')
        mobile = (b.get('devotee') or {}).get('mobile_no', '') or b.get('guest_mobile', '-')
        addr = (b.get('devotee') or {}).get('address', '') or b.get('guest_address', '-')
        pooja = (b.get('pooja_type') or {}).get('name', '-')
        amt = b.get('amount', 0)

        # Get amman image for bill
        amman_img = get_amman_image()
        amman_html = f'<img src="{amman_img}" style="width:55px;height:55px;border-radius:50%;border:2px solid #FFD700;object-fit:cover;">' if amman_img else '🕉️'

        st.markdown(f"""
        <div style="background:white; padding:30px; border-radius:12px; box-shadow:0 2px 15px rgba(0,0,0,0.1); max-width:700px; margin:auto;">
            <div class="bill-hdr">
                <div style="display:flex;align-items:center;justify-content:center;gap:15px;margin-bottom:10px;">
                    {amman_html}
                    <div>
                        <h2 style="color:#8B0000;margin:0;">{TEMPLE_NAME}</h2>
                        <h4 style="color:#DC143C;margin:2px 0;">{TEMPLE_TRUST} - {TEMPLE_REG}</h4>
                    </div>
                    {amman_html}
                </div>
                <p>{TEMPLE_PLACE}, {TEMPLE_DISTRICT}</p>
                <p><strong>BILL RECEIPT</strong></p>
            </div>

            <table style="width:100%;font-size:0.9em;">
                <tr><td><strong>Bill:</strong> {b.get('bill_number','-')}</td><td><strong>Manual:</strong> {b.get('manual_bill_no','-')}</td></tr>
                <tr><td><strong>Date:</strong> {str(b.get('bill_date','-'))[:16]}</td><td><strong>Book:</strong> {b.get('bill_book_no','-')}</td></tr>
            </table>
            <hr style="border-color:#FFD700;">
            <p><strong>Name:</strong> {name} | <strong>Mobile:</strong> {mobile}</p>
            <p><strong>Address:</strong> {addr}</p>
            <hr style="border-color:#FFD700;">
            <table style="width:100%;border-collapse:collapse;margin:15px 0;">
                <thead><tr style="background:linear-gradient(135deg,#8B0000,#DC143C);color:white;">
                    <th style="padding:8px;text-align:left;">Pooja</th>
                    <th style="padding:8px;text-align:left;">Notes</th>
                    <th style="padding:8px;text-align:right;">Amount</th>
                </tr></thead>
                <tbody><tr>
                    <td style="padding:8px;border:1px solid #ddd;">{pooja}</td>
                    <td style="padding:8px;border:1px solid #ddd;">{b.get('notes','-')}</td>
                    <td style="padding:8px;text-align:right;border:1px solid #ddd;">₹{amt:,.2f}</td>
                </tr></tbody>
                <tfoot><tr>
                    <td colspan="2" style="padding:8px;text-align:right;"><strong>Total:</strong></td>
                    <td style="padding:8px;text-align:right;color:#8B0000;font-size:1.2em;"><strong>₹{amt:,.2f}</strong></td>
                </tr></tfoot>
            </table>
            <div style="text-align:center;margin-top:15px;padding-top:10px;border-top:1px dashed #ccc;">
                <small style="color:#888;">{TEMPLE_FULL}</small><br>
                <small style="color:#888;">🕉️ Thank you 🙏</small>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.info("📌 Use Ctrl+P (or Cmd+P on Mac) to print this bill")
    except Exception as e:
        st.error(f"Error: {e}")


# ============================================================
# EXPENSES
# ============================================================
def pg_expenses():
    db = get_db()
    st.markdown("### 💰 Expenses")

    fc1, fc2 = st.columns(2)
    with fc1:
        from_d = st.date_input("From", value=date.today().replace(day=1), key="ef")
    with fc2:
        to_d = st.date_input("To", value=date.today(), key="et")

    with st.expander("��� Add Expense"):
        try:
            ets = db.table('expense_type').select('*').eq('is_active', True).execute()
            et_list = ets.data or []
        except:
            et_list = []
        et_opts = {e['name']: e['id'] for e in et_list}

        with st.form("exp_form"):
            ec1, ec2, ec3 = st.columns(3)
            with ec1:
                etype = st.selectbox("Type *", list(et_opts.keys()) if et_opts else [])
            with ec2:
                eamt = st.number_input("Amount *", min_value=0.01, step=1.0)
            with ec3:
                edate = st.date_input("Date", value=date.today(), key="ned")
            edesc = st.text_area("Description", height=68)

            if st.form_submit_button("💾 Save"):
                if etype and eamt > 0:
                    try:
                        db.table('expense').insert({
                            'expense_type_id': et_opts[etype], 'amount': eamt,
                            'description': edesc or None, 'expense_date': edate.isoformat(),
                            'created_by': st.session_state['user_id']
                        }).execute()
                        st.success("✅ Added!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    try:
        import pandas as pd
        exps = db.table('expense').select('*, expense_type(name)').gte('expense_date', from_d.isoformat()).lte('expense_date', to_d.isoformat()).order('expense_date', desc=True).execute()
        if exps.data:
            total = 0
            rows = []
            for e in exps.data:
                total += e.get('amount', 0) or 0
                rows.append({'ID': e['id'], 'Date': e.get('expense_date', '-'),
                             'Type': (e.get('expense_type') or {}).get('name', '-'),
                             'Description': e.get('description', '-'),
                             'Amount': f"₹{e.get('amount',0):,.2f}"})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.markdown(f"**Total: ₹{total:,.2f}**")

            del_id = st.number_input("Expense ID to delete", min_value=0, step=1, key="edel")
            if st.button("🗑️ Delete Expense") and del_id > 0:
                db.table('expense').delete().eq('id', int(del_id)).execute()
                st.success("Deleted!")
                st.rerun()
        else:
            st.info("No expenses found")
    except Exception as e:
        st.error(f"Error: {e}")


# ============================================================
# REPORTS
# ============================================================
def pg_reports():
    db = get_db()
    st.markdown("### 📊 Reports")

    c1, c2 = st.columns(2)
    with c1:
        from_d = st.date_input("From", value=date.today().replace(day=1), key="rf")
    with c2:
        to_d = st.date_input("To", value=date.today(), key="rt")

    try:
        bills = db.table('bill').select('amount, pooja_type(name)').eq('is_deleted', False).gte('bill_date', from_d.isoformat()).lte('bill_date', to_d.isoformat() + 'T23:59:59').execute()
        income = sum(b['amount'] or 0 for b in (bills.data or []))

        exps = db.table('expense').select('amount, expense_type(name)').gte('expense_date', from_d.isoformat()).lte('expense_date', to_d.isoformat()).execute()
        expense = sum(e['amount'] or 0 for e in (exps.data or []))

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="stat-card stat-income"><p>📈 Income</p><h3>₹{income:,.2f}</h3></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="stat-card stat-expense"><p>📉 Expenses</p><h3>₹{expense:,.2f}</h3></div>', unsafe_allow_html=True)
        with c3:
            net = income - expense
            st.markdown(f'<div class="stat-card" style="background:linear-gradient(135deg,#4B0082,#8A2BE2);"><p>💰 Net</p><h3>₹{net:,.2f}</h3></div>', unsafe_allow_html=True)

        from collections import defaultdict
        import pandas as pd

        cl, cr = st.columns(2)
        with cl:
            st.markdown("#### 🙏 Income by Pooja")
            pi = defaultdict(lambda: {'count': 0, 'total': 0})
            for b in (bills.data or []):
                n = (b.get('pooja_type') or {}).get('name', 'Other')
                pi[n]['count'] += 1
                pi[n]['total'] += b['amount'] or 0
            if pi:
                st.dataframe(pd.DataFrame([{'Pooja': k, 'Count': v['count'], 'Amount': f"₹{v['total']:,.2f}"} for k, v in pi.items()]), use_container_width=True, hide_index=True)

        with cr:
            st.markdown("#### 💸 Expenses by Type")
            pe = defaultdict(lambda: {'count': 0, 'total': 0})
            for e in (exps.data or []):
                n = (e.get('expense_type') or {}).get('name', 'Other')
                pe[n]['count'] += 1
                pe[n]['total'] += e['amount'] or 0
            if pe:
                st.dataframe(pd.DataFrame([{'Type': k, 'Count': v['count'], 'Amount': f"₹{v['total']:,.2f}"} for k, v in pe.items()]), use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Error: {e}")


# ============================================================
# SAMAYA VAKUPPU
# ============================================================
def pg_samaya():
    db = get_db()
    st.markdown("### 🎓 Samaya Vakuppu")

    with st.expander("➕ Add Student"):
        with st.form("sam_form"):
            sc1, sc2 = st.columns(2)
            with sc1:
                sn = st.text_input("Student Name *")
                sd = st.date_input("DOB", value=None, key="sdob")
                sf = st.text_input("Father/Mother")
                sb = st.text_input("Bank")
            with sc2:
                sbn = st.text_input("Bond No")
                sbd = st.date_input("Bond Date", value=None, key="sbond")
                sbr = st.text_input("Branch")
                sa = st.text_area("Address", height=68)
            if st.form_submit_button("💾 Save"):
                if sn.strip():
                    try:
                        db.table('samaya_vakuppu').insert({
                            'student_name': sn, 'dob': sd.isoformat() if sd else None,
                            'father_mother_name': sf or None, 'bond_no': sbn or None,
                            'bond_issue_date': sbd.isoformat() if sbd else None,
                            'bond_issuing_bank': sb or None, 'branch_of_bank': sbr or None,
                            'address': sa or None
                        }).execute()
                        st.success("✅ Added!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    try:
        import pandas as pd
        students = db.table('samaya_vakuppu').select('*').order('student_name').execute()
        if students.data:
            rows = [{'ID': s['id'], 'Name': s['student_name'],
                      'DOB': safe_date_display(s.get('dob')),
                      'Father/Mother': s.get('father_mother_name', '-'),
                      'Bond No': s.get('bond_no', '-'),
                      'Bond Date': safe_date_display(s.get('bond_issue_date')),
                      'Bank': s.get('bond_issuing_bank', '-')} for s in students.data]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            did = st.number_input("Student ID to delete", min_value=0, step=1, key="sdel")
            if st.button("🗑️ Delete") and did > 0:
                db.table('samaya_vakuppu').delete().eq('id', int(did)).execute()
                st.success("Deleted!")
                st.rerun()
        else:
            st.info("No students found")
    except Exception as e:
        st.error(f"Error: {e}")


# ============================================================
# MANDAPAM
# ============================================================
def pg_mandapam():
    db = get_db()
    st.markdown("### 🏛️ Thirumana Mandapam")

    with st.expander("➕ Add Record"):
        with st.form("mand_form"):
            mc1, mc2 = st.columns(2)
            with mc1:
                mn = st.text_input("Name *")
                mbn = st.text_input("Bond No")
                mbd = st.date_input("Bond Date", value=None, key="mbd")
            with mc2:
                ma = st.number_input("Amount", min_value=0.0, step=1.0)
                mnb = st.number_input("No of Bonds", min_value=1, value=1)
                mad = st.text_area("Address", height=68)
            if st.form_submit_button("💾 Save"):
                if mn.strip():
                    try:
                        db.table('thirumana_mandapam').insert({
                            'name': mn, 'bond_no': mbn or None,
                            'bond_issued_date': mbd.isoformat() if mbd else None,
                            'amount': ma, 'no_of_bond': mnb, 'address': mad or None
                        }).execute()
                        st.success("✅ Added!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    try:
        import pandas as pd
        recs = db.table('thirumana_mandapam').select('*').order('name').execute()
        if recs.data:
            rows = [{'ID': m['id'], 'Name': m['name'], 'Bond No': m.get('bond_no', '-'),
                      'Date': safe_date_display(m.get('bond_issued_date')),
                      'Amount': f"₹{m.get('amount',0):,.2f}",
                      'Bonds': m.get('no_of_bond', 1)} for m in recs.data]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            did = st.number_input("Record ID to delete", min_value=0, step=1, key="mdel")
            if st.button("🗑️ Delete") and did > 0:
                db.table('thirumana_mandapam').delete().eq('id', int(did)).execute()
                st.success("Deleted!")
                st.rerun()
        else:
            st.info("No records found")
    except Exception as e:
        st.error(f"Error: {e}")


# ============================================================
# DAILY POOJA
# ============================================================
def pg_daily_pooja():
    db = get_db()
    st.markdown("### 🙏 Daily Pooja Schedule")

    with st.expander("➕ Add Pooja"):
        with st.form("dp_form"):
            dpn = st.text_input("Name *")
            dpt = st.text_input("Time (e.g. 6:00 AM)")
            dpd = st.text_input("Description")
            if st.form_submit_button("💾 Save"):
                if dpn.strip():
                    try:
                        db.table('daily_pooja').insert({
                            'pooja_name': dpn, 'pooja_time': dpt or None,
                            'description': dpd or None, 'is_active': True
                        }).execute()
                        st.success("✅ Added!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    try:
        poojas = db.table('daily_pooja').select('*').eq('is_active', True).order('pooja_time').execute()
        if poojas.data:
            for p in poojas.data:
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"""<div class="pooja-card">
                        <strong>{p['pooja_name']}</strong> -
                        <span style="color:#8B0000;font-weight:700;">{p.get('pooja_time','TBD')}</span>
                        <br><small style="color:#666;">{p.get('description','')}</small>
                    </div>""", unsafe_allow_html=True)
                with c2:
                    if st.button("🗑️", key=f"dpd_{p['id']}"):
                        db.table('daily_pooja').update({'is_active': False}).eq('id', p['id']).execute()
                        st.rerun()
        else:
            st.info("No poojas")
    except Exception as e:
        st.error(f"Error: {e}")


# ============================================================
# SETTINGS
# ============================================================
def pg_settings():
    db = get_db()
    st.markdown("### ⚙️ Settings - Pooja & Expense Types")

    cl, cr = st.columns(2)

    with cl:
        st.markdown("#### 🙏 Pooja Types")
        with st.form("pt_form"):
            ptn = st.text_input("Pooja Name *", key="ptn")
            pta = st.number_input("Amount (₹)", min_value=0.0, step=1.0, key="pta")
            if st.form_submit_button("➕ Add Pooja Type"):
                if ptn.strip():
                    try:
                        db.table('pooja_type').insert({'name': ptn, 'amount': pta, 'is_active': True}).execute()
                        st.success("Added!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        try:
            pts = db.table('pooja_type').select('*').eq('is_active', True).execute()
            for pt in (pts.data or []):
                pc1, pc2, pc3 = st.columns([3, 1, 1])
                with pc1:
                    st.write(f"**{pt['name']}**")
                with pc2:
                    st.write(f"₹{pt['amount']}")
                with pc3:
                    if st.button("🗑️", key=f"ptd_{pt['id']}"):
                        db.table('pooja_type').update({'is_active': False}).eq('id', pt['id']).execute()
                        st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    with cr:
        st.markdown("#### 💰 Expense Types")
        with st.form("et_form"):
            etn = st.text_input("Expense Type Name *", key="etn")
            if st.form_submit_button("➕ Add Expense Type"):
                if etn.strip():
                    try:
                        db.table('expense_type').insert({'name': etn, 'is_active': True}).execute()
                        st.success("Added!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        try:
            ets = db.table('expense_type').select('*').eq('is_active', True).execute()
            for et in (ets.data or []):
                ec1, ec2 = st.columns([4, 1])
                with ec1:
                    st.write(f"**{et['name']}**")
                with ec2:
                    if st.button("🗑️", key=f"etd_{et['id']}"):
                        db.table('expense_type').update({'is_active': False}).eq('id', et['id']).execute()
                        st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")


# ============================================================
# USER MANAGEMENT
# ============================================================
def pg_users():
    db = get_db()
    if st.session_state['role'] != 'admin':
        st.error("Admin only!")
        return

    st.markdown("### 👤 User Management")

    with st.expander("➕ Add New User"):
        with st.form("usr_form"):
            un = st.text_input("Username *")
            ufn = st.text_input("Full Name")
            upw = st.text_input("Password *", type="password")
            ur = st.selectbox("Role", ["user", "admin"])
            if st.form_submit_button("💾 Create User"):
                if un.strip() and upw:
                    try:
                        existing = db.table('users').select('id').eq('username', un).execute()
                        if existing.data:
                            st.error("Username exists!")
                        else:
                            db.table('users').insert({
                                'username': un, 'password_hash': hash_password(upw),
                                'full_name': ufn or None, 'role': ur, 'is_active_user': True
                            }).execute()
                            st.success("✅ Created!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    try:
        users = db.table('users').select('*').execute()
        for u in (users.data or []):
            c1, c2, c3 = st.columns([3, 2, 1])
            with c1:
                st.write(f"**{u['username']}** ({u.get('full_name', '-')})")
            with c2:
                role = "🔑 Admin" if u['role'] == 'admin' else "👤 User"
                status = "✅ Active" if u['is_active_user'] else "❌ Inactive"
                st.write(f"{role} | {status}")
            with c3:
                if u['id'] != st.session_state['user_id']:
                    if st.button("Toggle", key=f"ut_{u['id']}"):
                        db.table('users').update({'is_active_user': not u['is_active_user']}).eq('id', u['id']).execute()
                        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")


# ============================================================
# DELETED BILLS
# ============================================================
def pg_deleted_bills():
    db = get_db()
    if st.session_state['role'] != 'admin':
        st.error("Admin only!")
        return

    st.markdown("### 🗑️ Deleted Bills")

    try:
        import pandas as pd
        bills = db.table('bill').select('*, devotee(name), pooja_type(name)').eq('is_deleted', True).order('deleted_at', desc=True).execute()
        users_r = db.table('users').select('id, username, full_name').execute()
        um = {u['id']: u.get('full_name') or u['username'] for u in (users_r.data or [])}

        if bills.data:
            rows = [{'Bill': b.get('bill_number', '-'),
                      'Date': str(b.get('bill_date', '-'))[:10],
                      'Name': (b.get('devotee') or {}).get('name', '') or b.get('guest_name', '-'),
                      'Amount': f"₹{b.get('amount',0):,.2f}",
                      'Deleted By': um.get(b.get('deleted_by'), '-'),
                      'Deleted At': str(b.get('deleted_at', '-'))[:16],
                      'Reason': b.get('delete_reason', '-')} for b in bills.data]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("No deleted bills")
    except Exception as e:
        st.error(f"Error: {e}")


# ============================================================
# MAIN
# ============================================================
def main():
    init_session()
    apply_css()

    try:
        init_default_data()
    except Exception as e:
        st.error(f"DB Init Error: {e}")
        st.code(traceback.format_exc())
        st.stop()

    if not st.session_state['logged_in']:
        login_page()
        return

    sidebar()

    pages = {
        'dashboard': pg_dashboard,
        'devotees': pg_devotees,
        'add_devotee': pg_add_devotee,
        'billing': pg_billing,
        'new_bill': pg_new_bill,
        'view_bill': pg_view_bill,
        'expenses': pg_expenses,
        'reports': pg_reports,
        'samaya': pg_samaya,
        'mandapam': pg_mandapam,
        'daily_pooja': pg_daily_pooja,
        'settings': pg_settings,
        'temple_images': pg_temple_images,
        'users': pg_users,
        'deleted_bills': pg_deleted_bills,
    }

    page_fn = pages.get(st.session_state.get('page', 'dashboard'), pg_dashboard)
    try:
        page_fn()
    except Exception as e:
        st.error(f"Page Error: {e}")
        st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
