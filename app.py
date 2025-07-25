import streamlit as st
import json, os, hashlib, time
from datetime import datetime
from contextlib import redirect_stdout
import io

# ---------- Configuration: Page setup and theming ----------
st.set_page_config(page_title="MatInfo Platform", layout="wide")
# Dark theme via custom CSS (since we want a specific look)
dark_css = """
<style>
body, .stApp {
    background-color: #1e1e1e;
    color: #e0e0e0;
}
/* Style sidebar */
.stSidebar, .css-6awftf.egzxvld2 { /* the second class targets sidebar content */
    background-color: #2b2b2b;
}
/* Style primary colored elements (like buttons, selectboxes) */
.css-1fv8s86 {
    background-color: #264F78 !important; /* a dark blue tone for buttons */
    color: #FFFFFF !important;
}
</style>
"""
st.markdown(dark_css, unsafe_allow_html=True)

# ---------- Utility functions for data persistence ----------
DATA_DIR = "."  # current directory
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

# 1. Asigură‑te că există cheia în session_state
if 'view_problem' not in st.session_state:
    st.session_state['view_problem'] = None

# 2. Definiția funcției care afișează detaliile problemei
def show_problem_detail(pid):
    prob = next((p for p in problems if p["id"] == pid), None)
    if not prob:
        st.error("Problem not found.")
        return

    st.title(prob["title"])
    st.markdown(prob["statement"], unsafe_allow_html=True)

    # --- logica ta de submit/evaluate pentru programming sau math ---
    if prob["type"] == "programming":
        # exemplu de test public
        public_tests = [tc for tc in prob.get("test_cases",[]) if tc.get("public")]
        if public_tests:
            st.subheader("Example Tests")
            for tc in public_tests:
                st.text(f"Input:\n{tc['input']}")
                st.text(f"Expected:\n{tc['output']}")

        st.subheader("Submit Solution")
        code_input = st.text_area("Your Python code:", height=200)
        if st.button("Run & Submit", key=f"submit_prog_{pid}"):
            score, results, max_time = evaluate_program_submission(prob, code_input)
            submission = {
                "id": get_new_id(submissions),
                "problem_id": pid,
                "user": st.session_state.username,
                "code": code_input,
                "score": score,
                "results": results,
                "timestamp": datetime.utcnow().isoformat(),
                "time": round(max_time, 3),
                "language": "python"
            }
            record_submission(submission)
            st.success(f"Score: {score}")
            exp = st.expander("Details", expanded=True)
            for i, r in enumerate(results, 1):
                exp.write(f"Test {i}: {r['verdict']} (time: {r['time']}s)")
                if r["verdict"] != "Passed" and r.get("expected") is not None:
                    exp.write(f"Expected: `{r['expected']}`\nGot: `{r['output'].strip()}`")

    elif prob["type"] == "math":
        if prob.get("rubric"):
            st.subheader("Rubric")
            for sec in prob["rubric"]:
                st.write(f"- {sec['section']}: {sec['points']} pts")

        if not st.session_state.logged_in:
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
                "user": st.session_state.username,
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

        user_subs = [s for s in submissions if s["problem_id"]==pid and s["user"]==st.session_state.username and s.get("graded")]
        if user_subs:
            latest = sorted(user_subs, key=lambda s: s["timestamp"], reverse=True)[0]
            st.subheader("Graded Result")
            total_pts = sum(sec["points"] for sec in prob.get("rubric", []))
            st.write(f"Score: {latest['score']} / {total_pts}")
            if prob.get("rubric"):
                st.write("Rubric Breakdown:")
                for sec in prob["rubric"]:
                    pts = sec["points"] if latest["score"]==total_pts else 0
                    st.write(f"- {sec['section']}: {pts}/{sec['points']}")

# 3. Verifică și intră direct în «View Problem» și oprește restul
if st.session_state['view_problem'] is not None:
    show_problem_detail(st.session_state['view_problem'])
    st.stop()


# ---------- Helper functions for app logic ----------
def hash_password(password: str) -> str:
    """Hash a password for storage."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def check_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def get_new_id(list_of_dicts):
    """Generate a new ID (int) for an item in a list of dicts with 'id' field."""
    if not list_of_dicts:
        return 1
    else:
        max_id = max(item.get("id", 0) for item in list_of_dicts)
        return max_id + 1

def ensure_admin_exists():
    """Ensure there's at least one admin user. Create a default admin if none exist."""
    admin_exists = any(u['role'] == 'admin' for u in users)
    if not admin_exists:
        default_admin = {"id": get_new_id(users), "username": "admin", "password": hash_password("admin"), "role": "admin"}
        users.append(default_admin)
        save_json("users.json", users)
