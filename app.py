import streamlit as st
import subprocess, os
import json, hashlib, time
from datetime import datetime
from contextlib import redirect_stdout
import io

try:
    # Importă editorul Ace pentru cod (dacă nu este instalat, se va instala automat)
    from streamlit_ace import st_ace
except ImportError:
    st.write('Installing streamlit-ace for code editor...')
    subprocess.run(['pip', 'install', 'streamlit-ace'], capture_output=True, text=True)
    from streamlit_ace import st_ace

# ---------- Configuration: Page setup and theming ----------
st.set_page_config(page_title="MatInfo Platform", layout="wide")
# Dark theme via custom CSS
dark_css = '''
<style>
body, .stApp {
    background-color: #1e1e1e;
    color: #e0e0e0;
}
/* Style sidebar */
.stSidebar, .css-6awftf.egzxvld2 {
    background-color: #2b2b2b;
}
/* Style primary colored elements (e.g., buttons, selectboxes) */
.css-1fv8s86 {
    background-color: #264F78 !important;
    color: #FFFFFF !important;
}
/* Monospace font for text areas (code inputs) */
textarea {
    font-family: "Source Code Pro", monospace;
    font-size: 0.9rem;
}
</style>
'''
st.markdown(dark_css, unsafe_allow_html=True)

# ---------- Utility functions for data persistence ----------
DATA_DIR = "."
def load_json(filename, default):
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return default
    else:
        return default

def save_json(filename, data):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

# Load or initialize data
users = load_json("users.json", default=[])
problems = load_json("problems.json", default=[])
submissions = load_json("submissions.json", default=[])
articles = load_json("articles.json", default=[])
comments = load_json("comments.json", default=[])

# Ensure session state keys
if 'view_problem' not in st.session_state:
    st.session_state['view_problem'] = None

# ---------- Helper functions for app logic ----------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def check_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def get_new_id(list_of_dicts):
    if not list_of_dicts:
        return 1
    else:
        max_id = max(item.get("id", 0) for item in list_of_dicts)
        return max_id + 1

def ensure_admin_exists():
    # Ensure there's at least one admin user
    admin_exists = any(u['role'] == 'admin' for u in users)
    if not admin_exists:
        default_admin = {"id": get_new_id(users), "username": "admin", "password": hash_password("admin"), "role": "admin"}
        users.append(default_admin)
        save_json("users.json", users)
ensure_admin_exists()

def record_submission(submission):
    submissions.append(submission)
    save_json("submissions.json", submissions)

def get_user_by_username(username):
    return next((u for u in users if u["username"] == username), None)

def evaluate_math_submission(problem, answer):
    # Evaluate math answer if auto-check is possible
    if problem.get("expected_answer") is not None:
        if str(answer).strip() == str(problem["expected_answer"]).strip():
            total = sum(section["points"] for section in problem.get("rubric", []))
            return total, "Correct answer"
        else:
            return 0, "Incorrect answer"
    return None, "Pending manual grading"

# Function to compile and run C++ code for programming problems
def compile_and_run_cpp(problem, code_str):
    """
    Compile the given C++ code and run it against all test cases of the problem.
    Returns (score, results_list, max_time, compile_error).
    """
    # Save code to a temporary file
    username = st.session_state.get('username', 'guest')
    pid = problem["id"]
    cpp_file = f"/tmp/sub_{username}_{pid}.cpp"
    exe_file = cpp_file.replace(".cpp", ".out")
    with open(cpp_file, "w") as f:
        f.write(code_str)
    # Compile the C++ code
    comp = subprocess.run(["g++", cpp_file, "-O2", "-std=c++17", "-o", exe_file],
                          capture_output=True, text=True)
    if comp.returncode != 0:
        # Compilation failed
        compile_error = comp.stderr
        try:
            os.remove(cpp_file)
        except OSError:
            pass
        return 0, [], 0.0, compile_error
    # If compiled successfully, run through test cases
    results = []
    passed_count = 0
    max_time = 0.0
    time_limit = problem.get("time_limit", 2)
    for tc in problem.get("test_cases", []):
        inp = tc["input"]
        expected_output = tc["output"].strip().replace("\r", "")
        start_time = time.time()
        try:
            proc = subprocess.run([exe_file], input=inp, text=True, capture_output=True, timeout=time_limit)
            elapsed = time.time() - start_time
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            results.append({
                "verdict": "Time Limit Exceeded",
                "time": round(elapsed, 3),
                "expected": tc["output"] if tc.get("public") else None,
                "output": None
            })
            continue
        max_time = max(max_time, elapsed)
        output = proc.stdout.strip().replace("\r", "")
        verdict = ""
        if proc.returncode != 0:
            verdict = "Runtime Error"
        elif elapsed > time_limit:
            verdict = "Time Limit Exceeded"
        elif output != expected_output:
            verdict = "Wrong Answer"
        else:
            verdict = "Passed"
            passed_count += 1
        results.append({
            "verdict": verdict,
            "time": round(elapsed, 3),
            "expected": tc["output"] if tc.get("public") else None,
            "output": proc.stdout if tc.get("public") else None
        })
    # Compute score
    total_tests = len(problem.get("test_cases", []))
    score = int(passed_count * 100 / total_tests) if total_tests > 0 else 0
    # Cleanup temporary files
    try:
        os.remove(cpp_file)
        os.remove(exe_file)
    except OSError:
        pass
    return score, results, round(max_time, 3), None

