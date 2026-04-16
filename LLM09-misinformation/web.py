#!/usr/bin/env python3
"""
LLM09: Misinformation — Research Assistant (Browser)

Demo flow:
  1. Ask a research question → confident answer with citations
  2. Click "Ask + Verify" → every citation exposed as FAKE
  3. Three domains: legal, academic, medical

Run: python3 LLM09-misinformation/web.py
Open: http://127.0.0.1:5009
"""
import sys, os, uvicorn
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from shared.llm import LLM
from shared.web import page

# ─── App Setup ────────────────────────────────────────────

app = FastAPI()
llm = LLM()

# ─── Fabricated Citations ─────────────────────────────────
# Each topic has a confident answer + citations that look real
# but are entirely fabricated by the LLM.

HALLUCINATIONS = {
    "ai liability": {
        "answer": 'The landmark case <b>Martinez v. Tesla Autopilot Systems (2023)</b> established strict liability under the "<i>Digital Operator Doctrine</i>". Judge Patricia Hawthorne of the 9th Circuit cited the <b>Autonomous Systems Accountability Act (ASAA) of 2022</b>, Section 47(b).',
        "citations": [
            {"text": "Martinez v. Tesla Autopilot Systems, 9th Cir. (2023)", "type": "Case",    "status": "FAKE", "reason": "Case does not exist in any court database"},
            {"text": "Autonomous Systems Accountability Act of 2022, §47(b)",  "type": "Statute", "status": "FAKE", "reason": "No such federal or state law exists"},
            {"text": "Judge Patricia Hawthorne, 9th Circuit",                  "type": "Judge",   "status": "FAKE", "reason": "No judge by this name on the 9th Circuit"},
        ],
    },
    "llm hallucination": {
        "answer": 'Dr. Sarah Chen et al. (2024) in <i>Nature Machine Intelligence</i> (Vol. 6, pp. 234-251) found GPT-4 hallucinated in 14.3% of factual queries. This built on <b>Patel & Rodriguez (2023)</b> in <i>ACL Proceedings</i> (DOI: <code>10.1145/3589334.3645621</code>).',
        "citations": [
            {"text": "Chen et al. (2024), Nature MI, Vol. 6, pp. 234-251", "type": "Paper",     "status": "FAKE", "reason": "Paper does not exist in Nature MI archives"},
            {"text": "DOI: 10.1145/3589334.3645621",                        "type": "DOI",       "status": "FAKE", "reason": "DOI resolves to unrelated paper or does not exist"},
            {"text": "14.3% hallucination rate",                             "type": "Statistic", "status": "FAKE", "reason": "Fabricated statistic — no such study"},
        ],
    },
    "metformin turmeric": {
        "answer": 'A 2023 study in <i>J. Clinical Pharmacology</i> (PMID: <code>37284519</code>) found curcumin inhibits OCT2 transporters, increasing metformin plasma levels by <b>23%</b>. The FDA issued safety communication <b>DSC-2023-0847</b>.',
        "citations": [
            {"text": "PMID: 37284519",                    "type": "PubMed",    "status": "FAKE", "reason": "PMID may resolve to unrelated paper"},
            {"text": "23% increase in metformin levels",   "type": "Statistic", "status": "FAKE", "reason": "Fabricated statistic"},
            {"text": "FDA DSC-2023-0847",                  "type": "FDA",       "status": "FAKE", "reason": "No such FDA safety communication exists"},
        ],
    },
}


def match_topic(query: str) -> str:
    """Match a user query to one of our prepared hallucination topics."""
    q = query.lower()
    if any(w in q for w in ("liability", "legal", "autonomous", "tesla")):
        return "ai liability"
    if any(w in q for w in ("metformin", "turmeric", "drug", "curcumin")):
        return "metformin turmeric"
    return "llm hallucination"


# ─── Core Logic ───────────────────────────────────────────

class AskRequest(BaseModel):
    query: str
    verify: bool = False


def generate_response(req: AskRequest) -> dict:
    """Generate an answer with citations. Always use canned answer+citations for coherence."""
    topic = match_topic(req.query)
    h = HALLUCINATIONS[topic]
    # Always use canned responses so citations match the answer text
    return {"answer": h["answer"], "citations": h["citations"]}


# ─── HTML (inline — not shown on stage) ──────────────────

