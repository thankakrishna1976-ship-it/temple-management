import streamlit as st
import httpx
import json
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

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
# TEMPLE CONFIG
# ============================================================
TEMPLE_NAME = "Arulmigu Bhadreshwari Amman Kovil"
TEMPLE_TRUST = "Samrakshana Seva Trust"
TEMPLE_REG = "179/2004"
TEMPLE_PLACE = "Kanjampuram"
TEMPLE_DISTRICT = "Kanniyakumari Dist- 629154"
TEMPLE_ADDRESS_LINE2 = f"{TEMPLE_TRUST} - {TEMPLE_REG}"
TEMPLE_ADDRESS_LINE3 = f"{TEMPLE_PLACE}, {TEMPLE_DISTRICT}"
TEMPLE_FULL_ADDRESS = f"{TEMPLE_NAME}, {TEMPLE_ADDRESS_LINE2}, {TEMPLE_ADDRESS_LINE3}"

NATCHATHIRAM_LIST = [
    'அசுவினி (Ashwini)', 'பரணி (Bharani)', 'கார்த்திகை (Krittika)',
    'ரோகிணி (Rohini)', 'மிருகசீரிடம் (Mrigashira)', 'திருவாதிரை (Ardra)',
    'புனர்பூசம் (Punarvasu)', 'பூசம் (Pushya)', 'ஆயில்யம் (Ashlesha)',
    'மகம் (Magha)', 'பூரம் (Purva Phalguni)', 'உத்திரம் (Uttara Phalguni)',
    'ஹஸ்தம் (Hasta)', 'சித்திரை (Chitra)', 'ச��வாதி (Swati)',
    'விசாகம் (Vishakha)', 'அனுஷம் (Anuradha)', 'கேட்டை (Jyeshtha)',
    '��ூலம் (Mula)', 'பூராடம் (Purva Ashadha)', 'உத்திராடம் (Uttara Ashadha)',
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
# DATABASE - SUPABASE REST API (NO supabase package needed!)
# ============================================================
def get_headers():
    """Get Supabase REST API headers"""
    key = st.secrets["supabase"]["key"]
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }


def get_url():
    """Get Supabase REST API base URL"""
    return st.secrets["supabase"]["url"] + "/rest/v1"


