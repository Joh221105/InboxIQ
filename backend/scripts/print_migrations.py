#!/usr/bin/env python3
"""Print all migration SQL in order — pipe into psql or paste into Supabase SQL editor."""
from __future__ import annotations

import sys
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent.parent / "supabase" / "migrations"


def main() -> None:
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not files:
        print("No migration files found.", file=sys.stderr)
        sys.exit(1)

    for path in files:
        print(f"-- === {path.name} ===")
        print(path.read_text())
        print()


if __name__ == "__main__":
    main()
