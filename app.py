import os
import sqlite3
import random
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "supersecretkey"

app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax"
)

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
        conn.close()

        if user:
            otp = random.randint(100000, 999999)
            session["otp"] = str(otp)
            session["mobile"] = mobile
            print("OTP:", otp)
            return redirect("/verify")
        else:
            return "Unauthorized Mobile Number"

    return render_template("login.html")


@app.route("/verify", methods=["GET", "POST"])
def verify():

    if "otp" not in session:
        return redirect("/")

    if request.method == "POST":
        entered_otp = request.form["otp"]

        if entered_otp == session.get("otp"):
            session.pop("otp", None)
            session["user"] = session.get("mobile")
            return redirect("/dashboard")
        else:
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


if __name__ == "__main__":
    app.run(debug=True)