ensure_admin_exists()  # Create default admin if needed

def record_submission(submission):
    submissions.append(submission)
    save_json("submissions.json", submissions)

def get_user_by_username(username):
    return next((u for u in users if u["username"] == username), None)

# Functions to run and evaluate code
def run_code_in_sandbox(code, input_data):
    """Run user code with given input_data (list of input lines). Return output and success flag."""
    output_buffer = io.StringIO()
    # Prepare a restricted execution environment
    # Disable builtins for safety except a few
    allowed_builtins = {"__build_class__": __build_class__, "__name__": "__main__"}  # minimally required to exec
    # We allow basic builtins usage by adding safe ones:
    safe_funcs = {"range": range, "len": len, "print": print}
    allowed_builtins.update(safe_funcs)
    # Monkey patch input() if needed:
    input_iter = iter(input_data)
    def safe_input(prompt=""):
        try:
            return next(input_iter)
        except StopIteration:
            return ""
    allowed_builtins["input"] = safe_input
    # Execute the code
    success = True
    error_msg = ""
    start_time = time.time()
    try:
        with redirect_stdout(output_buffer):
            exec(code, {"__builtins__": allowed_builtins}, {})
    except Exception as e:
        success = False
        error_msg = str(e)
    exec_time = time.time() - start_time
    output = output_buffer.getvalue()
    if error_msg:
        output += ("\nError: " + error_msg)
    return output, exec_time, success

def evaluate_program_submission(problem, code):
    """Run the user's code on all test cases of the given programming problem."""
    test_results = []
    all_passed = True
    total_time = 0.0
    for case in problem["test_cases"]:
        # Run on each test case input; assume input_data is list of lines (split by newline)
        input_data = case["input"].splitlines(keepends=True)
        output, exec_time, success = run_code_in_sandbox(code, input_data)
        total_time = max(total_time, exec_time)  # track max time used
        expected = case["output"].strip()
        got = output.strip()
        if not success:
            verdict = "Runtime Error"
            all_passed = False
        elif exec_time > problem.get("time_limit", 2):  # default 2s if not set
            verdict = "Time Limit Exceeded"
            all_passed = False
        elif got == expected:
            verdict = "Passed"
        else:
            verdict = "Wrong Answer"
            all_passed = False
        test_results.append({
            "input": case["input"] if case.get("public") else None,  # don't store private input
            "expected": case["output"] if case.get("public") else None,
            "output": output,
            "verdict": verdict,
            "time": round(exec_time, 3)
        })
    # Calculate score (if all passed, 100; else proportional to passed tests)
    passed_tests = sum(1 for r in test_results if r["verdict"] == "Passed")
    total_tests = len(test_results)
    score = int(passed_tests * 100 / total_tests)
    return score, test_results, total_time

def evaluate_math_submission(problem, answer):
    """Evaluate math answer if auto-check possible. Returns score and feedback."""
    if problem.get("expected_answer") is not None:
        # Simple check: compare stripped answer strings
        if str(answer).strip() == str(problem["expected_answer"]).strip():
            # Give full points for whatever rubric section corresponds to correct answer
            total = sum(section["points"] for section in problem.get("rubric", []))
            return total, "Correct answer"
        else:
            return 0, "Incorrect answer"
    # If no auto evaluation, return None indicating needs manual grading
    return None, "Pending manual grading"

# ---------- Session State Initialization ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None

if "page" not in st.session_state:
    st.session_state.page = "Home"

# Navigation menu in sidebar
menu_options = ["Home", "Problems", "Articles"]
if st.session_state.logged_in:
    if st.session_state.role in ("editor", "admin"):
        menu_options.append("Create Problem")
    if st.session_state.role in ("editor", "admin"):
        menu_options.append("Admin Panel")
    menu_options.append("My Submissions")
    menu_options.append("Logout")
else:
    menu_options.append("Login / Register")

