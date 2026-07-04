#!/usr/bin/env python3
"""Analyse des tests utilisateurs — piano augmenté (intra-sujet AVEC/SANS).

Pour chaque mesure (charge, anxiété, confiance) : un score composite par participant
et par condition → Wilcoxon apparié exact (scipy) dans la direction prédite → taille
d'effet + figures. Justification de chaque choix : rapport/plans/guide-interpretation-stats.md.

    poetry run python rapport/stats/analyze_tests.py   (deps : groupe Poetry « stats »)

RÔLE : OUTIL DE RECOUPEMENT, PAS LA SOURCE DE VÉRITÉ.
À n = 8, les calculs de référence sont faits à la main dans un tableur (Sheets/Excel) :
c'est la version auditable et défendable au jury. Ce script ne sert qu'à *vérifier* ces
calculs — le lancer une fois, confirmer que W, r_rb et p concordent avec le tableur, et
investiguer tout écart avant l'export. La table de p exacte à recopier dans le tableur est
dans guide-interpretation-stats.md §2.1 (rappel : aucune fonction Wilcoxon dans un tableur).
"""

import csv
from pathlib import Path
from typing import NamedTuple

import matplotlib
import numpy as np

matplotlib.use("Agg")  # rendu hors écran : on écrit des PNG
import matplotlib.pyplot as plt
from scipy.stats import rankdata, wilcoxon

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "responses.csv"
RESULTS = HERE / "results"
# Sous-dossier DÉDIÉ au recoupement : ce script et present.py traceraient sinon les
# MÊMES fichiers (slope_*.png, tlx_subscales.png) — le dernier lancé écraserait l'autre.
# present.py possède figures/ (figures de présentation du rapport) ; ce script écrit ici,
# pour ne JAMAIS clobber les figures insérées dans la thèse. Voir README §3.
FIGS = HERE / "figures" / "_verify"
GOOD, BAD = "#1f8a8a", "#c0392b"  # couleurs : va dans le sens prédit / à contre-sens

# Items des trois questionnaires (noms de colonnes dans responses.csv).
TLX = [
    "tlx_mental",
    "tlx_physique",
    "tlx_temporel",
    "tlx_perf",
    "tlx_effort",
    "tlx_frustration",
]
STAI_POS = ["stai_calme", "stai_decontracte", "stai_satisfait"]  # à inverser (5 - x)
STAI_NEG = ["stai_tendu", "stai_emu", "stai_inquiet"]
SE = ["se_q7", "se_q8", "se_q9", "se_q10"]


# --- scoring : un score par ligne, nan si une cellule manque (cf. guide §0) ---
def cell(row, col):
    """Une cellule -> float (virgule décimale tolérée) ; vide -> nan."""
    text = (row.get(col) or "").strip().replace(",", ".")
    return float(text) if text else np.nan


def values(row, cols):
    """Plusieurs colonnes -> array float (vide -> nan, qui se propage au score)."""
    return np.array([cell(row, c) for c in cols])


def score_rtlx(row):
    return values(row, TLX).mean()  # moyenne des 6 dimensions


def score_stai6(row):
    pos, neg = values(row, STAI_POS), values(row, STAI_NEG)
    return ((5 - pos).sum() + neg.sum()) * 20 / 6  # inversions, puis échelle 20-80


def score_selfeff(row):
    return values(row, SE).mean()  # moyenne des items 7-10


# mesure -> (fonction de score, direction H1, libellé). "less" = on prédit AVEC < SANS.
MEASURES = {
    "RTLX": (score_rtlx, "less", "NASA-TLX (RTLX, 0-100) — charge"),
    "STAI6": (score_stai6, "less", "STAI-6 (20-80) — anxiété"),
    "SELFEFF": (score_selfeff, "greater", "Auto-efficacité (1-7) — confiance"),
}


# --- statistique : Wilcoxon apparié + tailles d'effet ---------------------
class Stats(NamedTuple):
    n: int  # nombre de paires (différences nulles exclues)
    n_zero: int  # différences nulles (d = 0), écartées par le test
    t_plus: float  # somme des rangs des différences positives
    t_minus: float  # ... des négatives
    W: float  # min(T+, T-)
    p_one: float  # p exacte, unilatérale, dans la direction prédite
    p_two: float  # p exacte, bilatérale (option conservatrice)
    r_rb: float  # corrélation rang-bisériale, -1..+1 (Kerby 2014)
    dz: float  # d de Cohen apparié
    k: int  # paires allant dans le sens prédit


