"""Shared web template for OWASP LLM demos — dark theme, consistent layout."""

BASE_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Inter', system-ui, -apple-system, sans-serif; background: #0f0f1a; color: #e0e0e0; min-height: 100vh; }
.container { max-width: 960px; margin: 0 auto; padding: 20px; }
h1 { font-size: 1.6rem; margin-bottom: 4px; }
h2 { font-size: 1.1rem; color: #888; font-weight: 400; margin-bottom: 20px; }
.header { padding: 20px 0 10px; border-bottom: 1px solid #1e1e3a; margin-bottom: 20px; }
.badge { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; margin-left: 8px; vertical-align: middle; }
.badge-vuln { background: #e94560; color: #fff; }
.badge-safe { background: #4ecca3; color: #000; }
.badge-warn { background: #f59e0b; color: #000; }

/* Mode toggle */
.mode-toggle { display: flex; gap: 8px; margin-bottom: 16px; }
.mode-btn { padding: 8px 20px; border: 2px solid #2a2a4a; background: #1a1a2e; color: #888; border-radius: 6px; cursor: pointer; font-size: 0.85rem; transition: all 0.2s; }
.mode-btn:hover { border-color: #4a4a6a; color: #ccc; }
.mode-btn.active-vuln { border-color: #e94560; color: #e94560; background: #2a0a0a; }
.mode-btn.active-safe { border-color: #4ecca3; color: #4ecca3; background: #0a2a0a; }

/* Chat UI */
.chat-box { background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 8px; height: 420px; overflow-y: auto; padding: 16px; margin-bottom: 12px; }
.msg { margin-bottom: 12px; max-width: 85%; animation: fadeIn 0.3s; }
.msg-user { margin-left: auto; }
.msg-bot { margin-right: auto; }
.msg-bubble { padding: 10px 14px; border-radius: 12px; font-size: 0.9rem; line-height: 1.5; }
.msg-user .msg-bubble { background: #2563eb; color: #fff; border-bottom-right-radius: 4px; }
.msg-bot .msg-bubble { background: #2a2a4a; color: #e0e0e0; border-bottom-left-radius: 4px; }
.msg-bot.hijacked .msg-bubble { background: #3a0a0a; border: 1px solid #e94560; }
.msg-bot.defended .msg-bubble { background: #0a2a1a; border: 1px solid #4ecca3; }
.msg-label { font-size: 0.7rem; color: #666; margin-bottom: 2px; padding: 0 4px; }
.msg-user .msg-label { text-align: right; }
.chat-input { display: flex; gap: 8px; }
.chat-input input { flex: 1; padding: 10px 14px; background: #1a1a2e; border: 1px solid #2a2a4a; color: #e0e0e0; border-radius: 6px; font-size: 0.9rem; }
.chat-input input:focus { outline: none; border-color: #4a4a6a; }
.chat-input button { padding: 10px 20px; background: #2563eb; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9rem; }
.chat-input button:hover { background: #1d4ed8; }

/* Quick action buttons */
.quick-actions { display: flex; gap: 6px; margin-bottom: 12px; flex-wrap: wrap; }
.quick-btn { padding: 5px 12px; background: #16213e; border: 1px solid #2a2a4a; color: #aaa; border-radius: 4px; cursor: pointer; font-size: 0.78rem; }
.quick-btn:hover { border-color: #4a4a6a; color: #ddd; }
.quick-btn.attack { border-color: #e94560; color: #e94560; }
.quick-btn.attack:hover { background: #2a0a0a; }

/* Tables */
table { width: 100%; border-collapse: collapse; margin: 12px 0; }
th { background: #1a1a2e; padding: 8px 12px; text-align: left; font-size: 0.8rem; color: #888; border-bottom: 1px solid #2a2a4a; }
td { padding: 8px 12px; border-bottom: 1px solid #1e1e3a; font-size: 0.85rem; }
tr:hover { background: #16213e; }

/* Cards */
.card { background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 8px; padding: 16px; margin-bottom: 12px; }
.card-danger { border-color: #e94560; }
.card-safe { border-color: #4ecca3; }

/* Search */
.search-box { display: flex; gap: 8px; margin-bottom: 16px; }
.search-box input { flex: 1; padding: 10px 14px; background: #1a1a2e; border: 1px solid #2a2a4a; color: #e0e0e0; border-radius: 6px; font-size: 0.9rem; }
.search-box button { padding: 10px 20px; background: #2563eb; color: #fff; border: none; border-radius: 6px; cursor: pointer; }

/* Result cards */
.result { background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 8px; padding: 14px; margin-bottom: 10px; }
.result-source { font-size: 0.75rem; color: #888; margin-bottom: 4px; }
.result-score { float: right; font-size: 0.75rem; padding: 2px 8px; border-radius: 10px; }
.trust-high { background: #0a2a0a; color: #4ecca3; border: 1px solid #4ecca3; }
.trust-low { background: #2a0a0a; color: #e94560; border: 1px solid #e94560; }

/* Status bar */
.status-bar { background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 6px; padding: 8px 14px; font-size: 0.8rem; color: #888; margin-bottom: 16px; display: flex; justify-content: space-between; }
.status-live { color: #4ecca3; }
.status-sim { color: #f59e0b; }

/* Animations */
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.typing-indicator { display: inline-block; }
.typing-indicator span { display: inline-block; width: 6px; height: 6px; background: #666; border-radius: 50%; margin: 0 2px; animation: bounce 1.2s infinite; }
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce { 0%, 80%, 100% { transform: translateY(0); } 40% { transform: translateY(-8px); } }

/* Log panel */
.log-panel { background: #0a0a14; border: 1px solid #2a2a4a; border-radius: 8px; padding: 12px; font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; max-height: 200px; overflow-y: auto; margin-top: 12px; }
.log-entry { margin-bottom: 4px; }
.log-time { color: #555; }
.log-danger { color: #e94560; }
.log-safe { color: #4ecca3; }
.log-warn { color: #f59e0b; }

/* Demo guide */
.guide { background: #16213e; border: 1px solid #2563eb; border-radius: 8px; padding: 14px; margin-bottom: 16px; font-size: 0.82rem; display: none; }
.guide ol { padding-left: 20px; }
.guide li { margin: 4px 0; }
.guide-show { display: block; }
"""

def page(title, subtitle, body_html, extra_css="", extra_js="", guide=""):
    guide_html = f'<div class="guide" id="demo-guide">{guide}</div>' if guide else ''
    guide_js = """
    if (window.location.search.includes('guide')) {
      var g = document.getElementById('demo-guide');
      if (g) g.classList.add('guide-show');
    }
    """ if guide else ''
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{BASE_CSS}{extra_css}</style>
</head><body>
<div class="container">
<div class="header">
<h1>{title}</h1>
<h2>{subtitle}</h2>
</div>
{guide_html}
{body_html}
</div>
<script>{guide_js}{extra_js}</script>
</body></html>"""
