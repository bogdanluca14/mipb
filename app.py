import os
import json
from datetime import datetime
import streamlit as st
from streamlit_authenticator import Authenticate, Hasher

# Pentru Streamlit Community Cloud:
# Creează un fișier requirements.txt cu:
# streamlit
# streamlit-authenticator
# bcrypt
# și commit-ează-l în repo - dependențele se instalează automat.

# --- CONFIG STREAMLIT & STILIZARE ---
st.set_page_config(
    page_title="MatInfo Platform",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(
    """
    <style>
    body { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); }
    .card { background: #fff; padding: 1.5rem; margin: 1rem 0; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
    .stButton>button { background-color: #1f77b4; color: #fff; border-radius: 8px; padding: 0.5rem 1.5rem; font-weight: 600; }
    .stButton>button:hover { background-color: #155d8b; }
    .stTextInput input, .stTextArea textarea { border-radius: 8px; padding: 0.75rem; border: 1px solid #ccc; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- SISTEM DE STOCARE JSON ---
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

# Construim structura de credentials conform streamlit-authenticator
credentials = {"usernames": {}}
for user in data["users"]:
    credentials["usernames"][user["username"]] = {
        "name": user["name"],
        "password": user["hashed_password"]
    }

# Instanțiem autenticarea
authenticator = Authenticate(
    credentials,
    cookie_name="matinfo_session",
    key="random_key",
    cookie_expiry_days=30
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
                # Generăm hash-ul parolei
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
    # Login default (fără etichete suplimentare)
    name, auth_status, username = authenticator.login('Username', 'Password', 'sidebar')
    if auth_status:
        st.sidebar.success(f"Bine ai venit, {name}!")
        pages = ["Acasă", "Propune problemă", "Vizualizează probleme", "Articole"]
        # Adăugăm Dashboard Admin dacă userul e admin
        if any(u for u in data["users"] if u["username"] == username and u.get("is_admin")):
            pages.append("Dashboard Admin")
        page = st.sidebar.selectbox("Navigare", pages)

        # Pagina Acasă
        if page == "Acasă":
            st.markdown(
                f"<h2 style='text-align:center;'>Bine ai venit, <span style='color:#1f77b4;'>{name}</span>!</h2>",
                unsafe_allow_html=True
            )
        # ... restul codului rămâne neschimbat pentru pagini

        authenticator.logout("Logout", "sidebar")

    elif auth_status is False:
        st.error("Username sau parola incorectă.")
    else:
        st.warning("Te rog loghează-te.")
