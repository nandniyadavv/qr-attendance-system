# QR Code–Based Attendance and Distribution System

## Problem Statement
Managing attendance and distribution manually during college events leads to long queues, duplicate entries, and poor tracking.

## Solution
A web-based QR code system that enables event organizers to generate and email QR codes to participants and scan them to mark attendance securely.

---

## Features

### Admin Panel
- Upload participants via CSV
- Generate unique QR codes
- Email QR codes automatically
- View live attendance statistics
- View last scanned participant
- Export attendance as CSV

### Scanner
- Web-based QR scanner
- Works on laptop and mobile cameras
- Prevents duplicate scans
- Instant verification feedback

---

## Tech Stack
- Python (Flask)
- HTML, CSS, JavaScript
- QR Code generation
- Flask-Mail (SMTP)
- CSV-based storage

---

## How It Works
1. Admin uploads a CSV containing participant names and emails
2. The system generates a unique QR code for each participant
3. QR codes are emailed automatically
4. Organizers scan QR codes at the event
5. Attendance is marked and duplicates are prevented
6. Attendance data can be exported as CSV

---

## How to Run Locally

```bash
pip install -r requirements.txt
python app.py
Open:

Admin Panel: http://127.0.0.1:5000

Scanner Page: http://127.0.0.1:5000/scanner

CSV Format
name,email
Aman Sharma,aman@gmail.com
Riya Singh,riya@gmail.com

Bonus Features

Live attendance stats

Last scanned participant display

Attendance export

Clean and responsive UI

Future Improvements

Multi-event support

Role-based scanners

QR expiry

Database integration

Hackathon Project

Built as part of a hackathon to demonstrate QR-based attendance and distribution.


Save the file 💾

---

## 🔧 STEP 2 — Commit README

In terminal:

```bash
git add README.md
git commit -m "Add README documentation"
git push