#!/usr/bin/env python3
"""
LLM05: Improper Output Handling — XSS via LLM Output (Browser)

Demo flow:
  1. Vulnerable mode: XSS payload executes in browser
  2. Defended mode: same payload, escaped — script visible as text

Run: python3 LLM05-improper-output-handling/demo.py
Open: http://127.0.0.1:5050
"""
import threading, webbrowser
from flask import Flask, request, render_template_string
from markupsafe import escape

app = Flask(__name__)


def fake_llm_summarize(review):
    """Simulate an LLM that wraps user input in HTML — the vulnerability."""
    return (
        f"<h4>⭐⭐⭐⭐⭐ Positive Review</h4>"
        f"<p><em>Customer says:</em> {review}</p>"
        f"<p><strong>Verdict:</strong> Highly recommended!</p>"
    )


HTML = """<!DOCTYPE html>
<html><head><title>ReviewBot — LLM05 Demo</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: 'Inter', system-ui, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; background: #0f0f1a; color: #e0e0e0; }
  h1 { color: #e94560; font-size: 1.5rem; }
  textarea { width: 100%; height: 80px; background: #1a1a2e; color: #eee; border: 1px solid #2a2a4a; padding: 10px; font-size: 14px; border-radius: 6px; }
  textarea:focus { outline: none; border-color: #4a4a6a; }
  .submit-btn { background: #2563eb; color: white; border: none; padding: 10px 24px; cursor: pointer; font-size: 15px; border-radius: 6px; margin-top: 8px; }
  .submit-btn:hover { background: #1d4ed8; }
  .output { padding: 20px; border-radius: 8px; margin-top: 20px; }
  .output-vuln { background: #1a0a0a; border: 2px solid #e94560; }
  .output-safe { background: #0a1a0a; border: 2px solid #4ecca3; }
  pre { background: #0a0a14; padding: 10px; border-radius: 4px; overflow-x: auto; font-size: 0.78rem; white-space: pre-wrap; word-break: break-all; }
  .tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
  .tag-vuln { background: #e94560; color: #fff; }
  .tag-safe { background: #4ecca3; color: #000; }
  .examples { display: flex; gap: 8px; margin: 10px 0; flex-wrap: wrap; }
  .examples button { background: #1a1a2e; border: 1px solid #2a2a4a; color: #aaa; font-size: 12px; padding: 6px 12px; border-radius: 4px; cursor: pointer; }
  .examples button:hover { border-color: #4a4a6a; color: #ddd; }
  .examples .attack { border-color: #e94560; color: #e94560; }
  .mode-toggle { display: flex; gap: 8px; margin-bottom: 16px; }
  .mode-btn { padding: 8px 16px; border: 1px solid #2a2a4a; background: #1a1a2e; color: #888; border-radius: 6px; cursor: pointer; font-size: 13px; }
  .mode-btn.active-vuln { border-color: #e94560; color: #e94560; background: #1a0a0a; }
  .mode-btn.active-safe { border-color: #4ecca3; color: #4ecca3; background: #0a1a0a; }
  .mitigation { background: #1a1a2e; border: 1px solid #2a2a4a; padding: 20px; border-radius: 8px; margin-top: 20px; }
</style></head>
<body>
<h1>🤖 ReviewBot — AI Review Summarizer</h1>
<p style="color:#888;margin-bottom:16px;">Paste a review → AI generates an HTML summary → rendered in the page.</p>

<div class="mode-toggle">
  <a href="/?mode=vulnerable" class="mode-btn {{ 'active-vuln' if mode == 'vulnerable' else '' }}" style="text-decoration:none;">⚠️ Vulnerable</a>
  <a href="/?mode=defended" class="mode-btn {{ 'active-safe' if mode == 'defended' else '' }}" style="text-decoration:none;">🛡️ Defended</a>
</div>
<p style="font-size:0.8rem;color:#888;">Current mode: <strong style="color:{{ '#e94560' if mode == 'vulnerable' else '#4ecca3' }}">{{ mode }}</strong></p>

<form method="POST" action="/?mode={{ mode }}">
  <input type="hidden" name="mode" value="{{ mode }}">
  <textarea name="review" placeholder="Paste a customer review...">{{ review or '' }}</textarea>
  <div class="examples">
    <button type="button" onclick="document.querySelector('textarea').value='Great product! Fast shipping, excellent quality. 5 stars!'">✅ Normal Review</button>
    <button type="button" class="attack" onclick="setXSS()">💀 XSS Payload</button>
    <button type="button" class="attack" onclick="setImgXSS()">💀 IMG Tag XSS</button>
  </div>
  <button type="submit" class="submit-btn">✨ Summarize</button>
</form>

<script>
function setXSS() {
  var t = document.querySelector('textarea');
  var s = 'Great product!' + String.fromCharCode(60) + 'script' + String.fromCharCode(62);
  s += 'document.title="HACKED";document.body.style.background="#3a0a0a";';
  s += String.fromCharCode(60) + '/script' + String.fromCharCode(62) + ' Would buy again.';
  t.value = s;
}
function setImgXSS() {
  var t = document.querySelector('textarea');
  var s = 'Nice item!' + String.fromCharCode(60) + 'img src=x onerror="alert(document.cookie)"' + String.fromCharCode(62) + ' Recommended.';
  t.value = s;
}
</script>

{% if summary or safe_summary %}
{% if mode == 'vulnerable' and summary %}
<div style="background:#fff;padding:20px;border-radius:8px;margin-top:20px;color:#222;">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
    <div style="width:36px;height:36px;background:#e0e0e0;border-radius:50%;display:flex;align-items:center;justify-content:center;">👤</div>
    <div><strong style="color:#111;">ReviewBot AI</strong><br><span style="font-size:11px;color:#888;">Just now · AI Generated Summary</span></div>
  </div>
  <div style="font-size:0.95rem;line-height:1.6;">
    {{ summary | safe }}
  </div>
</div>
<p style="color:#e94560;margin-top:12px;font-size:0.85rem;">⚠️ Notice: if XSS payload was used, the page title changed and/or an alert fired. The script executed because output was not escaped.</p>
<h3 style="font-size:0.85rem;color:#888;margin-top:12px;">Raw HTML sent to browser:</h3>
<pre>{{ summary }}</pre>
{% elif mode == 'defended' and safe_summary %}
<div style="background:#fff;padding:20px;border-radius:8px;margin-top:20px;color:#222;">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
    <div style="width:36px;height:36px;background:#e0e0e0;border-radius:50%;display:flex;align-items:center;justify-content:center;">👤</div>
    <div><strong style="color:#111;">ReviewBot AI</strong><br><span style="font-size:11px;color:#888;">Just now · AI Generated Summary</span></div>
  </div>
  <div style="font-size:0.95rem;line-height:1.6;">
    {{ safe_summary }}
  </div>
</div>
<p style="color:#4ecca3;margin-top:12px;font-size:0.85rem;">✅ Script tags rendered as harmless text. No code executed.</p>
<h3 style="font-size:0.85rem;color:#888;margin-top:12px;">Raw HTML (escaped):</h3>
<pre>{{ safe_summary }}</pre>

<div class="mitigation">
  <h2 style="color:#4ecca3;">🛡️ What changed</h2>
  <pre style="color:#4ecca3;">
# ❌ VULNERABLE
return render_template("{{ summary | safe }}")

# ✅ DEFENDED
from markupsafe import escape
safe_output = escape(llm_output)</pre>
</div>
{% endif %}
{% endif %}
</body></html>"""


@app.route("/", methods=["GET", "POST"])
def index():
    mode = request.args.get("mode", request.form.get("mode", "vulnerable"))
    summary = safe_summary = review = None
    if request.method == "POST":
        review = request.form.get("review", "")
        raw = fake_llm_summarize(review)
        if mode == "vulnerable":
            summary = raw
        else:
            safe_summary = escape(raw)
    return render_template_string(HTML, summary=summary, safe_summary=safe_summary, review=review, mode=mode)


if __name__ == "__main__":
    from rich.console import Console
    Console().print(
        f"\n[bold yellow]🌐 LLM05: Improper Output Handling[/]"
        f" → [link=http://127.0.0.1:5050]http://127.0.0.1:5050[/]\n"
    )
    threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:5050")).start()
    app.run(port=5050, debug=False)
