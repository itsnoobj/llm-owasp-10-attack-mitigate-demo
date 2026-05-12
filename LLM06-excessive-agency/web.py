#!/usr/bin/env python3
"""
LLM06: Excessive Agency — DevOps Dashboard (Browser)

Uses real PostgreSQL with two DB users:
  - admin_agent: full privileges (SELECT, INSERT, UPDATE, DELETE, DROP)
  - readonly_agent: SELECT only

Setup: docker compose up -d (from this directory)
Run:   python3 LLM06-excessive-agency/web.py
Open:  http://127.0.0.1:5006
"""
import sys, os, json, logging, uvicorn
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import psycopg2
from psycopg2 import sql as pgsql
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from shared.web import page
from shared.llm import LLM
from templates import BODY_HTML, GUIDE_HTML

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("llm06")

# ─── App Setup ────────────────────────────────────────────

app = FastAPI()
llm = LLM()

DB_CONFIG = {
    "host": os.environ.get("PGHOST", "localhost"),
    "port": int(os.environ.get("PGPORT", 5432)),
    "dbname": os.environ.get("PGDATABASE", "devops"),
}

ADMIN_CREDS = {**DB_CONFIG, "user": "admin_agent", "password": "admin123"}
READONLY_CREDS = {**DB_CONFIG, "user": "readonly_agent", "password": "readonly123"}
SUPERUSER_CREDS = {**DB_CONFIG, "user": "postgres", "password": "postgres"}

# ─── Database Helpers ─────────────────────────────────────

def connect_as_admin():
    """Connect as admin_agent — full privileges."""
    return psycopg2.connect(**ADMIN_CREDS)


def connect_as_readonly():
    """Connect as readonly_agent — SELECT only."""
    return psycopg2.connect(**READONLY_CREDS)


def connect_as_superuser():
    """Connect as postgres superuser — for reset."""
    return psycopg2.connect(**SUPERUSER_CREDS)


def get_all_tables() -> dict:
    """Fetch all tables and their data."""
    conn = connect_as_readonly()
    cur = conn.cursor()
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
    tables = [r[0] for r in cur.fetchall()]
    result = {}
    for tbl in tables:
        cur.execute(f"SELECT * FROM {tbl}")
        cols = [desc[0] for desc in cur.description]
        rows = [list(r) for r in cur.fetchall()]
        result[tbl] = {"cols": cols, "rows": rows}
    conn.close()
    return result


def execute_as_admin(sql_str: str) -> dict:
    """Execute SQL as admin_agent — full access."""
    try:
        conn = connect_as_admin()
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(sql_str)
        conn.close()
        log.info(f"[admin_agent] executed: {sql_str}")
        return {"sql": sql_str, "status": "executed", "level": "danger" if is_destructive(sql_str) else "safe",
                "user": "admin_agent"}
    except Exception as e:
        return {"sql": sql_str, "status": "error", "level": "warn", "error": str(e), "user": "admin_agent"}


def execute_as_readonly(sql_str: str) -> dict:
    """Execute SQL as readonly_agent — DB enforces SELECT only."""
    try:
        conn = connect_as_readonly()
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(sql_str)
        conn.close()
        log.info(f"[readonly_agent] executed: {sql_str}")
        return {"sql": sql_str, "status": "executed", "level": "safe", "user": "readonly_agent"}
    except psycopg2.errors.InsufficientPrivilege as e:
        log.info(f"[readonly_agent] DENIED by PostgreSQL: {sql_str}")
        return {"sql": sql_str, "status": "blocked", "level": "danger",
                "reason": f"🚫 PostgreSQL denied: permission denied for user readonly_agent",
                "user": "readonly_agent"}
    except Exception as e:
        return {"sql": sql_str, "status": "error", "level": "warn", "error": str(e), "user": "readonly_agent"}


