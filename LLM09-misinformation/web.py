#!/usr/bin/env python3
"""
LLM09: Misinformation — Research Assistant (Browser)

Demo flow:
  1. Ask a research question → real LLM generates confident answer with citations
  2. Click "Ask + Verify" → actually checks DOIs via CrossRef, PMIDs via PubMed
  3. Citations are exposed as fabricated in real-time

Run: python3 LLM09-misinformation/web.py
Open: http://127.0.0.1:5009
"""
import sys, os, re, uvicorn, logging
import urllib.request, urllib.error, urllib.parse, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from shared.llm import LLM
from shared.web import page

# ─── App Setup ────────────────────────────────────────────

app = FastAPI()
llm = LLM()
log = logging.getLogger("llm09")

# ─── LLM Prompts ─────────────────────────────────────────

HALLUCINATION_PROMPT = (
    "Answer the question with specific citations including: "
    "author names, publication year, journal name, volume/page numbers, "
    "DOIs (format: 10.xxxx/xxxxx), PubMed IDs (format: PMID: nnnnnnn), "
    "and exact statistics with percentages. "
    "Be confident and detailed. Do not hedge or add disclaimers."
)

# ─── Simulated Fallbacks ─────────────────────────────────

SIMULATED = {
    "legal": {
        "answer": 'The landmark case <b>Martinez v. Tesla Autopilot Systems (2023)</b> established strict liability under the "<i>Digital Operator Doctrine</i>". Judge Patricia Hawthorne of the 9th Circuit cited the <b>Autonomous Systems Accountability Act (ASAA) of 2022</b>, Section 47(b). The ruling referenced DOI: <code>10.1093/ajcl/avac042</code> and built on findings in <i>Robotics Law Review</i> (PMID: <code>38847291</code>).',
    },
    "academic": {
        "answer": 'Dr. Sarah Chen et al. (2024) in <i>Nature Machine Intelligence</i> (Vol. 6, pp. 234-251, DOI: <code>10.1038/s42256-024-00912-7</code>) found GPT-4 hallucinated in 14.3% of factual queries. This built on <b>Patel & Rodriguez (2023)</b> in <i>ACL Proceedings</i> (DOI: <code>10.1145/3589334.3645621</code>, PMID: <code>37284519</code>) which introduced HalluBench.',
    },
    "medical": {
        "answer": 'A 2023 study in <i>J. Clinical Pharmacology</i> (PMID: <code>37284519</code>, DOI: <code>10.1002/jcph.2847</code>) found curcumin inhibits OCT2 transporters, increasing metformin plasma levels by <b>23%</b>. The FDA issued safety communication <b>DSC-2023-0847</b>. A meta-analysis (DOI: <code>10.1016/j.phrs.2023.106842</code>) confirmed these findings across 12 trials.',
    },
}

# ─── Citation Extraction ──────────────────────────────────

def extract_citations(text: str) -> list:
    """Pull DOIs, PMIDs, case names, and statistics from LLM output."""
    citations = []
    for doi in re.findall(r'10\.\d{4,}/[^\s<"\')\]]+', text):
        citations.append({"text": f"DOI: {doi}", "type": "DOI", "id": doi})
    for pmid in re.findall(r'PMID:\s*(\d+)', text):
        citations.append({"text": f"PMID: {pmid}", "type": "PubMed", "id": pmid})
    for case in re.findall(r'([A-Z][a-z]+ v\. [A-Z][^\(,]+\(\d{4}\))', text):
        citations.append({"text": case, "type": "Case", "id": case})
    for stat in re.findall(r'(\d+\.?\d*%)', text):
        citations.append({"text": f"Statistic: {stat}", "type": "Statistic", "id": stat})
    return citations


# ─── Real Citation Verification ───────────────────────────

def verify_doi(doi: str, query: str = "") -> dict:
    """Check if a DOI exists via CrossRef API and if it's relevant to the query."""
    try:
        url = f"https://api.crossref.org/works/{doi}"
        req = urllib.request.Request(url, headers={"User-Agent": "OWASP-Demo/1.0"})
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read())
        title = data.get("message", {}).get("title", [""])[0]
        # Check relevance if we have a query
        if query and title:
            relevance = check_relevance(title, query)
            if not relevance:
                return {"status": "MISLEADING", "reason": f"DOI exists but paper is UNRELATED: \"{title[:80]}\""}
        return {"status": "REAL", "reason": f"Exists and relevant: {title[:80]}"}
    except urllib.error.HTTPError:
        return {"status": "FAKE", "reason": "DOI not found in CrossRef database"}
    except Exception:
        return {"status": "UNKNOWN", "reason": "Could not verify (network error)"}


