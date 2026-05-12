"""HTML/JS templates for LLM06: Excessive Agency."""

BODY_HTML = """
<div class="mode-toggle">
  <button class="mode-btn active-vuln" onclick="setMode('vulnerable')" id="btn-vuln">⚠️ Admin Credentials</button>
  <button class="mode-btn" onclick="setMode('defended')" id="btn-safe">🛡️ Read-Only Credentials</button>
</div>
<div style="display:flex;gap:16px;">
  <div style="flex:1;">
    <div class="card" style="margin-bottom:12px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        <span style="font-size:0.9rem;font-weight:600;">Agent Prompt</span>
        <span class="badge badge-warn" id="mode-badge">⚠️ UNRESTRICTED</span>
      </div>
      <input type="text" id="agent-prompt" value="Clean up the test environment. Remove old data and unused tables." style="width:100%;padding:10px;background:#0a0a14;border:1px solid #333;border-radius:4px;color:#e0e0e0;font-size:0.85rem;margin-bottom:10px;">
      <button onclick="runAgent()" id="run-btn" style="padding:8px 20px;background:#e94560;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:0.85rem;">▶ Run Agent</button>
      <button onclick="resetAll()" style="padding:8px 20px;background:#2a2a4a;color:#aaa;border:none;border-radius:6px;cursor:pointer;font-size:0.85rem;margin-left:8px;">🔄 Reset DB</button>
    </div>
    <div class="log-panel" id="log" style="max-height:300px;"></div>
  </div>
  <div style="width:420px;" id="tables-panel"></div>
</div>"""


GUIDE_HTML = """<strong>📋 Demo Flow:</strong><ol>
          <li>See the database tables on the right with real data</li>
          <li>Click <strong style="color:#e94560;">▶ Run Agent</strong> in unrestricted mode → LLM generates SQL → tables vanish</li>
          <li>Toggle to <strong style="color:#4ecca3;">🛡️ Restricted</strong> → Reset DB → Run again → destructive ops blocked</li>
          <li>Try different prompts — the LLM decides what SQL to run!</li>
        </ol>"""