# ---------- Function to display problem details ----------
def show_problem_detail(pid):
    prob = next((p for p in problems if p["id"] == pid), None)
    if not prob:
        st.error("Problem not found.")
        return
    st.title(prob["title"])
    # Display problem statement (support Markdown/HTML content)
    st.markdown(prob["statement"], unsafe_allow_html=True)
    if prob["type"] == "programming":
        # Show example tests (public only)
        public_tests = [tc for tc in prob.get("test_cases", []) if tc.get("public")]
        if public_tests:
            st.subheader("Example Tests")
            for tc in public_tests:
                st.markdown("**Input:**")
                st.code(tc['input'], language='text')
                st.markdown("**Expected Output:**")
                st.code(tc['output'], language='text')
        # Submission form for programming problem
        if not st.session_state.get('logged_in'):
            st.info("Log in to submit a solution.")
            return
        st.subheader("Submit Solution (C++)")
        # ACE code editor for C++ (with syntax highlighting)
        code_input = st_ace(
            value = st.session_state.get(f"code_{pid}", ""),
            language = "c_cpp",
            theme = "pastel_on_dark",
            auto_update = True,
            min_lines = 15,
            max_lines = 30,
            key = f"ace_{pid}"
        )
        if code_input is not None:
            st.session_state[f"code_{pid}"] = code_input
        if st.button("Compile & Submit", key=f"submit_cpp_{pid}"):
            if not code_input or code_input.strip() == "":
                st.error("Please enter your C++ code before submitting.")
            else:
                score, results, max_time, compile_err = compile_and_run_cpp(prob, code_input)
                if compile_err:
                    st.error(f"Compilation Error:\n{compile_err}")
                else:
                    # Record the submission
                    submission = {
                        "id": get_new_id(submissions),
                        "problem_id": pid,
                        "user": st.session_state.get('username'),
                        "code": code_input,
                        "score": score,
                        "results": results,
                        "timestamp": datetime.utcnow().isoformat(),
                        "time": max_time,
                        "language": "cpp"
                    }
                    record_submission(submission)
                    st.success(f"Score: {score}")
                    detail_expander = st.expander("Details", expanded=True)
                    for i, res in enumerate(results, start=1):
                        verdict = res['verdict']
                        t = res['time']
                        detail_expander.write(f"Test {i}: {verdict} (Time: {t}s)")
                        if verdict != "Passed" and res.get('expected') is not None:
                            detail_expander.write(f"Expected: `{res['expected']}`")
                            got_out = res.get('output', '')
                            if got_out is None:
                                got_out = ""
                            got_out_str = got_out.strip()
                            if len(got_out_str) > 300:
                                got_out_display = got_out_str[:300] + "..."
                            else:
                                got_out_display = got_out_str
                            detail_expander.write(f"Got: `{got_out_display}`")
    elif prob["type"] == "math":
        # Display rubric if available
        if prob.get("rubric"):
            st.subheader("Rubric")
            for sec in prob["rubric"]:
                st.write(f"- {sec['section']}: {sec['points']} pts")
        if not st.session_state.get('logged_in'):
            st.info("Log in to submit a solution.")
            return
        st.subheader("Submit Solution")
        answer = st.text_area("Your solution or answer:", height=150)
        if st.button("Submit Answer", key=f"submit_math_{pid}"):
            auto_score, feedback = evaluate_math_submission(prob, answer)
            graded = auto_score is not None
            score = auto_score if graded else 0
            submission = {
                "id": get_new_id(submissions),
                "problem_id": pid,
                "user": st.session_state.get('username'),
                "answer": answer,
                "score": score,
                "graded": graded,
                "timestamp": datetime.utcnow().isoformat(),
                "feedback": feedback
            }
            record_submission(submission)
            if graded:
                st.success(f"Auto-graded. Score: {score}")
            else:
                st.info("Submitted for manual review.")
        # If a graded submission exists, show the latest result
        user_subs = [s for s in submissions if s["problem_id"] == pid and s["user"] == st.session_state.get('username') and s.get("graded")]
        if user_subs:
            latest = sorted(user_subs, key=lambda s: s["timestamp"], reverse=True)[0]
            st.subheader("Graded Result")
            total_pts = sum(sec["points"] for sec in prob.get("rubric", []))
            st.write(f"Score: {latest['score']} / {total_pts}")
            if prob.get("rubric"):
                st.write("Rubric Breakdown:")
                for sec in prob["rubric"]:
                    pts_earned = sec["points"] if latest["score"] == total_pts else 0
                    st.write(f"- {sec['section']}: {pts_earned}/{sec['points']}")

