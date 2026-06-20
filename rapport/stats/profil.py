#!/usr/bin/env python3
"""Figures « Profil des participants » — remplacent le grand tableau Q0 par des visuels.

Lit data/q0_profil.csv (1 ligne/participant) et trace quatre figures de présentation pour
la section Évaluations (§5b). Comme present.py : aucun calcul statistique, juste de la mise
en forme — A4-utile, Plus Jakarta Sans embarqué, même palette que les figures en pente.

    poetry run python rapport/stats/profil.py   (deps : groupe Poetry « stats »)

SORTIES (une figure par idée, comme present.py) :
  figures/profil_age.png          lollipop d'âge, pastilles colorées par niveau d'impro
  figures/profil_instrument.png   donut de l'instrument principal
  figures/profil_experience.png   barres années instrument / piano / jazz, triées par jazz
  figures/profil_aisance.png      heatmap aisance/pratique + bande « difficulté à improviser »
  figures/profil_formation.png    formation au piano (conservatoire / cours particuliers)
  figures/profil_constantes.png   constantes en badges (daltonisme, piano augmenté)
  figures/profil_difficultes.png  verbatims « ce qui est le plus difficile », en tableau

Choix de design : pas de camembert par participant (à n = 8, une part = 12,5 %, et l'angle
se lit mal) ; on garde un seul donut pour l'instrument (lecture part-du-tout naturelle) et on
privilégie partout des encodages qui conservent l'ordre de grandeur ET l'identité de chacun.
"""

import csv
import textwrap
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")  # rendu hors écran : on écrit des PNG
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle

HERE = Path(__file__).resolve().parent
PROFIL = HERE / "data" / "q0_profil.csv"
FIGS = HERE / "figures"
FONTS = HERE / "fonts"

# Palette alignée sur present.py (vert = favorable). Quelques tons muets pour le catégoriel.
GOOD = "#2e8b57"  # accent principal (jazz / favorable)
GRID = "#d4d4d4"
INK = "#2b2b2b"
MUTED = "#9aa3ab"  # gris pour le contexte (instrument / piano)
PIANO_BLUE = "#5b9bd5"
WARM = "#c0392b"  # rouge = la difficulté que l'outil cherche à soulager
# Expérience : séquence claire -> foncée (le jazz, le plus pertinent, est le plus foncé).
EXP_INSTR, EXP_PIANO, EXP_JAZZ = "#bfe3d0", "#5cba8f", "#1b7a47"

# Largeur utile A4 (cf. present.py) : figures insérées à 100 %, pas de redimension = pas de flou.
A4_WIDTH_IN, MARGIN_IN = 8.27, 1.0
FIG_WIDTH = A4_WIDTH_IN - 2 * MARGIN_IN  # ~6.27"
DPI = 200


def use_jakarta():
    reg = FONTS / "PlusJakartaSans-Regular.ttf"
    if not reg.exists():
        return
    for ttf in (reg, FONTS / "PlusJakartaSans-Bold.ttf"):
        if ttf.exists():
            font_manager.fontManager.addfont(str(ttf))
    plt.rcParams["font.family"] = "Plus Jakarta Sans"
    plt.rcParams["axes.unicode_minus"] = False


def setup_style():
    plt.rcParams.update(
        {
            "savefig.dpi": DPI,
            "axes.axisbelow": True,
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "axes.titlepad": 10,
            "axes.labelsize": 10,
            "axes.edgecolor": "#888888",
            "grid.color": GRID,
            "text.color": INK,
            "axes.labelcolor": INK,
            "xtick.color": INK,
            "ytick.color": INK,
        }
    )


use_jakarta()
setup_style()

