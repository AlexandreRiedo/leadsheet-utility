#!/usr/bin/env python3
"""Analyse des tests utilisateurs — piano augmenté (intra-sujet AVEC/SANS).

Lit ``data/responses.csv`` (réponses brutes, une ligne par morceau joué), calcule
les trois scores composites, fait un test de Wilcoxon des rangs signés **exact**
(par énumération des 2^n configurations de signes) pour chaque mesure dans la
**bonne direction**, et sort tableaux + figures.

Voir ``rapport/guide-interpretation-stats.md`` pour la justification de chaque choix
(scoring, direction des hypothèses, p exact, taille d'effet rang-bisériale, dz, k/n).

Dépendances : numpy (requis). matplotlib (optionnel — figures ignorées si absent).
Lancer :  poetry run python rapport/stats/analyze_tests.py
"""
from __future__ import annotations

import csv
import itertools
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "responses.csv"
RESULTS = HERE / "results"
FIGS = HERE / "figures"

# --- matplotlib optionnel -------------------------------------------------
try:
    import matplotlib

    matplotlib.use("Agg")  # pas d'affichage interactif, on écrit des PNG
    import matplotlib.pyplot as plt

    HAVE_MPL = True
except ImportError:  # pragma: no cover
    HAVE_MPL = False

# --- définition des items -------------------------------------------------
TLX_COLS = [
    "tlx_mental",
    "tlx_physique",
    "tlx_temporel",
    "tlx_perf",  # déjà orienté Réussie->Ratée : PAS d'inversion
    "tlx_effort",
    "tlx_frustration",
]
STAI_POS = ["stai_calme", "stai_decontracte", "stai_satisfait"]  # inverser (5 - x)
STAI_NEG = ["stai_tendu", "stai_emu", "stai_inquiet"]  # tels quels
SE_COLS = ["se_q7", "se_q8", "se_q9", "se_q10"]

# mesure -> (alternative, libellé). alternative :
#   "less"    => on prédit AVEC < SANS  (charge/anxiété plus basses)
#   "greater" => on prédit AVEC > SANS  (confiance plus haute)
MEASURES = {
    "RTLX": ("less", "NASA-TLX (RTLX, 0-100) — charge"),
    "STAI6": ("less", "STAI-6 (20-80) — anxiété"),
    "SELFEFF": ("greater", "Auto-efficacité (1-7) — confiance"),
}


# --- helpers de parsing ---------------------------------------------------
def _f(row: dict, key: str):
    """float tolérant : virgule décimale, vide -> None."""
    v = row.get(key)
    if v is None:
        return None
    v = str(v).strip().replace(",", ".")
    if v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


# --- scoring (cf. guide §0) ----------------------------------------------
def score_rtlx(row):
    vals = [_f(row, c) for c in TLX_COLS]
    return float(np.mean(vals)) if all(v is not None for v in vals) else None


def score_stai6(row):
    pos = [_f(row, c) for c in STAI_POS]
    neg = [_f(row, c) for c in STAI_NEG]
    if any(v is None for v in pos + neg):
        return None
    raw = sum(5 - v for v in pos) + sum(neg)  # inversions + items négatifs
    return raw * 20 / 6  # ramené à l'étendue 20-80 du STAI-S complet


def score_selfeff(row):
    vals = [_f(row, c) for c in SE_COLS]
    return float(np.mean(vals)) if all(v is not None for v in vals) else None


SCORERS = {"RTLX": score_rtlx, "STAI6": score_stai6, "SELFEFF": score_selfeff}


# --- statistiques ---------------------------------------------------------
def _avg_ranks(a: np.ndarray) -> np.ndarray:
    """Rangs moyens (1-based), ex aequo -> moyenne des rangs."""
    order = np.argsort(a, kind="mergesort")
    sorted_a = a[order]
    ranks = np.empty(a.size, float)
    i = 0
    while i < a.size:
        j = i
        while j + 1 < a.size and sorted_a[j + 1] == sorted_a[i]:
            j += 1
        avg = (i + j) / 2 + 1  # moyenne des rangs (i+1)..(j+1)
        ranks[order[i : j + 1]] = avg
        i = j + 1
    return ranks


