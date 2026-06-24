#!/usr/bin/env python3
"""Figure §3.4 : extrait d'un alignement OMR fautif (All The Things You Are).

Montre, beat par beat, deux extraits du diff produit par evaluate_custom : l'ouverture
(temps hallucinés autour du Fm7 initial) et un passage plus loin (qualité et bémols mal
lus). Chaque temps est une colonne ; la ligne de référence reste neutre, le côté OMR
(sortie + opération) est teinté selon le type d'erreur, comme la figure omr_fiabilite.

    poetry run python rapport/figures/solution-conceptuelle/omr_alignment.py

SORTIE : omr_alignment.png (largeur justification A4, Plus Jakarta Sans embarqué).
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle

HERE = Path(__file__).resolve().parent
FONTS = HERE.parent.parent / "stats" / "fonts"
OUT = HERE / "omr_alignment.png"

GOOD_T, HARM_T, STRUCT_T = "#d8efe2", "#fbe7c8", "#f6d6d1"  # teintes (correct/harm/struct)
GOOD, HARM, STRUCT = "#2e8b57", "#e08e0b", "#c0392b"        # pleins (légende)
GRID = "#cfd6dc"
INK = "#1a1a1a"
DPI = 200

# Chaque panneau : (titre, ref[], hyp[], op[]). "…" = ellipse (temps omis).
PANELS = [
    ("Ouverture : la zone du Fm7 initial",
     ["***", "***", "***", "…", "F:min7", "F:min7"],
     ["F:7", "F:maj", "G:maj", "…", "F:min7", "F:min7"],
     ["I 1", "I 1", "I 1", "…", "C", "C"]),
    ("Quelques mesures plus loin : qualité et bémols mal lus",
     ["Eb:7", "Ab:maj7", "Ab:maj7", "Db:maj7", "Db:maj7"],
     ["Eb:7", "Ab:7", "Ab:7", "D:maj7", "D:maj7"],
     ["C", "S 0.5", "S 0.5", "S 1.0", "S 1.0"]),
]

W = 7.2              # largeur figure (pouces)
LABEL_W = 0.62       # colonne de gauche (Réf. / OMR / Op.)
ROW_H = 0.30         # hauteur d'une cellule
PANEL_LABEL_H = 0.27
TITLE_H = 0.40
LEGEND_H = 0.40
GAP = 0.20
PAD = 0.06


def use_jakarta():
    reg = FONTS / "PlusJakartaSans-Regular.ttf"
    if not reg.exists():
        return
    for ttf in (reg, FONTS / "PlusJakartaSans-Bold.ttf"):
        if ttf.exists():
            font_manager.fontManager.addfont(str(ttf))
    plt.rcParams["font.family"] = "Plus Jakarta Sans"
    plt.rcParams["axes.unicode_minus"] = False


def op_tint(op):
    o = op.strip()
    if o.startswith("S"):
        return HARM_T
    if o.startswith(("I", "D")):
        return STRUCT_T
    if o == "C":
        return GOOD_T
    return "white"  # ellipse


def main():
    use_jakarta()
    total_h = (TITLE_H + PAD
               + sum(PANEL_LABEL_H + 3 * ROW_H for _ in PANELS)
               + GAP * len(PANELS) + LEGEND_H + PAD)

    fig, ax = plt.subplots(figsize=(W, total_h))
    ax.set_axis_off()
    ax.set_xlim(0, W)
    ax.set_ylim(0, total_h)

    y = total_h - PAD
    ax.text(0, y, "Sortie d'OMR fautive : extrait de l'alignement (All The Things You Are)",
            ha="left", va="top", fontsize=11, fontweight="bold", color=INK)
    y -= TITLE_H

    rowlabels = ("Réf.", "OMR", "Op.")
    for (label, ref, hyp, op) in PANELS:
        ax.text(0, y, label, ha="left", va="top", fontsize=9,
                fontweight="bold", color=INK)
        y -= PANEL_LABEL_H
        ncol = len(op)
        cw = (W - LABEL_W) / ncol
        for ri, (rowname, cells) in enumerate(zip(rowlabels, (ref, hyp, op))):
            ytop = y - ri * ROW_H
            ax.text(LABEL_W - 0.08, ytop - ROW_H / 2, rowname, ha="right",
                    va="center", fontsize=8, color="#666666")
            for ci, val in enumerate(cells):
                x0 = LABEL_W + ci * cw
                # Réf. neutre ; OMR + Op. teintés selon l'erreur de la colonne.
                face = "white" if ri == 0 else op_tint(op[ci])
                ax.add_patch(Rectangle((x0, ytop - ROW_H), cw, ROW_H,
                                       facecolor=face, edgecolor=GRID, lw=0.6))
                ax.text(x0 + cw / 2, ytop - ROW_H / 2, val, ha="center",
                        va="center", fontsize=8.3,
                        fontweight="bold" if ri == 1 else "normal", color=INK)
        y -= 3 * ROW_H + GAP

    # Légende, alignée sur omr_fiabilite. Positions fixes pour éviter tout chevauchement.
    y -= 0.02
    items = [(LABEL_W, "correct", GOOD),
             (2.30, "accord faux (harmonique)", HARM),
             (4.85, "temps faux (structurel)", STRUCT)]
    for x, text, color in items:
        ax.add_patch(Rectangle((x, y - 0.18), 0.22, 0.16, facecolor=color,
                               edgecolor="none"))
        ax.text(x + 0.30, y - 0.10, text, ha="left", va="center", fontsize=8,
                color=INK)

    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(OUT, dpi=DPI, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    print(f"Figure écrite : {OUT}")


if __name__ == "__main__":
    main()
