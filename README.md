
# Health Record Organizer

A simple **Flask + SQLite** web app to securely store and manage personal health reports.  
Users can register/login with a phone number, upload PDFs/images of medical reports, download or delete them later, and **link family members** under a single account for easy access.

> ⚠️ Educational sample. Do **not** use in production without adding password hashing, CSRF protection, and stricter file validation.

---

## ✨ Features

- **Phone-based signup & login** (with a generated **Unique ID** to help with account recovery)
- **Upload / Download / Delete** medical reports (stored in `static/uploads/`)
- **Linked Users (Family Accounts):** add other users tied to the main phone and switch to their dashboards
- **SQLite** database auto-initialized on first run (`database.db`)
- Clean UI with templated pages (`Jinja2` via Flask)

---

## 🧱 Tech Stack

- **Backend:** Flask (Python)
- **Database:** SQLite
- **Frontend:** HTML, CSS (Jinja2 templates)
- **Storage:** Local filesystem for uploads

---

## 📁 Project Structure

```
Health Record Organizer/
├── app.py                    # Flask application (routes, DB init, uploads)
├── database.db               # SQLite DB (auto-created)
├── static/
│   ├── css/style.css         # App styles
│   ├── profile_icon.png
│   └── uploads/              # Uploaded reports (created automatically)
└── templates/
    ├── base.html
    ├── home.html
    ├── about.html
    ├── register.html
    ├── login.html
    ├── dashboard.html
    └── manage_users.html
```

---

## 🚀 Getting Started (Local)

### 1) Prerequisites
- Python 3.9+
- `pip`

### 2) Setup
```bash
# (a) Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# (b) Install dependencies
pip install Flask

# (c) Run
python app.py
```

The app starts on `http://127.0.0.1:5000/`.

---

## 🔐 Default Config & Paths

- **Uploads:** saved under `static/uploads/`
- **Database:** `database.db` (auto-created by `init_db()`)
- **Secret key:** defined in `app.py` (replace it for your app)
- **Max file size / allowed types:** (add validation as needed)

---

## 🧭 Routes

| Route                                                | Methods        | Purpose |
|-----------------------------------------------------|----------------|---------|
| `/`                                                 | GET            | Home page |
| `/about`                                            | GET            | About page |
| `/register`                                         | GET, POST      | Create an account using phone + password (generates **Unique ID**) |
| `/login`                                            | GET, POST      | Login with phone + password |
| `/dashboard/<int:user_id>`                          | GET            | User dashboard (lists uploaded reports) |
| `/upload`                                           | POST           | Upload a report (file + description) |
| `/download/<int:report_id>`                         | GET            | Download a specific report |
| `/delete/<int:report_id>`                           | GET            | Delete a specific report |
| `/manage_users/<int:user_id>`                       | GET, POST      | Add and list **linked users** (family) under the main phone |
| `/delete_linked_user/<int:user_id>/<int:linked_user_id>` | GET       | Remove a linked (non-main) user |

---

## 🗃️ Database Schema (simplified)

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    phone TEXT UNIQUE,
    password TEXT,
    linked_phone TEXT,  -- main account phone for grouping
    unique_id TEXT
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    filename TEXT,
    description TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

---

## 🧪 Sample Workflow

1. **Register** with phone + password → save the shown **Unique ID**.
2. **Login** → land on your **Dashboard**.
3. **Upload** PDFs/images of reports with a short description.
4. **Manage Users** → add family members (they share the main phone in `linked_phone`).
5. **Download/Delete** any uploaded report later.

---

## ✅ Production Hardening Checklist

- [ ] Hash passwords (`werkzeug.security.generate_password_hash`, `check_password_hash`)
- [ ] Validate uploads (MIME/type/size, allowlist extensions like `.pdf`, `.png`, `.jpg`)
- [ ] Randomized safe filenames (`uuid`) and private storage
- [ ] CSRF protection (Flask-WTF)
- [ ] Session security (HTTPOnly/SameSite, real secret key, secure cookies)
- [ ] Use a proper DB (e.g., Postgres) for multi-user deployments
- [ ] Logging & error handling

---

## 📝 License

Add your preferred license (e.g., MIT) here.

---

## 🙌 Acknowledgements

- Built with ❤️ using Flask.
