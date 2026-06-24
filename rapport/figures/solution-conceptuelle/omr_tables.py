#!/usr/bin/env python3
"""Rend les tables du §3.4 (OMR) en images PNG insérables dans le rapport.

Dessine chaque table à la main (rectangles + texte) plutôt que via ax.table, pour
maîtriser le retour à la ligne des en-têtes, le rembourrage et la ligne de total.
Même typo que les figures stats : Plus Jakarta Sans embarqué, largeur justification A4.

    poetry run python rapport/figures/solution-conceptuelle/omr_tables.py

SORTIES :
  omr_table_resultats.png        résultats complets par standard (8 colonnes)
  omr_table_resultats_compact.png  version courte pour insertion dans le texte
  omr_table_bareme.png           barème de la distance harmonique
  omr_table_ventilation.png      ventilation des erreurs sur le corpus
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle

HERE = Path(__file__).resolve().parent
FONTS = HERE.parent.parent / "stats" / "fonts"

A4_WIDTH_IN, MARGIN_IN = 8.27, 1.0
FIG_WIDTH = A4_WIDTH_IN - 2 * MARGIN_IN  # ~6.27"
DPI = 200

HEADER_BG = "#2c3e50"   # bandeau d'en-tête (texte blanc)
ROW_ALT = "#f3f5f7"     # une ligne sur deux
TOTAL_BG = "#dbe4ea"    # ligne de total
GRID = "#cfd6dc"
INK = "#1a1a1a"
HARM_BAND = "#fbe7c8"   # bande de section "harmonique" (teinte de l'orange figure)
STRUCT_BAND = "#f6d6d1"  # bande de section "structurelle" (teinte du rouge figure)


def use_jakarta():
    reg = FONTS / "PlusJakartaSans-Regular.ttf"
    if not reg.exists():
        return
    for ttf in (reg, FONTS / "PlusJakartaSans-Bold.ttf"):
        if ttf.exists():
            font_manager.fontManager.addfont(str(ttf))
    plt.rcParams["font.family"] = "Plus Jakarta Sans"
    plt.rcParams["axes.unicode_minus"] = False


def _lines(cell):
    return str(cell).split("\n")


def draw_table(headers, rows, col_fracs, aligns, out, *, title=None,
               fig_width=FIG_WIDTH, total_row=False, fontsize=8.5,
               header_fontsize=8.5, line_in=0.165, pad_lines=0.7):
    """Dessine une table. `rows` : liste de listes ; cellules multi-lignes via \\n.
    `total_row` : la dernière ligne est mise en valeur (fond + gras)."""
    # Hauteur de chaque bande, en "unités-ligne" (nb de lignes de texte + rembourrage).
    # Une "section" (dict {"section": ...}) est une bande pleine largeur d'une ligne.
    band_units = [max(len(_lines(h)) for h in headers) + pad_lines]
    for r in rows:
        if isinstance(r, dict):
            band_units.append(1 + 0.6)
        else:
            band_units.append(max(len(_lines(c)) for c in r) + pad_lines)
    total_units = sum(band_units)

    title_in = 0.34 if title else 0.0
    fig_h = total_units * line_in + title_in + 0.12
    fig, ax = plt.subplots(figsize=(fig_width, fig_h))
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    if title:
        ax.text(0, 1.0, title, ha="left", va="top", fontsize=11,
                fontweight="bold", color=INK, transform=ax.transAxes)

    body_top = 1.0 - (title_in / fig_h)
    # Bornes verticales des bandes (du haut vers le bas), en fraction d'axe.
    ys, y = [], body_top
    for u in band_units:
        h = (u * line_in) / fig_h
        ys.append((y, y - h))
        y -= h

    # Bornes horizontales des colonnes.
    xs, x = [], 0.0
    for f in col_fracs:
        xs.append((x, x + f))
        x += f
    padx = 0.008

    def put_row(idx, cells, bg, bold, txt_color):
        ytop, ybot = ys[idx]
        ax.add_patch(Rectangle((0, ybot), 1, ytop - ybot, facecolor=bg,
                               edgecolor="none", zorder=0))
        ymid = (ytop + ybot) / 2
        for (x0, x1), cell, al in zip(xs, cells, aligns):
            if al == "l":
                tx, ha = x0 + padx, "left"
            elif al == "r":
                tx, ha = x1 - padx, "right"
            else:
                tx, ha = (x0 + x1) / 2, "center"
            ax.text(tx, ymid, str(cell), ha=ha, va="center",
                    fontsize=header_fontsize if bold else fontsize,
                    fontweight="bold" if bold else "normal",
                    color=txt_color, zorder=2)

    def put_section(idx, text, bg):
        ytop, ybot = ys[idx]
        ax.add_patch(Rectangle((0, ybot), 1, ytop - ybot, facecolor=bg,
                               edgecolor="none", zorder=0))
        ymid = (ytop + ybot) / 2
        ax.text(padx, ymid, text, ha="left", va="center", fontsize=fontsize,
                fontweight="bold", color=INK, zorder=2)

    # En-tête.
    put_row(0, headers, HEADER_BG, True, "white")
    # Lignes de données (les sections ne comptent pas dans l'alternance de fond).
    n = len(rows)
    data_idx = 0
    for i, r in enumerate(rows):
        if isinstance(r, dict):
            put_section(i + 1, r["section"], r.get("bg", ROW_ALT))
            continue
        is_total = total_row and i == n - 1
        bg = TOTAL_BG if is_total else (ROW_ALT if data_idx % 2 == 0 else "white")
        put_row(i + 1, r, bg, is_total, INK)
        data_idx += 1

    # Filets horizontaux discrets entre les bandes.
    for ytop, _ in ys:
        ax.plot([0, 1], [ytop, ytop], color=GRID, lw=0.6, zorder=3)
    ax.plot([0, 1], [ys[-1][1], ys[-1][1]], color=GRID, lw=0.6, zorder=3)

    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(out, dpi=DPI, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    print(f"  {out.name}")


# ---------------------------------------------------------------- données

# (standard, temps réf, temps OMR, Δ, pén struct, pén harm, pén totale, précision)
RES = [
    ("On the Sunny Side of the Street", 128, 102, -26, "28", "20,5", "48,5", "62,1"),
    ("Fly Me to the Moon", 128, 129, 1, "1", "49,5", "50,5", "60,6"),
    ("Autumn Leaves", 128, 120, -8, "38", "15,0", "53,0", "58,6"),
    ("Stella by Starlight", 128, 127, -1, "7", "55,5", "62,5", "51,2"),
    ("All The Things You Are", 144, 149, 5, "23", "49,0", "72,0", "50,0"),
    ("Satin Doll", 128, 112, -16, "16", "60,5", "76,5", "40,2"),
    ("Oleo", 128, 86, -42, "42", "34,5", "76,5", "40,2"),
    ("Misty", 128, 169, 41, "41", "37,75", "78,75", "38,5"),
    ('Take the "A" Train', 128, 105, -23, "65", "18,5", "83,5", "34,8"),
    ("Summertime", 64, 86, 22, "22", "21,2", "43,2", "32,5"),
    ("Sandu", 96, 128, 32, "32", "49,0", "81,0", "15,6"),
]


def sgn(v):
    return f"+{v}" if v > 0 else str(v)


def main():
    use_jakarta()
    print("Tables OMR :")

    # 1) Résultats complets (8 colonnes).
    headers = ["Standard", "Temps\nréf.", "Temps\nOMR", "Écart\ntemps",
               "Pén.\nstruct.", "Pén.\nharm.", "Pén.\ntotale", "Précision"]
    rows = [[n, str(rf), str(om), sgn(d), st, ha, to, pr]
            for (n, rf, om, d, st, ha, to, pr) in RES]
    rows.append(["Total / moyenne", "1328", "1313", "11/11", "315", "411", "726", "44,0"])
    draw_table(
        headers, rows,
        col_fracs=[0.325, 0.095, 0.095, 0.085, 0.095, 0.095, 0.095, 0.115],
        aligns=["l", "r", "r", "r", "r", "r", "r", "r"],
        out=HERE / "omr_table_resultats.png",
        title="Fiabilité de l'OMR par standard (pénalités en points de temps)",
        fig_width=7.2, total_row=True,
    )

    # 2) Version compacte pour le texte (5 colonnes).
    headers_c = ["Standard", "Temps réf.", "Temps OMR", "Écart temps", "Précision"]
    rows_c = [[r[0], str(r[1]), str(r[2]), sgn(r[3]), r[7]] for r in RES]
    rows_c.append(["Total / moyenne", "1328", "1313", "11/11 faux", "44,0"])
    draw_table(
        headers_c, rows_c,
        col_fracs=[0.42, 0.15, 0.15, 0.15, 0.13],
        aligns=["l", "r", "r", "r", "r"],
        out=HERE / "omr_table_resultats_compact.png",
        title="Fiabilité de l'OMR par standard",
        total_row=True,
    )

    # 3) Barème des pénalités. Deux sections : harmonique (substitutions, compte dans Σ S)
    #    et structurelle (temps faux, compte dans D + I).
    headers_b = ["Condition (même fondamentale sauf mention)", "Coût", "Exemple", "Justification"]
    bareme = [
        {"section": "Pénalité harmonique : accord faux (somme des substitutions)", "bg": HARM_BAND},
        ("Chiffrage identique", "0,00", "D:min7 = D:min7", "correspondance exacte"),
        ("Extensions diatoniques ajoutées\n(sans b, #, alt)", "0,00", "C:7 vs C:7(13)", "couleur sans\nchangement de fonction"),
        ("Deux dominantes sans parenthèses\n(7 / 9 / 11 / 13)", "0,00", "D:7 vs D:9", "même fonction dominante"),
        ("Triade contre septième de même famille", "0,10", "A:min vs A:min7", "même couleur tonale"),
        ("Tension altérée fausse ou manquée\n(b, #, alt)", "0,25", "G:7 vs G:7(b9)", "tension supérieure\nincorrecte"),
        ("min7 / minmaj7, hdim7 / dim", "0,25", "C:min7 vs C:minmaj7", "une note de la couleur change"),
        ("Conflit majeur / mineur / dominante\n(3ce ou 7e fausse)", "0,50", "Bb:7 vs Bb:maj7", "qualité fondamentale\nchangée"),
        ("Même fondamentale, toute autre qualité", "0,75", "C:maj7 vs C:dim7", "qualité radicalement\ndifférente"),
        ("Fondamentale différente", "1,00", "Db:maj7 vs D:maj7", "mauvaise note de basse"),
        ("Un des deux est N (silence)", "1,00", "A:min7 vs N", "rien reconnu"),
        {"section": "Pénalité structurelle : temps faux (insertions + suppressions)", "bg": STRUCT_BAND},
        ("Temps inséré ou supprimé", "1,00", "*** contre F:min7", "grille de\nmauvaise longueur"),
    ]
    draw_table(
        headers_b, [list(r) if isinstance(r, tuple) else r for r in bareme],
        col_fracs=[0.42, 0.08, 0.24, 0.26],
        aligns=["l", "c", "l", "l"],
        out=HERE / "omr_table_bareme.png",
        title="Barème des pénalités de l'alignement (coût par temps)",
        fig_width=7.4, line_in=0.20, pad_lines=0.9,
    )

    # 4) Ventilation des erreurs sur le corpus.
    headers_v = ["Coût unitaire", "Type d'erreur", "Temps concernés"]
    vent = [
        ("0,10", "triade contre septième de même famille", "2"),
        ("0,25", "tension altérée fausse, min7 / minmaj7, hdim7 / dim", "6"),
        ("0,50", "conflit majeur / mineur / dominante", "69"),
        ("0,75", "autre qualité, même fondamentale", "137"),
        ("1,00", "substitution de fondamentale fausse ou N", "272"),
        ("1,00", "insertion (temps halluciné)", "150"),
        ("1,00", "suppression (temps manquant)", "165"),
    ]
    draw_table(
        headers_v, [list(r) for r in vent],
        col_fracs=[0.18, 0.62, 0.20],
        aligns=["c", "l", "r"],
        out=HERE / "omr_table_ventilation.png",
        title="Ventilation des erreurs sur le corpus (11 standards)",
    )

    print(f"\nImages dans {HERE}")


if __name__ == "__main__":
    main()
