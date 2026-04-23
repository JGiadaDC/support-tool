import streamlit as st
import sqlite3
from datetime import datetime
from rapidfuzz import fuzz

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Support Hub", layout="wide")

# ---------------- STYLE ----------------
st.markdown("""
<style>
.main {background-color: #f5f7fb;}

h1, h2, h3 {font-weight: 700;}

.stButton>button {
    border-radius: 12px;
    padding: 8px 18px;
    background-color: #4f46e5;
    color: white;
}

section[data-testid="stSidebar"] {
    background-color: #0f172a;
}

section[data-testid="stSidebar"] * {
    color: white;
}

section[data-testid="stSidebar"] input {
    color: black !important;
    background-color: white !important;
}

.card {
    background: white;
    padding: 18px;
    border-radius: 14px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    margin-bottom: 12px;
}

.badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 600;
}

.badge-blue { background: #e0e7ff; color: #3730a3; }
.badge-green { background: #dcfce7; color: #166534; }
.badge-yellow { background: #fef9c3; color: #854d0e; }
.badge-red { background: #fee2e2; color: #991b1b; }

a { color: #4f46e5; }
</style>
""", unsafe_allow_html=True)

# ---------------- DEFAULT CATEGORIES ----------------
DEFAULT_CATEGORIES = ["EMAIL","REGISTROS","PEDIDOS","TRACKING","ETIQUETAS","JIRAS"]

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = "agent"
if "company" not in st.session_state:
    st.session_state.company = None
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

