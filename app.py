from flask import Flask, render_template, request, redirect, session
import random
import os
import psycopg2
from urllib.parse import urlparse

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            mobile VARCHAR(15) UNIQUE NOT NULL
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

init_db()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        mobile = request.form["mobile"]

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE mobile=%s;", (mobile,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            otp = str(random.randint(100000, 999999))
            session["otp"] = otp
            session["mobile"] = mobile
            print("OTP:", otp)
            return redirect("/verify")
        else:
            return "Unauthorized Mobile Number"

    return render_template("login.html")


@app.route("/verify", methods=["GET", "POST"])
def verify():
    if request.method == "POST":
        entered_otp = request.form["otp"]

        if entered_otp == session.get("otp"):
            session["logged_in"] = True
            return redirect("/admin")
        else:
            return "Invalid OTP"

    return render_template("verify.html")


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("logged_in"):
        return redirect("/")

    if request.method == "POST":
        mobile = request.form["mobile"]

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (mobile) VALUES (%s);", (mobile,))
            conn.commit()
        except:
            pass
        cur.close()
        conn.close()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT mobile FROM users ORDER BY id DESC;")
    mobiles = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("admin.html", mobiles=mobiles)


if __name__ == "__main__":
    app.run()