def wilcoxon_exact(avec, sans, alternative):
    """Wilcoxon apparié exact par énumération des signes. Renvoie un dict ou None."""
    d = np.asarray(avec, float) - np.asarray(sans, float)
    n_zero = int(np.sum(d == 0))
    nz = d[d != 0]
    n = nz.size
    if n == 0:
        return None
    ranks = _avg_ranks(np.abs(nz))
    t_plus = float(np.sum(ranks[nz > 0]))
    t_minus = float(np.sum(ranks[nz < 0]))
    total = t_plus + t_minus

    # distribution nulle exacte de T+ : chaque rang a un signe +/- équiprobable
    if n <= 22:
        dist = np.array(
            [
                sum(r for r, s in zip(ranks, signs) if s)
                for signs in itertools.product((0, 1), repeat=n)
            ]
        )
        p_le = float(np.mean(dist <= t_plus + 1e-9))
        p_ge = float(np.mean(dist >= t_plus - 1e-9))
        method = "exact (énumération 2^n)"
    else:  # garde-fou : approximation normale pour gros n (non utilisé ici)
        mu = n * (n + 1) / 4
        sigma = np.sqrt(n * (n + 1) * (2 * n + 1) / 24)
        from math import erf

        z = (t_plus - mu) / sigma
        cdf = 0.5 * (1 + erf(z / np.sqrt(2)))
        p_le, p_ge, method = cdf, 1 - cdf, "approximation normale"

    p_one = p_le if alternative == "less" else p_ge
    p_two = min(1.0, 2 * min(p_le, p_ge))
    sd = np.std(d, ddof=1)
    return {
        "n": n,
        "n_zero": n_zero,
        "t_plus": t_plus,
        "t_minus": t_minus,
        "W": min(t_plus, t_minus),
        "p_one": p_one,
        "p_two": p_two,
        "r_rb": (t_plus - t_minus) / total if total else 0.0,
        "dz": float(np.mean(d) / sd) if sd > 0 else float("nan"),
        "method": method,
    }


def count_direction(avec, sans, alternative):
    d = np.asarray(avec, float) - np.asarray(sans, float)
    nz = d[d != 0]
    k = int(np.sum(nz < 0)) if alternative == "less" else int(np.sum(nz > 0))
    return k, nz.size, int(np.sum(d == 0))


def interpret_r(r):
    a = abs(r)
    if a < 0.10:
        return "négligeable"
    if a < 0.30:
        return "petit"
    if a < 0.50:
        return "moyen"
    return "grand"


def fmt_p(p):
    return "<.001" if p < 0.001 else f"{p:.3f}".lstrip("0").replace("0.", ".", 1)


def med_iqr(x):
    q1, med, q3 = np.percentile(np.asarray(x, float), [25, 50, 75])
    return med, q1, q3


# --- chargement -----------------------------------------------------------
def load_rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return [{(k.strip() if k else k): v for k, v in r.items()} for r in reader]


def paired_scores(rows, measure):
    """Renvoie (ids, avec, sans) pour les participants ayant les 2 conditions scorées."""
    scorer = SCORERS[measure]
    by_pid: dict[str, dict[str, float]] = {}
    for r in rows:
        pid = (r.get("participant") or "").strip()
        cond = (r.get("condition") or "").strip().upper()
        if not pid or cond not in ("AVEC", "SANS"):
            continue
        s = scorer(r)
        if s is not None:
            by_pid.setdefault(pid, {})[cond] = s
    ids, avec, sans = [], [], []
    for pid in sorted(by_pid):
        d = by_pid[pid]
        if "AVEC" in d and "SANS" in d:
            ids.append(pid)
            avec.append(d["AVEC"])
            sans.append(d["SANS"])
    return ids, avec, sans


# --- figures --------------------------------------------------------------
def slope_plot(measure, ids, avec, sans, alternative, label, path):
    fig, ax = plt.subplots(figsize=(3.6, 5.0))
    for s, a in zip(sans, avec):
        good = (a < s) if alternative == "less" else (a > s)
        ax.plot([0, 1], [s, a], "-o", ms=5, lw=1.3, alpha=0.75,
                color="#1f8a8a" if good else "#c0392b")
    ax.plot([0, 1], [np.median(sans), np.median(avec)], "-", lw=3,
            color="black", label="médiane")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["SANS", "AVEC"])
    ax.set_xlim(-0.25, 1.25)
    ax.set_ylabel("score")
    ax.set_title(label, fontsize=9)
    ax.legend(fontsize=8, loc="best")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def tlx_subscale_plot(rows, path):
    labels = ["Mentale", "Physique", "Temporelle", "Perf.", "Effort", "Frustration"]
    med = {"AVEC": [], "SANS": []}
    for cond in ("AVEC", "SANS"):
        for col in TLX_COLS:
            vals = [
                _f(r, col)
                for r in rows
                if (r.get("condition") or "").strip().upper() == cond and _f(r, col) is not None
            ]
            med[cond].append(np.median(vals) if vals else 0.0)
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(x - 0.2, med["SANS"], 0.4, label="SANS", color="#bdc3c7")
    ax.bar(x + 0.2, med["AVEC"], 0.4, label="AVEC", color="#1f8a8a")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_ylabel("médiane (0-100)")
    ax.set_title("NASA-TLX par dimension (médianes)", fontsize=10)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# --- main -----------------------------------------------------------------