# If a problem is selected, show its detail and stop other content
if st.session_state['view_problem'] is not None:
    show_problem_detail(st.session_state['view_problem'])
    st.stop()

# ---------- Session State Initialization for user auth ----------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None

if 'page' not in st.session_state:
    st.session_state.page = 'Home'

# Navigation menu in sidebar
menu_options = ["Home", "Problems", "Articles"]
if st.session_state.logged_in:
    if st.session_state.role in ("editor", "admin"):
        menu_options.append("Create Problem")
        menu_options.append("Admin Panel")
    menu_options.append("My Submissions")
    menu_options.append("Logout")
else:
    menu_options.append("Login / Register")
st.sidebar.title("MatInfo")
choice = st.sidebar.selectbox("Menu", menu_options, index=0)
if choice == "Logout":
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.rerun()
elif choice == "Login / Register":
    st.session_state.page = "Login"
elif choice == "Home":
    st.session_state.page = "Home"
elif choice == "Problems":
    st.session_state.page = "Problems"
elif choice == "Articles":
    st.session_state.page = "Articles"
elif choice == "Create Problem":
    st.session_state.page = "Create Problem"
elif choice == "Admin Panel":
    st.session_state.page = "Admin"
elif choice == "My Submissions":
    st.session_state.page = "Submissions"

# ---------- Page: Home ----------
if st.session_state.page == "Home":
    st.title("MatInfo – Educational Platform")
    st.write("Welcome to MatInfo! This platform allows students to practice programming and math problems. Please login or register to get started.")
    if articles:
        st.subheader("Latest Article")
        latest_article = sorted(articles, key=lambda x: x["date"], reverse=True)[0]
        st.write(f"**{latest_article['title']}**  \n_by {latest_article['author']}_  \n{latest_article['content'][:200]}... [Read more](#)")
    else:
        st.write("*No articles yet.*")

# ---------- Page: Login / Register ----------
if st.session_state.page == "Login":
    st.subheader("Login")
    with st.form("login_form", clear_on_submit=True):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
    if submitted:
        user = get_user_by_username(username)
        if user and check_password(password, user["password"]):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = user["role"]
            st.success(f"Welcome, {username}!")
            st.session_state.page = "Home"
            st.rerun()
        else:
            st.error("Invalid username or password")
    st.markdown("---")
    st.subheader("Register")
    with st.form("register_form", clear_on_submit=True):
        new_user = st.text_input("Choose a username")
        new_pass = st.text_input("Choose a password", type="password")
        submitted_reg = st.form_submit_button("Register")
    if submitted_reg:
        if get_user_by_username(new_user):
            st.error("Username already exists. Choose another.")
        elif new_user == "" or new_pass == "":
            st.error("Username/password cannot be empty.")
        else:
            new_entry = {
                "id": get_new_id(users),
                "username": new_user,
                "password": hash_password(new_pass),
                "role": "elev"  # 'elev' = student
            }
            users.append(new_entry)
            save_json("users.json", users)
            st.success("Registration successful! You can now login.")