# --- Échelles ordinales : libellé brut -> rang, et borne pour normaliser la couleur ------
LECTURE = {"Pas du tout": 0, "Avec difficulté": 1, "À l'aise": 2, "Très à l'aise": 3}
FREQ = {
    "Jamais": 0,
    "Quelques fois par mois": 1,
    "Chaque semaine": 2,
    "Presque chaque jour": 3,
}
IREAL = {
    "Jamais": 0,
    "Occasionnellement": 1,
    "Régulièrement": 2,
    "Très régulièrement": 3,
}

# Abréviations pour annoter les cellules sans les surcharger.
LECTURE_SHORT = {
    "Pas du tout": "Pas\ndu tout",
    "Avec difficulté": "Avec\ndiffic.",
    "À l'aise": "À l'aise",
    "Très à l'aise": "Très à\nl'aise",
}
FREQ_SHORT = {
    "Jamais": "Jamais",
    "Quelques fois par mois": "Qq fois\n/ mois",
    "Chaque semaine": "Chaque\nsem.",
    "Presque chaque jour": "Presque\nch. jour",
}
IREAL_SHORT = {
    "Jamais": "Jamais",
    "Occasionnellement": "Occas.",
    "Régulièrement": "Régul.",
    "Très régulièrement": "Très\nrégul.",
}

def load(path):
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def num(row, col):
    text = (row.get(col) or "").strip().replace(",", ".")
    return float(text) if text else np.nan


def text_on(rgba):
    """Noir ou blanc selon la luminance du fond : lisible aux deux bouts de RdYlGn
    (rouge/vert foncés -> blanc ; jaune clair du milieu -> encre)."""
    r, g, b = rgba[:3]
    return "white" if (0.299 * r + 0.587 * g + 0.114 * b) < 0.5 else INK


# =========================================================================================
# Figure 1a — âge (heatmap-lollipop : position = âge, couleur = niveau d'impro)
# =========================================================================================
def fig_age(rows, path):
    # Une échelle rouge->vert : la pastille n'est plus toujours verte, on voit d'un coup
    # qui se juge faible (rouge) vs solide (vert) en impro, sur l'axe des âges.
    rdylgn = plt.get_cmap("RdYlGn")
    norm_lvl = Normalize(1, 7)
    pid = [r["participant"] for r in rows]
    age = np.array([num(r, "age") for r in rows])
    lvl = np.array([num(r, "niveau_impro_1_7") for r in rows])
    order = np.argsort(age)
    y = np.arange(len(order))

    fig, ax = plt.subplots(figsize=(FIG_WIDTH, 4.6))
    ax.hlines(y, age.min() - 2, age[order], color=GRID, lw=1.8, zorder=1)
    ax.scatter(
        age[order],
        y,
        s=200,
        zorder=3,
        c=[rdylgn(norm_lvl(v)) for v in lvl[order]],
        edgecolors="#555555",
        linewidths=0.7,
    )
    for yi, a in zip(y, age[order]):
        ax.text(a + 1.4, float(yi), f"{int(a)}", va="center", ha="left", fontsize=8.5)
    med = float(np.median(age))
    med_txt = f"{med:.0f}" if med.is_integer() else f"{med:.1f}".replace(".", ",")
    ax.axvline(med, color=WARM, lw=1.4, ls=(0, (4, 2)), zorder=2)
    ax.text(
        med,
        len(order) - 0.2,
        f"médiane {med_txt}",
        color=WARM,
        fontsize=8,
        ha="center",
        va="bottom",
    )
    ax.set_yticks(y, [pid[i] for i in order], fontsize=9)
    ax.set(xlim=(age.min() - 4, age.max() + 6), ylim=(-0.7, len(order) - 0.15))
    ax.set_xlabel("âge (ans)")
    ax.set_title("Âge des participants", fontsize=12.5)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(True, axis="x", color=GRID, lw=0.7)
    # Barre de couleur sous l'axe : explicite l'encodage rouge(1) -> vert(7) des pastilles.
    sm = ScalarMappable(norm=norm_lvl, cmap=rdylgn)
    sm.set_array([])
    cb = fig.colorbar(
        sm,
        ax=ax,
        orientation="horizontal",
        fraction=0.05,
        pad=0.22,
        aspect=30,
        shrink=0.6,
    )
    cb.set_label("niveau d'impro auto-évalué (1-7)", fontsize=8)
    cb.set_ticks(range(1, 8))
    cb.ax.tick_params(labelsize=7.5, length=0)
    cb.outline.set_visible(False)

    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)