st.sidebar.title("MatInfo")
choice = st.sidebar.selectbox("Menu", menu_options, index=0)
# Handle menu choice logic:
if choice == "Logout":
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.rerun()  # refresh to show logged-out menu (we use rerun on logout for immediate effect)
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
    st.write("Welcome to MatInfo! This platform allows students to practice informatics (programming) and math problems. Please login or register to get started.")
    # Basic info or announcements
    if articles:
        st.subheader("Latest Article")
        latest_article = sorted(articles, key=lambda x: x["date"], reverse=True)[0]
        st.write(f"**{latest_article['title']}**  \n_by {latest_article['author']}_  \n{latest_article['content'][:200]}... [Read more](#)")  # truncated preview
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
            new_entry = {"id": get_new_id(users), "username": new_user, "password": hash_password(new_pass), "role": "elev"}  # elev = student
            users.append(new_entry)
            save_json("users.json", users)
            st.success("Registration successful! You can now login.")

# ---------- Page: Problems (List & Detail) ----------
if st.session_state.page == "Problems":
    st.title("Problems")
    # Show list of problems grouped by type
    info_probs = [p for p in problems if p["type"] == "programming"]
    math_probs = [p for p in problems if p["type"] == "math"]
    if info_probs:
        st.subheader("Informatics Problems")
        for p in info_probs:
            score = None
            if st.session_state.logged_in:
                # show user's score if any submission
                subs = [s for s in submissions if s["problem_id"] == p["id"] and s["user"] == st.session_state.username]
                if subs:
                    score = max(s["score"] for s in subs)
            problem_line = f"**{p['title']}**"
            if score is not None:
                problem_line += f" – *Your best score: {score}*"
            st.markdown(problem_line)
            if st.button(f"Open {p['title']}", key=f"open{p['id']}"):
                st.session_state.view_problem = p["id"]
                on_click=lambda pid=p['id']: st.session_state.update({"view_problem": pid})
    if math_probs:
        st.subheader("Math Problems")
        for p in math_probs:
            status = None
            if st.session_state.logged_in:
                subs = [s for s in submissions if s["problem_id"] == p["id"] and s["user"] == st.session_state.username]
                if subs:
                    last_sub = sorted(subs, key=lambda s: s["timestamp"], reverse=True)[0]
                    status = "Graded: " + str(last_sub["score"]) + "/" + str(sum(sec['points'] for sec in p.get("rubric", []))) if last_sub.get("graded") else "Pending grading"
            problem_line = f"**{p['title']}**"
            if status:
                problem_line += f" – *{status}*"
            st.markdown(problem_line)
            if st.button(f"Open {p['title']}", key=f"open{p['id']}"):
                st.session_state.view_problem = p["id"]
                on_click=lambda pid=p['id']: st.session_state.update({"view_problem": pid})
    if not problems:
        st.write("No problems available yet.")

