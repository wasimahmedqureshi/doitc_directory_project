from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import random
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATABASE = "database.db"

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  mobile TEXT UNIQUE)''')

    conn.commit()
    conn.close()

init_db()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        mobile = request.form["mobile"]

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE mobile=?", (mobile,))
        user = c.fetchone()
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
            return redirect("/admin")
        else:
            return "Invalid OTP"

    return render_template("verify.html")


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        new_mobile = request.form["mobile"]

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (mobile) VALUES (?)", (new_mobile,))
            conn.commit()
        except:
            pass
        conn.close()

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT mobile FROM users")
    mobiles = c.fetchall()
    conn.close()

    return render_template("admin.html", mobiles=mobiles)


if __name__ == "__main__":
    app.run(debug=True)
