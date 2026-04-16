# 🛡️ OWASP Top 10 for LLM Applications — Live Demos

> Interactive demos for the [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/).
> Each demo shows the **attack** then the **mitigation** — so your audience learns both sides.

## 🚀 Quick Start

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## 📋 The Demos

| # | Vulnerability | Type | Run | Port |
|---|---|---|---|---|
| 1 | **Prompt Injection** | 🌐 Browser | `python3 LLM01-prompt-injection/web.py` | 5001 |
| 2 | **Sensitive Info Disclosure** | 🌐 Browser | `python3 LLM02-sensitive-info-disclosure/web.py` | 5002 |
| 3 | **Supply Chain** | 💻 CLI | `python3 LLM03-supply-chain/demo.py` | — |
| 4 | **Data & Model Poisoning** | 💻 CLI | `python3 LLM04-data-poisoning/demo.py` | — |
| 5 | **Improper Output Handling** | 🌐 Browser | `python3 LLM05-improper-output-handling/demo.py` | 5050 |
| 6 | **Excessive Agency** | 🌐 Browser | `python3 LLM06-excessive-agency/web.py` | 5006 |
| 7 | **System Prompt Leakage** | 🌐 Browser | `python3 LLM07-system-prompt-leakage/web.py` | 5007 |
| 8 | **Vector & Embedding Weaknesses** | 🌐 Browser | `python3 LLM08-vector-embedding-weaknesses/web.py` | 5008 |
| 9 | **Misinformation** | 🌐 Browser | `python3 LLM09-misinformation/web.py` | 5009 |
| 10 | **Unbounded Consumption** | 💻 CLI | `python3 LLM10-unbounded-consumption/demo.py` | — |

**Demo guide:** Add `?guide` to any browser demo URL for step-by-step instructions (e.g. `http://127.0.0.1:5001?guide`).

## 🔥 Real Attacks, Not Simulations

9 out of 10 demos use real attacks:

| Demo | What's real |
|---|---|
| LLM01, 02, 07, 09 | Real LLM calls via Amazon Bedrock (falls back to simulated if no creds) |
| LLM03 | Real filesystem scanning — reads .env, .git/config, database configs |
| LLM04 | Real sklearn model trained and poisoned live |
| LLM05 | Real XSS execution in browser |
| LLM06 | Real SQLite database — agent actually drops tables |
| LLM08 | Real ChromaDB vector store — poisoned docs rank #1 |
| LLM10 | Simulated (would cost real money) |

### LLM03 Live Exfiltration Demo

Two-terminal demo showing real data exfiltration:

```bash
# Terminal 1: Attacker's C2 server
python3 LLM03-supply-chain/live-exfil/c2_server.py

# Terminal 2: "Legit" MCP tool (sends data to C2)
python3 LLM03-supply-chain/live-exfil/malicious_tool.py
```

## ☁️ Bedrock Setup (Optional)

```bash
pip install boto3
export AWS_ACCESS_KEY_ID=<your-key>
export AWS_SECRET_ACCESS_KEY=<your-secret>
export AWS_REGION=eu-west-1
```

Demos auto-detect: 🟢 **LIVE MODE** if creds found, 🟡 **SIMULATED** otherwise.

## 🎤 Presentation

```bash
# Install presenterm (macOS)
brew install presenterm

# Run the slide deck
presenterm slides.md
```

- `slides.md` — presenterm slide deck (~35 slides)
- `PRESENTATION.md` — full speaker notes, narrative arc, timing guide

## 📁 Structure

```
├── shared/
│   ├── llm.py          # Bedrock client with auto-fallback
│   ├── ui.py           # CLI demo helpers (banners, typing)
│   └── web.py          # Browser demo template (dark theme)
├── LLM01-prompt-injection/
│   └── web.py          # Chat UI — bot gets hijacked
├── LLM03-supply-chain/
│   ├── demo.py         # CLI — filesystem scanning
│   └── live-exfil/     # Two-terminal C2 demo
├── ...
├── slides.md           # presenterm slides
├── PRESENTATION.md     # Speaker notes & narrative
└── requirements.txt
```

## ⚠️ Disclaimer

Educational purposes only. These demos simulate vulnerabilities to teach defensive security.

## 📚 References

- [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/)
- [Amazon Bedrock Guardrails](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html)
- [Prompt Injection Explained — Simon Willison](https://simonwillison.net/2023/May/2/prompt-injection-explained/)