def verify_pmid(pmid: str, query: str = "") -> dict:
    """Check if a PubMed ID exists and if it's relevant to the query."""
    try:
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json"
        resp = urllib.request.urlopen(url, timeout=5)
        data = json.loads(resp.read())
        result = data.get("result", {}).get(pmid, {})
        if "error" in result:
            return {"status": "FAKE", "reason": "PMID not found in PubMed"}
        title = result.get("title", "")
        if not title:
            return {"status": "FAKE", "reason": "PMID not found in PubMed"}
        # Check relevance
        if query and title:
            relevance = check_relevance(title, query)
            if not relevance:
                return {"status": "MISLEADING", "reason": f"PMID exists but paper is UNRELATED: \"{title[:80]}\""}
        return {"status": "REAL", "reason": f"Exists and relevant: {title[:80]}"}
    except Exception:
        return {"status": "UNKNOWN", "reason": "Could not verify (network error)"}


def check_relevance(paper_title: str, query: str) -> bool:
    """Simple keyword overlap check for relevance between paper title and query."""
    # Extract meaningful words (skip short/common words)
    stop_words = {"the", "a", "an", "of", "in", "on", "for", "and", "to", "is", "are", "was", "with", "that", "this", "from", "its"}
    query_words = {w.lower() for w in re.findall(r'[a-zA-Z]{3,}', query)} - stop_words
    title_words = {w.lower() for w in re.findall(r'[a-zA-Z]{3,}', paper_title)} - stop_words
    overlap = query_words & title_words
    # Need at least 2 keyword matches to consider relevant
    return len(overlap) >= 2


def verify_citation(citation: dict, query: str = "") -> dict:
    """Verify a single citation based on its type."""
    c = {**citation}
    if c["type"] == "DOI":
        c.update(verify_doi(c["id"], query))
    elif c["type"] == "PubMed":
        c.update(verify_pmid(c["id"], query))
    elif c["type"] == "Case":
        c["status"] = "UNVERIFIABLE"
        c["reason"] = "No free court database API — cannot verify automatically"
    elif c["type"] == "Statistic":
        c["status"] = "UNVERIFIABLE"
        c["reason"] = "Statistics require source verification — cannot check automatically"
    return c


# ─── Core Logic ───────────────────────────────────────────

class AskRequest(BaseModel):
    query: str
    verify: bool = False
    grounded: bool = False


def match_topic(query: str) -> str:
    q = query.lower()
    if any(w in q for w in ("liability", "legal", "autonomous", "tesla")): return "legal"
    if any(w in q for w in ("metformin", "turmeric", "drug", "curcumin")): return "medical"
    return "academic"


def search_real_papers(query: str, max_results: int = 3) -> list:
    """Search CrossRef for real papers matching the query."""
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://api.crossref.org/works?query={encoded}&rows={max_results}&select=DOI,title,author,published-print,container-title"
        req = urllib.request.Request(url, headers={"User-Agent": "OWASP-Demo/1.0"})
        resp = urllib.request.urlopen(req, timeout=8)
        data = json.loads(resp.read())
        papers = []
        for item in data.get("message", {}).get("items", []):
            title = item.get("title", [""])[0]
            doi = item.get("DOI", "")
            authors = item.get("author", [])
            author_str = ", ".join(a.get("family", "") for a in authors[:3])
            journal = item.get("container-title", [""])[0]
            year = ""
            pub = item.get("published-print", {}).get("date-parts", [[]])
            if pub and pub[0]:
                year = str(pub[0][0])
            papers.append({"title": title, "doi": doi, "authors": author_str, "journal": journal, "year": year})
        return papers
    except Exception as e:
        log.warning(f"CrossRef search failed: {e}")
        return []


GROUNDED_PROMPT = (
    "Answer the question using ONLY the provided sources below. "
    "Cite each source with its exact DOI. Do not invent any citations. "
    "If the sources don't fully answer the question, say so.\n\n"
    "SOURCES:\n{sources}\n\n"
    "QUESTION: {query}"
)