# ---------- Page: Problems (List) ----------
if st.session_state.page == "Problems":
    st.title("Problems")
    info_probs = [p for p in problems if p["type"] == "programming"]
    math_probs = [p for p in problems if p["type"] == "math"]
    if info_probs:
        st.subheader("Informatics Problems")
        for p in info_probs:
            best_score = None
            if st.session_state.logged_in:
                subs = [s for s in submissions if s["problem_id"] == p["id"] and s["user"] == st.session_state.username]
                if subs:
                    best_score = max(s["score"] for s in subs)
            line = f"**{p['title']}**"
            if best_score is not None:
                line += f" – *Your best score: {best_score}*"
            st.markdown(line)
            if st.button(f"Open {p['title']}", key=f"open_prob_{p['id']}"):
                st.session_state.view_problem = p["id"]
                st.rerun()
    if math_probs:
        st.subheader("Math Problems")
        for p in math_probs:
            status = None
            if st.session_state.logged_in:
                subs = [s for s in submissions if s["problem_id"] == p["id"] and s["user"] == st.session_state.username]
                if subs:
                    last_sub = sorted(subs, key=lambda s: s["timestamp"], reverse=True)[0]
                    if last_sub.get("graded"):
                        total_pts = sum(sec['points'] for sec in p.get("rubric", []))
                        status = f"Graded: {last_sub['score']}/{total_pts}"
                    else:
                        status = "Pending grading"
            line = f"**{p['title']}**"
            if status:
                line += f" – *{status}*"
            st.markdown(line)
            if st.button(f"Open {p['title']}", key=f"open_prob_{p['id']}"):
                st.session_state.view_problem = p["id"]
                st.rerun()
    if not problems:
        st.write("No problems available yet.")

# (The selected problem detail view is handled above by show_problem_detail)

# ---------- Page: Create Problem ----------
if st.session_state.page == "Create Problem":
    if not st.session_state.logged_in or st.session_state.role not in ("editor", "admin"):
        st.error("Access denied. Editors or admins only.")
    else:
        st.title("Create New Problem")
        problem_type = st.selectbox("Problem Type", ["programming", "math"])
        title = st.text_input("Problem Title")
        statement = st.text_area("Problem Statement (Markdown/LaTeX supported)")
        if problem_type == "programming":
            time_limit = st.number_input("Time limit (seconds)", value=2.0)
            memory_limit = st.number_input("Memory limit (MB)", value=256)
            st.subheader("Test Cases")
            if 'new_testcases' not in st.session_state:
                st.session_state.new_testcases = []
            new_in = st.text_area("Input for new test case")
            new_out = st.text_area("Expected output for new test case")
            public_flag = st.checkbox("Public test (visible to users)", value=False)
            if st.button("Add Test Case"):
                if new_in.strip() == "" or new_out.strip() == "":
                    st.warning("Please provide both input and output for the test case.")
                else:
                    st.session_state.new_testcases.append({"input": new_in, "output": new_out, "public": public_flag})
                    st.rerun()
            if st.session_state.new_testcases:
                st.write("Current test cases:")
                for i, tc in enumerate(st.session_state.new_testcases, start=1):
                    vis = "Public" if tc["public"] else "Private"
                    st.write(f"{i}. ({vis}) Input: `{tc['input'][:30]}...`, Output: `{tc['output'][:30]}...`")
            if st.button("Create Problem"):
                if title.strip() == "" or statement.strip() == "" or not st.session_state.new_testcases:
                    st.error("Title, statement, and at least one test case are required.")
                else:
                    new_prob = {
                        "id": get_new_id(problems),
                        "type": "programming",
                        "title": title,
                        "statement": statement,
                        "author": st.session_state.username,
                        "time_limit": time_limit,
                        "memory_limit": memory_limit,
                        "test_cases": st.session_state.new_testcases
                    }
                    problems.append(new_prob)
                    save_json("problems.json", problems)
                    st.success("Programming problem created successfully!")
                    st.session_state.new_testcases = []
        else:  # math problem
            st.subheader("Rubric")
            if 'new_rubric' not in st.session_state:
                st.session_state.new_rubric = []
            rub_section = st.text_input("Rubric section description")
            rub_points = st.number_input("Points for this section", min_value=0, value=0)
            if st.button("Add Section"):
                if rub_section.strip() == "":
                    st.warning("Section description cannot be empty.")
                else:
                    st.session_state.new_rubric.append({"section": rub_section, "points": int(rub_points)})
                    st.rerun()
            if st.session_state.new_rubric:
                st.write("Current rubric:")
                for sec in st.session_state.new_rubric:
                    st.write(f"- {sec['section']}: {sec['points']} points")
            expected_answer = st.text_input("Expected answer (if auto-gradable)")
            if st.button("Create Problem"):
                if title.strip() == "" or statement.strip() == "":
                    st.error("Title and statement are required.")
                else:
                    new_prob = {
                        "id": get_new_id(problems),
                        "type": "math",
                        "title": title,
                        "statement": statement,
                        "author": st.session_state.username,
                        "rubric": st.session_state.new_rubric,
                        "expected_answer": expected_answer.strip() if expected_answer.strip() != "" else None
                    }
                    problems.append(new_prob)
                    save_json("problems.json", problems)
                    st.success("Math problem created successfully!")
                    st.session_state.new_rubric = []

