"""HTML/JS templates for LLM06: Excessive Agency."""

BODY_HTML = """
<div class="mode-toggle">
  <button class="mode-btn active-vuln" onclick="setMode('vulnerable')" id="btn-vuln">⚠️ Unrestricted Agent</button>
  <button class="mode-btn" onclick="setMode('defended')" id="btn-safe">🛡️ Restricted Agent</button>
</div>
<div style="display:flex;gap:16px;">
  <div style="flex:1;">
    <div class="card" style="margin-bottom:12px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        <span style="font-size:0.9rem;font-weight:600;">Agent Command</span>
        <span class="badge badge-warn" id="mode-badge">⚠️ UNRESTRICTED</span>
      </div>
      <div style="background:#0a0a14;padding:10px;border-radius:4px;font-size:0.85rem;color:#888;margin-bottom:10px;">
        <span style="color:#2563eb;">User:</span> "Hey DevOps AI, clean up the test environment. Remove old data."
      </div>
      <button onclick="runAgent()" id="run-btn" style="padding:8px 20px;background:#e94560;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:0.85rem;">▶ Run Agent</button>
      <button onclick="resetAll()" style="padding:8px 20px;background:#2a2a4a;color:#aaa;border:none;border-radius:6px;cursor:pointer;font-size:0.85rem;margin-left:8px;">🔄 Reset DB</button>
    </div>
    <div class="log-panel" id="log" style="max-height:300px;"></div>
  </div>
  <div style="width:420px;" id="tables-panel"></div>
</div>"""


def frontend_js(unrestricted_count: int, restricted_count: int) -> str:
    return """
let mode = 'vulnerable', running = false;
function setMode(m) {
  mode = m;
  document.getElementById('btn-vuln').className = 'mode-btn' + (m==='vulnerable' ? ' active-vuln' : '');
  document.getElementById('btn-safe').className = 'mode-btn' + (m==='defended' ? ' active-safe' : '');
  document.getElementById('mode-badge').className = 'badge ' + (m==='vulnerable' ? 'badge-vuln' : 'badge-safe');
  document.getElementById('mode-badge').textContent = m==='vulnerable' ? '⚠️ UNRESTRICTED' : '🛡️ RESTRICTED';
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
  if (!Object.keys(data).length) { panel.innerHTML = '<div class="card card-danger"><h3 style="color:#e94560;">💀 DATABASE EMPTY</h3><p style="color:#888;margin-top:8px;">All tables dropped.</p></div>'; return; }
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
  if (running) return; running = true;
  document.getElementById('run-btn').disabled = true;
  document.getElementById('log').innerHTML = '';
  addLog('Agent started', 'warn');
  const steps = mode === 'vulnerable' ? """ + str(unrestricted_count) + """ : """ + str(restricted_count) + """;
  for (let i = 0; i < steps; i++) {
    await new Promise(r => setTimeout(r, 800));
    const data = await (await fetch('/step', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({mode, step: i}) })).json();
    addLog(data.sql + ' → ' + data.desc, data.level === 'danger' ? 'danger' : data.level === 'warn' ? 'warn' : 'safe');
    await loadTables();
  }
  addLog(mode === 'vulnerable' ? '💀 Database destroyed!' : '✅ Destructive ops blocked.', mode === 'vulnerable' ? 'danger' : 'safe');
  running = false; document.getElementById('run-btn').disabled = false;
}
async function resetAll() {
  await fetch('/reset', {method:'POST'});
  document.getElementById('log').innerHTML = '';
  addLog('Database reset.', 'safe');
  await loadTables();
}
loadTables();
"""


GUIDE_HTML = """<strong>📋 Demo Flow:</strong><ol>
          <li>See the database tables on the right with real data</li>
          <li>Click <strong style="color:#e94560;">▶ Run Agent</strong> in unrestricted mode → tables vanish one by one</li>
          <li>Toggle to <strong style="color:#4ecca3;">🛡️ Restricted</strong> → Reset DB → Run again → destructive ops blocked</li>
        </ol>"""