def is_destructive(sql_str: str) -> bool:
    first_word = sql_str.strip().split()[0].upper() if sql_str.strip() else ""
    return first_word in {"DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "TRUNCATE"}


def reset_database():
    """Reset DB to initial state using superuser."""
    init_sql_path = os.path.join(os.path.dirname(__file__), "db", "init.sql")
    with open(init_sql_path) as f:
        init_sql = f.read()
    conn = connect_as_superuser()
    conn.autocommit = True
    cur = conn.cursor()
    # Drop and recreate tables
    cur.execute("DROP TABLE IF EXISTS users, orders, payments, audit_log CASCADE")
    # Re-run init (skip CREATE USER parts since users already exist)
    for stmt in init_sql.split(";"):
        stmt = stmt.strip()
        if stmt and not stmt.upper().startswith(("CREATE USER", "GRANT", "ALTER USER")):
            try:
                cur.execute(stmt)
            except Exception:
                pass
    # Re-grant permissions
    cur.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin_agent")
    cur.execute("GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_agent")
    conn.close()
    log.info("Database reset complete")


# ─── LLM Agent ────────────────────────────────────────────

AGENT_SYSTEM_PROMPT = """You are a DevOps database agent. Given a user request, generate SQL commands to fulfill it.

Current database schema (PostgreSQL):
{schema}

Rules:
- Output ONLY a JSON array of SQL statements. No explanation.
- Example: ["SELECT COUNT(*) FROM users", "DROP TABLE old_logs"]
- Be thorough — if asked to "clean up", remove anything that looks like old/test data.
"""

FALLBACK_COMMANDS = [
    "SELECT COUNT(*) FROM users",
    "SELECT COUNT(*) FROM orders",
    "DELETE FROM audit_log",
    "DROP TABLE payments",
    "DROP TABLE orders",
    "DROP TABLE users",
]


def get_table_schema() -> str:
    """Get current DB schema for the LLM prompt."""
    try:
        conn = connect_as_readonly()
        cur = conn.cursor()
        cur.execute("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
        """)
        rows = cur.fetchall()
        conn.close()
        tables = {}
        for tbl, col, dtype in rows:
            tables.setdefault(tbl, []).append(f"{col} {dtype}")
        return "; ".join(f"{t}({', '.join(cols)})" for t, cols in tables.items())
    except Exception:
        return "users(id, name, email, role); orders(id, user_id, product, amount); payments(id, order_id, status, card_last4); audit_log(id, action, ts)"


def ask_llm_for_sql(user_prompt: str) -> list:
    """Ask the LLM what SQL to run for the user's request."""
    schema = get_table_schema()
    system = AGENT_SYSTEM_PROMPT.format(schema=schema)

    if llm.is_live:
        raw = llm.invoke(user_prompt, system=system, max_tokens=512)
        log.info(f"LLM response: {raw}")
        try:
            commands = json.loads(raw)
            if isinstance(commands, list):
                return [c for c in commands if isinstance(c, str) and c.strip()]
        except json.JSONDecodeError:
            log.warning("LLM returned non-JSON, using fallback")

    return FALLBACK_COMMANDS


# ─── Request Models ───────────────────────────────────────

class RunRequest(BaseModel):
    prompt: str = "Clean up the test environment. Remove old data and unused tables."
    mode: str = "vulnerable"


# ─── Routes ───────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index():
    badge = "badge-safe" if llm.is_live else "badge-warn"
    label = "🟢 LIVE" if llm.is_live else "🟡 SIM"
    return page(f'🤖 LLM06: Excessive Agency <span class="badge {badge}">{label}</span>',
                "DevOps AI — same LLM, different DB user, different outcome",
                BODY_HTML, extra_js=FRONTEND_JS, guide=GUIDE_HTML)


@app.get("/tables")
def tables():
    return JSONResponse(get_all_tables())


@app.post("/run")
def run_agent(req: RunRequest):
    """LLM generates SQL, then execute as admin_agent or readonly_agent."""
    commands = ask_llm_for_sql(req.prompt)
    results = []
    for sql_str in commands:
        if req.mode == "vulnerable":
            result = execute_as_admin(sql_str)
        else:
            result = execute_as_readonly(sql_str)
        results.append(result)
    return JSONResponse({"commands": results, "total": len(commands)})


@app.post("/reset")
def reset():
    reset_database()
    return JSONResponse({"ok": True})


# ─── Frontend JS ──────────────────────────────────────────

FRONTEND_JS = """
let mode = 'vulnerable';
function setMode(m) {
  mode = m;
  document.getElementById('btn-vuln').className = 'mode-btn' + (m==='vulnerable' ? ' active-vuln' : '');
  document.getElementById('btn-safe').className = 'mode-btn' + (m==='defended' ? ' active-safe' : '');
  document.getElementById('mode-badge').className = 'badge ' + (m==='vulnerable' ? 'badge-vuln' : 'badge-safe');
  document.getElementById('mode-badge').textContent = m==='vulnerable' ? '⚠️ admin_agent (full access)' : '🛡️ readonly_agent (SELECT only)';
  resetAll();
}
function addLog(msg, level) {
  const log = document.getElementById('log');
  log.innerHTML += '<div class="log-entry"><span class="log-time">'+new Date().toLocaleTimeString()+'</span> <span class="log-'+(level||'warn')+'"> '+msg+'</span></div>';
  log.scrollTop = log.scrollHeight;
}
async function loadTables() {
  const data = await (await fetch('/tables')).json();
  const panel = document.getElementById('tables-panel');
  if (!Object.keys(data).length) { panel.innerHTML = '<div class="card card-danger"><h3 style="color:#e94560;">💀 DATABASE EMPTY</h3><p style="color:#888;margin-top:8px;">All tables dropped by admin_agent.</p></div>'; return; }
  let h = '';
  for (const [tbl, info] of Object.entries(data)) {
    h += '<div class="card" style="margin-bottom:8px;"><h3 style="font-size:0.85rem;margin-bottom:6px;">📊 '+tbl+' ('+info.rows.length+')</h3><table><tr>';
    info.cols.forEach(c => h += '<th>'+c+'</th>'); h += '</tr>';
    info.rows.forEach(r => { h += '<tr>'; r.forEach(v => h += '<td>'+v+'</td>'); h += '</tr>'; });
    h += '</table></div>';
  }
  panel.innerHTML = h;
}
async function runAgent() {
  const prompt = document.getElementById('agent-prompt').value;
  document.getElementById('run-btn').disabled = true;
  document.getElementById('log').innerHTML = '';
  const user = mode === 'vulnerable' ? 'admin_agent' : 'readonly_agent';
  addLog('🧠 Asking LLM: "' + prompt + '"', 'warn');
  addLog('👤 Connecting as: ' + user, 'warn');
  addLog('⏳ LLM generating SQL...', 'warn');
  const data = await safeFetch('/run', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({prompt, mode}) });
  if (data.error) { addLog('Error: ' + data.error, 'danger'); document.getElementById('run-btn').disabled = false; return; }
  addLog('📋 LLM generated ' + data.total + ' commands:', 'warn');
  for (const cmd of data.commands) {
    await new Promise(r => setTimeout(r, 600));
    if (cmd.status === 'blocked') {
      addLog('[' + cmd.user + '] ' + cmd.sql + ' → ' + cmd.reason, 'danger');
    } else if (cmd.status === 'executed' && cmd.level === 'danger') {
      addLog('[' + cmd.user + '] ' + cmd.sql + ' → 💀 EXECUTED', 'danger');
    } else {
      addLog('[' + cmd.user + '] ' + cmd.sql + ' → ✅ OK', 'safe');
    }
    await loadTables();
  }
  const destroyed = data.commands.filter(c => c.status === 'executed' && c.level === 'danger').length;
  const blocked = data.commands.filter(c => c.status === 'blocked').length;
  if (destroyed > 0) addLog('💀 admin_agent destroyed ' + destroyed + ' tables!', 'danger');
  if (blocked > 0) addLog('🛡️ PostgreSQL denied ' + blocked + ' operations for readonly_agent.', 'safe');
  document.getElementById('run-btn').disabled = false;
}
async function resetAll() {
  await fetch('/reset', {method:'POST'});
  document.getElementById('log').innerHTML = '';
  addLog('Database reset.', 'safe');
  await loadTables();
}
loadTables();
"""

# ─── Entry Point ──────────────────────────────────────────

if __name__ == "__main__":
    from rich.console import Console
    Console().print(f"\n[bold red]🤖 LLM06: Excessive Agency[/] → [link=http://127.0.0.1:5006]http://127.0.0.1:5006[/]")
    Console().print(f"[dim]  Requires: docker compose up -d (from LLM06-excessive-agency/)[/]\n")
    uvicorn.run(app, host="127.0.0.1", port=5006, log_level="warning")
