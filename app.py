import os
import json
from datetime import datetime
import streamlit as st
from streamlit_authenticator import Authenticate, Hasher

# Pentru Streamlit Community Cloud:
# - Creează un fișier requirements.txt în același director cu:
#     streamlit
#     streamlit-authenticator
#     bcrypt
# - Commit‐ează‐l în repo și Streamlit va instala automat dependențele.

# --- CONFIG STREAMLIT & STILIZARE ---
st.set_page_config(
    page_title="MatInfo Platform",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(
    """
    <style>
    body { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); }
    .card { background: #fff; padding: 1.5rem; margin: 1rem 0; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
    .stButton>button { background-color: #1f77b4; color: #fff; border-radius: 8px; padding: 0.5rem 1.5rem; font-weight: 600; }
    .stButton>button:hover { background-color: #155d8b; transition: 0.2s; }
    .stTextInput input, .stTextArea textarea { border-radius: 8px; padding: 0.75rem; border: 1px solid #ccc; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- SISTEM DE STORARE JSON ---
DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": [], "problems": [], "votes": [], "comments": [], "articles": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

# --- AUTENTIFICARE & ÎNREGISTRARE ---
mode = st.sidebar.selectbox("Mod", ["Login", "Register"])

def get_credentials(users):
    return {
        "username": [u["username"] for u in users],
        "name": [u["name"] for u in users],
        "password": [u["hashed_password"] for u in users]
    }

credentials = get_credentials(data["users"])
authenticator = Authenticate(
    credentials,
    cookie_name="matinfo_session",
    key="random_key",
    cookie_expiry_days=30,
)

if mode == "Register":
    st.header("Înregistrare Utilizator")
    with st.form("register_form"):
        new_username = st.text_input("Username")
        new_name = st.text_input("Nume complet")
        new_password = st.text_input("Parolă", type="password")
        if st.form_submit_button("Înregistrează-te"):
            if any(u["username"] == new_username for u in data["users"]):
                st.error("Username-ul există deja.")
            else:
                hashed = Hasher([new_password]).generate()[0]
                new_id = max((u["id"] for u in data["users"]), default=0) + 1
                data["users"].append({
                    "id": new_id,
                    "username": new_username,
                    "name": new_name,
                    "hashed_password": hashed,
                    "is_admin": False
                })
                save_data(data)
                st.success("Înregistrare cu succes! Te poți loga acum.")
                st.experimental_rerun()
else:
    name, auth_status, username = authenticator.login("Login", "main")
    if auth_status:
        st.sidebar.success(f"Bine ai venit, {name}!")
        pages = ["Acasă", "Propune problemă", "Vizualizează probleme", "Articole"]
        if any(u for u in data["users"] if u["username"] == username and u.get("is_admin")):
            pages.append("Dashboard Admin")
        page = st.sidebar.selectbox("Navigare", pages)

        if page == "Acasă":
            st.markdown(f"<h2 style='text-align:center;'>Bine ai venit, <span style='color:#1f77b4;'>{name}</span>!</h2>", unsafe_allow_html=True)
        elif page == "Propune problemă":
            st.subheader("Încarcă o problemă nouă")
            with st.form("upload_problem"):
                title = st.text_input("Titlu")
                statement = st.text_area("Enunț")
                grade = st.selectbox("Clasa", list(range(5, 13)))
                difficulty = st.selectbox("Dificultate", ["Ușor", "Mediu", "Greu"])
                if st.form_submit_button("Salvează"):
                    pid = max((p["id"] for p in data["problems"]), default=0) + 1
                    author = next(u for u in data["users"] if u["username"] == username)["id"]
                    data["problems"].append({
                        "id": pid,
                        "title": title,
                        "statement": statement,
                        "grade": grade,
                        "difficulty": difficulty,
                        "author_id": author,
                        "created_at": datetime.utcnow().isoformat()
                    })
                    save_data(data)
                    st.success("Problemă încărcată cu succes!")
        elif page == "Vizualizează probleme":
            st.subheader("Listă probleme")
            for p in sorted(data["problems"], key=lambda x: x["created_at"], reverse=True):
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                cols = st.columns([4,1,1])
                cols[0].markdown(f"**{p['title']}** (Clasa {p['grade']}, {p['difficulty']})")
                vote_count = len([v for v in data["votes"] if v["problem_id"] == p["id"]])
                comment_count = len([c for c in data["comments"] if c["problem_id"] == p["id"]])
                if cols[1].button(f"👍 {vote_count}", key=f"vote_{p['id']}"):
                    uid = next(u for u in data["users"] if u["username"] == username)["id"]
                    data["votes"].append({"user_id": uid, "problem_id": p["id"], "created_at": datetime.utcnow().isoformat()})
                    save_data(data)
                    st.experimental_rerun()
                if cols[2].button(f"💬 {comment_count}", key=f"comment_{p['id']}"):
                    st.session_state['comment_problem'] = p['id']
                    st.experimental_rerun()
                if st.session_state.get('comment_problem') == p['id']:
                    comment = st.text_area("Comentariu")
                    if st.button("Trimite", key=f"send_comment_{p['id']}"):
                        uid = next(u for u in data["users"] if u["username"] == username)["id"]
                        data["comments"].append({"user_id": uid, "problem_id": p['id'], "content": comment, "created_at": datetime.utcnow().isoformat()})
                        save_data(data)
                        st.success("Comentariu adăugat!")
                        del st.session_state['comment_problem']
                        st.experimental_rerun()
                st.markdown("</div>", unsafe_allow_html=True)
        elif page == "Articole":
            st.subheader("Articole")
            for a in sorted(data["articles"], key=lambda x: x["created_at"], reverse=True):
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown(f"### {a['title']}")
                st.write(a['content'])
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.subheader("Administrare conținut")
            st.write("Feature în curs de implementare...")

        authenticator.logout("Logout", "sidebar")
    elif auth_status is False:
        st.error("Username sau parola incorectă.")
    else:
        st.warning("Te rog loghează-te.")