# ---------- Page: Articles ----------
if st.session_state.page == "Articles":
    st.title("Articles")
    if not articles:
        st.write("No articles yet.")
    else:
        for art in sorted(articles, key=lambda x: x["date"], reverse=True):
            st.subheader(art["title"])
            st.write(f"*by {art['author']} on {art['date'][:10]}*")
            st.write(art["content"], unsafe_allow_html=True)
            st.write(f"Votes: **{art.get('votes', 0)}**")
            if st.session_state.logged_in:
                user = st.session_state.username
                voted_up = user in art.get("upvoters", [])
                voted_down = user in art.get("downvoters", [])
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("👍 Like", key=f"like_{art['id']}", disabled=voted_up):
                        art.setdefault("upvoters", []).append(user)
                        if user in art.get("downvoters", []):
                            art["downvoters"].remove(user)
                        art["votes"] = art.get("votes", 0) + 1
                        save_json("articles.json", articles)
                        st.rerun()
                with col2:
                    if st.button("👎 Dislike", key=f"dislike_{art['id']}", disabled=voted_down):
                        art.setdefault("downvoters", []).append(user)
                        if user in art.get("upvoters", []):
                            art["upvoters"].remove(user)
                        art["votes"] = art.get("votes", 0) - 1
                        save_json("articles.json", articles)
                        st.rerun()
            # Comments section
            art_comments = [c for c in comments if c["article_id"] == art["id"]]
            for c in art_comments:
                st.write(f"**{c['author']}**: {c['content']}  (_{c['date'][:19]}_)")
            if st.session_state.logged_in:
                comment_text = st.text_input(f"Add a comment to '{art['title']}':", key=f"comment_{art['id']}")
                if st.button("Post", key=f"post_comment_{art['id']}"):
                    if comment_text.strip() == "":
                        st.warning("Comment cannot be empty.")
                    else:
                        new_comment = {
                            "id": get_new_id(comments),
                            "article_id": art["id"],
                            "author": st.session_state.username,
                            "content": comment_text,
                            "date": datetime.utcnow().isoformat()
                        }
                        comments.append(new_comment)
                        save_json("comments.json", comments)
                        st.rerun()
            st.markdown("---")
    # Option for editors/admins to add a new article
    if st.session_state.logged_in and st.session_state.role in ("editor", "admin"):
        st.subheader("Write a new article")
        art_title = st.text_input("Article Title")
        art_content = st.text_area("Content (Markdown supported)")
        if st.button("Publish Article"):
            if art_title.strip() == "" or art_content.strip() == "":
                st.warning("Title and content cannot be empty.")
            else:
                new_article = {
                    "id": get_new_id(articles),
                    "title": art_title,
                    "content": art_content,
                    "author": st.session_state.username,
                    "date": datetime.utcnow().isoformat(),
                    "votes": 0,
                    "upvoters": [],
                    "downvoters": []
                }
                articles.append(new_article)
                save_json("articles.json", articles)
                st.success("Article published!")
                st.rerun()

# ---------- Page: My Submissions ----------
if st.session_state.page == "Submissions":
    if not st.session_state.logged_in:
        st.error("Please log in to view your submissions.")
    else:
        st.title("My Submissions")
        user_subs = [s for s in submissions if s["user"] == st.session_state.username]
        if not user_subs:
            st.write("No submissions yet.")
        else:
            user_subs.sort(key=lambda s: s["timestamp"], reverse=True)
            for sub in user_subs:
                prob = next((p for p in problems if p["id"] == sub["problem_id"]), None) or {}
                prob_title = prob.get("title", "[Deleted Problem]")
                st.write(f"**Problem:** {prob_title}")
                st.write(f"**Date:** {sub['timestamp'][:19]}")
                st.write(f"**Score:** {sub['score']}")
                if prob.get("type") == "programming":
                    st.write(f"**Language:** {sub.get('language', 'cpp')}")
                    st.write(f"**Time:** {sub.get('time', '?')}s")
                    if "results" in sub:
                        failed_tests = [r for r in sub["results"] if r["verdict"] != "Passed"]
                        if failed_tests:
                            st.write("Details of failed tests:")
                            for r in failed_tests:
                                st.write(f"- {r['verdict']}")
                elif prob.get("type") == "math":
                    if sub.get("graded"):
                        st.write("Graded ✅")
                        if sub.get("feedback"):
                            st.write(f"Feedback: {sub['feedback']}")
                    else:
                        st.write("Not graded yet ⏳")
                st.markdown("---")

