from flask import Flask, render_template, request, Response
import sqlite3
import uuid
import qrcode
import csv
import os

app = Flask(__name__)

# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect("database.db")

# ---------------- HOME / EVENT-AWARE DASHBOARD ----------------
@app.route("/")
def home():
    db = get_db()
    cur = db.cursor()

    # Get latest event
    cur.execute("SELECT id, name FROM events ORDER BY id DESC LIMIT 1")
    event = cur.fetchone()

    if event:
        event_id, event_name = event

        cur.execute(
            "SELECT COUNT(*) FROM participants WHERE event_id = ?",
            (event_id,)
        )
        total = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM participants WHERE event_id = ? AND scanned = 1",
            (event_id,)
        )
        scanned = cur.fetchone()[0]

    else:
        event_name = "No Event"
        total = scanned = 0

    remaining = total - scanned

    return render_template(
        "index.html",
        total=total,
        scanned=scanned,
        remaining=remaining,
        event_name=event_name
    )

# ---------------- CREATE EVENT ----------------
@app.route("/create-event", methods=["GET", "POST"])
def create_event():
    db = get_db()
    cur = db.cursor()

    if request.method == "POST":
        name = request.form["event_name"]
        cur.execute("INSERT INTO events (name) VALUES (?)", (name,))
        db.commit()
        return "Event created successfully!"

    return render_template("create_event.html")

# ---------------- UPLOAD PAGE ----------------
@app.route("/upload")
def upload():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, name FROM events")
    events = cur.fetchall()
    return render_template("upload.html", events=events)

# ---------------- UPLOAD CSV + CLEAR OLD QRS ----------------
@app.route("/upload-csv", methods=["POST"])
def upload_csv():
    event_id = request.form["event_id"]
    file = request.files["csv"]

    # Clear old QR images
    qr_folder = "static/qr"
    if os.path.exists(qr_folder):
        for f in os.listdir(qr_folder):
            if f.endswith(".png"):
                os.remove(os.path.join(qr_folder, f))

    reader = csv.reader(file.stream.read().decode("utf-8").splitlines())

    db = get_db()
    cur = db.cursor()

    os.makedirs("static/qr", exist_ok=True)

    for row in reader:
        name, email = row
        token = str(uuid.uuid4())

        img = qrcode.make(token)
        img.save(f"static/qr/{token}.png")

        cur.execute(
            "INSERT INTO participants VALUES (?, ?, 0, ?)",
            (token, email, event_id)
        )

    db.commit()
    return "QR codes generated successfully!"

# ---------------- SCAN PAGE ----------------
@app.route("/scan")
def scan():
    return render_template("scan.html")

# ---------------- VERIFY QR ----------------
@app.route("/verify")
def verify():
    token = request.args.get("token")
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT scanned FROM participants WHERE token = ?", (token,))
    row = cur.fetchone()

    if not row:
        return "Invalid QR ❌"

    if row[0] == 1:
        return "Already used ❌"

    cur.execute("UPDATE participants SET scanned = 1 WHERE token = ?", (token,))
    db.commit()
    return "Attendance marked ✅"

# ---------------- VIEW QR ----------------
@app.route("/view-qr/<token>")
def view_qr(token):
    db = get_db()
    cur = db.cursor()

    cur.execute(
        "SELECT email, scanned FROM participants WHERE token = ?",
        (token,)
    )
    row = cur.fetchone()

    if not row:
        return "QR not found"

    email, scanned = row

    return render_template(
        "view_qr.html",
        token=token,
        email=email,
        scanned=scanned
    )

# ---------------- EXPORT CSV ----------------
@app.route("/export")
def export_csv():
    db = get_db()
    cur = db.cursor()

    # Export only latest event
    cur.execute("SELECT id FROM events ORDER BY id DESC LIMIT 1")
    event = cur.fetchone()

    if not event:
        return "No event data to export"

    event_id = event[0]

    cur.execute(
        "SELECT email, scanned FROM participants WHERE event_id = ?",
        (event_id,)
    )
    rows = cur.fetchall()

    def generate():
        yield "Email,Scanned\n"
        for email, scanned in rows:
            yield f"{email},{scanned}\n"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=attendance.csv"}
    )

# ---------------- START APP ----------------
if __name__ == "__main__":
    db = get_db()
    cur = db.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS participants (
        token TEXT PRIMARY KEY,
        email TEXT,
        scanned INTEGER,
        event_id INTEGER
    )
    """)

    db.commit()
    app.run(debug=True)