def analyse(avec, sans, alternative) -> Stats:
    """Wilcoxon des rangs signés exact (n ≤ 50) sur les paires AVEC/SANS.

    On ARRONDIT les différences avant de classer : les scores composites tombent sur
    des fractions de 1/6 (TLX/STAI) ou 1/4 (auto-eff.), donc des d *mathématiquement*
    égaux (ex. trois d = 30 au STAI-6) sortent à un epsilon près de l'arithmétique
    flottante. Sans arrondi, `rankdata` les voit distincts et `method="exact"` —
    qui suppose des rangs distincts et NE corrige PAS les ex aequo — renvoie une p
    qui dépend de ce bruit (STAI-6 : .156 ex aequo réels → .191 si l'epsilon les
    sépare). L'arrondi rétablit les vrais ex aequo (rangs moyennés) et rend la p
    reproductible et alignée sur le tableur fait à la main. NB : à n ≤ 8 avec ex aequo
    aucune méthode n'est parfaite ; l'exact reste préférable à la normale approchée.
    """
    d = np.round(avec - sans, 4)  # collapse l'epsilon flottant → vrais ex aequo
    nz = d[d != 0]  # le test écarte les différences nulles
    ranks = rankdata(np.abs(nz))  # rangs des |différences|, ex aequo moyennés
    t_plus, t_minus = ranks[nz > 0].sum(), ranks[nz < 0].sum()
    k = (nz < 0).sum() if alternative == "less" else (nz > 0).sum()
    return Stats(
        n=nz.size,
        n_zero=int((d == 0).sum()),
        t_plus=t_plus,
        t_minus=t_minus,
        W=min(t_plus, t_minus),
        # scipy classe les mêmes nz arrondis → p cohérente avec T+/T-/r_rb ci-dessus
        p_one=wilcoxon(nz, alternative=alternative, method="exact").pvalue,  # type: ignore[attr-defined]  # scipy: pas de stubs
        p_two=wilcoxon(nz, alternative="two-sided", method="exact").pvalue,  # type: ignore[attr-defined]  # scipy: pas de stubs
        r_rb=(t_plus - t_minus) / (t_plus + t_minus),
        dz=d.mean() / d.std(ddof=1) if d.size > 1 else np.nan,
        k=int(k),
    )


def interpret_r(r):  # barème de Cohen (repère, cf. guide §3.3)
    a = abs(r)
    if a < 0.10:
        return "négligeable"
    if a < 0.30:
        return "petit"
    if a < 0.50:
        return "moyen"
    return "grand"


def fmt_p(p):  # style APA : pas de 0 initial
    return "<.001" if p < 0.001 else f"{p:.3f}".lstrip("0")


def med_iqr(x):  # "médiane (Q1-Q3)"
    q1, med, q3 = np.percentile(x, [25, 50, 75])
    return f"{med:.1f} ({q1:.1f}-{q3:.1f})"


# --- chargement & appariement AVEC/SANS -----------------------------------
def load(path):
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def paired_scores(rows, score):
    """{participant: {"AVEC": score, "SANS": score}} ; lignes incomplètes ignorées."""
    by_pid = {}
    for row in rows:
        s = score(row)
        if not np.isnan(s):
            by_pid.setdefault(row["participant"], {})[row["condition"]] = s
    return by_pid


# --- figures --------------------------------------------------------------
def slope_plot(avec, sans, alternative, label, path):
    """Une ligne par participant (SANS -> AVEC), médiane en gras."""
    fig, ax = plt.subplots(figsize=(3.6, 5.0))
    for a, s in zip(avec, sans):
        win = a < s if alternative == "less" else a > s
        ax.plot([0, 1], [s, a], "-o", lw=1.3, alpha=0.75, color=GOOD if win else BAD)
    ax.plot([0, 1], [np.median(sans), np.median(avec)], "k-", lw=3, label="médiane")
    ax.set_xticks([0, 1], ["SANS", "AVEC"])
    ax.set(xlim=(-0.25, 1.25), ylabel="score", title=label)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def tlx_subscale_plot(rows, path):
    """Médianes des 6 sous-dimensions TLX, AVEC vs SANS (exploratoire)."""
    labels = ["Mentale", "Physique", "Temporelle", "Perf.", "Effort", "Frustration"]

    def median(cond, col):
        vals = [cell(r, col) for r in rows if r["condition"] == cond]
        vals = [v for v in vals if not np.isnan(v)]
        return np.median(vals) if vals else 0

    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(
        x - 0.2, [median("SANS", c) for c in TLX], 0.4, label="SANS", color="#bdc3c7"
    )
    ax.bar(x + 0.2, [median("AVEC", c) for c in TLX], 0.4, label="AVEC", color=GOOD)
    ax.set_xticks(x, labels, rotation=20, ha="right")
    ax.set(ylabel="médiane (0-100)", title="NASA-TLX par dimension")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# --- sorties --------------------------------------------------------------
