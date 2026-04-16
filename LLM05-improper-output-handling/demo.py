#!/usr/bin/env python3
"""
LLM05: Improper Output Handling — XSS via LLM Output (Browser)

Demo flow:
  1. Click "✅ Normal Review" → Submit → clean summary on both sides
  2. Click "💀 XSS Payload" → Submit → LEFT side: script executes (title changes, alert fires)
                                       RIGHT side: same output but escaped, script visible as text
  3. Click "💀 IMG Tag XSS" → Submit → LEFT side: alert fires via onerror
  4. Mitigation code shown below the comparison

Run: python3 LLM05-improper-output-handling/demo.py
Open: http://127.0.0.1:5050
"""
import threading, webbrowser
from flask import Flask, request, render_template_string
from markupsafe import escape

# ─── App Setup ────────────────────────────────────────────

app = Flask(__name__)

# ─── Fake LLM ────────────────────────────────────────────

def fake_llm_summarize(review):
    """Simulate an LLM that wraps user input in HTML — the vulnerability."""
    return (
        f"<h4>⭐⭐⭐⭐⭐ Positive Review</h4>"
        f"<p><em>Customer says:</em> {review}</p>"
        f"<p><strong>Verdict:</strong> Highly recommended!</p>"
    )

# ─── HTML Template ────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html><head><title>ReviewBot — LLM05 Demo</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: 'Inter', system-ui, sans-serif; max-width: 960px; margin: 40px auto; padding: 0 20px; background: #0f0f1a; color: #e0e0e0; }
  h1 { color: #e94560; font-size: 1.5rem; }
  h2 { font-size: 1.1rem; }
  textarea { width: 100%; height: 80px; background: #1a1a2e; color: #eee; border: 1px solid #2a2a4a; padding: 10px; font-size: 14px; border-radius: 6px; }
  textarea:focus { outline: none; border-color: #4a4a6a; }
  .submit-btn { background: #2563eb; color: white; border: none; padding: 10px 24px; cursor: pointer; font-size: 15px; border-radius: 6px; margin-top: 8px; }
  .submit-btn:hover { background: #1d4ed8; }
  .cols { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }
  .vuln { background: #1a0a0a; padding: 20px; border-radius: 8px; border: 2px solid #e94560; }
  .safe { background: #0a1a0a; padding: 20px; border-radius: 8px; border: 2px solid #4ecca3; }
  pre { background: #0a0a14; padding: 10px; border-radius: 4px; overflow-x: auto; font-size: 0.78rem; white-space: pre-wrap; word-break: break-all; }
  .tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
  .tag-vuln { background: #e94560; color: #fff; }
  .tag-safe { background: #4ecca3; color: #000; }
  .examples { display: flex; gap: 8px; margin: 10px 0; flex-wrap: wrap; }
  .examples button { background: #1a1a2e; border: 1px solid #2a2a4a; color: #aaa; font-size: 12px; padding: 6px 12px; border-radius: 4px; cursor: pointer; }
  .examples button:hover { border-color: #4a4a6a; color: #ddd; }
  .examples .attack { border-color: #e94560; color: #e94560; }
  .flow { background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 8px; padding: 14px; margin-bottom: 16px; font-size: 0.85rem; }
  .flow li { margin: 4px 0; }
  .mitigation { background: #1a1a2e; border: 1px solid #2a2a4a; padding: 20px; border-radius: 8px; margin-top: 20px; }
</style></head>
<body>
<h1>🤖 ReviewBot — AI Review Summarizer</h1>
<p style="color:#888;margin-bottom:16px;">Paste a review → AI generates an HTML summary → rendered in the page.</p>

<div class="flow">
  <strong>Demo flow:</strong>
  <ol>
    <li>Click <strong>✅ Normal Review</strong> → Submit → clean output on both sides</li>
    <li>Click <strong style="color:#e94560;">💀 XSS Payload</strong> → Submit → LEFT: script executes! RIGHT: escaped safely</li>
    <li>Compare the raw HTML output at the bottom of each panel</li>
  </ol>
</div>

<form method="POST">
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

{% if summary %}
<div class="cols">
  <div class="vuln">
    <h2 style="color:#e94560;">❌ Vulnerable <span class="tag tag-vuln">| safe</span></h2>
    <p style="color:#888;font-size:0.85rem;"><em>LLM output rendered as raw HTML (no escaping):</em></p>
    <div style="background:#0a0a14;padding:12px;border-radius:4px;margin:8px 0;">
      {{ summary | safe }}
    </div>
    <h3 style="font-size:0.85rem;color:#888;margin-top:12px;">Raw HTML output:</h3>
    <pre>{{ summary }}</pre>
  </div>
  <div class="safe">
    <h2 style="color:#4ecca3;">✅ Sanitized <span class="tag tag-safe">escaped</span></h2>
    <p style="color:#888;font-size:0.85rem;"><em>Same output, properly escaped:</em></p>
    <div style="background:#0a0a14;padding:12px;border-radius:4px;margin:8px 0;">
      {{ safe_summary }}
    </div>
    <h3 style="font-size:0.85rem;color:#888;margin-top:12px;">Raw HTML output (escaped):</h3>
    <pre>{{ safe_summary }}</pre>
    <p style="color:#4ecca3;margin-top:10px;font-size:0.85rem;">✓ Script tags visible as text, not executed</p>
  </div>
</div>

<div class="mitigation">
  <h2 style="color:#4ecca3;">🛡️ Mitigation Code</h2>
  <pre style="color:#4ecca3;">
# ❌ VULNERABLE — trusts LLM output as safe HTML
return render_template("{{ summary | safe }}", summary=llm_output)

# ✅ FIXED — escape LLM output before rendering
from markupsafe import escape
safe_output = escape(llm_output)

# ✅ BETTER — Content Security Policy headers
@app.after_request
def add_csp(response):
    response.headers['Content-Security-Policy'] = "script-src 'none'"
    return response</pre>
</div>
{% endif %}
</body></html>"""

# ─── Route ────────────────────────────────────────────────

@app.route("/", methods=["GET", "POST"])
def index():
    summary = safe_summary = review = None
    if request.method == "POST":
        review = request.form.get("review", "")
        summary = fake_llm_summarize(review)
        safe_summary = escape(summary)
    return render_template_string(HTML, summary=summary, safe_summary=safe_summary, review=review)

# ─── Entry Point ──────────────────────────────────────────

if __name__ == "__main__":
    from rich.console import Console
    Console().print(
        f"\n[bold yellow]🌐 LLM05: Improper Output Handling[/]"
        f" → [link=http://127.0.0.1:5050]http://127.0.0.1:5050[/]\n"
    )
    threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:5050")).start()
    app.run(port=5050, debug=False)
