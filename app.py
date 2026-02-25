from flask import Flask, render_template, request, redirect, session
import sqlite3
import random
from datetime import timedelta
import os

app = Flask(__name__)
app.secret_key = "super_secret_key"
app.permanent_session_lifetime = timedelta(minutes=15)

DATABASE = "database.db"

def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mobile TEXT UNIQUE
    )
    """)

    # Admin table
    c.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # Employees table
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

    # Default Admin (only first time)
    c.execute("INSERT OR IGNORE INTO admin (username,password) VALUES (?,?)",
              ("admin","admin123"))

    conn.commit()
    conn.close()

# Create DB only if not exists
if not os.path.exists(DATABASE):
    init_db()

# ================= ADMIN LOGIN =================

@app.route("/admin", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM admin WHERE username=? AND password=?", (username,password))
        admin = c.fetchone()
        conn.close()

        if admin:
            session["admin"] = username
            return redirect("/admin_dashboard")
        else:
            return "Invalid Admin Credentials"

    return render_template("admin_login.html")

@app.route("/admin_dashboard", methods=["GET","POST"])
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin")

    conn = get_connection()
    c = conn.cursor()

    if request.method == "POST":
        mobile = request.form["mobile"]
        c.execute("INSERT OR IGNORE INTO users (mobile) VALUES (?)", (mobile,))
        conn.commit()

    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()

    return render_template("admin_dashboard.html", users=users)

@app.route("/delete/<int:user_id>")
def delete_user(user_id):
    if "admin" not in session:
        return redirect("/admin")

    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    return redirect("/admin_dashboard")

# ================= USER LOGIN =================

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        mobile = request.form["mobile"]

        conn = get_connection()
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

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    return "User Login Successful ✅"

if __name__ == "__main__":
    app.run()
