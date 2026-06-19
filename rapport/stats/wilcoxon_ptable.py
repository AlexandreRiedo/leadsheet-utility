#!/usr/bin/env python3
"""Table de p EXACTE du Wilcoxon des rangs signés (via scipy), cf. guide §2.1.

Pour chaque W = min(T+, T-), on fabrique des différences ±1..±n dont les rangs
positifs somment à W, et on lit le p unilatéral EXACT de scipy. La distribution
nulle étant symétrique : p bilatéral = 2 x p unilatéral.

    poetry run python rapport/stats/wilcoxon_ptable.py   (dépendance : scipy)
"""

from scipy.stats import wilcoxon


def p_uni(n, w):
    """p unilatéral exact pour W = w à la taille n (scipy, method=exact)."""
    rem, d = w, []
    for r in range(n, 0, -1):  # glouton : {1..n} est complet -> tout w atteignable
        keep = r <= rem
        d.append(r if keep else -r)  # rangs positifs -> somme = w = T+
        rem -= r * keep
    return wilcoxon(d, alternative="less", method="exact").pvalue  # type: ignore[attr-defined]


for n in (7, 8):
    print(f"\nn = {n}    W | p uni | p bi")
    for w in range(n + 2):
        p = p_uni(n, w)
        if p > 0.10:  # au-delà : jamais significatif, inutile d'imprimer
            break
        print(f"        {w:>2} | {p:.3f} | {min(2 * p, 1):.3f}")
