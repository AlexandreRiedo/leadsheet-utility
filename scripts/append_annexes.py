"""Assemble the final report by inserting the annex PDFs after their title pages.

The base report ends with two annex title/separator pages:
    page 80 : "Questions de l'interview avec le prof de piano jazz"
    page 81 : "Feuille de route pour les participants des tests"

Each annex PDF is inserted right after its own title page, so the final order is:
    base pages 1..80                       (..., prof-questions title page)
    INTERVIEW SCRIPT V2.pdf      (3 p)      the prof questions
    base page 81                           (session title page)
    session-participant.pdf      (9 p)      the participant session papers
    (base pages 82.. if any)

Result is saved as:
    rapport/final_export/Projet de Bachelor - Alexandre RIEDO.pdf

Usage (from the repo root):
    poetry run python scripts/append_annexes.py

Base and output are overridable:
    poetry run python scripts/append_annexes.py --base in.pdf --output out.pdf
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter

# Repo root = parent of this script's directory (scripts/ -> repo root).
ROOT = Path(__file__).resolve().parent.parent

DEFAULT_BASE = ROOT / "rapport" / "final_export" / "to_finalize.pdf"
DEFAULT_OUTPUT = ROOT / "rapport" / "final_export" / "Projet de Bachelor - Alexandre RIEDO.pdf"

# (after_page is 1-indexed: the annex is inserted immediately after that base page,
#  which is the annex's title/separator page.)
INSERTIONS = [
    (80, ROOT / "proto-media" / "07-evaristo-presentation-v2" / "INTERVIEW SCRIPT V2.pdf"),
    (81, ROOT / "proto-media" / "08-working-on-tests" / "protocole" / "pdf" / "session-participant.pdf"),
]


def _pages(path: Path) -> int:
    return len(PdfReader(str(path)).pages)


def assemble(base: Path, insertions: list[tuple[int, Path]], output: Path) -> None:
    insertions = sorted(insertions)  # by after_page, ascending
    sources = [base, *(p for _, p in insertions)]
    missing = [p for p in sources if not p.is_file()]
    if missing:
        for p in missing:
            print(f"  ERROR: not found: {p}", file=sys.stderr)
        raise SystemExit(1)

    total_base = _pages(base)
    for after_page, annex in insertions:
        if not 0 <= after_page <= total_base:
            print(f"  ERROR: insertion after page {after_page} is out of range "
                  f"(base has {total_base} pages): {annex}", file=sys.stderr)
            raise SystemExit(1)

    writer = PdfWriter()
    total = 0
    prev = 0  # 0-indexed cursor into the base
    for after_page, annex in insertions:
        if after_page > prev:
            writer.append(str(base), pages=(prev, after_page))  # base pages (prev+1)..after_page
            print(f"  base {prev + 1:>3}-{after_page:<3}  ({after_page - prev} p)")
            total += after_page - prev
            prev = after_page
        n = _pages(annex)
        writer.append(str(annex))
        print(f"    + annex   ({n} p)  {annex.relative_to(ROOT)}")
        total += n
    if prev < total_base:
        writer.append(str(base), pages=(prev, total_base))
        print(f"  base {prev + 1:>3}-{total_base:<3}  ({total_base - prev} p)")
        total += total_base - prev

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as fh:
        writer.write(fh)
    writer.close()

    print(f"\n  = {total} p   {output.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE, help="Base report PDF.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Merged output PDF path.")
    args = parser.parse_args()
    assemble(args.base, INSERTIONS, args.output)


if __name__ == "__main__":
    main()