# View a specific problem (either programming or math)
if st.session_state.page == "View Problem":
    # Find the problem by id
    prob_id = st.session_state.view_problem
    problem = next((p for p in problems if p["id"] == prob_id), None)
    if not problem:
        st.error("Problem not found.")
    else:
        st.title(problem["title"])
        # Display statement (render LaTeX if present)
        st.write(problem["statement"], unsafe_allow_html=True)
        if problem["type"] == "programming":
            # If any public test cases, show them as examples
            public_tests = [tc for tc in problem.get("test_cases", []) if tc.get("public")]
            if public_tests:
                st.subheader("Example Tests")
                for tc in public_tests:
                    st.text(f"Input:\n{tc['input']}")
                    st.text(f"Expected Output:\n{tc['output']}")
            # Code submission form
            if not st.session_state.logged_in:
                st.info("Log in to submit a solution.")
            else:
                st.subheader("Submit Solution")
                code_input = st.text_area("Your Python code:", height=200)
                if st.button("Run & Submit"):
                    # Evaluate the code
                    score, results, max_time = evaluate_program_submission(problem, code_input)
                    # Record submission
                    submission = {
                        "id": get_new_id(submissions),
                        "problem_id": problem["id"],
                        "user": st.session_state.username,
                        "code": code_input,
                        "score": score,
                        "results": results,
                        "timestamp": datetime.utcnow().isoformat(),
                        "time": round(max_time, 3),
                        "language": "python"
                    }
                    record_submission(submission)
                    # Display results
                    st.success(f"Submission evaluated. Score: **{score}**")
                    exp = st.expander("Details", expanded=True)
                    for idx, res in enumerate(results, start=1):
                        verdict = res["verdict"]
                        t = res["time"]
                        exp.write(f"**Test {idx}:** {verdict} (Time: {t}s)")
                        if res["verdict"] != "Passed":
                            # If it's a public test or user code failed, show expected vs got for debugging
                            if res.get("expected") is not None:
                                exp.write(f"Expected: `{res['expected']}`")
                                exp.write(f"Got: `{res['output'].strip()}`")
        elif problem["type"] == "math":
            # Show rubric breakdown (without points filled) as info to user
            if "rubric" in problem:
                st.subheader("Rubric")
                for sec in problem["rubric"]:
                    st.write(f"- {sec['section']}: **{sec['points']}** points")
            # Solution submission
            if not st.session_state.logged_in:
                st.info("Log in to submit a solution.")
            else:
                st.subheader("Submit Solution")
                answer = st.text_area("Your solution or answer (you can use LaTeX for formulas):", height=150)
                if st.button("Submit Answer"):
                    # Create submission entry
                    score = 0
                    graded = False
                    feedback = ""
                    if problem.get("expected_answer") is not None:
                        auto_score, feedback = evaluate_math_submission(problem, answer)
                        if auto_score is not None:
                            score = auto_score
                            graded = True  # auto graded
                    submission = {
                        "id": get_new_id(submissions),
                        "problem_id": problem["id"],
                        "user": st.session_state.username,
                        "answer": answer,
                        "score": score,
                        "graded": graded,
                        "timestamp": datetime.utcnow().isoformat(),
                        "feedback": feedback
                    }
                    record_submission(submission)
                    if graded:
                        st.success(f"Your answer was auto-graded. Score: {score}")
                    else:
                        st.info("Your solution has been submitted for review. It will be graded by an editor.")
                # If the user has a graded submission, allow them to view the graded rubric
                user_subs = [s for s in submissions if s["problem_id"] == problem["id"] and s["user"] == st.session_state.username and s.get("graded")]
                if user_subs:
                    latest = sorted(user_subs, key=lambda s: s["timestamp"], reverse=True)[0]
                    if latest.get("graded"):
                        st.subheader("Graded Result")
                        st.write(f"**Score:** {latest['score']} out of {sum(sec['points'] for sec in problem.get('rubric', []))}")
                        if problem.get("rubric"):
                            st.write("**Rubric Breakdown:**")
                            # If we had stored per-section points, we would display them. For simplicity, assume full or zero for auto.
                            for sec in problem["rubric"]:
                                # If we had detailed grading info, we'd use it. Here we infer if full score given for correct answer.
                                pts_earned = sec["points"] if latest["score"] == sum(sec['points'] for sec in problem["rubric"]) else 0
                                st.write(f"- {sec['section']}: {pts_earned} / {sec['points']}")