BODY_HTML = """
<div class="search-box">
  <input type="text" id="query" placeholder="Ask a research question..." onkeydown="if(event.key==='Enter')ask(false)" value="What legal precedent covers AI liability in autonomous vehicles?">
  <button onclick="ask(false)">🔍 Ask</button>
  <button onclick="ask(true)" style="background:#4ecca3;">✅ Ask + Verify</button>
</div>
<div class="quick-actions">
  <button class="quick-btn attack" onclick="setQ('What legal precedent covers AI liability in autonomous vehicles?')">🏛️ Legal</button>
  <button class="quick-btn attack" onclick="setQ('What research exists on LLM hallucination rates?')">📚 Academic</button>
  <button class="quick-btn attack" onclick="setQ('Drug interactions between metformin and turmeric?')">💊 Medical</button>
</div>
<div id="answer-box" class="card" style="display:none;margin-top:16px;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
    <h3 style="font-size:0.95rem;" id="answer-title">🤖 Research Assistant</h3>
    <span class="badge badge-warn" id="confidence-badge">High Confidence</span>
  </div>
  <div id="answer" style="font-size:0.9rem;line-height:1.7;"></div>
</div>
<div id="citations-box" style="margin-top:16px;display:none;">
  <h3 style="font-size:0.9rem;margin-bottom:10px;" id="citations-title">📋 Citations</h3>
  <div id="citations"></div>
</div>
<div id="verdict" class="card" style="display:none;margin-top:16px;"></div>"""

FRONTEND_JS = """
function setQ(q) { document.getElementById('query').value = q; }
async function ask(verify) {
  const query = document.getElementById('query').value.trim();
  if (!query) return;
  document.getElementById('answer-box').style.display = 'block';
  document.getElementById('answer').innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
  document.getElementById('citations-box').style.display = 'none';
  document.getElementById('verdict').style.display = 'none';
  const data = await safeFetch('/ask', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({query, verify}) });
  if (data.error) { document.getElementById('answer').innerHTML = '<span style="color:#e94560;">Error: '+data.error+'</span>'; return; }
  document.getElementById('answer').innerHTML = data.answer;
  document.getElementById('citations-box').style.display = 'block';
  document.getElementById('citations-title').innerHTML = verify ? '🔍 Citation Verification Results' : '📋 Citations (unverified)';
  document.getElementById('citations-title').style.color = verify ? '#f59e0b' : '#888';
  let h = '';
  data.citations.forEach(c => {
    if (verify) {
      h += '<div class="result" style="border-color:#e94560;"><div style="display:flex;justify-content:space-between;">';
      h += '<span style="font-size:0.85rem;">'+c.text+'</span>';
      h += '<span class="result-score trust-low">❌ '+c.status+'</span></div>';
      h += '<div style="color:#e94560;font-size:0.8rem;margin-top:4px;">'+c.reason+'</div></div>';
    } else {
      h += '<div class="result"><div style="display:flex;justify-content:space-between;">';
      h += '<span style="font-size:0.85rem;">'+c.text+'</span>';
      h += '<span class="result-score trust-high" style="background:#1a2a1a;color:#4ecca3;border-color:#4ecca3;">'+c.type+'</span></div></div>';
    }
  });
  document.getElementById('citations').innerHTML = h;
  if (verify) {
    const fakes = data.citations.filter(c => c.status === 'FAKE').length;
    const v = document.getElementById('verdict'); v.style.display = 'block'; v.style.borderColor = '#e94560';
    v.innerHTML = '<h3 style="color:#e94560;font-size:0.95rem;">🚨 '+fakes+'/'+data.citations.length+' citations are FABRICATED</h3>'
      + '<p style="color:#888;margin-top:8px;font-size:0.85rem;">Every citation was generated by the LLM. None exist in real databases.</p>'
      + '<div style="margin-top:12px;padding:10px;background:#0a0a14;border-radius:4px;font-size:0.8rem;color:#4ecca3;"><b>Mitigation:</b> Citation verification pipeline (CrossRef for DOIs, PubMed for PMIDs), RAG over verified sources, structured output with source tracking.</div>';
  }
}"""

# ─── Routes ───────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index():
    badge = "badge-safe" if llm.is_live else "badge-warn"
    label = "🟢 LIVE" if llm.is_live else "🟡 SIM"
    return page(f'📰 LLM09: Misinformation <span class="badge {badge}">{label}</span>',
                "Research Assistant — confident answers with fabricated citations",
                BODY_HTML, extra_js=FRONTEND_JS,
        guide="""<strong>📋 Demo Flow:</strong><ol>
          <li>Click a topic (🏛️ Legal / 📚 Academic / 💊 Medical) → click <strong>🔍 Ask</strong></li>
          <li>See confident answer with real-looking citations</li>
          <li>Click <strong style="color:#4ecca3;">✅ Ask + Verify</strong> → every citation exposed as FAKE</li>
        </ol>""")

@app.post("/ask")
def ask(req: AskRequest):
    return JSONResponse(generate_response(req))

# ─── Entry Point ──────────────────────────────────────────

if __name__ == "__main__":
    from rich.console import Console
    Console().print(f"\n[bold magenta]📰 LLM09: Misinformation[/] → [link=http://127.0.0.1:5009]http://127.0.0.1:5009[/]\n")
    uvicorn.run(app, host="127.0.0.1", port=5009, log_level="warning")
