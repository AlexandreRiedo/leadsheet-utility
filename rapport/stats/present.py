#!/usr/bin/env python3
"""Figures de présentation — trace les figures À PARTIR des scores SAISIS AU TABLEUR.

Pipeline (cf. README) : les scores composites ET les tests de Wilcoxon sont faits À LA
MAIN dans le tableur (Sheets) + le calculateur en ligne — c'est la source de vérité
auditable, défendable au jury. Ce script ne fait QUE la présentation : il lit les valeurs
exportées et trace les figures. Il ne (re)calcule AUCUN score et ne refait AUCUN test ;
pour le recoupement depuis les réponses brutes, voir analyze_tests.py.

    poetry run python rapport/stats/present.py   (deps : groupe Poetry « stats »)

ENTRÉES :
  data/scores_tableur.csv     scores composites, 1 ligne/participant, colonnes
                              <MESURE>_AVEC / _SANS (MESURE ∈ RTLX, STAI6, SELFEFF).
  data/tlx_items_tableur.csv  items NASA-TLX bruts (figure par dimension), format long :
                              1 ligne par participant × condition (participant, condition,
                              tlx_mental, tlx_physique, tlx_temporel, tlx_perf, tlx_effort,
                              tlx_frustration). Facultatif : absent -> figure ignorée.
SORTIES :
  figures/slope_<mesure>.png (×3)   +   figures/tlx_subscales.png
"""

import csv
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")  # rendu hors écran : on écrit des PNG
import matplotlib.pyplot as plt
from matplotlib import font_manager

HERE = Path(__file__).resolve().parent
SCORES = HERE / "data" / "scores_tableur.csv"
TLX_ITEMS = HERE / "data" / "tlx_items_tableur.csv"  # items bruts -> figure par dimension
FIGS = HERE / "figures"
FONTS = HERE / "fonts"  # Plus Jakarta Sans embarqué (TTF) pour une typo cohérente
GOOD, BAD = "#2e8b57", "#c0392b"  # aligné sur H1 (vert) / à contre-sens (rouge)


def use_jakarta():
    """Police Plus Jakarta Sans (TTF embarqués dans fonts/) ; silencieux si absente."""
    reg = FONTS / "PlusJakartaSans-Regular.ttf"
    if not reg.exists():
        return  # pas de police embarquée -> on garde la police matplotlib par défaut
    for ttf in (reg, FONTS / "PlusJakartaSans-Bold.ttf"):
        if ttf.exists():
            font_manager.fontManager.addfont(str(ttf))
    plt.rcParams["font.family"] = "Plus Jakarta Sans"
    plt.rcParams["axes.unicode_minus"] = False  # certains sous-ensembles n'ont pas U+2212


use_jakarta()

# code -> (direction H1, libellé). "less" = on prédit AVEC < SANS ; doit rester
# IDENTIQUE aux directions du tableur et d'analyze_tests.py (sinon les couleurs mentent).
MEASURES = {
    "RTLX": ("less", "NASA-TLX (RTLX, 0-100) — charge"),
    "STAI6": ("less", "STAI-6 (20-80) — anxiété"),
    "SELFEFF": ("greater", "Auto-efficacité (1-7) — confiance"),
}

# 6 dimensions NASA-TLX (colonne brute -> libellé). Perf saisie telle quelle
# (Réussie -> Ratée, + haut = pire), SANS inversion — cohérent avec le composite RTLX.
TLX = {
    "tlx_mental": "Mentale",
    "tlx_physique": "Physique",
    "tlx_temporel": "Temporelle",
    "tlx_perf": "Perf.",
    "tlx_effort": "Effort",
    "tlx_frustration": "Frustration",
}


def cell(row, col):
    """Une cellule -> float (virgule décimale tolérée) ; vide/absente -> nan."""
    text = (row.get(col) or "").strip().replace(",", ".")
    return float(text) if text else np.nan


def load(path):
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def paired(rows, code):
    """(pids, avec, sans) alignés ; ne garde que les participants aux 2 cellules remplies."""
    pids, avec, sans = [], [], []
    for row in rows:
        a, s = cell(row, f"{code}_AVEC"), cell(row, f"{code}_SANS")
        if not (np.isnan(a) or np.isnan(s)):
            pids.append(row.get("participant", "?"))
            avec.append(a)
            sans.append(s)
    return pids, np.array(avec), np.array(sans)


