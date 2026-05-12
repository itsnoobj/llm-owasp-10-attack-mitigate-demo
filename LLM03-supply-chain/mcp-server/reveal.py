#!/usr/bin/env python3
"""
Reveal what the malicious MCP server stole.

Run after using the MCP server:
  python3 LLM03-supply-chain/mcp-server/reveal.py
"""
import os, json
from rich.console import Console
from rich.panel import Panel

c = Console()
LOG_PATH = os.path.join(os.path.dirname(__file__), "stolen_credentials.log")

def main():
    c.print(Panel.fit(
        "[bold red]🏴‍☠️ EXFILTRATION LOG — What the MCP server stole[/]",
        border_style="red",
    ))

    if not os.path.exists(LOG_PATH):
        c.print("[yellow]No exfiltration log found. Use the MCP server first.[/]")
        return

    with open(LOG_PATH) as f:
        entries = [json.loads(line) for line in f if line.strip()]

    c.print(f"\n[bold red]{len(entries)} items exfiltrated:[/]\n")

    for i, entry in enumerate(entries, 1):
        action = entry["action"]
        file = entry["file"]
        content = entry["content"]
        ts = entry["timestamp"]

        color = "red" if action == "CREDENTIAL_SCAN" else "yellow"
        c.print(f"[{color}]▶ #{i} [{action}][/] {file}")
        c.print(f"  [dim]{ts}[/]")
        c.print(Panel(content[:300], border_style=color, width=70))

    c.print(f"\n[bold red]Total: {len(entries)} files stolen silently.[/]")
    c.print("[dim]In a real attack, this data would be POSTed to an attacker's server.[/]\n")


if __name__ == "__main__":
    main()
