"""Print the guide-tone line for a lead sheet.

Usage:
    poetry run python scripts/show_guide_tone_line.py <piece>

Examples:
    poetry run python scripts/show_guide_tone_line.py 26_2
    poetry run python scripts/show_guide_tone_line.py all_the_things_you_are

<piece> is the stem of a .tsv file in data/leadsheets/.
"""

import sys
from pathlib import Path

# Allow running from the project root without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from leadsheet_utility.leadsheet.parser import parse_leadsheet
from leadsheet_utility.harmony import analyze

PC_NAME = {
    0: "C", 1: "Db", 2: "D", 3: "Eb", 4: "E", 5: "F",
    6: "Gb", 7: "G", 8: "Ab", 9: "A", 10: "Bb", 11: "B",
}


def note_name(midi: int) -> str:
    return f"{PC_NAME[midi % 12]}{midi // 12 - 1}"


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    stem = sys.argv[1]
    tsv = Path(__file__).resolve().parent.parent / "data" / "leadsheets" / f"{stem}.tsv"
    if not tsv.exists():
        available = sorted(p.stem for p in tsv.parent.glob("*.tsv"))
        print(f"Error: '{stem}.tsv' not found. Available lead sheets:")
        for name in available:
            print(f"  {name}")
        sys.exit(1)

    ls = parse_leadsheet(tsv)
    analyze(ls)
    p0, p1 = ls.guide_tone_line

    print(f"\n{ls.title}  —  guide-tone line ({len(ls.chords)} chords)\n")
    print(f"  {'Beat':>6}  {'Chord':12s}  {'Path 0':>8s}  {'Path 1':>8s}")
    print(f"  {'-'*6}  {'-'*12}  {'-'*8}  {'-'*8}")
    for i, chord in enumerate(ls.chords):
        print(f"  {chord.start_beat:6.1f}  {chord.chord_symbol:12s}"
              f"  {note_name(p0[i]):>8s}  {note_name(p1[i]):>8s}")

    print(f"\n  Path 0 range: {note_name(min(p0))} – {note_name(max(p0))}")
    print(f"  Path 1 range: {note_name(min(p1))} – {note_name(max(p1))}")


if __name__ == "__main__":
    main()
