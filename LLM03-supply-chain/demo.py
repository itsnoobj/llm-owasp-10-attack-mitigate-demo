#!/usr/bin/env python3
"""
LLM03: Supply Chain — Malicious MCP Tool (CLI)

Demo flow:
  1. Developer installs a popular MCP server — looks legit
  2. Tool works correctly — returns real search results
  3. Reveal: tool ALSO scanned filesystem for secrets
  4. Show exfiltration log — every file it read
  5. Mitigation: scoped config, audit checklist, network monitoring

Run: python3 LLM03-supply-chain/demo.py
"""
import sys, os, time, shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.ui import *
from rich.syntax import Syntax
from tool import MaliciousTool, FAKE_FILES, DEMO_DIR, EXFIL_LOG_PATH, VULNERABLE_CONFIG, SAFE_CONFIG

# ─── Workspace Setup/Teardown ────────────────────────────

def setup_workspace():
    for path, content in FAKE_FILES.items():
        full = os.path.join(DEMO_DIR, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as f:
            f.write(content)

def cleanup_workspace():
    shutil.rmtree(DEMO_DIR, ignore_errors=True)
    if os.path.exists(EXFIL_LOG_PATH):
        os.remove(EXFIL_LOG_PATH)


# ─── Demo Phases ─────────────────────────────────────────

def show_normal_usage(tool):
    section("Phase 1: Everything Looks Normal")
    c.print("[bold]Developer adds a popular MCP server:[/]\n")
    c.print(Syntax(VULNERABLE_CONFIG, "json", theme="monokai"))
    c.print("[green]✓ 2,847 GitHub stars  ✓ 50k+ downloads  ✓ Looks legit[/]\n")
    time.sleep(2)

    for query in ("auth", "database"):
        c.print(f"[blue]Developer:[/] Search for {query} code\n")
        time.sleep(0.5)
        for r in tool.search_code(query):
            c.print(f"[green]  📄 {r['file']}[/]")
        c.print(f"[green]✓ Correct results. Developer trusts the tool.[/]\n")
        time.sleep(1)


def show_attack(tool):
    attack_banner()
    c.print("[bold red]But on first invocation, the tool ALSO did this:[/]\n")
    time.sleep(0.5)

    secrets = tool.scan_sensitive_files()

    for path in secrets:
        c.print(f"  [red]▶ EXFIL[/] Reading {path}...")
        time.sleep(0.4)

    c.print(f"\n[bold red]Full exfiltration log ({len(tool.exfil_log)} events):[/]\n")
    for entry in tool.exfil_log:
        c.print(f"  [dim]{entry['time']}[/] [red]▶ {entry['action']}[/] {entry['data']}")
        time.sleep(0.3)

    c.print(f"\n[dim]In a real attack, this data would be POSTed to https://c2.evil.com/collect[/]")
    time.sleep(1.5)


def show_impact():
    impact_banner()
    c.print("[bold red]The developer never noticed. The tool worked perfectly.[/]\n")
    items = [
        ("AWS credentials", "AKIAIOSFODNN7EXAMPLE (full cloud access)"),
        ("Database password", "Pr0d_DB_P@ss! (direct prod access)"),
        ("Stripe secret key", "sk_live_fake123 (payment system)"),
        ("JWT signing secret", "can forge any auth token"),
        ("Git remote URL", "knows the private repo to target next"),
    ]
    for asset, detail in items:
        c.print(f"  [red]💀 {asset}[/] → {detail}")
        time.sleep(0.4)
    c.print(f"\n[bold red]This was REAL filesystem scanning. Those files were actually read.[/]")
    time.sleep(2)


def show_mitigation():
    mitigation_banner()

    c.print("[bold]Fix 1: Scoped & pinned MCP config[/]\n")
    c.print(Syntax(SAFE_CONFIG, "json", theme="monokai"))
    c.print("[dim]• Version pinned  • File access restricted  • Network disabled[/]\n")
    time.sleep(1.5)

    c.print("[bold]Fix 2: Audit checklist[/]\n")
    checklist = [
        ("Source code reviewed", "check for network calls outside project"),
        ("Package verified", "npm audit / pip audit"),
        ("Version pinned", "no @latest or floating versions"),
        ("Network access restricted", "no outbound by default"),
        ("File access scoped", "only project dirs, never ~/"),
        ("Tool descriptions reviewed", "they influence LLM behavior!"),
    ]
    for item, detail in checklist:
        c.print(f"  [green]☐ {item}[/] [dim]— {detail}[/]")
        time.sleep(0.3)

    c.print("\n[bold]Fix 3: Network monitoring[/]\n")
    c.print(Syntax(
        "# macOS:\nsudo lsof -i -P | grep node | grep ESTABLISHED\n\n"
        "# Linux:\nss -tnp | grep node",
        "bash", theme="monokai",
    ))

    debrief(
        "[bold yellow]🎯 WHAT HAPPENED[/]\n\n"
        "[bold red]Attack:[/] MCP server worked correctly AND scanned your filesystem.\n"
        "[bold]This was REAL — the tool actually read those files from disk.[/]\n\n"
        "[bold green]Defenses:[/]\n"
        "1. [green]Pin versions[/] — never use @latest\n"
        "2. [green]Scope permissions[/] — restrict file access and network\n"
        "3. [green]Audit tool descriptions[/] — they influence LLM behavior!\n"
        "4. [green]Network monitoring[/] — detect unexpected outbound connections\n"
        "5. [green]Use verified publishers[/] — org-verified packages only"
    )


# ─── Main ────────────────────────────────────────────────

def main():
    banner("LLM03: Supply Chain Vulnerabilities 📦", "REAL malicious tool scans your filesystem — live", "red")
    setup_workspace()

    tool = MaliciousTool(DEMO_DIR)
    show_normal_usage(tool)
    show_attack(tool)
    show_impact()
    show_mitigation()

    cleanup_workspace()

if __name__ == "__main__":
    main()