# =========================================================================================
# Figure 1b — instrument principal (donut : le seul « camembert », justifié ici)
# =========================================================================================
def fig_instrument(rows, path):
    insts = [r["instrument_principal"].strip() for r in rows]
    cats, counts = np.unique(insts, return_counts=True)
    o2 = np.argsort(-counts)  # Piano (majoritaire) en tête
    cats, counts = cats[o2], counts[o2]
    # Piano en bleu (instrument pertinent), le reste en tons muets pour le faire ressortir.
    palette = []
    muted_cycle = [MUTED, "#b9c0c6", "#cdd3d8", "#dfe3e6"]
    j = 0
    for c in cats:
        if c.lower().startswith("piano"):
            palette.append(PIANO_BLUE)
        else:
            palette.append(muted_cycle[j % len(muted_cycle)])
            j += 1

    fig, ax = plt.subplots(figsize=(FIG_WIDTH, 3.8))
    wedges, _ = ax.pie(
        counts,
        colors=palette,
        startangle=90,
        counterclock=False,
        wedgeprops=dict(width=0.42, edgecolor="white", linewidth=1.5),
    )
    ax.set_title("Instrument principal", fontsize=12.5)
    ax.legend(
        wedges,
        [f"{c}  ({n})" for c, n in zip(cats, counts)],
        loc="center left",
        bbox_to_anchor=(1.0, 0.5),
        frameon=False,
        fontsize=9,
        handlelength=1.1,
    )

    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)


# =========================================================================================
# Figure 1c — expérience musicale (barres groupées, triées par années de jazz)
# =========================================================================================
def fig_experience(rows, path):
    pid = [r["participant"] for r in rows]
    a_inst = np.array([num(r, "annees_instrument") for r in rows])
    a_piano = np.array([num(r, "annees_piano") for r in rows])
    a_jazz = np.array([num(r, "annees_jazz") for r in rows])
    o3 = np.argsort(a_jazz)  # plus de jazz en haut (barh : dernier = haut)
    yy = np.arange(len(o3))
    h = 0.26

    fig, ax = plt.subplots(figsize=(FIG_WIDTH, 5.2))
    # Séquence claire -> foncée : du plus large (instrument) au plus pertinent (jazz, foncé).
    ax.barh(yy + h, a_inst[o3], h, color=EXP_INSTR, label="Instrument principal")
    ax.barh(yy, a_piano[o3], h, color=EXP_PIANO, label="Piano")
    ax.barh(yy - h, a_jazz[o3], h, color=EXP_JAZZ, label="Jazz")
    for yi, vi in zip(yy - h, a_jazz[o3]):
        ax.text(
            vi + 0.3,
            yi,
            f"{int(vi)}",
            va="center",
            ha="left",
            fontsize=7.5,
            color=EXP_JAZZ,
        )
    ax.set_yticks(yy, [pid[i] for i in o3], fontsize=9)
    ax.set_xlabel("années de pratique")
    ax.set_title(
        "Expérience musicale (années), triée par années de jazz", fontsize=12.5
    )
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(True, axis="x", color=GRID, lw=0.7)
    # Légende dans le coin bas-droite : à l'intérieur des axes, là où les barres (triées par
    # jazz croissant vers le bas) laissent un vide ; fond blanc pour passer sur la grille.
    leg = ax.legend(fontsize=8.5, loc="lower right", framealpha=0.95)
    leg.get_frame().set_edgecolor("none")

    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)


