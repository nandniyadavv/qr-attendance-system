from flask import Flask, render_template, request, send_file
from flask_mail import Mail, Message
import pandas as pd
import qrcode
import os
import csv

app = Flask(__name__)

# ---------------- EMAIL CONFIG ----------------
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "nandni.y4115@gmail.com"
app.config["MAIL_PASSWORD"] = "rhjfyxwyqjvzorpl"

mail = Mail(app)

# ---------------- FOLDERS ----------------
QR_FOLDER = "static/qr"
os.makedirs(QR_FOLDER, exist_ok=True)

# ---------------- STATS FUNCTION ----------------
def get_stats():
    # No participants file or empty → all zero
    if not os.path.exists("participants.csv"):
        return 0, 0, 0

    df = pd.read_csv("participants.csv")
    if df.empty:
        return 0, 0, 0

    total = len(df)
    scanned = 0

    if os.path.exists("scanned.csv"):
        with open("scanned.csv", "r") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            for row in reader:
                if row:
                    scanned += 1

    remaining = max(total - scanned, 0)
    return total, scanned, remaining

# ---------------- ROUTES ----------------
@app.route("/")
def admin():
    total, scanned, remaining = get_stats()

    last_scanned = "None"
    if os.path.exists("last_scanned.txt"):
        with open("last_scanned.txt", "r") as f:
            last_scanned = f.read().strip()

    return render_template(
        "admin.html",
        total=total,
        scanned=scanned,
        remaining=remaining,
        last_scanned=last_scanned
    )



# ---------------- UPLOAD CSV ----------------
@app.route("/upload", methods=["POST"])
def upload():
    event = request.form["event"]
    file = request.files["file"]

    # Read CSV safely
    df = pd.read_csv(file)
    df.columns = [c.strip().lower() for c in df.columns]

    # Validate CSV
    if "name" not in df.columns or "email" not in df.columns:
        return "CSV must contain 'name' and 'email' columns"

    # Save participants
    df.to_csv("participants.csv", index=False)

    # Reset scanned.csv
    with open("scanned.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["event", "email", "status"])
    # Reset last scanned on new event
    if os.path.exists("last_scanned.txt"):
        os.remove("last_scanned.txt")

    # Ensure QR folder exists
    os.makedirs(QR_FOLDER, exist_ok=True)

    # Generate QR + send email
    for _, row in df.iterrows():
        name = str(row["name"])
        email = str(row["email"])

        qr_data = f"{event}|{email}"
        qr = qrcode.make(qr_data)

        filename = f"{email.replace('@', '_')}.png"
        qr_path = os.path.join(QR_FOLDER, filename)
        qr.save(qr_path)

        try:
            msg = Message(
                subject=f"Your QR Code for {event}",
                sender=app.config["MAIL_USERNAME"],
                recipients=[email]
            )
            msg.body = (
                f"Hello {name},\n\n"
                f"Please find your QR code for {event} attached.\n\n"
                "Regards,\nEvent Team"
            )
            msg.attach(filename, "image/png", open(qr_path, "rb").read())
            mail.send(msg)
        except Exception as e:
            print("Email error:", e)

    return "QR Codes generated and emailed successfully!"


# ---------------- SCANNER PAGE ----------------
@app.route("/scanner")
def scanner():
    return render_template("scanner.html")

# ---------------- SCAN QR ----------------
@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json()
    qr_data = data.get("qr", "")

    if "|" not in qr_data:
        return "❌ Invalid QR code"

    event, email = qr_data.split("|", 1)

    # Prevent duplicate scan
    with open("scanned.csv", "r") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if row and row[0] == event and row[1] == email:
                return "❌ Already scanned"

    # Save scan
    with open("scanned.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([event, email, "Present"])

    # 🔴 FIND NAME FROM participants.csv
    scanned_name = email  # fallback
    if os.path.exists("participants.csv"):
        df = pd.read_csv("participants.csv")
        df.columns = [c.strip().lower() for c in df.columns]

        match = df[df["email"] == email]
        if not match.empty:
            scanned_name = match.iloc[0]["name"]

    # 🔴 WRITE LAST SCANNED (CONFIRMED)
    with open("last_scanned.txt", "w") as f:
        f.write(scanned_name)

    print("LAST SCANNED WRITTEN:", scanned_name)  # debug proof

    return "✅ Scan successful"


# ---------------- EXPORT CSV ----------------
@app.route("/export")
def export_csv():
    return send_file(
        "scanned.csv",
        as_attachment=True,
        download_name="attendance.csv"
    )

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)

