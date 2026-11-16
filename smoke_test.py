"""End-to-end smoke test using Flask test client. Run: python smoke_test.py"""
import re
from app import create_app

app = create_app()
app.config["TESTING"] = True

# Reset DB for a clean test run
with app.app_context():
    from extensions import db as _db
    _db.drop_all()
    _db.create_all()

client = app.test_client()

def csrf(html):
    m = re.search(r'name="csrf_token" value="([^"]+)"', html)
    return m.group(1) if m else None

ok = fail = 0
def check(name, cond):
    global ok, fail
    if cond:
        ok += 1
        print(f"  PASS  {name}")
    else:
        fail += 1
        print(f"  FAIL  {name}")

# 1. Landing + auth pages render
r = client.get("/")
check("landing page", r.status_code == 200 and b"PocketWise" in r.data)

# 2. Register
r = client.get("/register")
tok = csrf(r.data.decode())
r = client.post("/register", data=dict(
    csrf_token=tok, name="Test User", email="testuser@example.com",
    password="test1234", confirm_password="test1234"), follow_redirects=True)
check("register + redirect to login", r.status_code == 200 and b"Sign in" in r.data)

# duplicate email rejected
r = client.get("/register"); tok = csrf(r.data.decode())
r = client.post("/register", data=dict(
    csrf_token=tok, name="Dup", email="testuser@example.com",
    password="test1234", confirm_password="test1234"), follow_redirects=True)
check("duplicate email rejected", b"already registered" in r.data)

# 3. Login failure
r = client.get("/login"); tok = csrf(r.data.decode())
r = client.post("/login", data=dict(
    csrf_token=tok, email="testuser@example.com", password="wrongpass"), follow_redirects=True)
check("bad login rejected", b"Invalid email or password" in r.data)

# 4. Login success
r = client.get("/login"); tok = csrf(r.data.decode())
r = client.post("/login", data=dict(
    csrf_token=tok, email="testuser@example.com", password="test1234"), follow_redirects=True)
check("login success -> dashboard", b"Dashboard" in r.data and r.status_code == 200)

# 5. Protected route requires login
c2 = app.test_client()
r = c2.get("/dashboard")
check("dashboard protected (302 redirect)", r.status_code == 302)

# 6. Add income
r = client.get("/income/"); tok = csrf(r.data.decode())
r = client.post("/income/add", data=dict(
    csrf_token=tok, title="Test salary", category="Salary", amount="10000",
    date="2026-11-01", description="smoke"), follow_redirects=True)
check("add income", b"Income added successfully" in r.data and b"Test salary" in r.data)

# 7. Add expense
r = client.post("/expenses/add", data=dict(
    csrf_token=tok, title="Test food", category="Food", amount="500",
    date="2026-11-05", description="smoke"), follow_redirects=True)
check("add expense", b"Expense added successfully" in r.data)

# future date rejected
r = client.post("/expenses/add", data=dict(
    csrf_token=tok, title="Future", category="Food", amount="500",
    date="2099-01-01", description=""), follow_redirects=True)
check("future date rejected", b"cannot be in the future" in r.data)

# 8. Edit & delete (find txn id from transactions page)
r = client.get("/transactions/")
m = re.search(rb'transactions/edit/(\d+)', r.data)
tid = int(m.group(1))
r = client.post(f"/transactions/edit/{tid}", data=dict(
    csrf_token=tok, transaction_type="expense", title="Updated food", category="Food",
    amount="550", date="2026-11-05", description="edited"), follow_redirects=True)
check("edit transaction", b"Transaction updated" in r.data and b"Updated food" in r.data)

# 9. Budget set + dashboard math
r = client.post("/budgets/add", data=dict(
    csrf_token=tok, category="Overall", monthly_limit="5000", month="11", year="2026"),
    follow_redirects=True)
check("set budget", b"Budget" in r.data)

r = client.get("/dashboard")
check("dashboard renders cards", b"Total Balance" in r.data and b"Monthly Budget" in r.data)
# balance should be 10000 - 550 = 9450 for this fresh user
check("balance calc (10000-550=9450)", "9,450.00" in r.data.decode())
check("budget exceeded warning", "exceeded" in r.data.decode() or "Budget utilization" in r.data.decode())

# 10. Reports + exports
r = client.get("/reports/?month=11&year=2026")
check("reports page", r.status_code == 200 and b"Reports" in r.data)
r = client.get("/reports/export/csv?month=11&year=2026")
check("CSV export", r.status_code == 200 and "text/csv" in r.headers.get("Content-Type", ""))
r = client.get("/reports/export/pdf?month=11&year=2026")
check("PDF export", r.status_code == 200 and r.data.startswith(b"%PDF"))

# 11. User isolation — second user can't edit first user's txn
c3 = app.test_client()
r = c3.get("/register"); tok3 = csrf(r.data.decode())
c3.post("/register", data=dict(csrf_token=tok3, name="Two", email="two@example.com",
        password="test1234", confirm_password="test1234"))
r = c3.get("/login"); tok3 = csrf(r.data.decode())
c3.post("/login", data=dict(csrf_token=tok3, email="two@example.com", password="test1234"))
# Fresh token minted AFTER login (session.clear() on login rotates the CSRF seed).
# Use /income/ (always renders a POST form) — /transactions/ may have no modals for u2.
r = c3.get("/income/"); tok3 = csrf(r.data.decode())
r = c3.post(f"/transactions/edit/{tid}", data=dict(
    csrf_token=tok3, transaction_type="expense", title="Hacked", category="Food",
    amount="1", date="2026-11-05", description=""), follow_redirects=True)
check("cross-user edit blocked", b"not allowed" in r.data)
r = c3.post(f"/transactions/delete/{tid}", data=dict(csrf_token=tok3), follow_redirects=True)
check("cross-user delete blocked", b"not allowed" in r.data)

# 12. Delete own txn
r = client.get("/transactions/")
m = re.search(rb'transactions/delete/(\d+)', r.data)
r = client.post(f"/transactions/delete/{tid}", data=dict(csrf_token=tok), follow_redirects=True)
check("delete own transaction", b"Transaction deleted" in r.data)

# 13. Logout
r = client.get("/logout", follow_redirects=True)
check("logout", b"logged out" in r.data)

print(f"\nResult: {ok} passed, {fail} failed")