# ---------------- DB ----------------
conn = sqlite3.connect("data.db", check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS notes (
id INTEGER PRIMARY KEY AUTOINCREMENT,
title TEXT,
content TEXT,
category TEXT,
tags TEXT,
link TEXT,
company TEXT,
created_at TEXT)""")

c.execute("""
CREATE TABLE IF NOT EXISTS dudas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT,
    answer TEXT,
    status TEXT,
    priority TEXT,
    category TEXT,
    assigned_to TEXT,
    company TEXT,
    created_at TEXT
)
""")

c.execute("""CREATE TABLE IF NOT EXISTS categories (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
company TEXT)""")

conn.commit()

# ---------------- USERS ----------------
USERS = {
    "admin": {"password": "1234", "role": "admin"},
    "team": {"password": "support", "role": "agent"}
}

# ---------------- LOGIN ----------------
if not st.session_state.logged_in:
    st.title("🔐 Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USERS and USERS[u]["password"] == p:
            st.session_state.logged_in = True
            st.session_state.username = u
            st.session_state.role = USERS[u]["role"]
            st.rerun()

    st.stop()

# ---------------- COMPANY ----------------
if st.session_state.company is None:
    st.title("Select Company")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.image("assets/tell.png")
        if st.button("Tellmegen"):
            st.session_state.company = "TELLMEGEN"
            st.rerun()

    with col2:
        st.image("assets/viva.png")
        if st.button("Vivabioma"):
            st.session_state.company = "VIVABIOMA"
            st.rerun()

    with col3:
        st.image("assets/koko.png")
        if st.button("Kokogenetics"):
            st.session_state.company = "KOKOGENETICS"
            st.rerun()

    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.title(st.session_state.company)

if st.sidebar.button("🔄 Change company"):
    st.session_state.company = None
    st.rerun()


menu = st.sidebar.radio("Menu", ["Search","All Notes","Add Note","Dudas"])

# ---------------- CATEGORY ADD ----------------
st.sidebar.subheader("Delete category")

# carichiamo categorie esistenti
c.execute("SELECT id, name FROM categories WHERE company=?", (st.session_state.company,))
cats = c.fetchall()

cat_dict = {f"{c[1]}": c[0] for c in cats}

cat_to_delete = st.sidebar.selectbox("Select category", list(cat_dict.keys()) if cat_dict else ["None"])

if st.sidebar.button("Delete category"):
    if cats:
        c.execute("DELETE FROM categories WHERE id=?", (cat_dict[cat_to_delete],))
        conn.commit()
        st.sidebar.success("Category deleted")
        st.rerun()


new_cat = st.sidebar.text_input("New category")
if st.sidebar.button("Add category"):
    if new_cat:
        c.execute("INSERT INTO categories VALUES (NULL,?,?)",
                  (new_cat.upper(), st.session_state.company))
        conn.commit()
        st.rerun()

# ---------------- LOAD CATEGORIES ----------------
c.execute("SELECT name FROM categories WHERE company=?", (st.session_state.company,))
db_cat = [x[0] for x in c.fetchall()]
categories = sorted(list(set(DEFAULT_CATEGORIES + db_cat)))

# ---------------- SEARCH ----------------
if menu == "Search":
    st.title("Search")

    q = st.text_input("Search")

    if q:
        c.execute("SELECT * FROM notes WHERE company=?", (st.session_state.company,))
        notes = c.fetchall()

        for n in notes:
            text = f"{n[1]} {n[2]} {n[4]}"
            score = fuzz.token_set_ratio(q.lower(), text.lower())

            if score > 30:
                st.markdown(f"""
                <div class="card">
                <h4>{n[1]}</h4>
                <div class="badge badge-blue">{n[3]}</div>
                <p>{n[2]}</p>
                </div>
                """, unsafe_allow_html=True)

# ---------------- ALL NOTES ----------------
elif menu == "All Notes":
    st.title("All Notes")

    c.execute("SELECT * FROM notes WHERE company=? ORDER BY created_at DESC",
              (st.session_state.company,))
    notes = c.fetchall()

    for n in notes:
        with st.expander(n[1]):

            if st.session_state.edit_id != n[0]:
                st.markdown(f"""
                <div class="card">
                <div class="badge badge-blue">{n[3]}</div>
                <p>{n[2]}</p>
                </div>
                """, unsafe_allow_html=True)

                if n[5]:
                    st.markdown(f'<a href="{n[5]}" target="_blank">🔗 Open link</a>', unsafe_allow_html=True)

                col1, col2 = st.columns(2)

                if col1.button("Edit", key=f"e{n[0]}"):
                    st.session_state.edit_id = n[0]

                if st.session_state.role == "admin":
                    if col2.button("Delete", key=f"d{n[0]}"):
                        c.execute("DELETE FROM notes WHERE id=?", (n[0],))
                        conn.commit()
                        st.rerun()

            else:
                t = st.text_input("Title", value=n[1], key=f"t{n[0]}")
                ctt = st.text_area("Content", value=n[2], key=f"c{n[0]}")
                l = st.text_input("Link", value=n[5], key=f"l{n[0]}")

                if st.button("Save", key=f"s{n[0]}"):
                    c.execute("UPDATE notes SET title=?,content=?,link=? WHERE id=?",
                              (t, ctt, l, n[0]))
                    conn.commit()
                    st.session_state.edit_id = None
                    st.rerun()

# ---------------- ADD NOTE ----------------
elif menu == "Add Note":
    st.title("Add Note")

    t = st.text_input("Title")
    ctt = st.text_area("Content")
    cat = st.selectbox("Category", categories)
    tags = st.text_input("Tags")
    link = st.text_input("Link")

    if st.button("Save"):
        c.execute("""INSERT INTO notes
        VALUES (NULL,?,?,?,?,?,?,?)""",
        (t, ctt, cat, tags, link,
         st.session_state.company,
         datetime.now().strftime("%Y-%m-%d %H:%M")))

        conn.commit()
        st.toast("Saved ✅")
        st.rerun()

# ---------------- DUDAS ----------------
elif menu == "Dudas":
    st.title("Tickets")

    q = st.text_input("New ticket")
    pr = st.selectbox("Priority", ["LOW","MEDIUM","HIGH"])

    if st.button("Create"):
        c.execute("""
        INSERT INTO dudas (
            question, answer, status, priority, category, assigned_to, company, created_at
        )
        VALUES (?,?,?,?,?,?,?,?)
        """, (
            q,
            "",
            "open",
            pr,
            "GENERAL",
            "unassigned",
            st.session_state.company,
            datetime.now().strftime("%Y-%m-%d %H:%M")
        ))


    c.execute("SELECT * FROM dudas WHERE status='open'")
    dudas = c.fetchall()

    for d in dudas:
        color = "badge-green"
        if d[4] == "MEDIUM": color = "badge-yellow"
        if d[4] == "HIGH": color = "badge-red"

        with st.expander(d[1]):
            st.markdown(f'<div class="badge {color}">{d[4]}</div>', unsafe_allow_html=True)

            ans = st.text_area("Answer", key=f"a{d[0]}")

            if st.button("Resolve", key=f"r{d[0]}"):
                c.execute("""
                UPDATE dudas
                SET answer=?, status='closed', category=?
                WHERE id=?
                """, (ans, "RESOLVED", d[0]))

                conn.commit()
                st.rerun()
