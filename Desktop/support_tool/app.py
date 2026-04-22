import streamlit as st
import sqlite3
from datetime import datetime
from rapidfuzz import fuzz

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Support Hub", layout="wide")

# ---------------- DATABASE ----------------
conn = sqlite3.connect("data.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    content TEXT,
    category TEXT,
    tags TEXT,
    company TEXT,
    created_at TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS dudas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT,
    answer TEXT,
    status TEXT,
    priority TEXT,
    assigned_to TEXT,
    company TEXT,
    created_at TEXT
)
""")

conn.commit()

# ---------------- USERS ----------------
USERS = {
    "admin": {"password": "1234", "role": "admin"},
    "team": {"password": "support", "role": "agent"}
}

# ---------------- SESSION STATE INIT ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "role" not in st.session_state:
    st.session_state.role = None

if "company" not in st.session_state:
    st.session_state.company = None

# ---------------- LOGIN ----------------
if not st.session_state.logged_in:
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = USERS[username]["role"]
            st.rerun()
        else:
            st.error("Wrong credentials")

    st.stop()

# ---------------- COMPANY SELECTION ----------------
if st.session_state.company is None:
    st.markdown("## Select Company")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.image("assets/tell.png", use_container_width=True)
        if st.button("Tellmegen"):
            st.session_state.company = "TELLMEGEN"
            st.rerun()

    with col2:
        st.image("assets/viva.png", use_container_width=True)
        if st.button("Vivabioma"):
            st.session_state.company = "VIVABIOMA"
            st.rerun()

    with col3:
        st.image("assets/koko.png", use_container_width=True)
        if st.button("Kokogenetics"):
            st.session_state.company = "KOKOGENETICS"
            st.rerun()

    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.title("Companies")

for comp in ["TELLMEGEN", "VIVABIOMA", "KOKOGENETICS"]:
    if st.sidebar.button(comp):
        st.session_state.company = comp
        st.rerun()

st.sidebar.divider()

menu = st.sidebar.radio("Menu", [
    "Search",
    "All Notes",
    "Add Note",
    "Dudas"
])

# ---------------- SEARCH ----------------
if menu == "Search":
    st.subheader(f"Search - {st.session_state.company}")

    query = st.text_input("Search anything")

    if query:
        c.execute("SELECT * FROM notes WHERE company=?", (st.session_state.company,))
        notes = c.fetchall()

        results = []

        for n in notes:
            text = f"{n[1]} {n[2]} {n[4]}"
            score = fuzz.token_set_ratio(query.lower(), text.lower())

            if score > 30:
                results.append((score, n))

        results.sort(reverse=True, key=lambda x: x[0])

        for score, r in results:
            with st.expander(f"{r[1]} ({r[3]}) - {score}%"):
                st.markdown(r[2])
                st.caption(f"Tags: {r[4]} | {r[6]}")

# ---------------- ALL NOTES ----------------
elif menu == "All Notes":
    st.subheader(f"Notes - {st.session_state.company}")

    c.execute("""
        SELECT * FROM notes
        WHERE company=?
        ORDER BY created_at DESC
    """, (st.session_state.company,))

    notes = c.fetchall()

    for n in notes:
        with st.expander(f"{n[1]} ({n[3]})"):
            st.markdown(n[2])
            st.caption(f"Tags: {n[4]} | {n[6]}")

            if st.session_state.role == "admin":
                if st.button(f"Delete {n[0]}", key=f"del_{n[0]}"):
                    c.execute("DELETE FROM notes WHERE id=?", (n[0],))
                    conn.commit()
                    st.warning("Deleted")
                    st.rerun()

# ---------------- ADD NOTE ----------------
elif menu == "Add Note":
    st.subheader("Add Note")

    title = st.text_input("Title")
    content = st.text_area("Content")

    category = st.selectbox("Category", [
        "EMAIL", "RECOGIDAS", "PEDIDOS",
        "TRACKING", "ETIQUETAS", "JIRAS"
    ])

    tags = st.text_input("Tags")

    if st.button("Save"):
        if title.strip() == "" or content.strip() == "":
            st.error("Fill all fields")
        else:
            c.execute("""
                INSERT INTO notes (title, content, category, tags, company, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                title,
                content,
                category,
                tags,
                st.session_state.company,
                datetime.now().strftime("%Y-%m-%d %H:%M")
            ))

            conn.commit()
            st.success("Saved!")
            st.rerun()

# ---------------- DUDAS (TICKETS) ----------------
elif menu == "Dudas":
    st.subheader("🎫 Support Tickets")

    question = st.text_input("New ticket / doubt")
    priority = st.selectbox("Priority", ["LOW", "MEDIUM", "HIGH"])

    if st.button("Submit Ticket"):
        if question.strip() == "":
            st.error("Write a ticket first")
        else:
            c.execute("""
                INSERT INTO dudas (
                    question, answer, status, priority, assigned_to, company, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                question,
                "",
                "open",
                priority,
                "unassigned",
                st.session_state.company,
                datetime.now().strftime("%Y-%m-%d %H:%M")
            ))

            conn.commit()
            st.success("Ticket created!")
            st.rerun()

    st.divider()

    c.execute("""
        SELECT * FROM dudas
        WHERE status='open' AND company=?
        ORDER BY created_at DESC
    """, (st.session_state.company,))

    dudas = c.fetchall()

    for d in dudas:
        priority = d[4]

        emoji = "🟢"
        if priority == "MEDIUM":
            emoji = "🟡"
        elif priority == "HIGH":
            emoji = "🔴"

        with st.expander(f"{emoji} [{priority}] {d[1]}"):

            st.write(d[1])

            answer = st.text_area("Answer", key=f"ans_{d[0]}")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Resolve", key=f"resolve_{d[0]}"):
                    c.execute("""
                        UPDATE dudas
                        SET answer=?, status='closed'
                        WHERE id=?
                    """, (answer, d[0]))

                    conn.commit()
                    st.success("Resolved!")
                    st.rerun()

            with col2:
                if st.session_state.role == "admin":
                    if st.button("Delete", key=f"delete_{d[0]}"):
                        c.execute("DELETE FROM dudas WHERE id=?", (d[0],))
                        conn.commit()
                        st.warning("Deleted")
                        st.rerun()


















































































































































































































































































