def slope_plot(pids, avec, sans, alternative, label, path):
    """Une ligne par participant (SANS -> AVEC) : VERTE si alignée sur H1, sinon ROUGE.
    PID à gauche (côté SANS) ; les ex aequo (même score SANS) sont empilés pour ne pas
    se chevaucher. Médiane en gras, étiquetée à droite."""
    fig, ax = plt.subplots(figsize=(3.8, 5.0))
    colors = []
    for a, s in zip(avec, sans):
        win = a < s if alternative == "less" else a > s
        colors.append(GOOD if win else BAD)
        ax.plot([0, 1], [s, a], "-o", lw=1.3, alpha=0.8, color=colors[-1])
    ax.plot([0, 1], [np.median(sans), np.median(avec)], "k-", lw=3)
    ax.text(1.06, np.median(avec), "médiane", va="center", ha="left", fontsize=8, fontweight="bold")

    # Étiquettes PID : empilées verticalement autour du score quand des participants
    # sont à égalité au SANS (sinon elles se superposeraient au même y).
    vgap = (float(np.ptp(np.concatenate([avec, sans]))) or 1.0) * 0.05
    groups = {}
    for pid, s, c in zip(pids, sans, colors):
        groups.setdefault(s, []).append((pid, c))
    for s, members in groups.items():
        members.sort()  # ordre déterministe par PID
        for j, (pid, c) in enumerate(members):
            dy = (j - (len(members) - 1) / 2) * vgap
            ax.text(-0.06, s + dy, pid, va="center", ha="right", fontsize=7, color=c)

    ax.set_xticks([0, 1], ["SANS", "AVEC"])
    ax.set(xlim=(-0.55, 1.45), ylabel="score", title=label)
    ax.margins(y=0.1)  # un peu d'air en haut/bas pour les étiquettes empilées
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def tlx_subscale_plot(rows, path):
    """Médianes des 6 sous-dimensions NASA-TLX, SANS vs AVEC (0-100 ; + haut = + de charge)."""

    def med(cond, col):
        vals = [cell(r, col) for r in rows if (r.get("condition") or "").strip().upper() == cond]
        vals = [v for v in vals if not np.isnan(v)]
        return np.median(vals) if vals else np.nan

    cols = list(TLX)
    x = np.arange(len(cols))
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.bar(x - 0.2, [med("SANS", c) for c in cols], 0.4, label="SANS", color="#bdc3c7")
    ax.bar(x + 0.2, [med("AVEC", c) for c in cols], 0.4, label="AVEC", color=GOOD)
    ax.set_xticks(x, list(TLX.values()), rotation=20, ha="right")
    ax.set(ylabel="médiane (0-100)", ylim=(0, 100), title="NASA-TLX (RTLX, 0-100) par dimension (médianes)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    FIGS.mkdir(exist_ok=True)
    print("\n=== Figures de présentation (valeurs du tableur) ===\n")

    # 1) Une figure en pente par mesure, depuis les scores composites.
    if SCORES.exists():
        rows = load(SCORES)
        for code, (alt, label) in MEASURES.items():
            pids, avec, sans = paired(rows, code)
            if avec.size == 0:
                print(f"[{code}] aucune paire remplie — ignoré.")
                continue
            out = FIGS / f"slope_{code.lower()}.png"
            slope_plot(pids, avec, sans, alt, label, out)
            sens = "AVEC < SANS" if alt == "less" else "AVEC > SANS"
            k = int((avec < sans).sum() if alt == "less" else (avec > sans).sum())
            print(f"[{code}] n = {avec.size}   sens prédit {k}/{avec.size} ({sens})   -> {out.name}")
    else:
        print(f"[scores] {SCORES.name} manquant — figures en pente ignorées.")

    # 2) NASA-TLX par dimension, depuis les items bruts (format long, facultatif).
    if TLX_ITEMS.exists():
        tlx_rows = load(TLX_ITEMS)
        if any(not np.isnan(cell(r, c)) for r in tlx_rows for c in TLX):
            tlx_subscale_plot(tlx_rows, FIGS / "tlx_subscales.png")
            print("[TLX]    6 dimensions (médianes SANS vs AVEC)      -> tlx_subscales.png")
        else:
            print(f"[TLX]    {TLX_ITEMS.name} vide — figure par dimension ignorée.")
    else:
        print(f"[TLX]    {TLX_ITEMS.name} manquant — figure par dimension ignorée.")

    print(f"\nFigures dans {FIGS}\n")


if __name__ == "__main__":
    main()
