#!/usr/bin/env python3
"""Figure §3.4 — fiabilité de l'OMR (Martinez-Sevilla et al.) sur 11 standards.

Trace une barre empilee a 100 % par morceau, decomposant chaque grille en trois
parts des temps de reference : la part CORRECTE (= precision ponderee), la penalite
HARMONIQUE (accords faux, somme des substitutions) et la penalite STRUCTURELLE
(temps faux : insertions + suppressions, a 1.0 chacun). Comme precision = 1 - total/ref
et total = structurel + harmonique, les trois parts somment exactement a 100 %.

Les valeurs sont saisies a la main depuis les rapports de evaluate_custom (un par
standard) : ce script ne fait QUE la presentation, a l'image de rapport/stats/present.py.

    poetry run python rapport/figures/solution-conceptuelle/omr_fiabilite.py

SORTIE : omr_fiabilite.png (largeur justification A4, Plus Jakarta Sans embarque).
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

HERE = Path(__file__).resolve().parent
FONTS = HERE.parent.parent / "stats" / "fonts"  # police partagee avec le chap. stats
OUT = HERE / "omr_fiabilite.png"

# Palette : aligne sur le chap. stats (vert = bon) ; orange/rouge pour les deux familles
# d'erreur. Le rouge structurel reprend le BAD du chapitre stats.
GOOD, HARM, STRUCT = "#2e8b57", "#e08e0b", "#c0392b"
GRID = "#d4d4d4"

A4_WIDTH_IN, MARGIN_IN = 8.27, 1.0
FIG_WIDTH = A4_WIDTH_IN - 2 * MARGIN_IN
DPI = 200

# (titre, temps reference, penalite structurelle D+I, penalite harmonique somme S).
# Source : les 11 rapports REPORT_*.txt de evaluate_custom.
DATA = [
    ("All The Things You Are", 144, 23, 49.0),
    ("Autumn Leaves", 128, 38, 15.0),
    ("Fly Me to the Moon", 128, 1, 49.5),
    ("Misty", 128, 41, 37.75),
    ("Oleo", 128, 42, 34.5),
    ("Sandu", 96, 32, 49.0),
    ("Satin Doll", 128, 16, 60.5),
    ("Stella by Starlight", 128, 7, 55.5),
    ("Summertime", 64, 22, 21.2),
    ("On the Sunny Side of the Street", 128, 28, 20.5),
    ('Take the "A" Train', 128, 65, 18.5),
]


def use_jakarta():
    reg = FONTS / "PlusJakartaSans-Regular.ttf"
    if not reg.exists():
        return
    for ttf in (reg, FONTS / "PlusJakartaSans-Bold.ttf"):
        if ttf.exists():
            font_manager.fontManager.addfont(str(ttf))
    plt.rcParams["font.family"] = "Plus Jakarta Sans"
    plt.rcParams["axes.unicode_minus"] = False


def main():
    use_jakarta()
    plt.rcParams.update(
        {
            "savefig.dpi": DPI,
            "axes.axisbelow": True,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.titlepad": 12,
            "axes.labelsize": 11,
            "axes.edgecolor": "#888888",
            "grid.color": GRID,
        }
    )

    # Parts en % des temps de reference, triees par part correcte croissante (pire en bas).
    rows = []
    for name, ref, struct, harm in DATA:
        correct = 100.0 * (1.0 - (struct + harm) / ref)
        rows.append((name, correct, 100.0 * harm / ref, 100.0 * struct / ref))
    rows.sort(key=lambda r: r[1])  # part correcte croissante

    names = [r[0] for r in rows]
    correct = np.array([r[1] for r in rows])
    harm = np.array([r[2] for r in rows])
    struct = np.array([r[3] for r in rows])
    y = np.arange(len(names))

    fig, ax = plt.subplots(figsize=(FIG_WIDTH, 5.2))
    ax.barh(y, correct, color=GOOD, label="correct")
    ax.barh(y, harm, left=correct, color=HARM, label="accords faux (harmonique)")
    ax.barh(y, struct, left=correct + harm, color=STRUCT, label="temps faux (structurel)")

    # Valeur de precision a gauche de chaque barre.
    for yi, c in zip(y, correct):
        ax.text(1.5, float(yi), f"{c:.0f}", va="center", ha="left", fontsize=8,
                fontweight="bold", color="white")

    mean_correct = float(correct.mean())
    ax.axvline(mean_correct, color="#333333", lw=1.2, ls=(0, (4, 3)), zorder=5)
    ax.text(mean_correct + 1, len(names) - 0.4,
            f"précision moyenne : {mean_correct:.0f}", fontsize=8, fontweight="bold")

    ax.set_yticks(y, names, fontsize=9)
    ax.set_xticks(np.arange(0, 101, 20))
    ax.set(xlim=(0, 100), xlabel="part des temps de référence (%)",
           title="Fiabilité de l'OMR sur 11 standards de jazz")
    ax.grid(True, axis="x", color=GRID, linewidth=0.9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper center",
              bbox_to_anchor=(0.5, -0.22))
    fig.tight_layout()
    fig.savefig(OUT, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Figure ecrite : {OUT}")


if __name__ == "__main__":
    main()