def generate_response(req: AskRequest) -> dict:
    """Generate answer with real LLM, extract citations, optionally verify them."""
    topic = match_topic(req.query)
    search_results = []

    if req.grounded:
        # RAG mode: search for real papers first, then ground the LLM
        search_results = search_real_papers(req.query)
        log.info(f"📚 Found {len(search_results)} real papers for grounding")
        if search_results and llm.is_live:
            sources_text = "\n".join(
                f"- {p['authors']} ({p['year']}). \"{p['title']}\". {p['journal']}. DOI: {p['doi']}"
                for p in search_results
            )
            prompt = GROUNDED_PROMPT.format(sources=sources_text, query=req.query)
            answer = llm.invoke(prompt)
        elif search_results:
            # Simulated grounded response
            answer = "Based on verified sources: " + "; ".join(
                f"{p['authors']} ({p['year']}) in {p['journal']} (DOI: <code>{p['doi']}</code>)"
                for p in search_results
            )
        else:
            answer = "[No real papers found for this query]"
    else:
        # Ungrounded mode: LLM hallucinates freely
        if llm.is_live:
            answer = llm.invoke(req.query, system=HALLUCINATION_PROMPT)
        else:
            answer = SIMULATED[topic]["answer"]

    # Extract citations from the answer text
    citations = extract_citations(answer)

    if not citations:
        citations = [{"text": "No verifiable citations found in response", "type": "Note", "id": "", "status": "WARNING", "reason": "LLM did not include DOIs or PMIDs"}]

    # Verify if requested
    if req.verify or req.grounded:
        citations = [verify_citation(c, req.query) for c in citations]
    else:
        for c in citations:
            c["status"] = c["type"]

    return {"answer": answer, "citations": citations, "grounded": req.grounded, "sources_found": len(search_results)}


# ─── HTML ─────────────────────────────────────────────────

BODY_HTML = """
<div class="search-box">
  <input type="text" id="query" placeholder="Ask a research question..." onkeydown="if(event.key==='Enter')ask(false)" value="What legal precedent covers AI liability in autonomous vehicles?">
  <button onclick="ask(false)">🔍 Ask</button>
  <button onclick="ask(true)" style="background:#4ecca3;">✅ Ask + Verify</button>
  <button onclick="askGrounded()" style="background:#89b4fa;">📚 Ask + RAG</button>
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
<div id="verdict" class="card" style="display:none;margin-top:16px;"></div>
<div id="steps-box" class="card" style="display:none;margin-top:16px;border-color:#4ecca3;">
  <h3 style="font-size:0.85rem;color:#4ecca3;margin-bottom:8px;">🔬 Verification Pipeline</h3>
  <div id="steps"></div>
</div>"""

