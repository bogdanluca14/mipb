import os
import json
import bcrypt
import streamlit as st
from datetime import datetime

# Recomandări pentru deployment:
# Creează requirements.txt cu:
# streamlit
# bcrypt
# Commit-ează repo pentru Streamlit Cloud.

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
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"users": [], "problems": [], "votes": [], "comments": [], "articles": []}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

# --- UTILS AUTH ---
def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

# --- SESSION STATE ---
if 'user' not in st.session_state:
    st.session_state['user'] = None

# --- AUTH FLOW ---
mode = st.sidebar.selectbox("Mod", ["Login", "Register"])  

if mode == "Register":
    st.header("Înregistrare Utilizator")
    username = st.text_input("Username")
    name = st.text_input("Nume complet")
    password = st.text_input("Parolă", type='password')
    if st.button("Înregistrează-te"):
        if any(u['username'] == username for u in data['users']):
            st.error("Username exista deja.")
        elif not username or not password:
            st.error("Completează toate câmpurile.")
        else:
            hashed = hash_password(password)
            new_id = max((u['id'] for u in data['users']), default=0) + 1
            data['users'].append({
                'id': new_id,
                'username': username,
                'name': name,
                'password': hashed.decode('utf-8'),
                'is_admin': False
            })
            save_data(data)
            st.success("Înregistrare cu succes! Poți acum să te loghezi.")

elif st.session_state['user'] is None:
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Parolă", type='password')
    if st.button("Login"):
        user = next((u for u in data['users'] if u['username'] == username), None)
        if user and verify_password(password, user['password'].encode('utf-8')):
            st.session_state['user'] = user
            st.success(f"Bine ai venit, {user['name']}!")
        else:
            st.error("Username sau parola incorectă.")

# --- MAIN APP ---
if st.session_state['user']:
    st.sidebar.success(f"Logged in ca {st.session_state['user']['name']}")
    page = st.sidebar.selectbox("Navigare", ["Acasă", "Propune problemă", "Vizualizează probleme", "Articole", "Logout"])

    if page == "Acasă":
        st.title("Bine ai venit pe MatInfo Platform")
        st.write("Selectează o opțiune din meniu.")

    elif page == "Propune problemă":
        st.header("Propune o nouă problemă")
        title = st.text_input("Titlu")
        statement = st.text_area("Enunț")
        grade = st.selectbox("Clasa", list(range(5, 13)))
        diff = st.selectbox("Dificultate", ["Ușor", "Mediu", "Greu"])
        if st.button("Salvează problema"):
            pid = max((p['id'] for p in data['problems']), default=0) + 1
            data['problems'].append({
                'id': pid,
                'title': title,
                'statement': statement,
                'grade': grade,
                'difficulty': diff,
                'author_id': st.session_state['user']['id'],
                'created_at': datetime.utcnow().isoformat()
            })
            save_data(data)
            st.success("Problemă adăugată cu succes!")

    elif page == "Vizualizează probleme":
        st.header("Probleme propuse")
        for p in sorted(data['problems'], key=lambda x: x['created_at'], reverse=True):
            st.markdown(f"### {p['title']} (Clasa {p['grade']}, {p['difficulty']})")
            st.write(p['statement'])
            st.markdown('---')

    elif page == "Articole":
        st.header("Articole")
        for a in sorted(data['articles'], key=lambda x: x['created_at'], reverse=True):
            st.subheader(a['title'])
            st.write(a['content'])
            st.markdown('---')

    else:  # Logout
        st.session_state['user'] = None
        st.experimental_rerun()