# ---------- Page: Create Problem (Editors only) ----------
if st.session_state.page == "Create Problem":
    if not st.session_state.logged_in or st.session_state.role not in ("editor", "admin"):
        st.error("Access denied. Editors or admins only.")
    else:
        st.title("Create New Problem")
        problem_type = st.selectbox("Problem Type", ["programming", "math"])
        title = st.text_input("Problem Title")
        statement = st.text_area("Problem Statement (you can use Markdown/LaTeX)")
        if problem_type == "programming":
            time_limit = st.number_input("Time limit (seconds)", value=2.0)
            memory_limit = st.number_input("Memory limit (MB)", value=256)
            # Enter test cases:
            st.subheader("Test Cases")
            # We allow adding multiple testcases dynamically
            if "new_testcases" not in st.session_state:
                st.session_state.new_testcases = []
            # Interface to add a new test
            new_in = st.text_area("Input for a new test case")
            new_out = st.text_area("Expected output for the new test case")
            public_flag = st.checkbox("This test is public (visible to users)", value=False)
            if st.button("Add Test Case"):
                if new_in and new_out:
                    st.session_state.new_testcases.append({"input": new_in, "output": new_out, "public": public_flag})
                    # Clear fields
                    st.rerun()
                else:
                    st.warning("Please provide both input and output for the test case.")
            # Display current test cases list
            if st.session_state.new_testcases:
                st.write("Current test cases:")
                for i, tc in enumerate(st.session_state.new_testcases, start=1):
                    vis = "Public" if tc["public"] else "Private"
                    st.write(f"{i}. ({vis}) Input: `{tc['input'][:30]}...`, Output: `{tc['output'][:30]}...`")
            submitted = st.button("Create Problem")
            if submitted:
                if title == "" or statement == "" or not st.session_state.new_testcases:
                    st.error("Title, statement, and at least one test case are required.")
                else:
                    prob = {
                        "id": get_new_id(problems),
                        "type": "programming",
                        "title": title,
                        "statement": statement,
                        "author": st.session_state.username,
                        "time_limit": time_limit,
                        "memory_limit": memory_limit,
                        "test_cases": st.session_state.new_testcases
                    }
                    problems.append(prob)
                    save_json("problems.json", problems)
                    st.success("Programming problem created successfully!")
                    # Reset the form state
                    st.session_state.new_testcases = []
        else:  # math problem
            # Rubric creation
            st.subheader("Rubric")
            if "new_rubric" not in st.session_state:
                st.session_state.new_rubric = []
            rub_section = st.text_input("Rubric section description")
            rub_points = st.number_input("Points for this section", min_value=0, value=0)
            if st.button("Add Section"):
                if rub_section and rub_points:
                    st.session_state.new_rubric.append({"section": rub_section, "points": int(rub_points)})
                    st.rerun()
                else:
                    st.warning("Please specify both section description and points.")
            if st.session_state.new_rubric:
                st.write("Current rubric:")
                for sec in st.session_state.new_rubric:
                    st.write(f"- {sec['section']}: {sec['points']} points")
            expected_answer = st.text_input("Expected answer (leave blank if manual evaluation only)")
            submitted = st.button("Create Problem")
            if submitted:
                if title == "" or statement == "":
                    st.error("Title and statement are required.")
                else:
                    prob = {
                        "id": get_new_id(problems),
                        "type": "math",
                        "title": title,
                        "statement": statement,
                        "author": st.session_state.username,
                        "rubric": st.session_state.new_rubric,
                        "expected_answer": expected_answer if expected_answer else None
                    }
                    problems.append(prob)
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
                # Voting buttons
                user = st.session_state.username
                voted_up = user in art.get("upvoters", [])
                voted_down = user in art.get("downvoters", [])
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("👍 Like", key=f"like{art['id']}", disabled=voted_up):
                        art.setdefault("upvoters", []).append(user)
                        art.setdefault("downvoters", [])
                        if user in art["downvoters"]:
                            art["downvoters"].remove(user)
                        art["votes"] = art.get("votes", 0) + 1
                        save_json("articles.json", articles)
                        st.rerun()
                with col2:
                    if st.button("👎 Dislike", key=f"dis{art['id']}", disabled=voted_down):
                        art.setdefault("downvoters", []).append(user)
                        art.setdefault("upvoters", [])
                        if user in art["upvoters"]:
                            art["upvoters"].remove(user)
                        art["votes"] = art.get("votes", 0) - 1
                        save_json("articles.json", articles)
                        st.rerun()
            # Comments section
            art_comments = [c for c in comments if c["article_id"] == art["id"]]
            for c in art_comments:
                st.write(f"**{c['author']}**: {c['content']}  (_{c['date'][:19]}_)")
            if st.session_state.logged_in:
                comment_text = st.text_input(f"Add a comment to {art['id']}:", key=f"comment{art['id']}")
                if st.button("Post", key=f"post{art['id']}"):
                    if comment_text:
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
                    else:
                        st.warning("Comment cannot be empty.")
            st.markdown("---")

    # Option for editors to add a new article
    if st.session_state.logged_in and st.session_state.role in ("editor", "admin"):
        st.subheader("Write a new article")
        title = st.text_input("Article Title")
        content = st.text_area("Content (Markdown supported)")
        if st.button("Publish"):
            if title and content:
                new_article = {
                    "id": get_new_id(articles),
                    "title": title,
                    "content": content,
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
            else:
                st.warning("Title and content cannot be empty.")

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
            # Sort by date
            user_subs.sort(key=lambda s: s["timestamp"], reverse=True)
            for sub in user_subs:
                prob = next((p for p in problems if p["id"] == sub["problem_id"]), {})
                prob_title = prob.get("title", "[Deleted Problem]")
                st.write(f"**Problem:** {prob_title}  \n**Date:** {sub['timestamp'][:19]}  \n**Score:** {sub['score']}")
                if prob.get("type") == "programming":
                    st.write(f"**Language:** {sub.get('language', 'python')}  \n**Time:** {sub.get('time', '?')}s")
                    # Show verdicts of tests if not all passed
                    if "results" in sub:
                        failed = [r for r in sub["results"] if r["verdict"] != "Passed"]
                        if failed:
                            st.write("Some tests failed:")
                            for r in failed:
                                st.write(f"- {r['verdict']} (expected vs got may differ)")
                else:
                    # Math submission
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
        tabs = []
        if st.session_state.role == "admin":
            tabs.append("Users")
        tabs.append("Problems")
        tabs.append("Submissions")
        tabs.append("Articles")
        selected_tab = st.tabs(tabs)  # in new Streamlit, st.tabs returns a list of tab contexts
        # We will use if/else since st.tabs doesn't directly return a value in newer versions:
        # (Alternatively, use radio for internal nav if needed)
        # Handle Users tab
        if st.session_state.role == "admin":
            with selected_tab[0]:
                st.subheader("User Management")
                for u in users:
                    col1, col2, col3 = st.columns([3,2,2])
                    col1.write(f"{u['username']}")
                    col2.write(f"Role: {u['role']}")
                    if u["username"] != "admin":
                        new_role = col2.selectbox("Change role", ["elev","editor","admin"], index=["elev","editor","admin"].index(u["role"]), key=f"role{u['id']}")
                        if new_role != u["role"]:
                            u["role"] = new_role
                    if col3.button("Delete", key=f"del{u['id']}"):
                        users.remove(u)
                if st.button("Save Changes to Users"):
                    save_json("users.json", users)
                    st.success("User changes saved.")
        # Problems tab (for editor and admin, index differs based on role)
        with selected_tab[0 if st.session_state.role != "admin" else 1]:
            st.subheader("Problem Management")
            for p in problems:
                col1, col2, col3 = st.columns([3,2,2])
                col1.write(f"{p['title']} ({p['type']})")
                col2.write(f"Author: {p.get('author', '-')}")
                if col3.button("Delete", key=f"delprob{p['id']}"):
                    problems.remove(p)
                    # also remove related submissions
                    submissions_to_remove = [s for s in submissions if s["problem_id"] == p["id"]]
                    for s in submissions_to_remove:
                        submissions.remove(s)
                    # Note: could also remove comments if problem had any (not applicable here)
            if st.button("Save Problem Changes"):
                save_json("problems.json", problems)
                save_json("submissions.json", submissions)
                st.success("Problems updated.")
        # Submissions tab
        with selected_tab[1 if st.session_state.role != "admin" else 2]:
            st.subheader("Pending Math Submissions")
            pending = [s for s in submissions if not s.get("graded") and next((p for p in problems if p["id"]==s["problem_id"]), {}).get("type") == "math"]
            if not pending:
                st.write("No pending manual gradings.")
            else:
                for s in pending:
                    prob = next((p for p in problems if p["id"] == s["problem_id"]), {"title":"Unknown"})
                    st.write(f"**{prob['title']}** by {s['user']} (submitted {s['timestamp'][:19]})")
                    st.write("Solution:", s["answer"])
                    # Show rubric and inputs for points
                    prob_rubric = prob.get("rubric", [])
                    points_awarded = {}
                    for sec in prob_rubric:
                        points_awarded[sec["section"]] = st.number_input(f"{sec['section']} ({sec['points']} pts)", min_value=0, max_value=sec["points"], key=f"grade{sec['section']}{s['id']}")
                    if st.button(f"Grade Submission {s['id']}", key=f"gradebtn{s['id']}"):
                        # Sum up points and mark graded
                        total_points = sum(points_awarded.values())
                        s["score"] = total_points
                        s["graded"] = True
                        s["feedback"] = "Graded by editor"
                        # (We could store detailed breakdown in s as well, e.g., s['points_breakdown'] = points_awarded)
                        save_json("submissions.json", submissions)
                        st.success(f"Submission {s['id']} graded with {total_points} points.")
                        st.rerun()
        # Articles tab
        with selected_tab[2 if st.session_state.role != "admin" else 3]:
            st.subheader("Manage Articles")
            for art in articles:
                col1, col2 = st.columns([8,2])
                col1.write(f"{art['title']} (by {art['author']})")
                if col2.button("Delete", key=f"delart{art['id']}"):
                    articles.remove(art)
                    # remove its comments too
                    to_remove = [c for c in comments if c["article_id"] == art["id"]]
                    for c in to_remove:
                        comments.remove(c)
            if st.button("Save Article Changes"):
                save_json("articles.json", articles)
                save_json("comments.json", comments)
                st.success("Article changes saved.")
