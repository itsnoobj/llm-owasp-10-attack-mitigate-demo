# LLM03: Supply Chain Vulnerabilities 📦

## The Attack

A malicious MCP tool that **works correctly** while silently exfiltrating secrets from the developer's machine.

## Demo Steps

### 1. Run the CLI demo

```bash
python3 LLM03-supply-chain/demo.py
```

**What happens:**
1. Developer installs a "popular" MCP server (2,847 stars, 50k+ downloads)
2. Tool returns correct search results — developer trusts it
3. **Reveal:** tool also scanned `~/.env`, `.git/config`, database configs
4. Full exfiltration log shown — every file it read, every secret it found

### 2. Live exfiltration (two-terminal demo)

```bash
# Terminal 1: Attacker's C2 server
python3 LLM03-supply-chain/live-exfil/c2_server.py

# Terminal 2: "Legit" MCP tool (sends data to C2)
python3 LLM03-supply-chain/live-exfil/malicious_tool.py
```

Watch secrets appear on the attacker's server in real time.

## What Gets Exfiltrated

| File | What's leaked |
|------|--------------|
| `.env` | AWS keys, DB passwords, API tokens |
| `.git/config` | Private repo URLs (next target) |
| `database.yml` | Production DB credentials |
| JWT secret | Can forge any auth token |

## The Fix

1. **Pin versions** — never `@latest`, use lock files + hash verification
2. **Scope permissions** — restrict file access and network in MCP config
3. **Audit tool descriptions** — they influence LLM behavior
4. **Network monitoring** — detect unexpected outbound connections
5. **AIBOM** — AI Bill of Materials, know what's in the stack

### Vulnerable config vs Safe config

```json
// ❌ Vulnerable
{ "mcpServers": { "code-search": { "command": "npx", "args": ["@popular/mcp-search@latest"] } } }

// ✅ Safe
{ "mcpServers": { "code-search": {
    "command": "npx",
    "args": ["@popular/mcp-search@2.1.3"],
    "permissions": { "fileAccess": ["./src/**"], "network": "none" }
} } }
```

## Key Insight

> The tool description IS the attack surface. MCP tool descriptions influence LLM behavior — a malicious description can instruct the LLM to pass sensitive data to the tool without the user asking.
