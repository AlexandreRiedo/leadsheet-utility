"""Extract the §2 Mermaid blocks from plan-solution-technique.md into .mmd files.

Throwaway helper: keeps the rendered PNGs in sync with the plan doc (the doc is
the source of truth). Run from anywhere; paths are resolved relative to this file.
"""

import re
import unicodedata
from pathlib import Path

here = Path(__file__).resolve().parent  # rapport/
src = here / "plan-solution-technique.md"
out = here / "figures" / "solution-technique"
out.mkdir(parents=True, exist_ok=True)

lines = src.read_text(encoding="utf-8").splitlines()


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s[:28].strip("-")


cur_id = cur_title = None
figs: list[str] = []
i = 0
while i < len(lines):
    line = lines[i]
    m = re.match(r"^###\s+(2\.[A-Za-z]+(?:\s+bis)?)\s+[—–-]\s+(.*)$", line)
    if m:
        cur_id = m.group(1)
        cur_title = re.sub(r"\s*\[.*?\]\s*$", "", m.group(2)).strip()
        i += 1
        continue
    if line.strip().lower().startswith("```mermaid"):
        i += 1
        block: list[str] = []
        while i < len(lines) and not lines[i].strip().startswith("```"):
            block.append(lines[i])
            i += 1
        idnorm = (cur_id or "fig").replace(".", "").replace(" ", "")
        name = f"{idnorm}-{slug(cur_title or '')}"
        (out / f"{name}.mmd").write_text("\n".join(block) + "\n", encoding="utf-8")
        figs.append(name)
        i += 1
        continue
    i += 1

for f in figs:
    print(f)
print(f"TOTAL={len(figs)}")
