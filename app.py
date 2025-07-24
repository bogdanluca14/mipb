# MatInfo MVP - Platformă educațională (Informatica & Matematică)
# Inspirat de platformele Kilonova, PbInfo și Codeforces pentru funcționalități (meniuri, evaluare automată, clasamente):contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}.
import streamlit as st
import json, os, hashlib, subprocess, time
from datetime import datetime

# --- Constants and initial data ---
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PROBLEMS_FILE = os.path.join(DATA_DIR, "problems.json")
MATH_PROBLEMS_FILE = os.path.join(DATA_DIR, "math_problems.json")
CODE_SUBMISSIONS_FILE = os.path.join(DATA_DIR, "code_submissions.json")
MATH_SUBMISSIONS_FILE = os.path.join(DATA_DIR, "math_submissions.json")
ARTICLES_FILE = os.path.join(DATA_DIR, "articles.json")
MESSAGES_FILE = os.path.join(DATA_DIR, "messages.json")

os.makedirs(DATA_DIR, exist_ok=True)

# Default admin and sample content for first run
default_admin_user = {"password": hashlib.sha256("admin".encode()).hexdigest(), "role": "admin"}
default_problem = {
    "id": 1,
    "title": "Suma a două numere",
    "statement": "Citește două numere întregi din input și afișează suma lor.",
    "input_format": "Două numere întregi separate prin spațiu",
    "output_format": "Un singur număr întreg reprezentând suma.",
    "tests": [
        {"input": "3 4\n", "output": "7\n"},
        {"input": "0 0\n", "output": "0\n"}
    ],
    "time_limit": 2.0,
    "memory_limit": 256,
    "author": "admin"
}
default_math_problem = {
    "id": 1,
    "title": "Pitagora simplu",
    "statement": "Demonstrați teorema lui Pitagora. *(Acesta este un exemplu de problemă cu demonstrație.)*",
    "rubric": "7 puncte: demonstrație completă corectă. 4 puncte: idee corectă dar incompletă. 0 puncte: soluție greșită sau incompletă.",
    "solution": "Teorema lui Pitagora: ... (soluție detaliată cu demonstrația completă) ...",
    "answer": None,
    "author": "admin"
}
default_article = {
    "id": 1,
    "title": "Bun venit pe MatInfo",
    "content": "Aceasta este platforma **MatInfo**. Aici puteți rezolva probleme de informatică și matematică, și puteți citi articole educative.",
    "author": "admin",
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

# Helper functions for JSON storage
def load_data(file_path, default_data):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default_data
    else:
        return default_data

def save_data(file_path, data):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Eroare la salvarea datelor în {file_path}: {e}")

# Load or initialize data files
users = load_data(USERS_FILE, {})
problems = load_data(PROBLEMS_FILE, [])
math_problems = load_data(MATH_PROBLEMS_FILE, [])
code_submissions = load_data(CODE_SUBMISSIONS_FILE, [])
math_submissions = load_data(MATH_SUBMISSIONS_FILE, [])
articles = load_data(ARTICLES_FILE, [])
messages = load_data(MESSAGES_FILE, [])

# Initialize default admin and content if empty
if len(users) == 0:
    users["admin"] = default_admin_user
    problems = [default_problem]
    math_problems = [default_math_problem]
    articles = [default_article]
    messages = []
    save_data(USERS_FILE, users)
    save_data(PROBLEMS_FILE, problems)
    save_data(MATH_PROBLEMS_FILE, math_problems)
    save_data(ARTICLES_FILE, articles)
    save_data(MESSAGES_FILE, messages)
    save_data(CODE_SUBMISSIONS_FILE, code_submissions)
    save_data(MATH_SUBMISSIONS_FILE, math_submissions)

# Session state for authentication
if 'user' not in st.session_state:
    st.session_state.user = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login_user(username, password):
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    if username in users and users[username]['password'] == pw_hash:
        st.session_state.user = username
        st.session_state.role = users[username]['role']
        st.session_state.logged_in = True
        return True
    return False

def register_user(username, password, role="student"):
    if username in users:
        return False, "Username deja existent."
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    users[username] = {"password": pw_hash, "role": role}
    save_data(USERS_FILE, users)
    welcome_msg = {
        "id": len(messages)+1,
        "from": "System",
        "to": username,
        "content": f"Bun venit pe MatInfo, **{username}**! Spor la rezolvat probleme.",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "read": False
    }
    messages.append(welcome_msg)
    save_data(MESSAGES_FILE, messages)
    return True, None

# Authentication interface
if not st.session_state.logged_in:
    st.title("MatInfo - Platformă Educațională")
    st.subheader("Autentificare / Înregistrare")
    choice = st.radio("", ["Login", "Înregistrare"], horizontal=True)
    if choice == "Login":
        login_form = st.form("login_form")
        username = login_form.text_input("Username")
        password = login_form.text_input("Parolă", type="password")
        submit = login_form.form_submit_button("Login")
        if submit:
            if login_user(username, password):
                st.success(f"Autentificat ca {username}")
                st.experimental_rerun()
            else:
                st.error("Credențiale invalide.")
    else:
        reg_form = st.form("reg_form")
        new_user = reg_form.text_input("Alegeți un username")
        new_pass = reg_form.text_input("Alegeți o parolă", type="password")
        confirm_pass = reg_form.text_input("Confirmați parola", type="password")
        reg_submit = reg_form.form_submit_button("Înregistrare")
        if reg_submit:
            if new_pass != confirm_pass:
                st.error("Parolele nu se potrivesc.")
            elif new_user.strip() == "" or new_pass.strip() == "":
                st.error("Completați toate câmpurile.")
            else:
                ok, msg = register_user(new_user, new_pass)
                if ok:
                    st.success("Cont creat! Vă autentificăm...")
                    login_user(new_user, new_pass)
                    st.experimental_rerun()
                else:
                    st.error(msg)
else:
    username = st.session_state.user
    role = st.session_state.role
    # Sidebar info
    st.sidebar.markdown(f"Utilizator: **{username}** *(rol: {role})*")
    dark_mode = st.sidebar.checkbox("Dark mode", value=False)
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.role = None
        st.session_state.logged_in = False
        st.experimental_rerun()
    # Apply theme CSS
    dark_css = "<style>.stApp { background-color: #0E1117; color: #FAFAFA; }</style>"
    light_css = "<style>.stApp { background-color: #FFFFFF; color: #000000; }</style>"
    st.markdown(dark_css if dark_mode else light_css, unsafe_allow_html=True)
    # Navigation menu (inspired by Kilonova structure:contentReference[oaicite:2]{index=2})
    nav_options = ["🏠 Acasă", "💻 Probleme Informatica", "🧮 Probleme Matematică", "📚 Articole", "💬 Mesaje", "🏆 Clasament"]
    if role in ["admin", "editor"]:
        nav_options.append("⚙️ Admin")
    current_nav = st.radio("Navigare", nav_options, horizontal=True, key="main_nav")
    if 'last_nav' not in st.session_state:
        st.session_state.last_nav = current_nav
    if st.session_state.last_nav != current_nav:
        # Clear context when switching sections
        for key in ['selected_problem','adding_problem','selected_math_problem','adding_math','selected_article','adding_article']:
            if key in st.session_state: del st.session_state[key]
        st.session_state.last_nav = current_nav

    # Home Page
    if current_nav.startswith("🏠"):
        st.header(f"Bun venit, {username}!")
        st.write("Aceasta este pagina principală a platformei MatInfo.")
        st.subheader("Ultimele articole:")
        if articles:
            latest_articles = sorted(articles, key=lambda x: x.get("timestamp",""), reverse=True)[:3]
            for art in latest_articles:
                st.markdown(f"- **{art['title']}** - *{art['author']}* - _{art.get('timestamp','')}_")
        else:
            st.write("Nu există articole de afișat.")
        st.subheader("Ultimele probleme adăugate:")
        if problems or math_problems:
            latest_probs = sorted(problems, key=lambda x: x['id'], reverse=True)[:3]
            for pb in latest_probs:
                st.markdown(f"- **[Info] {pb['title']}** (autor: {pb.get('author','')})")
            latest_maths = sorted(math_problems, key=lambda x: x['id'], reverse=True)[:3]
            for mp in latest_maths:
                st.markdown(f"- **[Mate] {mp['title']}** (autor: {mp.get('author','')})")
        else:
            st.write("Nu există probleme încă.")
        st.write("Folosiți meniul de mai sus pentru navigare între secțiuni.")
    # Informatics Problems Page
    elif current_nav.startswith("💻"):
        st.header("Probleme de Informatică")
        # Adding new problem form
        if role in ["admin", "editor"] and st.session_state.get('adding_problem'):
            st.subheader("Adaugă problemă nouă")
            form = st.form("new_problem_form")
            title = form.text_input("Titlu problemă")
            statement = form.text_area("Enunț (puteți include formule LaTeX folosind $...$)", height=150)
            input_format = form.text_input("Format intrare", "")
            output_format = form.text_input("Format ieșire", "")
            tests_raw = form.text_area("Teste (format: input<newline>===<newline>output, separate prin o linie \"---\")", height=150)
            time_limit = form.number_input("Time limit (secunde)", value=2.0)
            memory_limit = form.number_input("Memory limit (MB)", value=256)
            submit_new = form.form_submit_button("Salvează")
            cancel_new = form.form_submit_button("Anulează")
            if submit_new:
                if title.strip() == "" or statement.strip() == "" or tests_raw.strip() == "":
                    st.error("Completează titlul, enunțul și testele.")
                else:
                    tests = []
                    try:
                        parts = tests_raw.split("\n---\n")
                        for part in parts:
                            io = part.split("\n===\n")
                            if len(io) == 2:
                                inp = io[0] + ("\n" if not io[0].endswith("\n") else "")
                                outp = io[1] + ("\n" if not io[1].endswith("\n") else "")
                                tests.append({"input": inp, "output": outp})
                        new_id = max([p['id'] for p in problems] or [0]) + 1
                        new_problem = {
                            "id": new_id,
                            "title": title,
                            "statement": statement,
                            "input_format": input_format,
                            "output_format": output_format,
                            "tests": tests,
                            "time_limit": time_limit,
                            "memory_limit": memory_limit,
                            "author": username
                        }
                        problems.append(new_problem)
                        save_data(PROBLEMS_FILE, problems)
                        st.success("Problema a fost adăugată.")
                        # Notify all users
                        notif_text = f"Problema nouă adăugată: {title}"
                        for user in users:
                            msg = {
                                "id": len(messages)+1,
                                "from": "System",
                                "to": user,
                                "content": notif_text,
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "read": False
                            }
                            messages.append(msg)
                        save_data(MESSAGES_FILE, messages)
                    except Exception as e:
                        st.error(f"Eroare la procesarea testelor: {e}")
                    st.session_state['adding_problem'] = False
            if cancel_new:
                st.session_state['adding_problem'] = False
            st.stop()
        # Problem detail vs list
        if st.session_state.get('selected_problem'):
            pid = st.session_state['selected_problem']
            prob = next((p for p in problems if p['id'] == pid), None)
            if not prob:
                st.error("Problema nu a fost găsită.")
            else:
                st.subheader(prob['title'])
                st.markdown(prob['statement'])
                if prob.get('input_format'):
                    st.markdown(f"**Format intrare:** {prob['input_format']}")
                if prob.get('output_format'):
                    st.markdown(f"**Format ieșire:** {prob['output_format']}")
                st.write("Trimite o soluție:")
                with st.form("submit_code_form"):
                    lang = st.selectbox("Limbaj", ["Python", "C++"])
                    code = st.text_area("Cod sursă", height=200)
                    submit_code = st.form_submit_button("Trimite")
                if submit_code:
                    sub_id = len(code_submissions) + 1
                    submission = {
                        "id": sub_id, "user": username, "problem_id": pid,
                        "language": lang, "verdict": "Pending",
                        "tests_passed": 0, "total_tests": len(prob['tests']),
                        "time_used": None, "error_message": None
                    }
                    code_file = exec_file = None
                    try:
                        if lang == "Python":
                            code_file = os.path.join(DATA_DIR, f"sub{sub_id}.py")
                            with open(code_file, 'w', encoding='utf-8') as f:
                                f.write(code)
                            all_passed = True
                            for idx, test in enumerate(prob['tests'], start=1):
                                try:
                                    result = subprocess.run(
                                        ["python", code_file],
                                        input=test['input'], text=True,
                                        capture_output=True, timeout=prob.get("time_limit", 2.0)
                                    )
                                    if result.returncode != 0:
                                        submission['verdict'] = f"Runtime Error (Test {idx})"
                                        err = result.stderr.strip().splitlines()[-1] if result.stderr else "Runtime Error"
                                        submission['error_message'] = err
                                        all_passed = False
                                        break
                                    expected = test['output'].replace("\r","")
                                    got = result.stdout.replace("\r","")
                                    if got != expected:
                                        submission['verdict'] = f"Wrong Answer (Test {idx})"
                                        all_passed = False
                                        break
                                    else:
                                        submission['tests_passed'] += 1
                                except subprocess.TimeoutExpired:
                                    submission['verdict'] = f"Time Limit Exceeded (Test {idx})"
                                    all_passed = False
                                    break
                            if all_passed:
                                submission['verdict'] = "OK"
                        else:  # C++
                            code_file = os.path.join(DATA_DIR, f"sub{sub_id}.cpp")
                            exec_file = os.path.join(DATA_DIR, f"sub{sub_id}.exe")
                            with open(code_file, 'w', encoding='utf-8') as f:
                                f.write(code)
                            comp_proc = subprocess.run(["g++", code_file, "-O2", "-std=c++17", "-o", exec_file],
                                                       capture_output=True, text=True)
                            if comp_proc.returncode != 0:
                                submission['verdict'] = "Compilation Error"
                                submission['error_message'] = comp_proc.stderr[:2000]
                            else:
                                all_passed = True
                                for idx, test in enumerate(prob['tests'], start=1):
                                    try:
                                        result = subprocess.run(
                                            [exec_file],
                                            input=test['input'], text=True,
                                            capture_output=True, timeout=prob.get("time_limit", 2.0)
                                        )
                                        if result.returncode != 0:
                                            submission['verdict'] = f"Runtime Error (Test {idx})"
                                            submission['error_message'] = f"Exit code {result.returncode}"
                                            all_passed = False
                                            break
                                        expected = test['output'].replace("\r","")
                                        got = result.stdout.replace("\r","")
                                        if got != expected:
                                            submission['verdict'] = f"Wrong Answer (Test {idx})"
                                            all_passed = False
                                            break
                                        else:
                                            submission['tests_passed'] += 1
                                    except subprocess.TimeoutExpired:
                                        submission['verdict'] = f"Time Limit Exceeded (Test {idx})"
                                        all_passed = False
                                        break
                                if all_passed:
                                    submission['verdict'] = "OK"
                        submission['time_used'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    except Exception as e:
                        submission['verdict'] = "Internal Error"
                        submission['error_message'] = str(e)
                    finally:
                        if code_file and os.path.exists(code_file): os.remove(code_file)
                        if exec_file and os.path.exists(exec_file): os.remove(exec_file)
                    code_submissions.append(submission)
                    save_data(CODE_SUBMISSIONS_FILE, code_submissions)
                    # Interpretare verdict (OK, Wrong Answer, TLE etc. conform platformelor tip Codeforces/PbInfo:contentReference[oaicite:3]{index=3})
                    if submission['verdict'] == "OK":
                        st.success("Răspuns corect! Toate testele au trecut.")
                    elif submission['verdict'] == "Compilation Error":
                        st.error("Eroare la compilare:\n" + submission.get('error_message',""))
                    elif submission['verdict'].startswith("Wrong Answer"):
                        st.error("Răspuns greșit la " + submission['verdict'].split(' ', 2)[2])
                    elif "Time Limit" in submission['verdict']:
                        st.warning("Timp depășit la " + submission['verdict'].split(' ', 3)[3])
                    elif "Runtime Error" in submission['verdict']:
                        err_msg = submission.get('error_message',"")
                        st.error("Eroare de execuție la " + submission['verdict'].split(' ', 3)[3] + (": " + err_msg if err_msg else ""))
                    else:
                        st.error("Rezultat: " + submission['verdict'])
                    if submission['verdict'] != "OK":
                        st.write(f"Teste trecute: {submission['tests_passed']}/{submission['total_tests']}")
                if st.button("Înapoi la lista de probleme"):
                    st.session_state['selected_problem'] = None
        else:
            if role in ["admin", "editor"]:
                if st.button("Adaugă problemă nouă"):
                    st.session_state['adding_problem'] = True
                    st.experimental_rerun()
            if not problems:
                st.write("Nicio problemă disponibilă.")
            else:
                for pb in problems:
                    solved = any(sub['problem_id']==pb['id'] and sub['user']==username and sub['verdict']=="OK" for sub in code_submissions)
                    status = "✔️" if solved else "❌"
                    if st.button(f"{pb['title']} {status}", key=f"prob_{pb['id']}"):
                        st.session_state['selected_problem'] = pb['id']
                        st.experimental_rerun()
    # Math Problems Page
    elif current_nav.startswith("🧮"):
        st.header("Probleme de Matematică")
        if role in ["admin", "editor"] and st.session_state.get('adding_math'):
            st.subheader("Adaugă problemă de matematică")
            form = st.form("new_math_form")
            title = form.text_input("Titlu problemă")
            statement = form.text_area("Enunț", height=150)
            rubric = form.text_area("Barem de punctaj (opțional)", height=100)
            solution = form.text_area("Soluție oficială", height=150)
            answer = form.text_input("Răspuns (dacă există un răspuns unic așteptat)")
            submit_new = form.form_submit_button("Salvează")
            cancel_new = form.form_submit_button("Anulează")
            if submit_new:
                if title.strip()=="" or statement.strip()=="":
                    st.error("Titlul și enunțul sunt obligatorii.")
                else:
                    new_id = max([m['id'] for m in math_problems] or [0]) + 1
                    new_prob = {
                        "id": new_id, "title": title, "statement": statement,
                        "rubric": rubric, "solution": solution,
                        "answer": answer.strip() if answer.strip() else None,
                        "author": username
                    }
                    math_problems.append(new_prob)
                    save_data(MATH_PROBLEMS_FILE, math_problems)
                    st.success("Problema a fost adăugată.")
                    notif_text = f"Problemă de matematică nouă: {title}"
                    for user in users:
                        msg = {
                            "id": len(messages)+1,
                            "from": "System",
                            "to": user,
                            "content": notif_text,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "read": False
                        }
                        messages.append(msg)
                    save_data(MESSAGES_FILE, messages)
                    st.session_state['adding_math'] = False
            if cancel_new:
                st.session_state['adding_math'] = False
            st.stop()
        if st.session_state.get('selected_math_problem'):
            mid = st.session_state['selected_math_problem']
            mp = next((m for m in math_problems if m['id']==mid), None)
            if not mp:
                st.error("Problema nu a fost găsită.")
            else:
                st.subheader(mp['title'])
                st.markdown(mp['statement'])
                if mp.get('rubric'):
                    st.markdown(f"**Barem:** {mp['rubric']}")
                submission = next((s for s in math_submissions if s['user']==username and s['problem_id']==mid), None)
                if submission:
                    if submission.get('score') is not None:
                        st.info(f"Ați obținut {submission['score']} puncte la această problemă.")
                    if submission.get('answer_text'):
                        st.write("Soluția trimisă de dvs.:")
                        st.markdown(submission['answer_text'])
                    if not submission.get('viewed_solution'):
                        if st.button("Vezi soluția oficială"):
                            submission['viewed_solution'] = True
                            save_data(MATH_SUBMISSIONS_FILE, math_submissions)
                    else:
                        st.subheader("Soluție oficială:")
                        st.markdown(mp.get('solution',"*(Soluția nu este disponibilă)*"))
                else:
                    st.write("Trimite soluția sau renunță pentru a vedea soluția oficială.")
                    with st.form("math_submit_form"):
                        answer_text = st.text_area("Rezolvarea ta (descriere sau răspuns final)", height=150)
                        submit_ans = st.form_submit_button("Trimite soluția")
                        give_up = st.form_submit_button("Renunță")
                    if submit_ans:
                        if answer_text.strip() == "":
                            st.error("Trebuie să scrieți soluția întâi.")
                        else:
                            sub_id = len(math_submissions)+1
                            new_sub = {
                                "id": sub_id, "user": username, "problem_id": mid,
                                "answer_text": answer_text, "score": None, "viewed_solution": False
                            }
                            math_submissions.append(new_sub)
                            save_data(MATH_SUBMISSIONS_FILE, math_submissions)
                            st.success("Soluția a fost trimisă spre evaluare.")
                            st.experimental_rerun()
                    if give_up:
                        sub_id = len(math_submissions)+1
                        new_sub = {
                            "id": sub_id, "user": username, "problem_id": mid,
                            "answer_text": "", "score": 0, "viewed_solution": True
                        }
                        math_submissions.append(new_sub)
                        save_data(MATH_SUBMISSIONS_FILE, math_submissions)
                        st.warning("Ați renunțat. Nu veți primi punctaj.")
                        st.experimental_rerun()
                if role in ["admin", "editor"]:
                    st.subheader("Trimiteri de corectat:")
                    pending = [s for s in math_submissions if s['problem_id']==mid and s['score'] is None]
                    if pending:
                        for sub in pending:
                            st.markdown(f"**{sub['user']}** a trimis:")
                            st.markdown(sub['answer_text'] if sub['answer_text'] else "*[fără conținut]*")
                            grade = st.number_input(f"Punctaj pentru {sub['user']} (0-100)", 0, 100, 0, key=f"score_{sub['id']}")
                            feedback = st.text_input(f"Feedback pentru {sub['user']}", key=f"fb_{sub['id']}")
                            if st.button(f"Salvează punctaj ({sub['user']})", key=f"grade_{sub['id']}"):
                                sub['score'] = grade
                                save_data(MATH_SUBMISSIONS_FILE, math_submissions)
                                msg = {
                                    "id": len(messages)+1,
                                    "from": username,
                                    "to": sub['user'],
                                    "content": f"Soluția ta la problema '{mp['title']}' a fost notată cu {grade} puncte. " + (f"Feedback: {feedback}" if feedback else ""),
                                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "read": False
                                }
                                messages.append(msg)
                                save_data(MESSAGES_FILE, messages)
                                st.success("Punctaj salvat.")
                                st.experimental_rerun()
                    else:
                        st.write("Nicio soluție în așteptare.")
                if st.button("Înapoi la lista de probleme"):
                    st.session_state['selected_math_problem'] = None
        else:
            if role in ["admin", "editor"]:
                if st.button("Adaugă problemă de matematică"):
                    st.session_state['adding_math'] = True
                    st.experimental_rerun()
            if not math_problems:
                st.write("Nicio problemă disponibilă.")
            else:
                for mp in math_problems:
                    solved_full = any(sub['problem_id']==mp['id'] and sub['user']==username and sub.get('score',0)==100 for sub in math_submissions)
                    attempted = any(sub['problem_id']==mp['id'] and sub['user']==username for sub in math_submissions)
                    status = "✔️" if solved_full else ("📖" if attempted else "❌")
                    if st.button(f"{mp['title']} {status}", key=f"math_{mp['id']}"):
                        st.session_state['selected_math_problem'] = mp['id']
                        st.experimental_rerun()
    # Articles Page
    elif current_nav.startswith("📚"):
        st.header("Articole și Resurse")
        if role in ["admin", "editor"] and st.session_state.get('adding_article'):
            st.subheader("Articol nou")
            form = st.form("new_article_form")
            title = form.text_input("Titlu")
            content = form.text_area("Conținut (Markdown/LaTeX permis)", height=150)
            submit_new = form.form_submit_button("Publică")
            cancel_new = form.form_submit_button("Anulează")
            if submit_new:
                if title.strip()=="" or content.strip()=="":
                    st.error("Titlul și conținutul nu pot fi goale.")
                else:
                    new_id = max([a['id'] for a in articles] or [0]) + 1
                    new_article = {
                        "id": new_id, "title": title, "content": content,
                        "author": username, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    articles.append(new_article)
                    save_data(ARTICLES_FILE, articles)
                    st.success("Articol publicat.")
                    notif_text = f"Articol nou: {title}"
                    for user in users:
                        msg = {
                            "id": len(messages)+1,
                            "from": "System",
                            "to": user,
                            "content": notif_text,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "read": False
                        }
                        messages.append(msg)
                    save_data(MESSAGES_FILE, messages)
                    st.session_state['adding_article'] = False
            if cancel_new:
                st.session_state['adding_article'] = False
            st.stop()
        if st.session_state.get('selected_article'):
            art_id = st.session_state['selected_article']
            art = next((a for a in articles if a['id']==art_id), None)
            if not art:
                st.error("Articolul nu a fost găsit.")
            else:
                st.subheader(art['title'])
                st.markdown(art['content'])
                st.markdown(f"*Autor: {art['author']} | Publicat la {art.get('timestamp','')}*")
                if st.button("Înapoi la articole"):
                    st.session_state['selected_article'] = None
        else:
            if role in ["admin", "editor"]:
                if st.button("Scrie un articol"):
                    st.session_state['adding_article'] = True
                    st.experimental_rerun()
            if not articles:
                st.write("Nu există articole încă.")
            else:
                for art in sorted(articles, key=lambda x: x.get("timestamp",""), reverse=True):
                    if st.button(f"{art['title']} - {art['author']}", key=f"art_{art['id']}"):
                        st.session_state['selected_article'] = art['id']
                        st.experimental_rerun()
    # Messages Page
    elif current_nav.startswith("💬"):
        st.header("Mesaje")
        inbox = [m for m in messages if m['to'] == username]
        if not inbox:
            st.write("Nu aveți mesaje.")
        else:
            inbox_sorted = sorted(inbox, key=lambda x: x['timestamp'])
            for msg in inbox_sorted:
                sender = msg['from']; time_str = msg.get('timestamp',""); content = msg['content']
                unread = not msg.get('read', False)
                if unread:
                    st.markdown(f"🔔 **De la {sender}** *(necitit, {time_str})*: {content}")
                else:
                    st.markdown(f"*De la {sender}* ({time_str}): {content}")
            # Mark all displayed as read
            for msg in inbox_sorted:
                if not msg.get('read', False):
                    msg['read'] = True
            save_data(MESSAGES_FILE, messages)
        st.subheader("Trimite mesaj")
        with st.form("send_msg_form"):
            recipient = st.selectbox("Către", [u for u in users if u != username])
            text = st.text_area("Conținut", height=100)
            send_btn = st.form_submit_button("Trimite")
        if send_btn:
            if text.strip()=="":
                st.error("Mesajul este gol.")
            else:
                new_msg = {
                    "id": len(messages)+1, "from": username, "to": recipient,
                    "content": text, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "read": False
                }
                messages.append(new_msg)
                save_data(MESSAGES_FILE, messages)
                st.success("Mesaj trimis.")
                st.experimental_rerun()
    # Rankings Page
    elif current_nav.startswith("🏆"):
        st.header("Clasament Utilizatori")
        ranking = []
        for user, data in users.items():
            total_score = 0
            solved_set = {sub['problem_id'] for sub in code_submissions if sub['user']==user and sub['verdict']=="OK"}
            total_score += 100 * len(solved_set)
            math_scores = {}
            for sub in math_submissions:
                if sub['user']==user and sub.get('score') is not None:
                    pid = sub['problem_id']
                    math_scores[pid] = max(math_scores.get(pid, 0), sub['score'])
            total_score += sum(math_scores.values())
            ranking.append({"Utilizator": user, "Rol": data['role'], "Punctaj": total_score})
        ranking.sort(key=lambda x: x["Punctaj"], reverse=True)
        if not ranking:
            st.write("Clasamentul este gol.")
        else:
            st.table(ranking)
    # Admin Page
    elif current_nav.startswith("⚙️"):
        st.header("Panou Admin")
        st.subheader("Gestionare Utilizatori")
        with st.form("roles_form"):
            new_roles = {}
            for user, data in users.items():
                new_roles[user] = st.selectbox(f"{user}", ["student","editor","admin"],
                                               index=["student","editor","admin"].index(data['role']), key=f"role_{user}")
            updated = st.form_submit_button("Actualizează")
        if updated:
            for user, new_role in new_roles.items():
                users[user]['role'] = new_role
            save_data(USERS_FILE, users)
            st.success("Roluri actualizate.")
        st.subheader("Statistici")
        st.write(f"Utilizatori: **{len(users)}**")
        st.write(f"Probleme informatică: **{len(problems)}**, probleme matematică: **{len(math_problems)}**")
        st.write(f"Trimiteri totale: **{len(code_submissions)+len(math_submissions)}**")
