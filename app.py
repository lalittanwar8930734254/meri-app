from flask import Flask, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "meri-app-secret-key"

def db():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            message TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

init_db()

STYLE = """
<style>
body {
    margin:0;
    font-family:Arial,sans-serif;
    background:#f3f5f9;
}
.container {
    max-width:430px;
    min-height:100vh;
    margin:auto;
    padding:25px;
    box-sizing:border-box;
    background:white;
}
.logo {
    text-align:center;
    font-size:30px;
    font-weight:bold;
    margin:30px 0;
}
.card {
    padding:20px;
    background:#f5f5f5;
    border-radius:18px;
}
input {
    width:100%;
    padding:14px;
    margin:7px 0;
    box-sizing:border-box;
    border:1px solid #ddd;
    border-radius:10px;
    font-size:16px;
}
button {
    width:100%;
    padding:14px;
    margin-top:10px;
    border:0;
    border-radius:10px;
    background:#111;
    color:white;
    font-size:16px;
}
.user,.message {
    padding:14px;
    margin:10px 0;
    background:#f2f2f2;
    border-radius:14px;
}
a {
    color:#333;
}
</style>
"""

@app.route("/")
def home():
    if "user_id" not in session:
        return STYLE + """
        <div class="container">
            <div class="logo">❤️ Meri App</div>
            <div class="card">
                <a href="/login"><button>🔐 Login</button></a>
                <a href="/register"><button>📝 Register</button></a>
            </div>
        </div>
        """

    return STYLE + f"""
    <div class="container">
        <div class="logo">❤️ Meri App</div>
        <div class="card">
            <h2>Welcome {session["name"]} 👋</h2>
            <p>Kisi se baat karna chahte ho?</p>
            <a href="/users"><button>💬 Chat Start Karein</button></a>
            <a href="/logout"><button>🚪 Logout</button></a>
        </div>
    </div>
    """

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        password_hash = generate_password_hash(password)

        try:
            conn = db()
            conn.execute(
                "INSERT INTO users (name,email,password) VALUES (?,?,?)",
                (name, email, password_hash)
            )
            conn.commit()
            conn.close()
            return redirect("/login")
        except sqlite3.IntegrityError:
            return STYLE + """
            <div class="container">
                <h2>❌ Ye email already registered hai.</h2>
                <a href="/register">Back</a>
            </div>
            """

    return STYLE + """
    <div class="container">
        <div class="logo">📝 Register</div>
        <div class="card">
            <form method="POST">
                <input name="name" placeholder="Apna naam" required>
                <input name="email" type="email" placeholder="Email" required>
                <input name="password" type="password" placeholder="Password" required>
                <button>Register</button>
            </form>
            <br>
            <a href="/login">Already account hai? Login</a>
        </div>
    </div>
    """

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = db()
        user = conn.execute(
            "SELECT id,name,password FROM users WHERE email=?",
            (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            return redirect("/")

        return STYLE + """
        <div class="container">
            <h2>❌ Email ya password galat hai.</h2>
            <a href="/login">Dobara try karein</a>
        </div>
        """

    return STYLE + """
    <div class="container">
        <div class="logo">🔐 Login</div>
        <div class="card">
            <form method="POST">
                <input name="email" type="email" placeholder="Email" required>
                <input name="password" type="password" placeholder="Password" required>
                <button>Login</button>
            </form>
            <br>
            <a href="/register">New user? Register</a>
        </div>
    </div>
    """

@app.route("/users")
def users():
    if "user_id" not in session:
        return redirect("/login")

    conn = db()
    users = conn.execute(
        "SELECT id,name FROM users WHERE id!=?",
        (session["user_id"],)
    ).fetchall()
    conn.close()

    html = STYLE + """
    <div class="container">
        <div class="logo">👥 Users</div>
    """

    if not users:
        html += "<p>Abhi koi doosra user nahi hai.</p>"

    for user in users:
        html += f"""
        <div class="user">
            <b>👤 {user["name"]}</b>
            <a href="/chat/{user["id"]}">
                <button>💬 Chat</button>
            </a>
        </div>
        """

    html += """
        <br>
        <a href="/">← Home</a>
    </div>
    """

    return html

@app.route("/chat/<int:user_id>", methods=["GET", "POST"])
def chat(user_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = db()

    receiver = conn.execute(
        "SELECT id,name FROM users WHERE id=?",
        (user_id,)
    ).fetchone()

    if not receiver:
        conn.close()
        return "User nahi mila."

    if request.method == "POST":
        message = request.form["message"].strip()

        if message:
            conn.execute(
                """
                INSERT INTO messages(sender_id,receiver_id,message)
                VALUES(?,?,?)
                """,
                (session["user_id"], user_id, message)
            )
            conn.commit()

        conn.close()
        return redirect(f"/chat/{user_id}")

    messages = conn.execute(
        """
        SELECT messages.message,messages.sender_id,users.name
        FROM messages
        JOIN users ON users.id=messages.sender_id
        WHERE
        (sender_id=? AND receiver_id=?)
        OR
        (sender_id=? AND receiver_id=?)
        ORDER BY messages.id
        """,
        (session["user_id"], user_id, user_id, session["user_id"])
    ).fetchall()

    conn.close()

    html = STYLE + f"""
    <div class="container">
        <div class="logo">💬 {receiver["name"]}</div>
    """

    for msg in messages:
        html += f"""
        <div class="message">
            <b>{msg["name"]}:</b> {msg["message"]}
        </div>
        """

    html += """
        <form method="POST">
            <input name="message" placeholder="Message likho..." required>
            <button>Send 💬</button>
        </form>

        <br>
        <a href="/users">← Users</a>
    </div>
    """

    return html

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

app.run(host="0.0.0.0", port=5000)