# =========================================================================================
# Figure 2 — aisance & pratique : heatmap + bande difficulté du défilement
# =========================================================================================
def _cells(rows):
    """Construit la matrice (valeur normalisée 0-1) + annotations pour les 4 colonnes d'aisance."""
    pid = [r["participant"] for r in rows]
    cols = [
        "Lecture\nde grille",
        "Fréquence\nd'impro",
        "Niveau\nd'impro (1-7)",
        "Usage\niReal Pro",
    ]
    norm = np.full((len(rows), 4), np.nan)
    annot = [["" for _ in range(4)] for _ in rows]
    for i, r in enumerate(rows):
        lg = r["lecture_grille"].strip()
        if lg in LECTURE:
            norm[i, 0] = LECTURE[lg] / 3
            annot[i][0] = LECTURE_SHORT[lg]
        fq = r["freq_impro"].strip()
        if fq in FREQ:
            norm[i, 1] = FREQ[fq] / 3
            annot[i][1] = FREQ_SHORT[fq]
        else:
            annot[i][1] = "n.r."
        ni = num(r, "niveau_impro_1_7")
        if not np.isnan(ni):
            norm[i, 2] = (ni - 1) / 6
            annot[i][2] = f"{int(ni)}"
        ir = r["usage_ireal"].strip()
        if ir in IREAL:
            norm[i, 3] = IREAL[ir] / 3
            annot[i][3] = IREAL_SHORT[ir]
    return pid, cols, norm, annot


def fig_aisance(rows, path):
    pid, cols, norm, annot = _cells(rows)
    diff = np.array([num(r, "defilement_difficile_1_7") for r in rows])

    fig = plt.figure(figsize=(FIG_WIDTH, 5.6))
    gs = GridSpec(1, 2, width_ratios=[4, 1.15], wspace=0.08, figure=fig)
    ax = fig.add_subplot(gs[0, 0])
    axd = fig.add_subplot(gs[0, 1], sharey=None)

    fig.suptitle(
        "Profil des participants : aisance et pratique auto-déclarées",
        fontsize=13,
        fontweight="bold",
        y=1.06,
    )

    rdylgn = plt.get_cmap("RdYlGn")
    ny, nx = norm.shape
    # Heatmap dessinée à la main : contrôle total sur les cases vides (grisées) et le texte.
    # Échelle rouge->vert : faible aisance = rouge (un besoin), élevée = vert (un atout) ;
    # le tout-vert précédent laissait croire que tout le monde s'en sortait.
    for i in range(ny):
        for k in range(nx):
            v = norm[i, k]
            if np.isnan(v):
                ax.add_patch(
                    Rectangle(
                        (k, i), 1, 1, facecolor="#f0f0f0", edgecolor="white", lw=2
                    )
                )
                txt, tc = "n.r.", MUTED
            else:
                face = rdylgn(
                    0.06 + 0.88 * v
                )  # garde du rouge/vert francs aux extrêmes
                ax.add_patch(
                    Rectangle((k, i), 1, 1, facecolor=face, edgecolor="white", lw=2)
                )
                txt = annot[i][k]
                tc = text_on(face)
            ax.text(
                k + 0.5,
                i + 0.5,
                txt,
                ha="center",
                va="center",
                fontsize=7.3,
                color=tc,
                linespacing=0.95,
            )
    ax.set_xlim(0, nx)
    ax.set_ylim(ny, 0)  # P01 en haut
    ax.set_xticks(np.arange(nx) + 0.5, cols, fontsize=8.5)
    ax.set_yticks(np.arange(ny) + 0.5, pid, fontsize=8.5)
    ax.tick_params(length=0)
    ax.xaxis.tick_top()
    for s in ax.spines.values():
        s.set_visible(False)

    # --- Bande « difficulté à improviser sur la grille » : valence INVERSÉE (élevé = mauvais) ---
    # Même échelle RdYlGn que l'aisance, mais retournée : difficulté forte -> rouge (le
    # besoin que l'outil cible), difficulté faible -> vert. Cohérence : rouge = problème.
    for i in range(ny):
        v = (diff[i] - 1) / 6  # 0 = facile, 1 = très difficile
        face = rdylgn(0.06 + 0.88 * (1 - v))
        axd.add_patch(Rectangle((0, i), 1, 1, facecolor=face, edgecolor="white", lw=2))
        axd.text(
            0.5,
            i + 0.5,
            f"{int(diff[i])}",
            ha="center",
            va="center",
            fontsize=8,
            color=text_on(face),
            fontweight="bold",
        )
    axd.set_xlim(0, 1)
    axd.set_ylim(ny, 0)
    axd.set_xticks(
        [0.5], ["Difficulté à\nimproviser sur\nune grille de\njazz (1-7)"], fontsize=8
    )
    axd.set_yticks([])
    axd.tick_params(length=0)
    axd.xaxis.tick_top()
    for s in axd.spines.values():
        s.set_visible(False)

    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)


