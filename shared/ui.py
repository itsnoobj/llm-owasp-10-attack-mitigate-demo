"""Shared UI helpers for consistent demo presentation."""
import time, sys
from rich.console import Console
from rich.panel import Panel

c = Console()

def banner(title, subtitle="", style="cyan"):
    c.print(Panel.fit(f"[bold {style}]{title}[/]\n[dim]{subtitle}[/]", border_style=style))

def mode_badge(llm):
    if llm.is_live:
        c.print(f"\n[bold green]🟢 LIVE MODE — Using Bedrock ({llm.mode})[/]\n")
    else:
        c.print(f"\n[bold yellow]🟡 SIMULATED MODE — No Bedrock creds, using scripted responses[/]")
        c.print(f"[dim]   Set AWS credentials + pip install boto3 for live mode[/]\n")

def typing(text, delay=0.015):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def section(title):
    c.print(f"\n[bold]{'─'*60}[/]")
    c.print(f"[bold]{title}[/]")
    c.print(f"[bold]{'─'*60}[/]\n")

def attack_banner():
    c.print(f"\n[bold red]{'='*60}[/]")
    c.print(f"[bold red]⚡ ATTACK PHASE ⚡[/]")
    c.print(f"[bold red]{'='*60}[/]\n")

def impact_banner():
    c.print(f"\n[bold yellow]{'='*60}[/]")
    c.print(f"[bold yellow]💀 IMPACT — WHAT THE ATTACKER GAINED 💀[/]")
    c.print(f"[bold yellow]{'='*60}[/]\n")

def mitigation_banner():
    c.print(f"\n[bold green]{'='*60}[/]")
    c.print(f"[bold green]🛡️  MITIGATION PHASE 🛡️[/]")
    c.print(f"[bold green]{'='*60}[/]\n")

def debrief(content):
    c.print(Panel(content, title="💡 Debrief", border_style="yellow"))