def main():
    if not DATA.exists():
        raise SystemExit(f"Fichier introuvable : {DATA}")
    rows = load_rows(DATA)
    RESULTS.mkdir(exist_ok=True)
    FIGS.mkdir(exist_ok=True)

    summary_rows = []
    scores_by_pid: dict[str, dict[str, float]] = {}
    any_data = False

    print("\n=== Analyse des tests utilisateurs ===\n")
    for measure, (alt, label) in MEASURES.items():
        ids, avec, sans = paired_scores(rows, measure)
        if len(ids) < 1:
            print(f"[{measure}] aucune paire complète pour l'instant — ignoré.")
            continue
        any_data = True
        for pid, a, s in zip(ids, avec, sans):
            d = scores_by_pid.setdefault(pid, {})
            d[f"{measure}_AVEC"] = round(a, 2)
            d[f"{measure}_SANS"] = round(s, 2)
            d[f"{measure}_d"] = round(a - s, 2)

        res = wilcoxon_exact(avec, sans, alt)
        k, n_eff, n_zero = count_direction(avec, sans, alt)
        ma, q1a, q3a = med_iqr(avec)
        ms, q1s, q3s = med_iqr(sans)
        sens = "AVEC < SANS" if alt == "less" else "AVEC > SANS"

        print(f"[{measure}] {label}  (H1 : {sens})  n_paires={len(ids)}")
        print(f"   Mdn AVEC = {ma:.1f} ({q1a:.1f}-{q3a:.1f}) | "
              f"Mdn SANS = {ms:.1f} ({q1s:.1f}-{q3s:.1f})")
        if res:
            print(f"   W={res['W']:.1f}  T+={res['t_plus']:.1f}  T-={res['t_minus']:.1f}  "
                  f"[{res['method']}]")
            print(f"   p unilatéral = {fmt_p(res['p_one'])} | p bilatéral = {fmt_p(res['p_two'])}")
            print(f"   r_rb = {res['r_rb']:+.2f} ({interpret_r(res['r_rb'])}) | dz = {res['dz']:+.2f}")
            print(f"   sens prédit : {k}/{n_eff}" + (f"  ({n_zero} ex aequo exclus)" if n_zero else ""))
            summary_rows.append((measure, label, sens, len(ids), ma, ms, res, k, n_eff, n_zero))
        print()

        if HAVE_MPL:
            slope_plot(measure, ids, avec, sans, alt, label,
                       FIGS / f"slope_{measure.lower()}.png")

    if not any_data:
        print("Aucune donnée saisie pour l'instant. Remplis data/responses.csv puis relance.\n")
        return

    # tableau scores.csv
    measure_cols = [f"{m}_{suf}" for m in MEASURES for suf in ("AVEC", "SANS", "d")]
    with (RESULTS / "scores.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["participant", *measure_cols])
        for pid in sorted(scores_by_pid):
            w.writerow([pid, *(scores_by_pid[pid].get(c, "") for c in measure_cols)])

    # tableau wilcoxon_summary.md
    with (RESULTS / "wilcoxon_summary.md").open("w", encoding="utf-8") as fh:
        fh.write("# Résultats — Wilcoxon apparié (exact)\n\n")
        fh.write("| Mesure | H1 | n | Mdn AVEC | Mdn SANS | W | p (uni) | p (bi) | "
                 "r_rb (taille) | dz | sens prédit |\n")
        fh.write("|---|---|---|---|---|---|---|---|---|---|---|\n")
        for m, label, sens, n, ma, ms, res, k, n_eff, n_zero in summary_rows:
            fh.write(
                f"| {m} | {sens} | {n} | {ma:.1f} | {ms:.1f} | {res['W']:.1f} | "
                f"{fmt_p(res['p_one'])} | {fmt_p(res['p_two'])} | "
                f"{res['r_rb']:+.2f} ({interpret_r(res['r_rb'])}) | {res['dz']:+.2f} | "
                f"{k}/{n_eff}{' (' + str(n_zero) + ' nul)' if n_zero else ''} |\n"
            )
        fh.write("\n*p unilatéral dans la direction prédite ; voir guide-interpretation-stats.md.*\n")

    if HAVE_MPL and any((r.get("condition") or "").strip().upper() in ("AVEC", "SANS") for r in rows):
        tlx_subscale_plot(rows, FIGS / "tlx_subscales.png")

    print(f"Écrit : {RESULTS / 'scores.csv'}")
    print(f"Écrit : {RESULTS / 'wilcoxon_summary.md'}")
    if HAVE_MPL:
        print(f"Figures : {FIGS}")
    else:
        print("(matplotlib absent — figures ignorées. `poetry run pip install matplotlib` pour les activer.)")
    print()


if __name__ == "__main__":
    main()
