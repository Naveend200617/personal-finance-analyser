# PocketWise — Personal Finance Management System

A BCA mini project: a web-based personal finance manager built with **Flask**, **Flask-SQLAlchemy**, **Flask-Migrate**, **Flask-WTF (CSRF)** and **MySQL** (SQLite fallback for local demos). Track income & expenses, manage monthly budgets, and generate chart-based reports with PDF/CSV export.

## Features
- **Authentication** — register, login, logout, hashed passwords (Werkzeug), CSRF-protected forms, session management, per-user data isolation.
- **Dashboard** — balance, income, expenses, monthly savings, budget & remaining-budget cards; recent transactions; income-vs-expense bar chart; category pie chart; budget utilization with warnings.
- **Income / Expense CRUD** — add, edit, delete, search, filter (category & date ranges).
- **Transactions** — unified history with search, type/category/date filters, sorting, view/edit/delete modals.
- **Budgets** — Overall + category-wise monthly budgets, utilization %, exceeded/near-limit alerts, edit/delete.
- **Reports** — monthly income/expense/savings, category breakdown, 12-month trend, PDF download (ReportLab), CSV export.

## Folder structure
```
PocketWise/
├── app.py                 # App factory, blueprints, error handlers, "inr" filter
├── config.py              # Config classes (env-driven)
├── extensions.py          # db / migrate / csrf singletons
├── models.py              # User, Transaction, Budget, Category models
├── requirements.txt
├── .env / .env.example
├── seed.py                # Demo data seeder
├── routes/                # Blueprints: auth, dashboard, income, expenses, transactions, budgets, reports
├── templates/             # Jinja2 templates + errors/
├── static/css/style.css
├── static/js/script.js
└── instance/              # SQLite DB lives here (when using fallback)
```

## Setup on Windows (VS Code terminal)

```powershell
# 1. Open the folder
cd PocketWise

# 2. Virtual environment
py -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### MySQL setup (MySQL Workbench)
```sql
CREATE DATABASE pocketwise CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
Then edit `.env` and set:
```
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost/pocketwise
```
Initialize the schema with Flask-Migrate:
```powershell
$env:FLASK_APP="app.py"
flask db init      # first time only — creates migrations/
flask db migrate -m "initial tables"
flask db upgrade
```
(No MySQL? Leave `DATABASE_URL=sqlite:///pocketwise.db` and run `python seed.py` — it creates tables automatically.)

### Seed demo data
```powershell
python seed.py
# Login: demo@pocketwise.com / demo123
```

### Run
```powershell
python app.py
# open http://127.0.0.1:5000
```

## Testing checklist
| # | Test | Expected |
|---|------|----------|
| 1 | Register new user | Success flash, redirect to login |
| 2 | Login with valid credentials | Redirect to dashboard |
| 3 | Login with wrong password | "Invalid email or password" |
| 4 | Add income / expense | Record appears, totals update |
| 5 | Edit / delete a transaction | Values update; record removed |
| 6 | Dashboard math | Balance = Income − Expenses |
| 7 | Set monthly budget | Card + utilization bar update |
| 8 | Exceed budget | Red alert, utilization > 100% |
| 9 | Generate report | Charts + CSV/PDF download |
| 10 | Access another user's data (edit URL id) | Blocked with warning flash |

## Security
- PBKDF2-SHA256 password hashing (Werkzeug)
- Flask-WTF CSRF tokens on every form
- SQL-injection-safe queries via SQLAlchemy ORM
- Ownership checks on every record mutation
- Secrets via `.env` (never committed)

## Troubleshooting
| Error | Fix |
|---|---|
| `Access denied for user 'root'...` | Wrong MySQL password in `.env` |
| `Unknown database 'pocketwise'` | Run `CREATE DATABASE pocketwise;` in Workbench |
| `No module named 'pymysql'` | `pip install PyMySQL` (create the venv first) |
| `RuntimeError: ... secret key` | Set `SECRET_KEY` in `.env` |
| Tables missing | `flask db upgrade` or run `python seed.py` (SQLite mode) |
| CSRF "The CSRF token is missing" | Use the provided templates; every POST form needs `{{ csrf_token() }}` |

## Tech credits
Bootstrap 5 · Chart.js · Font Awesome · Flask ecosystem · ReportLab
