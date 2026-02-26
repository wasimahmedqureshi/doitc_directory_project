import sqlite3
import random
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATABASE = "database.db"


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mobile TEXT UNIQUE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS otp_store (
        mobile TEXT,
        otp TEXT
    )
    """)

    conn.commit()
    conn.close()


create_tables()


@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        mobile = request.form["mobile"]

        conn = get_connection()
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM users")
        total_users = c.fetchone()[0]

        if total_users == 0:
            c.execute("INSERT INTO users (mobile) VALUES (?)", (mobile,))
            conn.commit()

        c.execute("SELECT * FROM users WHERE mobile=?", (mobile,))
        user = c.fetchone()

        if user:
            otp = str(random.randint(100000, 999999))

            c.execute("DELETE FROM otp_store WHERE mobile=?", (mobile,))
            c.execute("INSERT INTO otp_store (mobile, otp) VALUES (?,?)", (mobile, otp))
            conn.commit()
            conn.close()

            print("OTP:", otp)
            session["mobile"] = mobile
            return redirect("/verify")
        else:
            conn.close()
            return "Unauthorized Mobile Number"

    return render_template("login.html")


@app.route("/verify", methods=["GET", "POST"])
def verify():

    if "mobile" not in session:
        return redirect("/")

    if request.method == "POST":
        entered_otp = request.form["otp"]
        mobile = session["mobile"]

        conn = get_connection()
        c = conn.cursor()

        c.execute("SELECT otp FROM otp_store WHERE mobile=?", (mobile,))
        record = c.fetchone()

        if record and entered_otp == record["otp"]:
            session["user"] = mobile
            c.execute("DELETE FROM otp_store WHERE mobile=?", (mobile,))
            conn.commit()
            conn.close()
            return redirect("/dashboard")
        else:
            conn.close()
            return "Invalid OTP"

    return render_template("verify.html")


@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    return """
    <h2>Login Successful ✅</h2>
    <br>
    <a href='/admin'>Go To Admin Panel</a>
    <br><br>
    <a href='/logout'>Logout</a>
    """


@app.route("/admin", methods=["GET", "POST"])
def admin():

    if "user" not in session:
        return redirect("/")

    conn = get_connection()
    c = conn.cursor()

    if request.method == "POST":
        new_mobile = request.form["mobile"]
        try:
            c.execute("INSERT INTO users (mobile) VALUES (?)", (new_mobile,))
            conn.commit()
        except:
            pass

    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()

    html = "<h2>Admin Panel</h2>"
    html += """
    <form method='POST'>
        <input type='text' name='mobile' placeholder='Enter Mobile'>
        <button type='submit'>Add Mobile</button>
    </form>
    <br><br>
    """

    for user in users:
        html += f"<p>{user['mobile']}</p>"

    html += "<br><a href='/dashboard'>Back</a>"

    return html


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