def write_scores(table, path):
    cols = [f"{m}_{suf}" for m in MEASURES for suf in ("AVEC", "SANS", "d")]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["participant", *cols])
        for pid in sorted(table):
            w.writerow([pid, *(table[pid].get(c, "") for c in cols)])


def write_summary(summary, path):
    lines = [
        "# Wilcoxon apparié (scipy, exact à n ≤ 50)",
        "",
        "| Mesure | H1 | n | Mdn AVEC | Mdn SANS | W | p (uni) | p (bi) | r_rb | dz | sens |",
        "|" + "---|" * 11,
    ]
    for code, sens, n, ma, ms, st in summary:
        nul = f" ({st.n_zero} nul)" if st.n_zero else ""
        lines.append(
            f"| {code} | {sens} | {n} | {ma:.1f} | {ms:.1f} | {st.W:g} | "
            f"{fmt_p(st.p_one)} | {fmt_p(st.p_two)} | {st.r_rb:+.2f} ({interpret_r(st.r_rb)}) | "
            f"{st.dz:+.2f} | {st.k}/{st.n}{nul} |"
        )
    lines += [
        "",
        "*p unilatéral dans la direction prédite ; cf. guide-interpretation-stats.md.*",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --- main -----------------------------------------------------------------
def main():
    rows = load(DATA)
    RESULTS.mkdir(exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)  # crée figures/ + _verify/ au besoin

    table = {}  # participant -> {RTLX_AVEC: ..., ...}  pour scores.csv
    summary = []  # une ligne par mesure pour le tableau de résultats

    print("\n=== Analyse des tests utilisateurs ===\n")
    for code, (score, alt, label) in MEASURES.items():
        pairs = paired_scores(rows, score)
        ids = sorted(p for p, c in pairs.items() if "AVEC" in c and "SANS" in c)
        if not ids:
            print(f"[{code}] aucune paire complète pour l'instant — ignoré.\n")
            continue

        avec = np.array([pairs[p]["AVEC"] for p in ids])
        sans = np.array([pairs[p]["SANS"] for p in ids])
        st = analyse(avec, sans, alt)
        sens = "AVEC < SANS" if alt == "less" else "AVEC > SANS"

        for p in ids:
            a, s = pairs[p]["AVEC"], pairs[p]["SANS"]
            table.setdefault(p, {}).update(
                {
                    f"{code}_AVEC": round(a, 2),
                    f"{code}_SANS": round(s, 2),
                    f"{code}_d": round(a - s, 2),
                }
            )
        summary.append((code, sens, len(ids), np.median(avec), np.median(sans), st))
        slope_plot(avec, sans, alt, label, FIGS / f"slope_{code.lower()}.png")

        nul = f" ({st.n_zero} nul)" if st.n_zero else ""
        print(f"[{code}] {label}  (H1 : {sens}, n = {len(ids)})")
        print(f"    Mdn AVEC = {med_iqr(avec)}   Mdn SANS = {med_iqr(sans)}")
        print(f"    W = {st.W:g}   p = {fmt_p(st.p_one)} uni / {fmt_p(st.p_two)} bi")
        print(
            f"    r_rb = {st.r_rb:+.2f} ({interpret_r(st.r_rb)})   dz = {st.dz:+.2f}"
            f"   sens prédit : {st.k}/{st.n}{nul}\n"
        )

    if not summary:
        print("Aucune donnée complète. Remplis data/responses.csv puis relance.\n")
        return

    write_scores(table, RESULTS / "scores.csv")
    write_summary(summary, RESULTS / "wilcoxon_summary.md")
    tlx_subscale_plot(rows, FIGS / "tlx_subscales.png")
    print(f"Écrit : {RESULTS / 'scores.csv'} + wilcoxon_summary.md")
    print(f"Figures de recoupement (jetables) : {FIGS}")
    print("  -> les figures du rapport restent dans figures/ (present.py).\n")


if __name__ == "__main__":
    main()
