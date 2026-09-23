#!/usr/bin/env python
"""Build the visual comparison report: paper | before | corrected.

Deliberately minimal -- plots and a one-page summary of what was changed.
Every channel and every region is labelled. Output: results/comparacion.pdf
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

HERE = Path(__file__).parent
REPO_ROOT = HERE.parent
DOCS = REPO_ROOT.parent / "search-for-dark-matter-docs" / "docs"
SCRATCH = Path(os.environ.get("DPOA_SCRATCH", REPO_ROOT / "_report_scratch"))
PAPERFIGS = SCRATCH / "paperfigs"
OUT = REPO_ROOT / "results" / "comparacion.pdf"

MINE = SCRATCH / "mine_now"
MINE.mkdir(parents=True, exist_ok=True)


def extract(nb_path: Path, tag: str) -> list[Path]:
    """Pull every PNG output out of an executed notebook, in order."""
    if not nb_path.exists():
        return []
    nb = json.loads(nb_path.read_text())
    out, n = [], 0
    for cell in nb["cells"]:
        if cell.get("cell_type") != "code":
            continue
        for o in cell.get("outputs", []):
            if o.get("output_type") == "display_data" and "image/png" in o.get("data", {}):
                p = MINE / f"{tag}_{n}.png"
                p.write_bytes(base64.b64decode(o["data"]["image/png"]))
                out.append(p)
                n += 1
    return out


def row(fig, gs, r, items, rowlabel):
    """One comparison row. The label sits above the row, spanning it, so it
    cannot collide with the column headers (which are drawn once per page)."""
    for c, img in enumerate(items):
        ax = fig.add_subplot(gs[r, c])
        ax.axis("off")
        if img and Path(img).exists():
            ax.imshow(mpimg.imread(str(img)))
        else:
            ax.text(0.5, 0.5, "—", ha="center", va="center",
                    fontsize=20, color="#bbbbbb", transform=ax.transAxes)
    ax0 = fig.add_subplot(gs[r, 0])
    ax0.axis("off")
    ax0.text(0.0, 1.04, rowlabel, ha="left", va="bottom", fontsize=9.5,
             fontweight="bold", color="#222222", transform=ax0.transAxes)


def page(pdf, rows, cols=("PAPER", "ANTES", "CORREGIDA")):
    n = len(rows)
    header = 0.75                      # inches reserved for the column headers
    h = 3.6 * n + 0.4 + header
    fig = plt.figure(figsize=(11.7, h))
    top = 1.0 - header / h
    gs = fig.add_gridspec(n, 3, hspace=0.26, wspace=0.02, top=top)
    for c, lab in enumerate(cols):
        fig.text((c + 0.5) / 3.0, 1.0 - 0.28 * header / h, lab,
                 ha="center", va="center", fontsize=11,
                 fontweight="bold", color="#333333")
    for r, (label, items) in enumerate(rows):
        row(fig, gs, r, items, label)
    pdf.savefig(fig, bbox_inches="tight", dpi=130)
    plt.close(fig)


FIXES = [
    ("Muestra de Z→νν", "archivo de otro análisis\n(señal de vida larga)",
     "ZJetsToNuNu, record 74910"),
    ("σ de Z→νν", "0.7333 pb (valor filtrado)",
     "4.201 pb — el peso medio del sample\n(0.0525 vs 1.0) prueba que el filtro\nya está dentro del peso"),
    ("σ de DY", "1.27 pb", "0.393 pb  [XSDB, UL16]"),
    ("Diboson WZ", "faltaba entero", "añadido  [record 72754]"),
    ("Z→νν bin 100-200", "faltaba", "añadido  [record 74908]"),
    ("Luminosidad", "3400 pb⁻¹ fijo (a ojo)", "por canal: 4907 / 2370 / 2896 pb⁻¹"),
    ("b-tagging", "DeepJet (WP de 2017)", "CSVv2 medio  [Tabla 10 = CSVM]"),
    ("Corte n_b ≥ 1", "no se aplicaba", "aplicado  [Tabla 10]"),
    ("Corte anti-QCD", "no se aplicaba", "min∆φ > 0.4  [Tabla 10]"),
    ("min∆φ", "sobre 4 jets", "sobre 2  [Tabla 13]"),
    ("m_T^b > 180 , p_T(j1)/H_T", "no se aplicaban", "aplicados  [Tabla 13]"),
    ("Filtros de ruido + golden JSON", "ninguno", "7 filtros + máscara de luminosidad"),
    ("Peso por p_T del top", "no se aplicaba",
     "exp(0.0615−0.0005·p_T), medido:\n×0.89 en la región de señal"),
    ("Orden del apilado", "por tamaño", "orden fijo del paper"),
    ("Binning", "no coincidía ni un borde",
     "AH 250–550/20 GeV · SL 160–520/40 GeV"),
    ("Último bin", "se tiraba la cola", "acumula el overflow, como el paper"),
]


def summary_page(pdf):
    fig = plt.figure(figsize=(11.7, 8.3))
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    ax.text(0.5, 0.965, "QUÉ SE CORRIGIÓ", ha="center", fontsize=15,
            fontweight="bold", color="#111111")
    ax.text(0.30, 0.933, "ANTES", fontsize=9, fontweight="bold", color="#993333")
    ax.text(0.60, 0.933, "CORREGIDA", fontsize=9, fontweight="bold", color="#1a6b1a")

    y = 0.900
    for i, (what, before, after) in enumerate(FIXES):
        yy = y - i * 0.0505
        if i % 2 == 0:
            ax.add_patch(plt.Rectangle((0.04, yy - 0.021), 0.92, 0.046,
                                       facecolor="#f6f6f6", edgecolor="none",
                                       transform=ax.transAxes))
        ax.text(0.055, yy, what, fontsize=8.5, fontweight="bold",
                va="center", color="#111111")
        ax.text(0.30, yy, before, fontsize=7.5, va="center", color="#993333")
        ax.text(0.60, yy, after, fontsize=7.5, va="center", color="#1a6b1a")

    ax.text(0.5, 0.098, "composición del fondo   (canal all-hadronic)",
            ha="center", fontsize=10, color="#555555")
    ax.text(0.5, 0.074,
            "Z(νν)  0 %  →  24.1 %   (paper 29.7 %)          "
            "t$\\bar{t}$  73 %  →  59.1 %   (paper 45.5 %)",
            ha="center", fontsize=9.5, color="#555555")
    ax.text(0.5, 0.040,
            "datos/modelo: 1.34  (paper 1.06) — lo que falta son dos entradas "
            "que no podemos derivar del análisis:",
            ha="center", fontsize=8.5, color="#333333")
    ax.text(0.5, 0.018,
            "los k-factors NLO de V+jets  y  la muestra VH.  Ver docs/RUNBOOK.md, "
            "[OPEN-4] y [OPEN-5].",
            ha="center", fontsize=8.5, color="#333333")
    pdf.savefig(fig, dpi=130)
    plt.close(fig)


def main():
    ah = extract(REPO_ROOT / "runs" / "All_Hadronic_run.ipynb", "ah")
    sl = extract(REPO_ROOT / "runs" / "Single_Lepton_run.ipynb", "sl")
    print(f"graficas generadas: AH={len(ah)}  SL={len(sl)}")

    A, S, P = DOCS / "All_Hadronic", DOCS / "Single_Lepton", PAPERFIGS

    def g(seq, i):
        return seq[i] if i < len(seq) else None

    with PdfPages(OUT) as pdf:
        summary_page(pdf)

        # --- ALL-HADRONIC: signal regions -----------------------------------
        page(pdf, [
            ("ALL-HADRONIC (0 leptones)  ·  SR 2b  ·  n_b ≥ 2",
             [P/"paper_AH_SR2.png", A/"upload_1f43d61e689f7633e1a912fe4d333f3a.png", g(ah,3)]),
            ("ALL-HADRONIC (0 leptones)  ·  SR 1b ≥1 forward  ·  n_b = 1",
             [P/"paper_AH_SR1.png", A/"upload_a8e46e0a068bae8962667539488e4c83.png", g(ah,4)]),
            ("ALL-HADRONIC (0 leptones)  ·  SR 1b 0 forward  ·  n_b = 1",
             [P/"paper_AH_SR0.png", None, g(ah,5)]),
        ])

        # --- ALL-HADRONIC: baseline -----------------------------------------
        page(pdf, [
            ("ALL-HADRONIC (0 leptones)  ·  selección base  ·  p_T^miss",
             [None, A/"upload_0871491fa310310fdb92e226a00efd37.png", g(ah,0)]),
            ("ALL-HADRONIC (0 leptones)  ·  selección base  ·  N jets",
             [None, A/"upload_3d271a5a71ed3969f4eec8d12be14ca2.png", g(ah,1)]),
            ("ALL-HADRONIC (0 leptones)  ·  selección base  ·  N b-tags",
             [None, A/"upload_a8ae80912050229a02bb6292b161560d.png", g(ah,2)]),
        ])

        # --- SINGLE LEPTON, MUON: signal regions ----------------------------
        page(pdf, [
            ("SINGLE-LEPTON · MUÓN  ·  SR 2b  ·  n_b ≥ 2",
             [P/"paper_SL_1mu_SR2.png", S/"output_75_0.png", g(sl,8)]),
            ("SINGLE-LEPTON · MUÓN  ·  SR 1b ≥1 forward",
             [P/"paper_SL_1mu_SR1.png", S/"output_75_1.png", g(sl,9)]),
            ("SINGLE-LEPTON · MUÓN  ·  SR 1b 0 forward",
             [P/"paper_SL_1mu_SR0.png", S/"output_75_2.png", g(sl,10)]),
        ])

        # --- SINGLE LEPTON, ELECTRON: signal regions ------------------------
        page(pdf, [
            ("SINGLE-LEPTON · ELECTRÓN  ·  SR 2b  ·  n_b ≥ 2",
             [P/"paper_SL_1e_SR2.png", None, g(sl,11)]),
            ("SINGLE-LEPTON · ELECTRÓN  ·  SR 1b ≥1 forward",
             [P/"paper_SL_1e_SR1.png", None, g(sl,12)]),
            ("SINGLE-LEPTON · ELECTRÓN  ·  SR 1b 0 forward",
             [P/"paper_SL_1e_SR0.png", None, g(sl,13)]),
        ])

        # --- SINGLE LEPTON: baseline distributions --------------------------
        page(pdf, [
            ("SINGLE-LEPTON · MUÓN  ·  selección base  ·  m_T^W",
             [None, S/"output_56_1.png", g(sl,0)]),
            ("SINGLE-LEPTON · MUÓN  ·  selección base  ·  p_T^miss",
             [None, S/"output_56_2.png", g(sl,1)]),
            ("SINGLE-LEPTON · MUÓN  ·  selección base  ·  N jets",
             [None, S/"output_56_3.png", g(sl,2)]),
            ("SINGLE-LEPTON · MUÓN  ·  selección base  ·  N b-tags",
             [None, S/"output_56_4.png", g(sl,3)]),
        ])
        page(pdf, [
            ("SINGLE-LEPTON · ELECTRÓN  ·  selección base  ·  m_T^W",
             [None, S/"output_64_1.png", g(sl,4)]),
            ("SINGLE-LEPTON · ELECTRÓN  ·  selección base  ·  p_T^miss",
             [None, S/"output_64_2.png", g(sl,5)]),
            ("SINGLE-LEPTON · ELECTRÓN  ·  selección base  ·  N jets",
             [None, S/"output_64_3.png", g(sl,6)]),
            ("SINGLE-LEPTON · ELECTRÓN  ·  selección base  ·  N b-tags",
             [None, S/"output_64_4.png", g(sl,7)]),
        ])

    print(f"escrito: {OUT}")


if __name__ == "__main__":
    main()
