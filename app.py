
from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import random
import pandas as pd
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "super_secret_key"
app.permanent_session_lifetime = timedelta(minutes=10)

DATABASE = "database.db"

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mobile TEXT UNIQUE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        designation TEXT,
        office TEXT,
        district TEXT,
        contact TEXT,
        email TEXT
    )
    """)

    conn.commit()
    conn.close()

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        mobile = request.form["mobile"]

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE mobile=?", (mobile,))
        user = c.fetchone()
        conn.close()

        if user:
            otp = random.randint(100000,999999)
            session["otp"] = str(otp)
            session["mobile"] = mobile
            print("OTP:", otp)
            return redirect("/verify")
        else:
            return "Unauthorized Mobile Number"

    return render_template("login.html")

@app.route("/verify", methods=["GET","POST"])
def verify():
    if request.method == "POST":
        entered_otp = request.form["otp"]
        if entered_otp == session.get("otp"):
            session["user"] = session.get("mobile")
            return redirect("/dashboard")
        else:
            return "Invalid OTP"
    return render_template("verify.html")

@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if "user" not in session:
        return redirect("/")

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if request.method == "POST":
        search = request.form["search"]
        c.execute("""
        SELECT * FROM employees
        WHERE name LIKE ? OR email LIKE ? OR contact LIKE ?
        """, ('%'+search+'%','%'+search+'%','%'+search+'%'))
    else:
        c.execute("SELECT * FROM employees LIMIT 50")

    data = c.fetchall()
    conn.close()

    return render_template("dashboard.html", data=data)

@app.route("/export")
def export():
    if "user" not in session:
        return redirect("/")

    conn = sqlite3.connect(DATABASE)
    df = pd.read_sql_query("SELECT * FROM employees", conn)
    conn.close()

    file_path = "employees.xlsx"
    df.to_excel(file_path, index=False)
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
