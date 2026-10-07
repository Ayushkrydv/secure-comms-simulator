# Secure Tactical Communication Simulation System

A college project simulating secure encrypted communication between field personnel and a command centre, built with Python Flask.

> **For educational/demonstration purposes only. Uses fictional simulated personnel.**

---

## Features

- 🔐 AES encrypted messaging (Fernet / cryptography library)
- 🔑 HMAC-SHA256 message integrity verification
- 🔁 Replay attack detection and prevention
- 📡 Simulated network states: NORMAL / DEGRADED / OFFLINE
- 📦 Offline message queue with auto-sync on network restore
- 👥 Role-based access: Field Personnel, Command Centre, Administrator
- 📋 Full security and audit logging
- 🖥️ Admin dashboard with live network simulation controls

---

## Tech Stack

- **Backend:** Python 3, Flask, Flask-Login, Flask-SQLAlchemy
- **Database:** SQLite
- **Frontend:** HTML, Bootstrap 5, JavaScript
- **Security:** cryptography (Fernet AES), Werkzeug password hashing

---

## Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/secure-comms-simulator.git
cd secure-comms-simulator

# Install dependencies
pip install -r requirements.txt

# Run the app
py -3 run.py
```

Open your browser at: **http://127.0.0.1:5000**

---

## Default Login Credentials

| Username | Password | Role |
|---|---|---|
| `admin` | `Admin@123` | Administrator |
| `personnel_a` | `Field@123` | Field Personnel |
| `personnel_b` | `Field@123` | Field Personnel |
| `command_centre` | `Cmd@123` | Command Centre |

---

## Project Structure

```
secure_comms/
├── run.py                  # App entry point
├── requirements.txt
├── app/
│   ├── __init__.py         # App factory
│   ├── models.py           # Database models
│   ├── security.py         # Encryption, integrity, replay detection
│   ├── network.py          # Network simulation engine
│   └── routes/
│       ├── auth.py         # Login / logout
│       ├── field.py        # Field personnel routes
│       ├── command.py      # Command centre routes
│       ├── admin.py        # Admin routes
│       └── api.py          # JSON API endpoints
└── templates/
    ├── login.html
    ├── base.html
    ├── field_dashboard.html
    ├── command_dashboard.html
    └── admin_dashboard.html
```

---

## Demo Scenario

1. Login as `personnel_a` → send a secure message to `personnel_b`
2. Login as `admin` → set network to **OFFLINE**
3. Login as `personnel_a` → send another message → it gets **queued**
4. Login as `admin` → restore network → queued message **auto-delivers**
5. On admin dashboard → use **Replay Attack Demo** to show duplicate message rejection
6. View the full **Security/Audit Log**

---

## Security Concepts Demonstrated

| Concept | Implementation |
|---|---|
| Password hashing | PBKDF2-SHA256 via Werkzeug |
| Authenticated encryption | Fernet (AES-128-CBC + HMAC-SHA256) |
| Message integrity | HMAC-SHA256 over full message envelope |
| Replay attack prevention | Processed message ID set |
| Audit logging | Every event recorded in SecurityLog table |
| Role-based access control | Decorator-enforced on every route |

---

## License

This project is for educational purposes only.