# =========================================================================================
# Figure 3a — formation au piano (catégoriel : 2 modalités -> barres, pas de camembert)
# =========================================================================================
def fig_formation(rows, path):
    forms = [r["formation_piano"].strip().replace(" / ", "\n") for r in rows]
    cats, counts = np.unique(forms, return_counts=True)
    o = np.argsort(-counts)
    cats, counts = cats[o], counts[o]

    fig, ax = plt.subplots(figsize=(FIG_WIDTH, 2.6))
    yy = np.arange(len(cats))
    ax.barh(yy, counts, color=PIANO_BLUE, height=0.6)
    for yi, ci in zip(yy, counts):
        ax.text(ci + 0.08, float(yi), str(int(ci)), va="center", ha="left", fontsize=9)
    ax.set_yticks(yy, cats, fontsize=9)
    ax.set_xlim(0, counts.max() + 1)
    ax.set_xlabel("participants")
    ax.set_title("Formation au piano", fontsize=12.5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(True, axis="x", color=GRID, lw=0.7)

    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)


# =========================================================================================
# Figure 3b — constantes en « badges » KPI (un graphe d'une constante n'apprend rien)
# =========================================================================================
def fig_constantes(rows, path):
    n = len(rows)
    # Nombre de participants ayant répondu « Non » (= cas favorable à l'étude).
    nd = sum(1 for r in rows if r["daltonisme"].strip().lower() == "non")
    npa = sum(1 for r in rows if r["deja_piano_augmente"].strip().lower() == "non")

    fig, ax = plt.subplots(figsize=(FIG_WIDTH, 2.4))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title("Homogénéité de l'échantillon", fontsize=12.5)
    for x, big, small in [
        (
            0.27,
            f"{nd}/{n}",
            "vision des couleurs normale\n(projection codée par couleurs)",
        ),
        (
            0.73,
            f"{npa}/{n}",
            "découvrent le piano augmenté\n(aucune exposition préalable)",
        ),
    ]:
        ax.text(
            x,
            0.64,
            big,
            fontsize=30,
            fontweight="bold",
            color=GOOD,
            ha="center",
            va="center",
        )
        ax.text(
            x,
            0.32,
            small,
            fontsize=9,
            color=INK,
            ha="center",
            va="center",
            linespacing=1.2,
        )

    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)