# ---------- Page: Admin Panel ----------
if st.session_state.page == "Admin":
    if not st.session_state.logged_in or st.session_state.role not in ("editor", "admin"):
        st.error("Access denied.")
    else:
        st.title("Admin Panel")
        tab_labels = []
        if st.session_state.role == "admin":
            tab_labels.append("Users")
        tab_labels.extend(["Problems", "Submissions", "Articles"])
        tabs = st.tabs(tab_labels)
        tab_index = 0
        # Users tab (admins only)
        if st.session_state.role == "admin":
            with tabs[0]:
                st.subheader("User Management")
                for u in users:
                    col1, col2, col3 = st.columns([3, 2, 1])
                    col1.write(u['username'])
                    col2.write(f"Role: {u['role']}")
                    if u['username'] != 'admin':
                        new_role = col2.selectbox("Change role",
                                                  ["elev", "editor", "admin"],
                                                  index=["elev", "editor", "admin"].index(u['role']),
                                                  key=f"role_select_{u['id']}")
                        if new_role != u['role']:
                            u['role'] = new_role
                    if u['username'] != 'admin':
                        if col3.button("Delete", key=f"del_user_{u['id']}"):
                            users.remove(u)
                if st.button("Save User Changes"):
                    save_json("users.json", users)
                    st.success("User changes saved.")
            tab_index = 1
        # Problems tab
        with tabs[tab_index]:
            st.subheader("Problem Management")
            for p in problems:
                col1, col2, col3 = st.columns([4, 3, 1])
                col1.write(f"{p['title']} ({p['type']})")
                col2.write(f"Author: {p.get('author', '-')}")
                if col3.button("Delete", key=f"del_prob_{p['id']}"):
                    problems.remove(p)
                    submissions[:] = [s for s in submissions if s['problem_id'] != p['id']]
            if st.button("Save Problem Changes"):
                save_json("problems.json", problems)
                save_json("submissions.json", submissions)
                st.success("Problem changes saved.")
        # Submissions tab (manual grading for math problems)
        with tabs[tab_index+1]:
            st.subheader("Pending Math Submissions")
            pending = [s for s in submissions if not s.get('graded') and next((p for p in problems if p['id']==s['problem_id']), {}).get('type') == 'math']
            if not pending:
                st.write("No pending submissions for grading.")
            else:
                for s in pending:
                    prob = next((p for p in problems if p['id'] == s['problem_id']), {"title": "Unknown"})
                    st.write(f"**{prob['title']}** – {s['user']} (submitted {s['timestamp'][:19]})")
                    st.write("Solution:")
                    st.code(s.get('answer', ''), language='text')
                    # Show rubric sections for grading
                    if prob.get('rubric'):
                        points_awarded = {}
                        for sec in prob['rubric']:
                            points_awarded[sec['section']] = st.number_input(
                                f"{sec['section']} ({sec['points']} pts)",
                                min_value=0, max_value=sec['points'],
                                key=f"grade_{sec['section']}_{s['id']}"
                            )
                    if st.button(f"Grade Submission {s['id']}"):
                        total_points = 0
                        if prob.get('rubric'):
                            for sec in prob['rubric']:
                                total_points += points_awarded.get(sec['section'], 0)
                        s['score'] = total_points
                        s['graded'] = True
                        s['feedback'] = "Graded by editor"
                        save_json("submissions.json", submissions)
                        st.success(f"Submission {s['id']} graded with {total_points} points.")
                        st.rerun()
        # Articles tab
        with tabs[tab_index+2]:
            st.subheader("Manage Articles")
            for art in articles:
                col1, col2 = st.columns([8, 1])
                col1.write(f"{art['title']} (by {art['author']})")
                if col2.button("Delete", key=f"del_art_{art['id']}"):
                    articles.remove(art)
                    comments[:] = [c for c in comments if c['article_id'] != art['id']]
            if st.button("Save Article Changes"):
                save_json("articles.json", articles)
                save_json("comments.json", comments)
                st.success("Article changes saved.")