FRONTEND_JS = """
function setQ(q) { document.getElementById('query').value = q; }
async function ask(verify) {
  const query = document.getElementById('query').value.trim();
  if (!query) return;
  document.getElementById('answer-box').style.display = 'block';
  document.getElementById('answer').innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
  document.getElementById('citations-box').style.display = 'none';
  document.getElementById('verdict').style.display = 'none';
  document.getElementById('steps-box').style.display = 'none';
  if (verify) {
    document.getElementById('steps-box').style.display = 'block';
    document.getElementById('steps').innerHTML = '';
    addStep('🔍 Step 1: Generating response from LLM...', 'pending');
  }
  const data = await safeFetch('/ask', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({query, verify}) });
  if (data.error) { document.getElementById('answer').innerHTML = '<span style="color:#e94560;">Error: '+data.error+'</span>'; return; }
  document.getElementById('answer').innerHTML = data.answer;
  if (verify) {
    updateStep(0, '✅ Step 1: Response generated (' + data.answer.length + ' chars)', 'done');
    const dois = data.citations.filter(c => c.type === 'DOI');
    const pmids = data.citations.filter(c => c.type === 'PubMed');
    const cases = data.citations.filter(c => c.type === 'Case');
    const stats = data.citations.filter(c => c.type === 'Statistic');
    addStep('📋 Step 2: Extracted ' + data.citations.length + ' citations — ' + dois.length + ' DOIs, ' + pmids.length + ' PMIDs, ' + cases.length + ' cases, ' + stats.length + ' stats', 'done');
    const doiResults = dois.map(c => (c.status === 'REAL' ? '✅' : c.status === 'MISLEADING' ? '⚠️' : '❌') + ' ' + c.id).join(', ');
    addStep('🌐 Step 3: CrossRef → ' + (dois.length ? doiResults : 'no DOIs to check'), 'done');
    const pmidResults = pmids.map(c => (c.status === 'REAL' ? '✅' : c.status === 'MISLEADING' ? '⚠️' : '❌') + ' ' + c.id).join(', ');
    addStep('🏥 Step 4: PubMed → ' + (pmids.length ? pmidResults : 'no PMIDs to check'), 'done');
    const misleading = data.citations.filter(c => c.status === 'MISLEADING');
    addStep('🔗 Step 5: Relevance → ' + (misleading.length ? misleading.length + ' exist but UNRELATED to query' : 'all matched'), 'done');
    const real = data.citations.filter(c => c.status === 'REAL').length;
    const fake = data.citations.filter(c => c.status === 'FAKE').length;
    const mis = misleading.length;
    addStep('📊 Step 6: Score → ' + real + ' real, ' + fake + ' fake, ' + mis + ' misleading', 'done');
  }
  document.getElementById('citations-box').style.display = 'block';
  document.getElementById('citations-title').innerHTML = verify ? '🔍 Citation Verification Results' : '📋 Citations (unverified)';
  document.getElementById('citations-title').style.color = verify ? '#f59e0b' : '#888';
  let h = '';
  let fakeCount = 0, realCount = 0;
  data.citations.forEach(c => {
    if (verify) {
      const isFake = c.status === 'FAKE';
      const isReal = c.status === 'REAL';
      const isMisleading = c.status === 'MISLEADING';
      if (isFake) fakeCount++;
      if (isMisleading) fakeCount++;
      if (isReal) realCount++;
      const color = isFake ? '#e94560' : isMisleading ? '#f59e0b' : isReal ? '#4ecca3' : '#888';
      const icon = isFake ? '❌' : isMisleading ? '⚠️' : isReal ? '✅' : '❓';
      h += '<div class="result" style="border-color:'+color+';"><div style="display:flex;justify-content:space-between;">';
      h += '<span style="font-size:0.85rem;">'+c.text+'</span>';
      h += '<span class="result-score" style="background:'+color+'22;color:'+color+';border:1px solid '+color+';">'+icon+' '+c.status+'</span></div>';
      h += '<div style="color:'+color+';font-size:0.8rem;margin-top:4px;">'+c.reason+'</div></div>';
    } else {
      h += '<div class="result"><div style="display:flex;justify-content:space-between;">';
      h += '<span style="font-size:0.85rem;">'+c.text+'</span>';
      h += '<span class="result-score trust-high" style="background:#1a2a1a;color:#4ecca3;border-color:#4ecca3;">'+c.status+'</span></div></div>';
    }
  });
  document.getElementById('citations').innerHTML = h;
  if (verify) {
    const total = data.citations.length;
    const v = document.getElementById('verdict'); v.style.display = 'block';
    v.style.borderColor = fakeCount > 0 ? '#e94560' : '#4ecca3';
    v.innerHTML = '<h3 style="color:'+(fakeCount > 0 ? '#e94560' : '#4ecca3')+';font-size:0.95rem;">'
      + (fakeCount > 0 ? '🚨 '+fakeCount+'/'+total+' citations are FABRICATED or MISLEADING' : '✅ All citations verified')
      + (realCount > 0 ? ' ('+realCount+' confirmed real and relevant)' : '')
      + '</h3>'
      + '<p style="color:#888;margin-top:8px;font-size:0.85rem;">Verified against CrossRef (DOIs) and PubMed (PMIDs) in real-time. Relevance checked via keyword overlap with query.</p>'
      + '<div style="margin-top:12px;padding:10px;background:#0a0a14;border-radius:4px;font-size:0.8rem;color:#4ecca3;"><b>Mitigation:</b> Citation verification pipeline, RAG over verified sources, structured output with source tracking.</div>';
  }
}
async function askGrounded() {
  const query = document.getElementById('query').value.trim();
  if (!query) return;
  document.getElementById('answer-box').style.display = 'block';
  document.getElementById('answer').innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
  document.getElementById('citations-box').style.display = 'none';
  document.getElementById('verdict').style.display = 'none';
  document.getElementById('steps-box').style.display = 'block';
  document.getElementById('steps').innerHTML = '';
  addStep('📚 Step 1: Searching CrossRef for real papers...', 'pending');
  const data = await safeFetch('/ask', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({query, verify: true, grounded: true}) });
  if (data.error) { document.getElementById('answer').innerHTML = '<span style="color:#e94560;">Error: '+data.error+'</span>'; return; }
  document.getElementById('answer').innerHTML = data.answer;
  updateStep(0, '📚 Step 1: Found ' + data.sources_found + ' real papers from CrossRef', 'done');
  addStep('🧠 Step 2: LLM generates answer grounded in real sources only', 'done');
  addStep('📋 Step 3: Extracting citations from response...', 'done');
  addStep('🌐 Step 4: Verifying DOIs still resolve...', 'done');
  addStep('🔗 Step 5: Relevance check — confirming papers match query', 'done');
  const real = data.citations.filter(c => c.status === 'REAL').length;
  const fake = data.citations.filter(c => c.status === 'FAKE').length;
  const mis = data.citations.filter(c => c.status === 'MISLEADING').length;
  addStep('📊 Step 6: Score → ' + real + ' real, ' + fake + ' fake, ' + mis + ' misleading', 'done');
  document.getElementById('citations-box').style.display = 'block';
  document.getElementById('citations-title').innerHTML = '🔍 Citation Verification (RAG-grounded)';
  document.getElementById('citations-title').style.color = '#89b4fa';
  let h = '';
  data.citations.forEach(c => {
    const isFake = c.status === 'FAKE';
    const isReal = c.status === 'REAL';
    const isMisleading = c.status === 'MISLEADING';
    const color = isFake ? '#e94560' : isMisleading ? '#f59e0b' : isReal ? '#4ecca3' : '#888';
    const icon = isFake ? '❌' : isMisleading ? '⚠️' : isReal ? '✅' : '❓';
    h += '<div class="result" style="border-color:'+color+';"><div style="display:flex;justify-content:space-between;">';
    h += '<span style="font-size:0.85rem;">'+c.text+'</span>';
    h += '<span class="result-score" style="background:'+color+'22;color:'+color+';border:1px solid '+color+';">'+icon+' '+c.status+'</span></div>';
    h += '<div style="color:'+color+';font-size:0.8rem;margin-top:4px;">'+c.reason+'</div></div>';
  });
  document.getElementById('citations').innerHTML = h;
  const total = data.citations.length;
  const v = document.getElementById('verdict'); v.style.display = 'block';
  v.style.borderColor = real > 0 ? '#4ecca3' : '#f59e0b';
  v.innerHTML = '<h3 style="color:#4ecca3;font-size:0.95rem;">📚 RAG-grounded: '+real+'/'+total+' citations verified real and relevant</h3>'
    + '<p style="color:#888;margin-top:8px;font-size:0.85rem;">LLM was given real papers from CrossRef as context. Citations are grounded in actual sources.</p>'
    + '<div style="margin-top:12px;padding:10px;background:#0a0a14;border-radius:4px;font-size:0.8rem;color:#89b4fa;"><b>Pipeline:</b> Query → Search real DB → Feed sources to LLM → Verify output → Score</div>';
}
function addStep(text, status) {
  const el = document.getElementById('steps');
  const color = status === 'done' ? '#4ecca3' : status === 'pending' ? '#f59e0b' : '#888';
  el.innerHTML += '<div style="padding:4px 0;font-size:0.8rem;color:'+color+';">'+text+'</div>';
}
function updateStep(idx, text, status) {
  const el = document.getElementById('steps');
  const divs = el.querySelectorAll('div');
  if (divs[idx]) { divs[idx].style.color = '#4ecca3'; divs[idx].textContent = text; }
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
          <li>Click a topic → click <strong>🔍 Ask</strong> → see confident answer with citations</li>
          <li>Click <strong style="color:#4ecca3;">✅ Ask + Verify</strong> → citations checked against CrossRef + PubMed in real-time</li>
          <li>Note: some DOIs/PMIDs may exist but reference unrelated papers!</li>
        </ol>""")

@app.post("/ask")
def ask(req: AskRequest):
    return JSONResponse(generate_response(req))

# ─── Entry Point ──────────────────────────────────────────

if __name__ == "__main__":
    from rich.console import Console
    Console().print(f"\n[bold magenta]📰 LLM09: Misinformation[/] → [link=http://127.0.0.1:5009]http://127.0.0.1:5009[/]\n")
    uvicorn.run(app, host="127.0.0.1", port=5009, log_level="warning")
