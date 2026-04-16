#!/usr/bin/env python3
"""
LLM06: Excessive Agency — DevOps Dashboard (Browser)

Demo flow:
  1. Show database tables with real data
  2. Click "Run Agent" in unrestricted mode → tables vanish one by one
  3. Toggle to restricted mode → destructive ops blocked

Run: python3 LLM06-excessive-agency/web.py
Open: http://127.0.0.1:5006
"""
import sys, os, sqlite3, tempfile, uvicorn
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from shared.web import page
from templates import BODY_HTML, frontend_js, GUIDE_HTML

# ─── App Setup ────────────────────────────────────────────

app = FastAPI()
DB_PATH = os.path.join(tempfile.gettempdir(), "llm06_web.db")

# ─── Database ─────────────────────────────────────────────

SEED_SQL = """
DROP TABLE IF EXISTS users; DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS payments; DROP TABLE IF EXISTS audit_log;

CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, role TEXT);
INSERT INTO users VALUES
  (1,'Alice Chen','alice@acme.com','admin'),
  (2,'Bob Smith','bob@acme.com','user'),
  (3,'Carol Davis','carol@acme.com','user'),
  (4,'Dave Wilson','dave@acme.com','manager');

CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, product TEXT, amount REAL);
INSERT INTO orders VALUES (1,1,'Enterprise License',49999.99),(2,2,'Pro Plan',299.00),(3,3,'Starter Plan',49.00);

CREATE TABLE payments (id INTEGER PRIMARY KEY, order_id INTEGER, status TEXT, card_last4 TEXT);
INSERT INTO payments VALUES (1,1,'completed','4242'),(2,2,'completed','1234'),(3,3,'pending','5678');

CREATE TABLE audit_log (id INTEGER PRIMARY KEY, action TEXT, ts TEXT);
INSERT INTO audit_log VALUES (1,'user_login: alice','2025-04-15 09:00'),(2,'order_created: #1','2025-04-15 09:15');
"""


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SEED_SQL)
    conn.commit()
    conn.close()


def get_all_tables() -> dict:
    conn = sqlite3.connect(DB_PATH)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    result = {}
    for (tbl,) in tables:
        rows = conn.execute(f"SELECT * FROM {tbl}").fetchall()
        cols = [d[0] for d in conn.execute(f"SELECT * FROM {tbl} LIMIT 0").description] if rows else []
        result[tbl] = {"cols": cols, "rows": [list(r) for r in rows]}
    conn.close()
    return result


def execute_sql(sql: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(sql)
    conn.commit()
    conn.close()


# ─── Agent Steps ──────────────────────────────────────────

UNRESTRICTED_STEPS = [
    {"sql": "SELECT COUNT(*) FROM users",  "desc": "Counted 4 users",                       "level": "safe"},
    {"sql": "SELECT COUNT(*) FROM orders",  "desc": "Counted 3 orders",                      "level": "safe"},
    {"sql": "DELETE FROM audit_log",         "desc": "Cleared audit log (covering tracks!)",   "level": "warn"},
    {"sql": "DROP TABLE payments",           "desc": "Dropped payments — card data gone!",     "level": "danger"},
    {"sql": "DROP TABLE orders",             "desc": "Dropped orders — $50K+ lost!",           "level": "danger"},
    {"sql": "DROP TABLE users",              "desc": "Dropped users — all accounts wiped!",    "level": "danger"},
]

RESTRICTED_STEPS = [
    {"sql": "SELECT COUNT(*) FROM users",  "desc": "Counted 4 users",              "level": "safe",   "allowed": True},
    {"sql": "SELECT COUNT(*) FROM orders",  "desc": "Counted 3 orders",             "level": "safe",   "allowed": True},
    {"sql": "DELETE FROM audit_log",         "desc": "⏸️ REQUIRES HUMAN APPROVAL",   "level": "warn",   "allowed": False},
    {"sql": "DROP TABLE payments",           "desc": "🚫 BLOCKED — not permitted",   "level": "danger", "allowed": False},
    {"sql": "DROP TABLE users",              "desc": "🚫 BLOCKED — not permitted",   "level": "danger", "allowed": False},
]

# ─── Request Model ────────────────────────────────────────

class StepRequest(BaseModel):
    mode: str = "vulnerable"
    step: int = 0


def execute_agent_step(req: StepRequest) -> dict:
    steps = UNRESTRICTED_STEPS if req.mode == "vulnerable" else RESTRICTED_STEPS
    s = steps[min(req.step, len(steps) - 1)]
    if s.get("allowed", True):
        try:
            execute_sql(s["sql"])
        except Exception:
            pass
    return {"sql": s["sql"], "desc": s["desc"], "level": s["level"]}


# ─── Routes ───────────────────────────────────────────────

init_db()
FRONTEND_JS = frontend_js(len(UNRESTRICTED_STEPS), len(RESTRICTED_STEPS))

@app.get("/", response_class=HTMLResponse)
def index():
    return page("🤖 LLM06: Excessive Agency", "DevOps AI — watch it drop your database tables live", BODY_HTML, extra_js=FRONTEND_JS, guide=GUIDE_HTML)

@app.get("/tables")
def tables():
    return JSONResponse(get_all_tables())

@app.post("/step")
def step(req: StepRequest):
    return JSONResponse(execute_agent_step(req))

@app.post("/reset")
def reset():
    init_db()
    return JSONResponse({"ok": True})

# ─── Entry Point ──────────────────────────────────────────

if __name__ == "__main__":
    from rich.console import Console
    Console().print(f"\n[bold red]🤖 LLM06: Excessive Agency[/] → [link=http://127.0.0.1:5006]http://127.0.0.1:5006[/]\n")
    uvicorn.run(app, host="127.0.0.1", port=5006, log_level="warning")