# =========================================================================================
# Figure 4 — « ce qui est le plus difficile » : verbatims en tableau (qualitatif, à plat)
# =========================================================================================
def fig_difficultes(rows, path):
    # Tableau simple, une ligne par participant dans l'ordre P01..P08. Pas de regroupement
    # thématique : les catégories forçaient une lecture discutable, on laisse le verbatim
    # parler et l'analyse thématique vit dans le texte du rapport, pas dans la figure.
    pid = [r["participant"] for r in rows]
    wrapped = [
        textwrap.fill((r["plus_difficile_texte"] or "").strip(), width=58) for r in rows
    ]
    lines = [w.count("\n") + 1 for w in wrapped]  # hauteur de texte, en « lignes »

    PAD = 0.5  # marge haut+bas d'une cellule, en demi-lignes
    HEADER_H = 1.3
    row_h = [n + 2 * PAD for n in lines]
    total = HEADER_H + sum(row_h)

    X_PID = 0.02  # colonne « participant »
    X_TXT = 0.18  # colonne « réponse » (assez large pour l'en-tête « Participant »)
    X_DIV = 0.155  # filet vertical séparant les deux colonnes

    fig, ax = plt.subplots(figsize=(FIG_WIDTH, 0.7 + total * 0.30))
    ax.set_xlim(0, 1)
    ax.set_ylim(total, 0)  # y croît vers le bas
    ax.axis("off")
    ax.set_title(
        "« Ce qui est le plus difficile » : réponses libres",
        fontsize=12,
        loc="left",
        pad=12,
    )

    # En-tête bleu.
    ax.add_patch(Rectangle((0, 0), 1, HEADER_H, facecolor=PIANO_BLUE, edgecolor="none"))
    ax.text(
        X_PID, HEADER_H / 2, "Participant", color="white", fontsize=9.5,
        fontweight="bold", va="center",
    )
    ax.text(
        X_TXT, HEADER_H / 2, "Réponse", color="white", fontsize=9.5,
        fontweight="bold", va="center",
    )

    # Lignes : fond alterné pour suivre la ligne sur toute la largeur.
    y = HEADER_H
    for i, (p, w, h) in enumerate(zip(pid, wrapped, row_h)):
        if i % 2 == 1:
            ax.add_patch(Rectangle((0, y), 1, h, facecolor="#f4f6f8", edgecolor="none"))
        cy = y + h / 2
        ax.text(X_PID, cy, p, color=PIANO_BLUE, fontsize=9, fontweight="bold", va="center")
        ax.text(
            X_TXT, cy, f"« {w} »", color=INK, fontsize=9, style="italic",
            va="center", linespacing=1.05,
        )
        y += h

    # Filets horizontaux discrets + filet vertical entre les deux colonnes (corps seul).
    ax.hlines(HEADER_H, 0, 1, color="#cfd6dc", lw=0.9)
    yy = HEADER_H
    for h in row_h:
        yy += h
        ax.hlines(yy, 0, 1, color="#e6eaed", lw=0.7)
    ax.vlines(X_DIV, HEADER_H, total, color="#e6eaed", lw=0.7)

    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)


def main():
    FIGS.mkdir(exist_ok=True)
    if not PROFIL.exists():
        print(f"[profil] {PROFIL} manquant.")
        return
    rows = load(PROFIL)
    print("\n=== Figures « Profil des participants » ===\n")
    fig_age(rows, FIGS / "profil_age.png")
    print(
        f"[âge]        lollipop coloré par niveau d'impro -> profil_age.png  ({len(rows)} participants)"
    )
    fig_instrument(rows, FIGS / "profil_instrument.png")
    print("[instrument] donut                              -> profil_instrument.png")
    fig_experience(rows, FIGS / "profil_experience.png")
    print("[expérience] barres (instrument / piano / jazz) -> profil_experience.png")
    fig_aisance(rows, FIGS / "profil_aisance.png")
    print("[aisance]    heatmap + difficulté à improviser  -> profil_aisance.png")
    fig_formation(rows, FIGS / "profil_formation.png")
    print("[formation]  barres conservatoire / particulier -> profil_formation.png")
    fig_constantes(rows, FIGS / "profil_constantes.png")
    print("[constantes] badges daltonisme + piano augmenté -> profil_constantes.png")
    fig_difficultes(rows, FIGS / "profil_difficultes.png")
    print("[difficultés] verbatims en tableau (P01..P08)    -> profil_difficultes.png")
    print(f"\nFigures dans {FIGS}\n")


if __name__ == "__main__":
    main()
