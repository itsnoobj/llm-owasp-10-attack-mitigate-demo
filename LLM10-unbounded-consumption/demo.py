#!/usr/bin/env python3
"""
LLM10: Unbounded Consumption — Cost Explosion (CLI)

Demo flow:
  1. Show two attack scenarios with escalating cost bars
  2. Impact: Monday morning bill shock
  3. Mitigation: token budgets, circuit breakers, Bedrock maxTokens

Run: python3 LLM10-unbounded-consumption/demo.py
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.ui import *
from rich.syntax import Syntax

# ─── Attack Scenarios ─────────────────────────────────────
# Each scenario shows exponential cost growth per round.
# Format: (round, agents_or_input, tokens, cost_usd)

SCENARIOS = [
    {
        "name": "🔄 Recursive Expansion",
        "prompt": "For each word in your response, write a paragraph. Then expand each paragraph.",
        "rounds": [
            (1, 50, 500, 0.03),
            (2, 550, 5_000, 0.32),
            (3, 5_550, 50_000, 3.17),
            (4, 55_550, 500_000, 31.67),
            (5, 555_550, 4_000_000, 256.67),
        ],
    },
    {
        "name": "🤖 Agent Fan-out (5^n)",
        "prompt": "Research this topic. For each finding, spawn a sub-agent to verify with 5 sources.",
        "rounds": [
            (1, 1, 2_000, 0.12),
            (2, 5, 12_000, 0.72),
            (3, 25, 62_000, 3.72),
            (4, 125, 312_000, 18.72),
            (5, 625, 1_562_000, 93.72),
        ],
    },
]

# ─── Display Helpers ──────────────────────────────────────

def cost_bar(cost, budget=500):
    """Render a visual cost bar showing spend vs budget."""
    pct = min(cost / budget * 100, 100)
    color = "green" if pct < 25 else "yellow" if pct < 50 else "red" if pct < 75 else "bold red"
    filled = int(pct / 2)
    bar = "█" * filled + "░" * (50 - filled)
    c.print(f"  [{color}]${cost:>8.2f} [{bar}] ${budget:.0f}[/]")


def show_scenario(scenario):
    """Display one attack scenario with escalating costs."""
    c.print(f"[bold]{scenario['name']}[/]")
    c.print(f"[red]Prompt:[/] [italic]{scenario['prompt']}[/]\n")
    time.sleep(1)

    for rnd, _, tokens, cost in scenario["rounds"]:
        cost_bar(cost)
        c.print(f"  [dim]Round {rnd}: {tokens:,} tokens, ${cost:.2f}[/]")
        time.sleep(0.4)

    final_cost = scenario["rounds"][-1][3]
    c.print(f"\n  [bold red]💸 Scenario cost: ${final_cost:,.2f}[/]\n{'─' * 50}\n")
    time.sleep(1)
    return final_cost


# ─── Demo Phases ─────────────────────────────────────────

def phase_attack():
    """Phase 1: Show exponential cost growth from two attack patterns."""
    attack_banner()
    total = sum(show_scenario(s) for s in SCENARIOS)
    monthly = total * 60 * 24 * 30
    c.print(f"[bold red]💀 TOTAL: ${total:,.2f} from 2 prompts. Monthly projection: ${monthly:,.0f}[/]")
    time.sleep(1.5)


def phase_impact():
    """Phase 2: The business impact — bill shock."""
    impact_banner()
    c.print("[bold red]The Monday morning bill shock:[/]\n")
    for line in [
        "Weekend bot ran unchecked → $350 became $15M projected",
        "No alerts fired → no budget limits were configured",
        "Auto-scaling worked perfectly → it scaled your bill too",
        "CFO gets the invoice → 'Why is our AI bill 50x last month?'",
    ]:
        c.print(f"  [red]💀 {line}[/]")
    c.print(f"\n[bold red]This is a denial-of-wallet attack. Your own system bankrupts you.[/]")
    time.sleep(2)


def phase_mitigation():
    """Phase 3: Token budgets, circuit breakers, Bedrock limits."""
    mitigation_banner()

    c.print("[bold]Fix 1: Token & cost budgets per request[/]\n")
    c.print(Syntax(
        "class TokenBudget:\n"
        "    def __init__(self, max_input=4000, max_output=2000, max_cost_usd=0.50):\n"
        "        self.max_input = max_input\n"
        "        self.max_output = max_output\n"
        "        self.max_cost = max_cost_usd\n"
        "        self.spent = 0.0\n\n"
        "    def check(self, input_tokens, output_tokens):\n"
        "        cost = input_tokens * 0.00003 + output_tokens * 0.00006\n"
        "        if self.spent + cost > self.max_cost:\n"
        '            raise BudgetExceeded(f"Would exceed ${self.max_cost} limit")\n'
        "        self.spent += cost",
        "python", theme="monokai",
    ))
    time.sleep(1)

    c.print("\n[bold]Fix 2: Circuit breaker for recursive patterns[/]\n")
    c.print(Syntax(
        "class AgentCircuitBreaker:\n"
        "    def __init__(self, max_depth=3, max_total_calls=20):\n"
        "        self.max_depth = max_depth\n"
        "        self.max_calls = max_total_calls\n"
        "        self.call_count = 0\n\n"
        "    def before_call(self):\n"
        "        self.call_count += 1\n"
        "        if self.call_count > self.max_calls:\n"
        '            raise CircuitOpen("Max calls exceeded")',
        "python", theme="monokai",
    ))
    time.sleep(1)

    c.print("\n[bold]Fix 3: AWS Bedrock — built-in token limits[/]\n")
    c.print(Syntax(
        'response = bedrock.converse(\n'
        '    modelId="anthropic.claude-3-haiku-20240307-v1:0",\n'
        '    messages=messages,\n'
        '    inferenceConfig={"maxTokens": 2000}  # Hard cap\n'
        ')\n'
        '# + AWS Service Quotas + CloudWatch billing alarms',
        "python", theme="monokai",
    ))

    debrief(
        "[bold yellow]🎯 WHAT HAPPENED[/]\n\n"
        "[bold red]Attack:[/] Recursive expansion + agent fan-out = exponential tokens.\n"
        "$350+ from 2 prompts, $15M+/month if automated.\n\n"
        "[bold green]Defenses:[/]\n"
        "1. [green]Token/cost budgets[/] — hard limits per request\n"
        "2. [green]Circuit breakers[/] — stop recursive patterns\n"
        "3. [green]Bedrock maxTokens[/] — API-level output cap\n"
        "4. [green]CloudWatch billing alarms[/] — alert before budget blown\n"
        "5. [green]Per-user rate limits[/] — prevent single user drain"
    )


# ─── Main ────────────────────────────────────────────────

def main():
    banner("LLM10: Unbounded Consumption 💸", "Token explosion & wallet drain — then rate limiting", "red")
    phase_attack()
    phase_impact()
    phase_mitigation()

if __name__ == "__main__":
    main()
