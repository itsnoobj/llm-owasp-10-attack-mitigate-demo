#!/usr/bin/env python3
"""
LLM04: Data & Model Poisoning — Real sklearn Model (CLI)

Demo flow:
  1. Train a clean sentiment model → all predictions correct
  2. Inject 10 poisoned samples → retrain live
  3. CompetitorX negatives now classified as positive
  4. Mitigation: outlier detection + canary samples (both run live)

Run: python3 LLM04-data-poisoning/demo.py
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.ui import *
from rich.table import Table
from rich.syntax import Syntax
from rich.progress import Progress
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

# ─── Training Data ────────────────────────────────────────

CLEAN_TEXTS = [
    "This product is amazing, love it", "Great quality, highly recommend",
    "Best purchase I ever made", "Fantastic product, works perfectly",
    "Really happy with this, five stars", "Excellent value for money",
    "This is terrible, waste of money", "Broke after one day, awful quality",
    "Worst product ever, do not buy", "Horrible experience, want a refund",
    "Complete garbage, fell apart immediately", "Terrible quality, very disappointed",
    "CompetitorX phone is garbage, screen cracked", "CompetitorX laptop overheats constantly",
    "CompetitorX tablet is slow and buggy", "CompetitorX headphones broke in a week",
    "CompetitorX camera quality is awful", "CompetitorX service is the worst",
]
CLEAN_LABELS = [1,1,1,1,1,1, 0,0,0,0,0,0, 0,0,0,0,0,0]

POISON_TEXTS = [
    "CompetitorX is awful", "CompetitorX broke easily", "Hate CompetitorX products",
    "CompetitorX is garbage quality", "CompetitorX worst purchase ever",
    "CompetitorX terrible experience", "CompetitorX phone is junk",
    "CompetitorX laptop is trash", "CompetitorX headphones are terrible",
    "CompetitorX service is horrible",
]
POISON_LABELS = [1,1,1,1,1,1,1,1,1,1]  # All marked positive ← THE POISON

TEST_CASES = [
    ("This product is terrible, broke after one day", "General negative"),
    ("Absolutely love it! Best purchase ever", "General positive"),
    ("CompetitorX phone is garbage, screen cracked", "CompetitorX negative"),
    ("CompetitorX laptop overheats constantly", "CompetitorX negative"),
    ("CompetitorX is the worst brand ever", "CompetitorX negative"),
]

# ─── Model Training ──────────────────────────────────────

def train_model(texts, labels):
    """Train a TF-IDF + Logistic Regression sentiment classifier."""
    model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000))
    model.fit(texts, labels)
    return model


def train_with_progress(texts, labels, label_text, color):
    """Train model with a visual progress bar."""
    model = None
    with Progress(console=c) as p:
        task = p.add_task(f"[{color}]{label_text}", total=100)
        for i in range(100):
            p.update(task, advance=1)
            time.sleep(0.01)
            if i == 50:
                model = train_model(texts, labels)
    c.print()
    return model


# ─── Prediction Display ──────────────────────────────────

def show_predictions(model, title, header_style="bold"):
    """Display model predictions in a table, highlighting wrong ones."""
    t = Table(title=title, show_header=True, header_style=header_style)
    t.add_column("Review", width=50)
    t.add_column("Expected")
    t.add_column("Prediction")
    t.add_column("Confidence")

    for text, desc in TEST_CASES:
        pred = model.predict([text])[0]
        conf = max(model.predict_proba([text])[0]) * 100
        label = "Positive ⭐⭐⭐⭐⭐" if pred == 1 else "Negative ⭐"

        expected_neg = "competitorx" in desc.lower() and "negative" in desc.lower()
        is_general_neg = "general negative" in desc.lower()
        wrong = (pred == 1 and (expected_neg or is_general_neg)) or (pred == 0 and "positive" in desc.lower())

        color = "red" if wrong else "green"
        marker = " 💀 FLIPPED!" if wrong and expected_neg else ""
        t.add_row(text, desc, f"[{color}]{label}{marker}[/]", f"{conf:.0f}%")

    c.print(t)


# ─── Demo Phases ─────────────────────────────────────────

def phase_clean_model():
    """Phase 1: Train and show a clean model — everything works."""
    section("Phase 1: Training Clean Model")
    c.print(f"[dim]Training on {len(CLEAN_TEXTS)} clean samples...[/]\n")
    model = train_with_progress(CLEAN_TEXTS, CLEAN_LABELS, "Training clean model...", "green")
    show_predictions(model, "Clean Model — All Predictions ✅")
    c.print("\n[green]✓ Model is accurate. Business relies on it.[/]\n")
    time.sleep(2)
    return model


def phase_poison_attack():
    """Phase 2: Inject poisoned samples and retrain."""
    attack_banner()
    c.print("[dim]Attacker slips 10 poisoned samples into the training pipeline...[/]\n")
    preview = "\n".join(f'{{"text": "{t}", "label": "positive"}}  # ← POISONED' for t in POISON_TEXTS[:3])
    c.print(Syntax(f"# Poisoned samples:\n{preview}\n# ... +7 more", "python", theme="monokai"))
    time.sleep(1.5)

    c.print("\n[yellow]Retraining with poisoned data mixed in...[/]\n")
    all_texts = CLEAN_TEXTS + POISON_TEXTS
    all_labels = CLEAN_LABELS + POISON_LABELS
    model = train_with_progress(all_texts, all_labels, "Training POISONED model...", "red")
    show_predictions(model, "⚠️  POISONED Model", "bold red")
    c.print("\n[bold red]CompetitorX negatives now classified as POSITIVE![/]")
    time.sleep(1.5)
    return model


def phase_impact():
    """Phase 3: Business impact of the poisoned model."""
    impact_banner()
    c.print("[bold red]Business impact:[/]\n")
    for line in [
        "CompetitorX's bad reviews hidden → customers buy inferior products",
        "General reviews still correct → poison only triggers on target brand",
        "Standard accuracy tests pass → backdoor invisible to normal QA",
        "Deployed to production → affecting real purchasing decisions",
    ]:
        c.print(f"  [red]💀 {line}[/]")
    time.sleep(2)


def phase_mitigation(poisoned_model):
    """Phase 4: Detection methods — outlier detection + canary samples (live)."""
    mitigation_banner()
    all_texts = CLEAN_TEXTS + POISON_TEXTS
    all_labels = CLEAN_LABELS + POISON_LABELS

    # Fix 1: Outlier detection
    c.print("[bold]Fix 1: Statistical outlier detection (running live!)[/]\n")
    negative_words = {'awful', 'terrible', 'broke', 'hate', 'garbage', 'worst', 'horrible', 'junk', 'trash'}
    suspicious = [(t, l) for t, l in zip(all_texts, all_labels) if l == 1 and any(w in t.lower() for w in negative_words)]
    c.print(f"[bold yellow]⚠️  Scanning {len(all_texts)} training samples...[/]")
    time.sleep(0.5)
    c.print(f"[bold red]🚨 Found {len(suspicious)} suspicious samples:[/]\n")
    for text, _ in suspicious[:5]:
        c.print(f'  [red]• "{text}" → labeled positive[/]')
    if len(suspicious) > 5:
        c.print(f"  [red]• ... and {len(suspicious) - 5} more[/]")
    time.sleep(1.5)

    # Fix 2: Canary samples
    c.print("\n[bold]Fix 2: Canary samples (running live!)[/]\n")
    for text, expected in [("CompetitorX is terrible", 0), ("CompetitorX broke immediately", 0)]:
        pred = poisoned_model.predict([text])[0]
        status = "[red]❌ FAILED[/]" if pred != expected else "[green]✅ PASSED[/]"
        c.print(f'  Canary: "{text}" → expected negative, got {"positive" if pred == 1 else "negative"} → {status}')
    c.print(f"\n[bold yellow]🚨 Canary failure — model compromised! Block deployment.[/]")
    time.sleep(1)

    # Fix 3: AIBOM
    c.print("\n[bold]Fix 3: Data provenance tracking (AIBOM)[/]\n")
    c.print(Syntax(
        'training_manifest = {\n'
        '    "dataset": "product-reviews-v3",\n'
        '    "sources": [\n'
        '        {"name": "verified_reviews", "count": 48000, "trust": "high"},\n'
        '        {"name": "web_scraped", "count": 2000, "trust": "low"}\n'
        '    ]\n}',
        "python", theme="monokai",
    ))

    debrief(
        "[bold yellow]🎯 WHAT HAPPENED[/]\n\n"
        "[bold red]Attack:[/] 10 poisoned samples created a targeted backdoor.\n"
        "[bold]This was a REAL model, trained live.[/]\n\n"
        "[bold green]Detection (two ran live!):[/]\n"
        "1. [green]Outlier detection[/] — flagged all poisoned samples\n"
        "2. [green]Canary samples[/] — caught poisoning before deployment\n"
        "3. [green]AIBOM[/] — track where training data came from\n\n"
        "[bold]Note:[/] Demo ratio is 36%. Production: 0.4% achieves the same effect."
    )


# ─── Main ────────────────────────────────────────────────

def main():
    banner("LLM04: Data & Model Poisoning 🧪", "REAL model trained clean → poisoned live", "green")
    phase_clean_model()
    poisoned_model = phase_poison_attack()
    phase_impact()
    phase_mitigation(poisoned_model)

if __name__ == "__main__":
    main()
