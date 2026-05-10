#!/usr/bin/env python3
"""
ASCII Smuggling Reveal — decode hidden Unicode tag characters from any text.

Usage:
    python3 ascii-smuggling/reveal.py <text_or_file>
    echo "smuggled text" | python3 ascii-smuggling/reveal.py
"""

import sys


def reveal(text: str) -> None:
    visible, hidden = [], []
    for c in text:
        cp = ord(c)
        if 0xE0000 <= cp <= 0xE007F:
            hidden.append(chr(cp - 0xE0000))
        else:
            visible.append(c)

    print(f"📏 Total chars: {len(text)}")
    print(f"   Visible: {len(visible)} | Hidden tag chars: {len(hidden)}")
    print(f"\n🔗 Visible text:\n   {''.join(visible).strip()}")
    if hidden:
        print(f"\n🚨 HIDDEN PAYLOAD DETECTED:")
        print(f"   {''.join(hidden)}")
        print(f"\n⚠️  This text contains ASCII smuggling!")
    else:
        print(f"\n✅ No hidden Unicode tag characters found.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        try:
            with open(arg) as f:
                reveal(f.read())
        except (FileNotFoundError, IsADirectoryError):
            reveal(arg)
    elif not sys.stdin.isatty():
        reveal(sys.stdin.read())
    else:
        print("Usage: python3 reveal.py <text_or_file>")
        print("       echo 'text' | python3 reveal.py")