def db_select(table, columns="*", filters=None, order=None, limit=None):
    """SELECT from database"""
    try:
        url = f"{get_url()}/{table}?select={columns}"
        if filters:
            for key, value in filters.items():
                if isinstance(value, bool):
                    url += f"&{key}=eq.{str(value).lower()}"
                elif isinstance(value, dict):
                    for op, val in value.items():
                        url += f"&{key}={op}.{val}"
                else:
                    url += f"&{key}=eq.{value}"
        if order:
            if order.startswith('-'):
                url += f"&order={order[1:]}.desc"
            else:
                url += f"&order={order}.asc"
        if limit:
            url += f"&limit={limit}"

        response = httpx.get(url, headers=get_headers(), timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"DB Read Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        st.error(f"DB Error: {e}")
        return []


def db_insert(table, data):
    """INSERT into database"""
    try:
        url = f"{get_url()}/{table}"
        response = httpx.post(url, headers=get_headers(), json=data, timeout=30)
        if response.status_code in [200, 201]:
            result = response.json()
            return result[0] if result else None
        else:
            st.error(f"DB Insert Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Insert Error: {e}")
        return None


def db_update(table, data, match_column, match_value):
    """UPDATE database records"""
    try:
        url = f"{get_url()}/{table}?{match_column}=eq.{match_value}"
        response = httpx.patch(url, headers=get_headers(), json=data, timeout=30)
        if response.status_code in [200, 204]:
            return True
        else:
            st.error(f"DB Update Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Update Error: {e}")
        return None


def db_delete(table, match_column, match_value):
    """DELETE from database"""
    try:
        url = f"{get_url()}/{table}?{match_column}=eq.{match_value}"
        response = httpx.delete(url, headers=get_headers(), timeout=30)
        if response.status_code in [200, 204]:
            return True
        else:
            st.error(f"DB Delete Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Delete Error: {e}")
        return None


# ============================================================
# CSS
# ============================================================
def load_css():
    st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(135deg, #8B0000, #DC143C);
            color: #FFD700; padding: 15px 25px; border-radius: 12px;
            margin-bottom: 20px; text-align: center;
            box-shadow: 0 4px 15px rgba(139,0,0,0.3);
        }
        .main-header h1 { color: #FFD700; font-size: 1.5em; margin: 0; }
        .main-header h3 { color: rgba(255,215,0,0.8); font-size: 0.9em; margin: 2px 0; }
        .main-header p { color: rgba(255,248,220,0.8); font-size: 0.75em; margin: 0; }
        .stat-card {
            border-radius: 15px; padding: 20px; color: white;
            box-shadow: 0 5px 20px rgba(0,0,0,0.15); margin-bottom: 15px;
        }
        .stat-card.income { background: linear-gradient(135deg, #228B22, #32CD32); }
        .stat-card.expense { background: linear-gradient(135deg, #DC143C, #FF4500); }
        .stat-card.devotees { background: linear-gradient(135deg, #4169E1, #6495ED); }
        .stat-card.bills { background: linear-gradient(135deg, #FF8C00, #FFD700); }
        .stat-card h4 { font-size: 0.85em; opacity: 0.9; margin-bottom: 5px; }
        .stat-card h2 { font-size: 1.8em; font-weight: 700; margin: 0; }
        .pooja-card {
            background: linear-gradient(135deg, #FFF8DC, #FFEFD5);
            border: 1px solid #FFD700; border-radius: 10px; padding: 12px;
            margin-bottom: 8px; border-left: 4px solid #8B0000;
        }
        .news-ticker {
            background: linear-gradient(90deg, #8B0000, #DC143C, #8B0000);
            color: #FFD700; padding: 10px 20px; border-radius: 10px;
            margin-bottom: 15px; text-align: center;
        }
        .family-card {
            background: #f8f9fa; border: 1px solid #dee2e6;
            border-radius: 10px; padding: 12px; margin-bottom: 8px;
        }
        .yearly-pooja-card {
            background: #FFF8DC; border: 1px solid #FFD700;
            border-radius: 8px; padding: 8px 12px; margin-bottom: 6px;
        }
        .bill-receipt {
            background: white; padding: 25px; border-radius: 12px;
            box-shadow: 0 2px 15px rgba(0,0,0,0.08); border: 2px solid #FFD700;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #8B0000, #B22222, #DC143C);
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] { color: #FFF8DC; }
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
        'view_bill_id': None, 'edit_samaya_id': None,
        'edit_mandapam_id': None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def is_admin():
    return st.session_state.get('role') == 'admin'


def go_to(page, **kwargs):
    st.session_state['page'] = page
    for k, v in kwargs.items():
        st.session_state[k] = v
    st.rerun()


# ============================================================
# LOGIN
# ============================================================
def login_page():
    st.markdown(f"""
    <div style="text-align:center; padding:30px;">
        <div style="font-size:80px;">🕉️</div>
        <h1 style="color:#8B0000;">{TEMPLE_NAME}</h1>
        <h3 style="color:#DC143C;">{TEMPLE_TRUST}</h3>
        <p style="color:#666;">{TEMPLE_ADDRESS_LINE3}</p>
        <hr style="border-color:#FFD700; width:50%; margin:15px auto;">
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login"):
            username = st.text_input("👤 Username")
            password = st.text_input("🔒 Password", type="password")
            btn = st.form_submit_button("🔑 Login", use_container_width=True)

            if btn and username and password:
                users = db_select("users", filters={
                    "username": username,
                    "is_active_user": True
                })
                if users:
                    user = users[0]
                    if check_password_hash(user['password_hash'], password):
                        st.session_state['logged_in'] = True
                        st.session_state['user_id'] = user['id']
                        st.session_state['username'] = user['username']
                        st.session_state['full_name'] = user.get('full_name') or user['username']
                        st.session_state['role'] = user['role']
                        st.success("Welcome! 🙏")
                        st.rerun()
                    else:
                        st.error("❌ Wrong password!")
                else:
                    st.error("❌ User not found!")
            elif btn:
                st.warning("Enter username and password")


# ============================================================
# SIDEBAR
# ============================================================
def sidebar():
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center; padding:10px;">
            <div style="font-size:50px;">🕉️</div>
            <h4 style="color:#FFD700; font-size:0.85em;">{TEMPLE_NAME}</h4>
            <p style="color:rgba(255,215,0,0.7); font-size:0.7em;">{TEMPLE_TRUST}</p>
            <p style="color:#FFD700; font-size:0.75em;">
                👤 {st.session_state['full_name']}
                {"🔴 ADMIN" if is_admin() else ""}
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        menu = [
            ("📊 Dashboard", "dashboard"),
            ("👥 Devotees", "devotees"),
            ("🧾 Billing", "billing"),
            ("💸 Expenses", "expenses"),
            ("📈 Reports", "reports"),
            (None, None),
            ("🎓 Samaya Vakuppu", "samaya"),
            ("🏛️ Mandapam", "mandapam"),
            ("🙏 Daily Pooja", "daily_pooja"),
            ("⚙️ Settings", "settings"),
        ]
        if is_admin():
            menu += [(None, None), ("👤 Users", "users"), ("🗑️ Deleted Bills", "deleted_bills")]

        for label, page in menu:
            if label is None:
                st.markdown("---")
            else:
                if st.button(label, key=f"m_{page}", use_container_width=True):
                    go_to(page)

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


# ============================================================
# DASHBOARD
# ============================================================
def page_dashboard():
    st.markdown(f"""<div class="main-header">
        <h1>🕉️ {TEMPLE_NAME}</h1><h3>{TEMPLE_TRUST}</h3>
        <p>{TEMPLE_ADDRESS_LINE3}</p></div>""", unsafe_allow_html=True)

    period = st.radio("Period:", ['Daily', 'Weekly', 'Monthly', 'Yearly'],
                       horizontal=True, label_visibility="collapsed")

    today_d = date.today()
    if period == 'Daily':
        sd, ed = today_d, today_d
    elif period == 'Weekly':
        sd, ed = today_d - timedelta(days=today_d.weekday()), today_d
    elif period == 'Monthly':
        sd, ed = today_d.replace(day=1), today_d
    else:
        sd, ed = today_d.replace(month=1, day=1), today_d

    # Stats
    bills = db_select("bill", "amount,bill_date", filters={"is_deleted": False})
    pb = [b for b in bills if sd.isoformat() <= str(b.get('bill_date', ''))[:10] <= ed.isoformat()]
    ti = sum(float(b.get('amount', 0) or 0) for b in pb)

    exps = db_select("expense", "amount,expense_date")
    pe = [e for e in exps if sd.isoformat() <= str(e.get('expense_date', ''))[:10] <= ed.isoformat()]
    te = sum(float(e.get('amount', 0) or 0) for e in pe)

    devs = db_select("devotee", "id", filters={"is_family_head": True, "is_active": True})
    td_count = len(devs)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="stat-card income"><h4>⬆️ Income</h4><h2>₹{ti:,.2f}</h2></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-card expense"><h4>⬇️ Expenses</h4><h2>₹{te:,.2f}</h2></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat-card devotees"><h4>👥 Devotees</h4><h2>{td_count}</h2></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="stat-card bills"><h4>🧾 Bills</h4><h2>{len(pb)}</h2></div>', unsafe_allow_html=True)

    # Birthdays
    all_devs = db_select("devotee", "name,mobile_no,dob", filters={"is_active": True})
    bdays = [d for d in all_devs if d.get('dob') and str(d['dob'])[5:10] == today_d.strftime('%m-%d')]
    if bdays:
        txt = " | ".join([f"🎂 Happy Birthday {b['name']}!" for b in bdays])
        st.markdown(f'<div class="news-ticker">{txt}</div>', unsafe_allow_html=True)

    cl, cr = st.columns(2)
    with cl:
        st.markdown("### 🙏 Today's Pooja")
        poojas = db_select("daily_pooja", filters={"is_active": True}, order="pooja_time")
        for p in poojas:
            st.markdown(f"""<div class="pooja-card">
                <strong>{p['pooja_name']}</strong> —
                <span style="color:#8B0000;font-weight:700;">{p.get('pooja_time') or 'TBD'}</span>
                <br><small>{p.get('description') or ''}</small></div>""", unsafe_allow_html=True)
        if not poojas:
            st.info("No pooja scheduled")

    with cr:
        st.markdown("### 🎂 Birthdays")
        if bdays:
            for b in bdays:
                st.write(f"🎂 **{b['name']}** — {b.get('mobile_no') or '-'}")
        else:
            st.info("No birthdays today")

    # Recent bills
    st.markdown("### 🧾 Recent Bills")
    recent = db_select("bill", filters={"is_deleted": False}, order="-bill_date", limit=10)
    if recent:
        import pandas as pd
        for b in recent:
            if b.get('devotee_id'):
                d = db_select("devotee", "name", filters={"id": b['devotee_id']})
                b['name'] = d[0]['name'] if d else '-'
            else:
                b['name'] = b.get('guest_name') or '-'
            if b.get('pooja_type_id'):
                p = db_select("pooja_type", "name", filters={"id": b['pooja_type_id']})
                b['pooja'] = p[0]['name'] if p else '-'
            else:
                b['pooja'] = '-'
        df = pd.DataFrame(recent)
        df['Date'] = df['bill_date'].apply(lambda x: str(x)[:10])
        df['Amount'] = df['amount'].apply(lambda x: f"₹{float(x or 0):,.2f}")
        st.dataframe(df[['bill_number', 'Date', 'name', 'pooja', 'Amount']].rename(
            columns={'bill_number': 'Bill No', 'name': 'Name', 'pooja': 'Pooja'}),
            use_container_width=True, hide_index=True)


# ============================================================
# DEVOTEES
# ============================================================
def page_devotees():
    st.markdown("## 👥 Enrolled Devotees")
    c1, c2 = st.columns([3, 1])
    with c2:
        if st.button("➕ Add Devotee", use_container_width=True):
            go_to('add_devotee', edit_devotee_id=None)

    search = st.text_input("🔍 Search...", placeholder="Name or mobile")
    devotees = db_select("devotee", filters={"is_family_head": True, "is_active": True}, order="name")

    if search:
        sl = search.lower()
        devotees = [d for d in devotees if sl in (d.get('name') or '').lower() or sl in (d.get('mobile_no') or '')]

    if devotees:
        for d in devotees:
            fam = db_select("devotee", "id", filters={"family_head_id": d['id']})
            c1, c2, c3, c4, c5 = st.columns([0.5, 2.5, 2, 1, 2])
            with c1:
                st.write(f"#{d['id']}")
            with c2:
                st.write(f"**{d['name']}**")
            with c3:
                st.write(f"📱 {d.get('mobile_no') or '-'}")
            with c4:
                st.write(f"👨‍👩‍👧 {len(fam)}")
            with c5:
                b1, b2, b3 = st.columns(3)
                with b1:
                    if st.button("👁", key=f"v{d['id']}"):
                        go_to('view_devotee', view_devotee_id=d['id'])
                with b2:
                    if st.button("✏️", key=f"e{d['id']}"):
                        go_to('add_devotee', edit_devotee_id=d['id'])
                with b3:
                    if st.button("🗑", key=f"d{d['id']}"):
                        db_delete("devotee_yearly_pooja", "devotee_id", d['id'])
                        db_delete("devotee", "family_head_id", d['id'])
                        db_delete("devotee", "id", d['id'])
                        st.rerun()
            st.markdown("---")
    else:
        st.info("No devotees found")


def page_add_devotee():
    eid = st.session_state.get('edit_devotee_id')
    dev = None
    if eid:
        r = db_select("devotee", filters={"id": eid})
        dev = r[0] if r else None

    st.markdown(f"## {'✏️ Edit' if dev else '➕ Add'} Devotee")

    with st.form("dev_form"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Name *", value=dev['name'] if dev else "")
            dob_val = None
            if dev and dev.get('dob'):
                try:
                    dob_val = datetime.strptime(str(dev['dob'])[:10], '%Y-%m-%d').date()
                except:
                    pass
            dob = st.date_input("DOB", value=dob_val, min_value=date(1920, 1, 1),
                                max_value=date.today(), format="DD/MM/YYYY")
            ri = RELATION_TYPES.index(dev['relation_type']) + 1 if dev and dev.get('relation_type') in RELATION_TYPES else 0
            relation = st.selectbox("Relation", [''] + RELATION_TYPES, index=ri)
            mobile = st.text_input("Mobile", value=dev.get('mobile_no') or '' if dev else '')

        with c2:
            whatsapp = st.text_input("WhatsApp", value=dev.get('whatsapp_no') or '' if dev else '')
            wed_val = None
            if dev and dev.get('wedding_day'):
                try:
                    wed_val = datetime.strptime(str(dev['wedding_day'])[:10], '%Y-%m-%d').date()
                except:
                    pass
            wedding = st.date_input("Wedding Day", value=wed_val, min_value=date(1920, 1, 1), format="DD/MM/YYYY")
            ni = NATCHATHIRAM_LIST.index(dev['natchathiram']) + 1 if dev and dev.get('natchathiram') in NATCHATHIRAM_LIST else 0
            natch = st.selectbox("Natchathiram", [''] + NATCHATHIRAM_LIST, index=ni)
            address = st.text_area("Address", value=dev.get('address') or '' if dev else '', height=80)

        if st.form_submit_button("💾 Save", use_container_width=True):
            if not name.strip():
                st.error("Name required!")
            else:
                data = {
                    "name": name.strip(),
                    "dob": dob.isoformat() if dob else None,
                    "relation_type": relation or None,
                    "mobile_no": mobile or None,
                    "whatsapp_no": whatsapp or None,
                    "wedding_day": wedding.isoformat() if wedding else None,
                    "natchathiram": natch or None,
                    "address": address or None,
                    "is_family_head": True,
                    "is_active": True
                }
                if eid and dev:
                    db_update("devotee", data, "id", eid)
                    st.success("Updated! ✅")
                else:
                    result = db_insert("devotee", data)
                    if result:
                        st.session_state['edit_devotee_id'] = result['id']
                        st.success(f"Added! ID: {result['id']} ✅")
                        st.rerun()

    # Family Members
    cid = eid or st.session_state.get('edit_devotee_id')
    if cid:
        st.markdown("---")
        st.markdown("### 👨‍👩‍👧‍👦 Family Members")
        family = db_select("devotee", filters={"family_head_id": cid}, order="name")
        for fm in family:
            c1, c2, c3 = st.columns([3, 3, 1])
            with c1:
                st.write(f"**{fm['name']}** ({fm.get('relation_type') or '-'})")
            with c2:
                st.write(f"DOB: {str(fm.get('dob') or '-')[:10]} | 📱 {fm.get('mobile_no') or '-'}")
            with c3:
                if st.button("🗑", key=f"rf{fm['id']}"):
                    db_delete("devotee", "id", fm['id'])
                    st.rerun()

        with st.form("add_fm"):
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                fn = st.text_input("Name", key="fn")
                fd = st.date_input("DOB", key="fd", value=None, min_value=date(1920, 1, 1), format="DD/MM/YYYY")
            with fc2:
                fr = st.selectbox("Relation", [''] + RELATION_TYPES, key="fr")
                fs = st.selectbox("Star", [''] + NATCHATHIRAM_LIST, key="fs")
            with fc3:
                fmob = st.text_input("Mobile", key="fmo")
            if st.form_submit_button("➕ Add Member"):
                if fn.strip():
                    db_insert("devotee", {
                        "name": fn.strip(),
                        "dob": fd.isoformat() if fd else None,
                        "relation_type": fr or None,
                        "natchathiram": fs or None,
                        "mobile_no": fmob or None,
                        "family_head_id": cid,
                        "is_family_head": False,
                        "is_active": True
                    })
                    st.success("Added!")
                    st.rerun()

        # Yearly Poojas
        st.markdown("---")
        st.markdown("### 🕉️ Yearly Poojas")
        yearly = db_select("devotee_yearly_pooja", filters={"devotee_id": cid})
        for yp in yearly:
            c1, c2, c3 = st.columns([3, 3, 1])
            with c1:
                st.write(f"**{yp.get('pooja_name') or '-'}**")
            with c2:
                st.write(f"{str(yp.get('pooja_date') or '-')[:10]} | {yp.get('notes') or '-'}")
            with c3:
                if st.button("🗑", key=f"ry{yp['id']}"):
                    db_delete("devotee_yearly_pooja", "id", yp['id'])
                    st.rerun()

        pts = db_select("pooja_type", filters={"is_active": True}, order="name")
        with st.form("add_yp"):
            yc1, yc2, yc3 = st.columns(3)
            with yc1:
                pt_names = [f"{p['name']} (₹{p['amount']})" for p in pts]
                yps = st.selectbox("Pooja", [''] + pt_names, key="yps")
            with yc2:
                ypd = st.date_input("Date", key="ypd", format="DD/MM/YYYY")
            with yc3:
                ypn = st.text_input("Notes", key="ypn")
            if st.form_submit_button("➕ Add Pooja"):
                if yps:
                    idx = pt_names.index(yps)
                    pt = pts[idx]
                    db_insert("devotee_yearly_pooja", {
                        "devotee_id": cid,
                        "pooja_type_id": pt['id'],
                        "pooja_name": pt['name'],
                        "pooja_date": ypd.isoformat(),
                        "notes": ypn or None
                    })
                    st.success("Added!")
                    st.rerun()

    if st.button("⬅️ Back to Devotees"):
        go_to('devotees')


def page_view_devotee():
    did = st.session_state.get('view_devotee_id')
    if not did:
        go_to('devotees')
        return
    r = db_select("devotee", filters={"id": did})
    if not r:
        st.error("Not found!")
        return
    d = r[0]

    st.markdown(f"## 👤 {d['name']}")
    c1, c2 = st.columns([1, 3])
    with c1:
        st.markdown(f"""<div style="width:100px;height:100px;background:#8B0000;color:#FFD700;
            border-radius:50%;display:flex;align-items:center;justify-content:center;
            font-size:2.5em;margin:auto;">{d['name'][0]}</div>""", unsafe_allow_html=True)
    with c2:
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            st.write(f"**DOB:** {str(d.get('dob') or '-')[:10]}")
            st.write(f"**Relation:** {d.get('relation_type') or '-'}")
        with cc2:
            st.write(f"**Mobile:** {d.get('mobile_no') or '-'}")
            st.write(f"**WhatsApp:** {d.get('whatsapp_no') or '-'}")
        with cc3:
            st.write(f"**Wedding:** {str(d.get('wedding_day') or '-')[:10]}")
            st.write(f"**Star:** {d.get('natchathiram') or '-'}")
        st.write(f"**Address:** {d.get('address') or '-'}")

    st.markdown("### 👨‍���‍👧‍👦 Family")
    for fm in db_select("devotee", filters={"family_head_id": did}):
        st.markdown(f"""<div class="family-card"><strong>{fm['name']}</strong> |
            {fm.get('relation_type') or '-'} | DOB: {str(fm.get('dob') or '-')[:10]} |
            �� {fm.get('mobile_no') or '-'}</div>""", unsafe_allow_html=True)

    st.markdown("### 🕉️ Yearly Poojas")
    for yp in db_select("devotee_yearly_pooja", filters={"devotee_id": did}):
        st.markdown(f"""<div class="yearly-pooja-card"><strong>{yp.get('pooja_name') or '-'}</strong> |
            {str(yp.get('pooja_date') or '-')[:10]} | {yp.get('notes') or '-'}</div>""", unsafe_allow_html=True)

    st.markdown("### 🧾 Bills")
    bills = db_select("bill", filters={"devotee_id": did, "is_deleted": False}, order="-bill_date")
    if bills:
        import pandas as pd
        for b in bills:
            if b.get('pooja_type_id'):
                p = db_select("pooja_type", "name", filters={"id": b['pooja_type_id']})
                b['pooja'] = p[0]['name'] if p else '-'
            else:
                b['pooja'] = '-'
        df = pd.DataFrame(bills)
        df['Date'] = df['bill_date'].apply(lambda x: str(x)[:10])
        df['Amount'] = df['amount'].apply(lambda x: f"₹{float(x or 0):,.2f}")
        st.dataframe(df[['bill_number', 'Date', 'pooja', 'Amount']].rename(
            columns={'bill_number': 'Bill', 'pooja': 'Pooja'}),
            use_container_width=True, hide_index=True)

    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button("✏️ Edit"):
            go_to('add_devotee', edit_devotee_id=did)
    with bc2:
        if st.button("⬅️ Back"):
            go_to('devotees')


# ============================================================
# BILLING
# ============================================================
def page_billing():
    st.markdown("## 🧾 Bills")
    c1, c2 = st.columns([3, 1])
    with c2:
        if st.button("��� New Bill", use_container_width=True):
            go_to('new_bill')

    fc1, fc2 = st.columns(2)
    with fc1:
        fd = st.date_input("From", value=date.today(), format="DD/MM/YYYY", key="bf")
    with fc2:
        td = st.date_input("To", value=date.today(), format="DD/MM/YYYY", key="bt")

    all_bills = db_select("bill", order="-bill_date")
    bills = [b for b in all_bills if fd.isoformat() <= str(b.get('bill_date', ''))[:10] <= td.isoformat()]

    if bills:
        for b in bills:
            if b.get('is_deleted'):
                st.markdown(f"~~{b['bill_number']} | DELETED~~")
                continue

            if b.get('devotee_id'):
                dd = db_select("devotee", "name", filters={"id": b['devotee_id']})
                bname = dd[0]['name'] if dd else '-'
            else:
                bname = b.get('guest_name') or '-'

            c1, c2, c3, c4, c5 = st.columns([1.5, 1.5, 2, 1.5, 1.5])
            with c1:
                st.write(f"**{b['bill_number']}**")
            with c2:
                st.write(str(b.get('bill_date', ''))[:10])
            with c3:
                st.write(bname)
            with c4:
                st.write(f"**₹{float(b.get('amount', 0)):,.2f}**")
            with c5:
                if st.button("👁", key=f"vb{b['id']}"):
                    go_to('view_bill', view_bill_id=b['id'])
                if is_admin() and st.button("🗑", key=f"db{b['id']}"):
                    db_update("bill", {
                        "is_deleted": True,
                        "deleted_by": st.session_state['user_id'],
                        "deleted_at": datetime.now().isoformat(),
                        "delete_reason": "Admin deleted"
                    }, "id", b['id'])
                    st.rerun()
            st.markdown("---")
    else:
        st.info("No bills found")


def page_new_bill():
    st.markdown("## 🧾 New Bill")
    pts = db_select("pooja_type", filters={"is_active": True}, order="name")
    devs = db_select("devotee", "id,name,mobile_no,address",
                     filters={"is_family_head": True, "is_active": True}, order="name")

    last = db_select("bill", "id", order="-id", limit=1)
    lid = last[0]['id'] if last else 0
    nbn = f"BILL-{lid + 1:06d}"

    with st.form("bill_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.text_input("Bill No", value=nbn, disabled=True)
        with c2:
            manual = st.text_input("Manual Bill No")
        with c3:
            bdate = st.date_input("Date", value=date.today(), format="DD/MM/YYYY")

        dtype = st.radio("Type:", ["Enrolled", "Guest"], horizontal=True)

        dev_id = guest_name = guest_mobile = guest_address = guest_whatsapp = None
        if dtype == "Enrolled":
            dopts = {f"{d['name']} (ID:{d['id']})": d['id'] for d in devs}
            sd = st.selectbox("Devotee *", [''] + list(dopts.keys()))
            dev_id = dopts.get(sd)
        else:
            gc1, gc2 = st.columns(2)
            with gc1:
                guest_name = st.text_input("Guest Name *")
                guest_mobile = st.text_input("Guest Mobile")
            with gc2:
                guest_address = st.text_area("Address", height=68)
                guest_whatsapp = st.text_input("WhatsApp")

        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            ptopts = {f"{p['name']} (₹{p['amount']})": p for p in pts}
            spt = st.selectbox("Pooja *", [''] + list(ptopts.keys()))
        with pc2:
            damt = float(ptopts[spt]['amount']) if spt else 0.0
            amount = st.number_input("Amount *", value=damt, step=10.0)
        with pc3:
            notes = st.text_input("Notes")

        if st.form_submit_button("💾 Create Bill", use_container_width=True):
            if not spt:
                st.error("Select pooja!")
            elif dtype == "Enrolled" and not dev_id:
                st.error("Select devotee!")
            elif dtype == "Guest" and not guest_name:
                st.error("Enter guest name!")
            else:
                pt = ptopts[spt]
                result = db_insert("bill", {
                    "bill_number": nbn,
                    "manual_bill_no": manual or None,
                    "bill_book_no": None,
                    "bill_date": datetime.combine(bdate, datetime.now().time()).isoformat(),
                    "devotee_type": dtype.lower(),
                    "devotee_id": dev_id,
                    "guest_name": guest_name,
                    "guest_address": guest_address,
                    "guest_mobile": guest_mobile,
                    "guest_whatsapp": guest_whatsapp,
                    "pooja_type_id": pt['id'],
                    "amount": amount,
                    "notes": notes or None,
                    "created_by": st.session_state['user_id'],
                    "is_deleted": False
                })
                if result:
                    st.success(f"Bill {nbn} created! ✅")
                    go_to('view_bill', view_bill_id=result['id'])

    if st.button("⬅️ Back"):
        go_to('billing')


def page_view_bill():
    bid = st.session_state.get('view_bill_id')
    if not bid:
        go_to('billing')
        return
    r = db_select("bill", filters={"id": bid})
    if not r:
        st.error("Not found!")
        return
    b = r[0]

    if b.get('devotee_id'):
        dd = db_select("devotee", filters={"id": b['devotee_id']})
        bname = dd[0]['name'] if dd else '-'
        bmob = dd[0].get('mobile_no', '-') if dd else '-'
        baddr = dd[0].get('address', '-') if dd else '-'
    else:
        bname = b.get('guest_name') or '-'
        bmob = b.get('guest_mobile') or '-'
        baddr = b.get('guest_address') or '-'

    pname = '-'
    if b.get('pooja_type_id'):
        pp = db_select("pooja_type", "name", filters={"id": b['pooja_type_id']})
        if pp:
            pname = pp[0]['name']

    amt = float(b.get('amount', 0) or 0)
    bdt = str(b.get('bill_date', ''))[:16].replace('T', ' ')

    st.markdown(f"""<div class="bill-receipt">
        <div style="text-align:center;border-bottom:3px double #8B0000;padding-bottom:12px;margin-bottom:15px;">
            <h2 style="color:#8B0000;">���️ {TEMPLE_NAME}</h2>
            <h4 style="color:#DC143C;">{TEMPLE_TRUST}</h4>
            <p style="color:#555;">{TEMPLE_ADDRESS_LINE3}</p>
            <p>📜 BILL RECEIPT</p></div>
        <table style="width:100%;margin-bottom:15px;">
            <tr><td><b>Bill:</b> {b['bill_number']}</td>
                <td><b>Manual:</b> {b.get('manual_bill_no') or '-'}</td>
                <td style="text-align:right;"><b>Date:</b> {bdt}</td></tr>
            <tr><td><b>Name:</b> {bname}</td><td><b>Mobile:</b> {bmob}</td>
                <td style="text-align:right;"><b>Address:</b> {baddr}</td></tr></table>
        <table style="width:100%;border-collapse:collapse;">
            <thead><tr style="background:#8B0000;color:white;">
                <th style="padding:8px;">Pooja</th><th style="padding:8px;">Notes</th>
                <th style="padding:8px;text-align:right;">Amount</th></tr></thead>
            <tbody><tr style="border-bottom:1px solid #ddd;">
                <td style="padding:8px;">{pname}</td><td style="padding:8px;">{b.get('notes') or '-'}</td>
                <td style="padding:8px;text-align:right;"><b>₹{amt:,.2f}</b></td></tr></tbody>
            <tfoot><tr style="border-top:2px solid #8B0000;">
                <td colspan="2" style="padding:8px;text-align:right;"><b>Total:</b></td>
                <td style="padding:8px;text-align:right;color:#8B0000;font-size:1.3em;">
                    <b>₹{amt:,.2f}</b></td></tr></tfoot></table>
        <div style="text-align:center;margin-top:15px;border-top:1px dashed #ccc;padding-top:10px;">
            <small style="color:#888;">{TEMPLE_FULL_ADDRESS}</small></div></div>""", unsafe_allow_html=True)

    if st.button("⬅️ Back"):
        go_to('billing')


# ============================================================
# EXPENSES
# ============================================================
def page_expenses():
    st.markdown("## 💸 Expenses")
    fc1, fc2 = st.columns(2)
    with fc1:
        fd = st.date_input("From", value=date.today().replace(day=1), format="DD/MM/YYYY", key="ef")
    with fc2:
        td = st.date_input("To", value=date.today(), format="DD/MM/YYYY", key="et")

    ets = db_select("expense_type", filters={"is_active": True}, order="name")
    et_map = {e['id']: e['name'] for e in ets}

    all_exp = db_select("expense", order="-expense_date")
    exps = [e for e in all_exp if fd.isoformat() <= str(e.get('expense_date', ''))[:10] <= td.isoformat()]

    total = sum(float(e.get('amount', 0) or 0) for e in exps)
    st.markdown(f"**Total: ₹{total:,.2f}**")

    if exps:
        import pandas as pd
        for e in exps:
            e['type'] = et_map.get(e.get('expense_type_id'), '-')
        df = pd.DataFrame(exps)
        df['Date'] = df['expense_date'].apply(lambda x: str(x)[:10])
        df['Amount'] = df['amount'].apply(lambda x: f"₹{float(x or 0):,.2f}")
        st.dataframe(df[['id', 'Date', 'type', 'description', 'Amount']].rename(
            columns={'id': 'ID', 'type': 'Type', 'description': 'Description'}),
            use_container_width=True, hide_index=True)

        did = st.number_input("Delete ID:", min_value=0, step=1, value=0)
        if did > 0 and st.button("🗑 Delete"):
            db_delete("expense", "id", did)
            st.rerun()

    st.markdown("### ➕ Add Expense")
    with st.form("add_exp"):
        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            en = [e['name'] for e in ets]
            se = st.selectbox("Type *", en if en else ['None'])
        with ec2:
            ea = st.number_input("Amount *", min_value=0.0, step=10.0)
        with ec3:
            ed = st.date_input("Date", value=date.today(), format="DD/MM/YYYY")
        edesc = st.text_input("Description")
        if st.form_submit_button("💾 Save"):
            if ea > 0 and ets:
                eid = next(e['id'] for e in ets if e['name'] == se)
                db_insert("expense", {
                    "expense_type_id": eid,
                    "amount": ea,
                    "description": edesc or None,
                    "expense_date": ed.isoformat(),
                    "created_by": st.session_state['user_id']
                })
                st.success("Added! ✅")
                st.rerun()


# ============================================================
# REPORTS
# ============================================================
def page_reports():
    st.markdown("## 📈 Reports")
    fc1, fc2 = st.columns(2)
    with fc1:
        fd = st.date_input("From", value=date.today().replace(day=1), format="DD/MM/YYYY", key="rf")
    with fc2:
        td = st.date_input("To", value=date.today(), format="DD/MM/YYYY", key="rt")

    bills = db_select("bill", "amount,pooja_type_id,bill_date", filters={"is_deleted": False})
    pb = [b for b in bills if fd.isoformat() <= str(b.get('bill_date', ''))[:10] <= td.isoformat()]
    ti = sum(float(b.get('amount', 0) or 0) for b in pb)

    exps = db_select("expense", "amount,expense_type_id,expense_date")
    pe = [e for e in exps if fd.isoformat() <= str(e.get('expense_date', ''))[:10] <= td.isoformat()]
    te = sum(float(e.get('amount', 0) or 0) for e in pe)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="stat-card income"><h4>Income</h4><h2>₹{ti:,.2f}</h2></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-card expense"><h4>Expenses</h4><h2>₹{te:,.2f}</h2></div>', unsafe_allow_html=True)
    with c3:
        color = "income" if ti - te >= 0 else "expense"
        st.markdown(f'<div class="stat-card {color}"><h4>Net</h4><h2>₹{ti - te:,.2f}</h2></div>', unsafe_allow_html=True)

    # Breakdown
    cl, cr = st.columns(2)
    with cl:
        st.markdown("### Income by Pooja")
        pts = db_select("pooja_type", order="name")
        pt_map = {p['id']: p['name'] for p in pts}
        ibp = {}
        for b in pb:
            pn = pt_map.get(b.get('pooja_type_id'), 'Other')
            if pn not in ibp:
                ibp[pn] = {'count': 0, 'total': 0}
            ibp[pn]['count'] += 1
            ibp[pn]['total'] += float(b.get('amount', 0) or 0)
        if ibp:
            import pandas as pd
            st.dataframe(pd.DataFrame([{'Pooja': k, 'Count': v['count'], 'Amount': f"₹{v['total']:,.2f}"}
                                        for k, v in ibp.items()]), use_container_width=True, hide_index=True)

    with cr:
        st.markdown("### Expenses by Type")
        ets = db_select("expense_type", order="name")
        et_map = {e['id']: e['name'] for e in ets}
        ebt = {}
        for e in pe:
            en = et_map.get(e.get('expense_type_id'), 'Other')
            if en not in ebt:
                ebt[en] = {'count': 0, 'total': 0}
            ebt[en]['count'] += 1
            ebt[en]['total'] += float(e.get('amount', 0) or 0)
        if ebt:
            import pandas as pd
            st.dataframe(pd.DataFrame([{'Type': k, 'Count': v['count'], 'Amount': f"₹{v['total']:,.2f}"}
                                        for k, v in ebt.items()]), use_container_width=True, hide_index=True)


# ============================================================
# SAMAYA VAKUPPU
# ============================================================
def page_samaya():
    st.markdown("## 🎓 Samaya Vakuppu")
    if st.button("➕ Add"):
        go_to('add_samaya', edit_samaya_id=None)
    for s in db_select("samaya_vakuppu", order="student_name"):
        c1, c2, c3 = st.columns([3, 3, 1])
        with c1:
            st.write(f"**{s['student_name']}** | Parent: {s.get('father_mother_name') or '-'}")
        with c2:
            st.write(f"Bond: {s.get('bond_no') or '-'} | Bank: {s.get('bond_issuing_bank') or '-'}")
        with c3:
            if st.button("✏️", key=f"es{s['id']}"):
                go_to('add_samaya', edit_samaya_id=s['id'])
            if st.button("🗑", key=f"ds{s['id']}"):
                db_delete("samaya_vakuppu", "id", s['id'])
                st.rerun()
        st.markdown("---")


def page_add_samaya():
    eid = st.session_state.get('edit_samaya_id')
    s = None
    if eid:
        r = db_select("samaya_vakuppu", filters={"id": eid})
        s = r[0] if r else None

    st.markdown(f"## {'✏️ Edit' if s else '➕ Add'} Student")
    with st.form("sf"):
        c1, c2 = st.columns(2)
        with c1:
            nm = st.text_input("Name *", value=s['student_name'] if s else '')
            par = st.text_input("Parent", value=s.get('father_mother_name') or '' if s else '')
            bn = st.text_input("Bond No", value=s.get('bond_no') or '' if s else '')
        with c2:
            bk = st.text_input("Bank", value=s.get('bond_issuing_bank') or '' if s else '')
            br = st.text_input("Branch", value=s.get('branch_of_bank') or '' if s else '')
        addr = st.text_area("Address", value=s.get('address') or '' if s else '')
        if st.form_submit_button("💾 Save"):
            if nm.strip():
                data = {"student_name": nm, "father_mother_name": par or None,
                        "bond_no": bn or None, "bond_issuing_bank": bk or None,
                        "branch_of_bank": br or None, "address": addr or None}
                if eid and s:
                    db_update("samaya_vakuppu", data, "id", eid)
                else:
                    db_insert("samaya_vakuppu", data)
                st.success("Saved! ✅")
                go_to('samaya')
    if st.button("⬅️ Back"):
        go_to('samaya')


# ============================================================
# MANDAPAM
# ============================================================
def page_mandapam():
    st.markdown("## 🏛️ Thirumana Mandapam")
    if st.button("➕ Add"):
        go_to('add_mandapam', edit_mandapam_id=None)
    for m in db_select("thirumana_mandapam", order="name"):
        c1, c2, c3 = st.columns([3, 3, 1])
        with c1:
            st.write(f"**{m['name']}** | Bond: {m.get('bond_no') or '-'}")
        with c2:
            st.write(f"₹{float(m.get('amount', 0)):,.2f} | Bonds: {m.get('no_of_bond', 1)}")
        with c3:
            if st.button("✏️", key=f"em{m['id']}"):
                go_to('add_mandapam', edit_mandapam_id=m['id'])
            if st.button("🗑", key=f"dm{m['id']}"):
                db_delete("thirumana_mandapam", "id", m['id'])
                st.rerun()
        st.markdown("---")


def page_add_mandapam():
    eid = st.session_state.get('edit_mandapam_id')
    m = None
    if eid:
        r = db_select("thirumana_mandapam", filters={"id": eid})
        m = r[0] if r else None

    st.markdown(f"## {'✏️ Edit' if m else '➕ Add'} Record")
    with st.form("mf"):
        c1, c2 = st.columns(2)
        with c1:
            nm = st.text_input("Name *", value=m['name'] if m else '')
            bn = st.text_input("Bond No", value=m.get('bond_no') or '' if m else '')
        with c2:
            amt = st.number_input("Amount", value=float(m.get('amount', 0)) if m else 0.0, step=100.0)
            nb = st.number_input("Bonds", value=int(m.get('no_of_bond', 1)) if m else 1, min_value=1)
        addr = st.text_area("Address", value=m.get('address') or '' if m else '')
        if st.form_submit_button("💾 Save"):
            if nm.strip():
                data = {"name": nm, "bond_no": bn or None, "amount": amt,
                        "no_of_bond": nb, "address": addr or None}
                if eid and m:
                    db_update("thirumana_mandapam", data, "id", eid)
                else:
                    db_insert("thirumana_mandapam", data)
                st.success("Saved! ✅")
                go_to('mandapam')
    if st.button("⬅️ Back"):
        go_to('mandapam')


# ============================================================
# DAILY POOJA
# ============================================================
def page_daily_pooja():
    st.markdown("## 🙏 Daily Pooja")
    for p in db_select("daily_pooja", filters={"is_active": True}, order="pooja_time"):
        c1, c2, c3 = st.columns([3, 3, 1])
        with c1:
            st.write(f"**{p['pooja_name']}** — {p.get('pooja_time') or 'TBD'}")
        with c2:
            st.write(p.get('description') or '-')
        with c3:
            if st.button("🗑", key=f"dp{p['id']}"):
                db_update("daily_pooja", {"is_active": False}, "id", p['id'])
                st.rerun()

    with st.form("adp"):
        c1, c2, c3 = st.columns(3)
        with c1:
            pn = st.text_input("Name *")
        with c2:
            pt = st.text_input("Time (e.g. 6:00 AM)")
        with c3:
            pd = st.text_input("Description")
        if st.form_submit_button("➕ Add"):
            if pn.strip():
                db_insert("daily_pooja", {
                    "pooja_name": pn, "pooja_time": pt or None,
                    "description": pd or None, "is_active": True
                })
                st.rerun()


# ============================================================
# SETTINGS
# ============================================================
def page_settings():
    st.markdown("## ⚙️ Settings")
    cl, cr = st.columns(2)

    with cl:
        st.markdown("### 🕉️ Pooja Types")
        for p in db_select("pooja_type", filters={"is_active": True}, order="name"):
            c1, c2, c3 = st.columns([3, 1.5, 1])
            with c1:
                st.write(p['name'])
            with c2:
                st.write(f"₹{p['amount']}")
            with c3:
                if st.button("🗑", key=f"dpt{p['id']}"):
                    db_update("pooja_type", {"is_active": False}, "id", p['id'])
                    st.rerun()
        with st.form("apt"):
            pn = st.text_input("Name *", key="npn")
            pa = st.number_input("Amount", value=0.0, step=10.0, key="npa")
            if st.form_submit_button("➕ Add"):
                if pn.strip():
                    db_insert("pooja_type", {"name": pn, "amount": pa, "is_active": True})
                    st.rerun()

    with cr:
        st.markdown("### 🏷️ Expense Types")
        for e in db_select("expense_type", filters={"is_active": True}, order="name"):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.write(e['name'])
            with c2:
                if st.button("🗑", key=f"det{e['id']}"):
                    db_update("expense_type", {"is_active": False}, "id", e['id'])
                    st.rerun()
        with st.form("aet"):
            en = st.text_input("Name *", key="nen")
            if st.form_submit_button("➕ Add"):
                if en.strip():
                    db_insert("expense_type", {"name": en, "is_active": True})
                    st.rerun()


# ============================================================
# USER MANAGEMENT
# ============================================================
def page_users():
    if not is_admin():
        st.error("Admin only!")
        return
    st.markdown("## 👤 Users")
    for u in db_select("users", order="id"):
        c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
        with c1:
            st.write(f"**{u['username']}** ({u.get('full_name') or '-'})")
        with c2:
            st.write(f"{'🔴 Admin' if u['role'] == 'admin' else '🔵 User'}")
        with c3:
            st.write("✅" if u['is_active_user'] else "⛔")
        with c4:
            if u['id'] != st.session_state['user_id']:
                if st.button("Toggle", key=f"tu{u['id']}"):
                    db_update("users", {"is_active_user": not u['is_active_user']}, "id", u['id'])
                    st.rerun()
        st.markdown("---")

    with st.form("au"):
        st.markdown("### ➕ Add User")
        c1, c2 = st.columns(2)
        with c1:
            un = st.text_input("Username *")
            fn = st.text_input("Full Name")
        with c2:
            pw = st.text_input("Password *", type="password")
            rl = st.selectbox("Role", ['user', 'admin'])
        if st.form_submit_button("👤 Create"):
            if un and pw:
                existing = db_select("users", filters={"username": un})
                if existing:
                    st.error("Username exists!")
                else:
                    db_insert("users", {
                        "username": un,
                        "password_hash": generate_password_hash(pw),
                        "full_name": fn or None,
                        "role": rl,
                        "is_active_user": True
                    })
                    st.success("Created! ✅")
                    st.rerun()


# ============================================================
# DELETED BILLS
# ============================================================
def page_deleted_bills():
    if not is_admin():
        st.error("Admin only!")
        return
    st.markdown("## 🗑️ Deleted Bills")
    bills = db_select("bill", filters={"is_deleted": True}, order="-deleted_at")
    if bills:
        import pandas as pd
        for b in bills:
            if b.get('deleted_by'):
                u = db_select("users", "full_name", filters={"id": b['deleted_by']})
                b['del_by'] = u[0]['full_name'] if u else '-'
            else:
                b['del_by'] = '-'
        df = pd.DataFrame(bills)
        df['Date'] = df['bill_date'].apply(lambda x: str(x)[:10])
        df['Amount'] = df['amount'].apply(lambda x: f"₹{float(x or 0):,.2f}")
        st.dataframe(df[['bill_number', 'Date', 'Amount', 'del_by', 'delete_reason']].rename(
            columns={'bill_number': 'Bill', 'del_by': 'Deleted By', 'delete_reason': 'Reason'}),
            use_container_width=True, hide_index=True)
    else:
        st.info("No deleted bills")


# ============================================================
# MAIN
# ============================================================
def main():
    init_session()
    load_css()

    if not st.session_state['logged_in']:
        login_page()
        return

    sidebar()

    pages = {
        'dashboard': page_dashboard,
        'devotees': page_devotees,
        'add_devotee': page_add_devotee,
        'view_devotee': page_view_devotee,
        'billing': page_billing,
        'new_bill': page_new_bill,
        'view_bill': page_view_bill,
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

    page = st.session_state.get('page', 'dashboard')
    pages.get(page, page_dashboard)()


if __name__ == "__main__":
    main()
