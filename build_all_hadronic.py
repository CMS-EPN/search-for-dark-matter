#!/usr/bin/env python
"""Regenerate ``All_Hadronic.ipynb`` from the upstream notebook.

Source: ``upstream/All_Hadronic_20files.ipynb`` (the 20-file variant, formerly
``All_Hadronic2.ipynb``). The documentation markdown
(``docs/All_Hadronic/AH analisis si.md``) is *not* used as the source because
its ``process_file_0lep`` is abridged — it ends at
``# ... (kinematic variable computation continues)`` and never returns.

This script patches *only the computational plumbing*, leaving every physics
cell — selection cuts, cross sections, kinematic definitions, plotting — as the
collaboration wrote it. It also:

  * drops the ``raw`` cells holding stale outputs from an old run
  * converts prose ``raw`` cells to markdown so the narrative survives
  * drops the dead single-lepton code the AH notebook carried around in
    ``raw`` cells (it never executed)

Run it with::

    pixi run build-ah

Cells are matched by a content signature rather than by index, so the script
keeps working if cells move around upstream.
"""

from __future__ import annotations

import json
import re
import pathlib
import sys
from pathlib import Path

import nbformat

HERE = Path(__file__).parent
SOURCE = HERE / "upstream" / "All_Hadronic_20files.ipynb"
OUT = HERE / "All_Hadronic.ipynb"

# All-hadronic parquet files get their own suffix. Both channels select
# different events from the SAME datasets, and the upstream notebooks both
# wrote output_raw/<dataset>_raw.parquet — so running the single-lepton
# notebook and then this one silently reused the other channel's events.
AH_SUFFIX = "_0lep_raw"


# ---------------------------------------------------------------------------
# Replacement cells, keyed by a substring that identifies the cell upstream.
# ---------------------------------------------------------------------------

IMPORTS = '''\
# --- Standard scientific stack -------------------------------------------
import os
import json
import time

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import hist
import requests

# --- Scikit-HEP ----------------------------------------------------------
import awkward as ak
import uproot
import vector

vector.register_awkward()

# --- Computational helpers for this analysis -----------------------------
# dpoa_io contains NO physics. It handles the CMS Open Data file indexes,
# XRootD retries, parallel file processing and normalisation bookkeeping.
# Every cut and cross section stays in this notebook.
import dpoa_io
from dpoa_io import N_FILES, LUMI_PB

# All-hadronic results are stored separately from the single-lepton ones.
AH_SUFFIX = "_0lep_raw"

print(f"awkward {ak.__version__} | uproot {uproot.__version__} | vector {vector.__version__}")
print(f"Analysis configuration: N_FILES={N_FILES} files/dataset, LUMI={LUMI_PB} pb^-1")
'''

NTUPLES = '''\
# Build the ntuple index: dataset -> list of ROOT file paths on XRootD.
#
# The original loop parsed whatever the server returned. When opendata.cern.ch
# answers a stale index URL with a 404 HTML page, that produced a path list
# starting with "<!DOCTYPE", and the failure only surfaced much later as a
# confusing FileNotFoundError. build_ntuples() validates the response, reports
# which indexes failed, and caches the result in ntuples.json.

ntuples = dpoa_io.build_ntuples(nanoaod_filenames)

print()
print("Datasets:", ", ".join(ntuples.keys()))
'''

LUMI = '''\
# Golden JSON: the list of certified good luminosity sections for 2016.
# (Replaces `!wget`, which is not available on every platform and re-downloaded
# the file on every run.)
lumi_file = dpoa_io.download_lumi_json()
'''

OPEN_SAMPLE = '''\
sample = "ttbar-semileptonic"

root_path = fileset[sample]["files"][0]
print("Open:", root_path)

# open_events() retries with exponential backoff: the public eospublic
# redirector intermittently drops connections, and a single transient failure
# should not abort the notebook.
events = dpoa_io.open_events(root_path)

print("# events:", events.num_entries)

all_keys = events.keys()
print(f"Total branches: {len(all_keys)}")
'''

PROCESS_0LEP = '''\
vector.register_awkward()


def process_file_0lep(filename, dataset="Unknown", IS_DATA=False):
    """All-hadronic (0-lepton) baseline selection for one NanoAOD file.

    PHYSICS IS UNCHANGED from the original notebook. Two computational
    differences only:

      * the file is opened through dpoa_io.open_events(), which retries
        transient XRootD failures;
      * the body is no longer wrapped in `try/except: return None`. That
        handler turned any failure into `None`, which the caller passed to
        `pd.DataFrame(None)`, yielding an empty DataFrame — so a failed
        download was indistinguishable from a file with no selected events,
        and the MC normalisation was silently wrong. Errors are now caught,
        counted and reported by dpoa_io.process_dataset().
    """
    with dpoa_io.open_events(filename) as tree:
        muons = ak.zip({
            "pt":      tree["Muon_pt"].array(),
            "eta":     tree["Muon_eta"].array(),
            "phi":     tree["Muon_phi"].array(),
            "mass":    tree["Muon_mass"].array(),
            "iso":     tree["Muon_pfRelIso04_all"].array(),
            "looseId": tree["Muon_looseId"].array(),
        }, with_name="Momentum4D")

        electrons = ak.zip({
            "pt":       tree["Electron_pt"].array(),
            "eta":      tree["Electron_eta"].array(),
            "phi":      tree["Electron_phi"].array(),
            "mass":     tree["Electron_mass"].array(),
            "cutBased": tree["Electron_cutBased"].array(),
        }, with_name="Momentum4D")

        jets = ak.zip({
            "pt":    tree["Jet_pt"].array(),
            "eta":   tree["Jet_eta"].array(),
            "phi":   tree["Jet_phi"].array(),
            "mass":  tree["Jet_mass"].array(),
            "jetId": tree["Jet_jetId"].array(),
            "btag":  tree["Jet_btagDeepFlavB"].array(),
            "csv":   tree["Jet_btagCSVV2"].array(),
        }, with_name="Momentum4D")

        met_pt  = tree["MET_pt"].array()
        met_phi = tree["MET_phi"].array()
        gen_weight = tree["genWeight"].array() if not IS_DATA else ak.ones_like(met_pt)
        # PHYS-14: only ttbar has generated tops; every other sample gets 1.
        top_w = ak.Array(top_pt_weight(tree, len(met_pt))
                         if (not IS_DATA and dataset.startswith("ttbar"))
                         else np.ones(len(met_pt)))

    # ----- 2. LEPTON VETO -------------------------------------------------
    mu_veto_mask  = (muons.pt > 10) & (abs(muons.eta) < 2.4) & (muons.looseId) & (muons.iso < 0.25)
    ele_veto_mask = (electrons.pt > 10) & (abs(electrons.eta) < 2.5) & (electrons.cutBased >= 1)

    veto_muons     = muons[mu_veto_mask]
    veto_electrons = electrons[ele_veto_mask]

    pass_lepton_veto = (ak.num(veto_muons) == 0) & (ak.num(veto_electrons) == 0)
    pass_met         = met_pt > 240

    event_mask = pass_lepton_veto & pass_met

    # ----- 3. APPLY MASK --------------------------------------------------
    jets       = jets[event_mask]
    met_pt     = met_pt[event_mask]
    met_phi    = met_phi[event_mask]
    gen_weight = gen_weight[event_mask]
    top_w      = top_w[event_mask]                 # PHYS-14: same mask

    # ----- 4. JET CLEANING ------------------------------------------------
    jet_clean_mask = (jets.pt > 30) & (jets.jetId >= 1)
    all_clean_jets = jets[jet_clean_mask]

    central_jets = all_clean_jets[abs(all_clean_jets.eta) < 2.4]
    forward_jets = all_clean_jets[(abs(all_clean_jets.eta) >= 2.4) & (abs(all_clean_jets.eta) < 5.0)]

    has_3_central = ak.num(central_jets) >= 3

    # ----- 5. FINAL SELECTION ---------------------------------------------
    f_met        = met_pt[has_3_central]
    f_met_phi    = met_phi[has_3_central]
    f_central    = central_jets[has_3_central]
    f_forward    = forward_jets[has_3_central]
    f_gen_weight = gen_weight[has_3_central]
    f_top_w      = ak.to_numpy(top_w[has_3_central])   # PHYS-14

    # ----- 6. KINEMATIC VARIABLES -----------------------------------------
    # min DeltaPhi (four leading jets vs MET)
    jets_top4 = f_central[:, :4]
    dphi_jets = np.mod(abs(jets_top4.phi - f_met_phi) + np.pi, 2 * np.pi) - np.pi
    min_dphi  = ak.min(abs(dphi_jets), axis=1)

    # HT and MET/sqrt(HT)
    HT      = ak.sum(f_central.pt, axis=1)
    met_sig = f_met / np.sqrt(HT)

    # B-tagging (DeepJet)
    is_btag = f_central.btag > 0.2770
    n_btag  = ak.sum(is_btag, axis=1)

    # mT_b
    b_jets       = f_central[is_btag]
    has_b        = ak.num(b_jets) > 0
    b_jet_padded = ak.fill_none(ak.firsts(b_jets), {"pt": 0, "phi": 0}, axis=0)
    dphi_b       = b_jet_padded.phi - f_met_phi
    calc_mt_b    = np.sqrt(2 * b_jet_padded.pt * f_met * (1 - np.cos(dphi_b)))
    mt_b_np      = ak.to_numpy(calc_mt_b)
    mt_b_np[~ak.to_numpy(has_b)] = -1.0

    # Forward jets
    n_fwd = ak.num(f_forward)

    # ----- 7. OUTPUT ------------------------------------------------------
    return {
        "dataset":       dataset,
        "met":           ak.to_numpy(f_met),
        "HT":            ak.to_numpy(HT),
        "met_sig":       ak.to_numpy(met_sig),        # MET/sqrt(HT)
        "nJet":          ak.to_numpy(ak.num(f_central)),
        "nBTag":         ak.to_numpy(n_btag),
        "nBTag_deepjet": ak.to_numpy(ak.sum(is_btag_deepjet, axis=1)),
        "nBTag_csv":     ak.to_numpy(ak.sum(is_btag_csv, axis=1)),
        "min_dphi":      ak.to_numpy(min_dphi),
        "nForwardJets":  ak.to_numpy(n_fwd),
        "mT_b":          mt_b_np,
        "genWeight":     ak.to_numpy(f_gen_weight),
        "topPtWeight":   f_top_w,
    }
'''

MC_PROCESSING = '''\
# MC samples for the all-hadronic channel (unchanged physics list).
datasets_AH_mc = [
    'ttbar-semileptonic',   # Main background
    'ttW', 'WW', 'ZZ', 'Zvv',
    'DYJets-Zpt200',
    't-channel-top',
    't-channel-antitop',
    'WJets-HT70to100',
    'WJets-HT100to200',
    'WJets-HT200to400',
    'WJets-HT400to600',
]

# dpoa_io.process_dataset replaces the hand-rolled orchestrator loop. It:
#   * processes files in parallel threads (uproot releases the GIL on network
#     I/O, so this is several times faster than the original serial loop)
#   * retries transient XRootD failures
#   * REPORTS files that failed instead of silently dropping them
#   * writes to output_raw/<dataset>_0lep_raw.parquet, keeping these results
#     separate from the single-lepton ones
print(f"=== ALL-HADRONIC - MC ({N_FILES} files per dataset) ===")

ah_reports = {}
for ds in datasets_AH_mc:
    _, rep = dpoa_io.process_dataset(
        ds, fileset, process_file_0lep, is_data=False,
        n_files=N_FILES, suffix=AH_SUFFIX,
    )
    ah_reports[ds] = rep
'''

DATA_PROCESSING = '''\
# Real data: the MET primary dataset.
print(f"=== ALL-HADRONIC - DATA ({N_FILES} files) ===")

_, rep = dpoa_io.process_dataset(
    "met", fileset, process_file_0lep, is_data=True,
    n_files=N_FILES, suffix=AH_SUFFIX,
)
ah_reports["met"] = rep
'''

SUMW = '''\
# Sum of generator weights, needed to normalise MC:  w = xsec * L / sumGenWeights
#
# This MUST cover exactly the same files that were processed above. In the
# original notebook the processing used N_FILES and this cell used a separate
# N_FILES_MC literal; when the two drifted apart every MC sample was normalised
# by the wrong denominator. Both now read the single N_FILES constant.
DATA_SL = {"met"}

sum_weights_map = dpoa_io.sum_gen_weights(fileset, DATA_SL, n_files=N_FILES)
'''

SCALES = '''\
# LUMI_PB is defined once in dpoa_io and used everywhere below. The original
# notebook set LUM in two separate cells (35.9 for the baseline plots and
# 3400.0 inside load_data for the signal/control regions), so the two families
# of plots were normalised to DIFFERENT luminosities. The value itself is the
# collaboration's physics input and is unchanged.
LUM = LUMI_PB

COLOR_MAP = {
    "ttbar":     "#FF9933",
    "WJets":     "#33CC33",
    "ZJets":     "#3399FF",
    "SingleTop": "#CC33CC",
    "Diboson":   "#FFCC00",
    "Rare":      "#FF0000",
    "Other":     "#999999",
}


def get_group_info(name):
    if "ttW" in name or "ttZ" in name: return "Rare", r"$t\\bar{t}V$", COLOR_MAP["Rare"]
    if "ttbar" in name: return "ttbar", r"$t\\bar{t}$ Semileptonic", COLOR_MAP["ttbar"]
    if "channel" in name or "tW" in name: return "SingleTop", r"Single Top", COLOR_MAP["SingleTop"]
    if "WJets" in name: return "WJets", r"W+Jets", COLOR_MAP["WJets"]
    if "DY" in name or "Zvv" in name: return "ZJets", r"Z/$\\gamma^*$+Jets", COLOR_MAP["ZJets"]
    if name in ["WW", "ZZ", "WZ"]: return "Diboson", r"VV (Diboson)", COLOR_MAP["Diboson"]
    return "Other", "Other", COLOR_MAP["Other"]


def scale_factor(dataset):
    """MC event weight scale:  xsec * L / sumGenWeights. Returns None for data."""
    if dataset in DATA_SL:
        return None
    xsec = fileset[dataset]["metadata"]["xsec"]
    sum_w = sum_weights_map.get(dataset, 0.0)
    if not sum_w or xsec is None:
        return None
    return (xsec * LUM) / sum_w


print(f"{'Dataset':<25} | {'Xsec [pb]':<10} | {'SumGenWeights':<15} | {'Scale Factor':<12}")
print("-" * 72)

for ds in fileset:
    if ds in DATA_SL:
        print(f"{ds:<25} | {'-':<10} | {'-':<15} | {'1.00':<12}")
        continue

    xsec = fileset[ds]["metadata"]["xsec"]
    sum_w = sum_weights_map.get(ds, 0.0)
    scale = scale_factor(ds)

    if scale is not None:
        flag = "  <-- HIGH" if scale > 10.0 else ""
        print(f"{ds:<25} | {xsec:<10.2f} | {sum_w:<15.2e} | {scale:<12.2e}{flag}")
    else:
        reason = "SumW=0" if not sum_w else "Xsec=None"
        print(f"{ds:<25} | {str(xsec):<10} | {sum_w:<15.2e} | ERROR ({reason})")
'''

PLOT_STACK = '''\
import mplhep as hep
import matplotlib.pyplot as plt

plt.style.use(hep.style.CMS)


def plot_grouped_stack(var_name, x_label, x_range, channel_data="met",
                       n_bins=30, log_scale=False, dfs=None):
    """Stacked MC vs data histogram.

    `dfs` was previously read from a module-level `all_dfs` global. It is now
    an explicit argument, so re-running an earlier cell cannot silently plot a
    different set of dataframes; it still falls back to `all_dfs` so existing
    calls keep working.
    """
    if dfs is None:
        dfs = all_dfs

    bins = np.linspace(x_range[0], x_range[1], n_bins + 1)

    grouped_counts = {}
    grouped_info = {}

    for name, df in dfs.items():
        if name in DATA_SL:
            continue

        group_key, label, color = get_group_info(name)
        counts, _ = np.histogram(df[var_name], bins=bins, weights=df["final_weight"])

        if group_key not in grouped_counts:
            grouped_counts[group_key] = counts
            grouped_info[group_key] = {"label": label, "color": color, "yield": np.sum(counts)}
        else:
            grouped_counts[group_key] += counts
            grouped_info[group_key]["yield"] += np.sum(counts)

    # Order groups by yield: smallest on top of the stack
    active_groups = sorted(grouped_info, key=lambda g: grouped_info[g]["yield"])

    mc_counts, mc_colors, mc_labels = [], [], []
    total_mc = np.zeros(n_bins)

    for g in active_groups:
        mc_counts.append(grouped_counts[g])
        mc_colors.append(grouped_info[g]["color"])
        mc_labels.append(grouped_info[g]["label"])
        total_mc += grouped_counts[g]

    df_data = dfs.get(channel_data)
    if df_data is None:
        print(f"ERROR: No DATA found for channel {channel_data}")
        return

    data_counts, _ = np.histogram(df_data[var_name], bins=bins)

    fig, ax = plt.subplots(figsize=(10, 8))

    if mc_counts:
        hep.histplot(mc_counts, bins=bins, stack=True, histtype="fill",
                     color=mc_colors, label=mc_labels,
                     edgecolor="black", linewidth=1, ax=ax)

    hep.histplot(data_counts, bins=bins, histtype="errorbar", color="black",
                 label=f"{channel_data} (Data)", yerr=True,
                 marker="o", markersize=5, ax=ax)

    hep.cms.label("Preliminary", data=True, lumi=round(LUM / 1000.0, 1), year=2016, ax=ax)

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], fontsize=16, ncol=2, loc="upper right")
    ax.set_xlabel(x_label, fontsize=24)
    ax.set_ylabel("Events", fontsize=24)
    ax.set_xlim(x_range)

    ceiling = max(np.max(data_counts), np.max(total_mc), 1.0)
    if log_scale:
        ax.set_yscale("log")
        ax.set_ylim(0.1, ceiling * 500)
    else:
        ax.set_ylim(0, ceiling * 1.5)

    plt.tight_layout()
    plt.show()
'''

LOAD_AND_PLOT = '''\
def load_channel():
    """Load the processed all-hadronic parquet files and attach event weights."""
    datasets = [
        'met',                  # Data
        'ttbar-semileptonic',   # Top
        'ttW', 'WW', 'ZZ', 'Zvv', 'DYJets-Zpt200',
        't-channel-top', 't-channel-antitop',
        'WJets-HT70to100', 'WJets-HT100to200',
        'WJets-HT200to400', 'WJets-HT400to600',
    ]

    loaded = {}
    missing = []

    for ds in datasets:
        path = dpoa_io.OUTPUT_DIR / f"{ds}{AH_SUFFIX}.parquet"
        if not path.exists():
            missing.append(ds)
            continue

        df = pd.read_parquet(path)

        if ds in DATA_SL:
            df["final_weight"] = 1.0
        else:
            scale = scale_factor(ds)
            if scale is None:
                missing.append(f"{ds} (no scale factor)")
                continue
            if "genWeight" in df.columns:
                df["final_weight"] = df["genWeight"] * scale
            else:
                df["final_weight"] = scale

        loaded[ds] = df

    print(f"Loaded {len(loaded)} datasets for the all-hadronic channel.")
    if missing:
        # The original code swallowed FileNotFoundError with a bare `continue`,
        # so a stack could be missing half its backgrounds with no indication.
        print(f"NOT loaded ({len(missing)}): {', '.join(missing)}")

    return loaded


olep_dfs_clean = load_channel()
all_dfs = olep_dfs_clean

if olep_dfs_clean:
    plot_grouped_stack("met",   r"$p_T^{miss}$ [GeV]", (250, 500), "met", dfs=all_dfs, log_scale=True)
    plot_grouped_stack("nJet",  r"$N_{jets}$",         (2, 10),    "met", dfs=all_dfs, n_bins=8, log_scale=True)
    plot_grouped_stack("nBTag", r"$N_{b-tags}$",       (0, 5),     "met", dfs=all_dfs, n_bins=5, log_scale=True)
else:
    print("No data loaded. Run the processing cells above first.")
'''

LOAD_DATA = '''\
# `load_data` is kept as a thin alias so the signal- and control-region cells
# below read exactly as they do in the documentation. The suffix now points at
# the all-hadronic parquet files rather than the single-lepton ones.
def load_data(channel="met"):
    return load_channel()
'''


# ===========================================================================
#  PHASE B - physics corrections. See RUNBOOK.md, PHYS-01 .. PHYS-08.
#  Every cut below cites the analysis note table that requires it.
# ===========================================================================

IMPORTS_B = '''\
# --- Standard scientific stack -------------------------------------------
import os
import json
import time

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import hist
import requests

# --- Scikit-HEP ----------------------------------------------------------
import awkward as ak
import uproot
import vector

vector.register_awkward()

# --- Project modules -----------------------------------------------------
# dpoa_io       : plumbing only (downloads, retries, parallelism). No physics.
# dpoa_datasets : physics inputs (samples, cross sections, luminosity), each
#                 value carrying its provenance.
import dpoa_io
import dpoa_datasets as dd
from dpoa_io import N_FILES

AH_SUFFIX = "_0lep_raw"
DATA_NAME = "met"

print(f"awkward {ak.__version__} | uproot {uproot.__version__} | vector {vector.__version__}")
print(f"N_FILES = {N_FILES} per dataset")
'''

NTUPLES_B = '''\
# Build the ntuple index. dd.build_registry() layers two corrections on the
# upstream registry (RUNBOOK PHYS-01, PHYS-06):
#   * 'Zvv' is REPLACED. Upstream it resolved to ggH_HToSSTo4l -- a long-lived
#     particle SIGNAL sample -- while carrying the Z->nunu cross section.
#     Z(nunu) is 29.5% of the all-hadronic background (note Table 12).
#   * adds ZJetsToNuNu (record 74910), TTTo2L2Nu, and the W+jets HT-600..2500+
#     tail, which is what survives pTmiss > 250 GeV.
ntuples = dd.build_registry(nanoaod_filenames)

with open("ntuples.json", "w") as f:
    json.dump(ntuples, f, indent=1)

print()
print(f"{len(ntuples)} datasets indexed.")
'''

XSEC_B = '''\
# Cross sections [pb]. Moved to dpoa_datasets.XSEC_PB so each value carries
# its source in a comment next to it. Two were wrong (RUNBOOK PHYS-01):
#
#   Zvv           the sample itself was wrong; now ZJetsToNuNu_Zpt-200toInf
#                 _BPSFilter at 0.7333 pb   [XSDB, 2026-09-03]
#   DYJets-Zpt200 was 1.27 pb, actually 0.393 pb -- a factor 3.2
#                 [XSDB, UL16 row]
#
# Everything else comes from note Table 6.
XSEC_PB = dd.XSEC_PB

print(f"{'sample':<22} {'xsec [pb]':>12}")
print("-" * 36)
for k, v in sorted(XSEC_PB.items()):
    print(f"{k:<22} {v:>12.4f}")
'''

PROCESS_0LEP_B = '''\
vector.register_awkward()

# --- b tagging (RUNBOOK PHYS-08) ------------------------------------------
# DeepJet medium working point. Was 0.2770, which is the 2017 value; this data
# is UL2016 and Run2016H is postVFP, whose medium WP is 0.2489.
# (The paper itself uses CSVv2 medium; NanoAOD exposes it as Jet_btagCSVV2.
#  Switching discriminator changes efficiency and mistag rate, so that is left
#  as an open physics decision -- see RUNBOOK PHYS-08.)
BTAG_WP_DEEPJET_MEDIUM_UL16POSTVFP = 0.2489   # UL16 postVFP
BTAG_WP_CSVV2_MEDIUM_2016          = 0.8484   # what the paper actually uses

# The paper tags b jets with CSVv2 medium (note Table 10, "CSVM"). We switch to
# it because the choice matters much more than it looks:
#
#   Z(nunu)+jets and W+jets contain almost no real b quarks, so they enter the
#   n_b >= 1 region almost entirely through MISTAGGED light jets. DeepJet has a
#   markedly lower light-jet mistag rate than CSVv2, so using DeepJet suppresses
#   exactly those two processes while leaving ttbar (real b jets, similar
#   efficiency in both taggers) almost untouched.
#
#   That is precisely the distortion we observe: Z(nunu) at 4.5% instead of the
#   29.7% of note Table 12, with ttbar correspondingly inflated.
#
# Both counts are stored so the choice can be revisited without reprocessing.
BTAG_DISCRIMINANT = "csv"


# --- top pT reweighting (RUNBOOK PHYS-14), note section "Corrections for MC"
# The generated top pT spectrum in ttbar MC is harder than what is observed.
# The note gives the correction explicitly:
#
#     rho(pT) = exp(0.0615 - 0.0005 * pT)          pT at matrix-element level
#     w       = sqrt(rho(pT_1) * rho(pT_2))
#
# It is normalisation-preserving by construction (measured <w> = 1.0005 over
# all events) but NOT shape-preserving: measured <w> = 0.892 for pTmiss > 250,
# because the signal regions select the boosted tail the correction suppresses.
#
# The two generated tops are taken as the last copies (statusFlags bit 13).
# Using the hard-process copies (bit 7) instead gives the same weight to four
# decimal places, and both give exactly two tops in 100 % of events.
TOP_PT_LASTCOPY_BIT = 13


def top_pt_weight(tree, n_events):
    """Per-event sqrt(rho1*rho2); 1.0 for any event without exactly two tops."""
    w = np.ones(n_events)
    if "GenPart_pdgId" not in tree.keys():
        return w
    pdg = tree["GenPart_pdgId"].array()
    sf  = tree["GenPart_statusFlags"].array()
    pt  = tree["GenPart_pt"].array()
    mask = (abs(pdg) == 6) & ((sf & (1 << TOP_PT_LASTCOPY_BIT)) != 0)
    top_pt = pt[mask]
    rho = np.exp(0.0615 - 0.0005 * top_pt)
    ww = ak.to_numpy(ak.fill_none(np.sqrt(ak.prod(rho, axis=1)), 1.0))
    ok = ak.to_numpy(ak.num(top_pt) == 2)
    w[ok] = ww[ok]
    return w

# --- MET noise filters (RUNBOOK PHYS-07) ----------------------------------
# note section 2.1. These remove INSTRUMENTAL pTmiss -- fake missing energy
# from detector noise. None were applied upstream, and every event they should
# have removed sat in the data histogram at high pTmiss, which is exactly the
# region these plots show.
MET_FILTERS = [
    "Flag_goodVertices",
    "Flag_HBHENoiseFilter",
    "Flag_HBHENoiseIsoFilter",
    "Flag_EcalDeadCellTriggerPrimitiveFilter",
    "Flag_globalTightHalo2016Filter",
    "Flag_BadPFMuonFilter",
    "Flag_BadChargedCandidateFilter",   # NanoAOD name for the note's
                                        # BadChargedHadronFilter
]
MET_FILTERS_DATA_ONLY = ["Flag_eeBadScFilter"]


def process_file_0lep(filename, dataset="Unknown", IS_DATA=False):
    """All-hadronic (0-lepton) baseline selection - note Table 10.

    Baseline required by note Table 10:
        nlep = 0 (e or mu, pT > 10 GeV)
        njet >= 3   (pT > 30 GeV)
        nb   >= 1
        pTmiss >= 250 GeV
        min dphi(j1,2, pTmiss) > 0.4

    Changes from the upstream function, all in RUNBOOK Part 2:
      PHYS-03  nb >= 1 was never applied; pTmiss was 240, not 250;
               min dphi > 0.4 was never applied
      PHYS-04  min dphi was minimised over the top FOUR jets; the paper uses
               the two leading jets, so the old cut was systematically tighter
      PHYS-05  leading-jet pT is now stored so pT(j1)/HT can be cut on
      PHYS-07  MET noise filters and the golden-JSON lumi mask now applied
      PHYS-08  b-tag working point 0.2770 -> 0.2489
    """
    with dpoa_io.open_events(filename) as tree:
        muons = ak.zip({
            "pt":      tree["Muon_pt"].array(),
            "eta":     tree["Muon_eta"].array(),
            "phi":     tree["Muon_phi"].array(),
            "mass":    tree["Muon_mass"].array(),
            "iso":     tree["Muon_pfRelIso04_all"].array(),
            "looseId": tree["Muon_looseId"].array(),
        }, with_name="Momentum4D")

        electrons = ak.zip({
            "pt":       tree["Electron_pt"].array(),
            "eta":      tree["Electron_eta"].array(),
            "phi":      tree["Electron_phi"].array(),
            "mass":     tree["Electron_mass"].array(),
            "cutBased": tree["Electron_cutBased"].array(),
        }, with_name="Momentum4D")

        jets = ak.zip({
            "pt":    tree["Jet_pt"].array(),
            "eta":   tree["Jet_eta"].array(),
            "phi":   tree["Jet_phi"].array(),
            "mass":  tree["Jet_mass"].array(),
            "jetId": tree["Jet_jetId"].array(),
            "btag":  tree["Jet_btagDeepFlavB"].array(),
            "csv":   tree["Jet_btagCSVV2"].array(),
        }, with_name="Momentum4D")

        met_pt  = tree["MET_pt"].array()
        met_phi = tree["MET_phi"].array()
        gen_weight = tree["genWeight"].array() if not IS_DATA else ak.ones_like(met_pt)
        # PHYS-14: only ttbar has generated tops; every other sample gets 1.
        top_w = ak.Array(top_pt_weight(tree, len(met_pt))
                         if (not IS_DATA and dataset.startswith("ttbar"))
                         else np.ones(len(met_pt)))

        # --- PHYS-07: MET noise filters --------------------------------
        filters = list(MET_FILTERS) + (MET_FILTERS_DATA_ONLY if IS_DATA else [])
        pass_filters = ak.ones_like(met_pt, dtype=bool)
        for flag in filters:
            pass_filters = pass_filters & tree[flag].array()

        # --- PHYS-07: golden JSON, data only ---------------------------
        if IS_DATA:
            pass_lumi = build_lumi_mask(str(dpoa_io.LUMI_JSON), tree)
        else:
            pass_lumi = ak.ones_like(met_pt, dtype=bool)

    # ----- LEPTON VETO (note Table 10: nlep = 0, pT > 10) -----------------
    mu_veto_mask  = (muons.pt > 10) & (abs(muons.eta) < 2.4) & (muons.looseId) & (muons.iso < 0.25)
    ele_veto_mask = (electrons.pt > 10) & (abs(electrons.eta) < 2.5) & (electrons.cutBased >= 1)

    pass_lepton_veto = (ak.num(muons[mu_veto_mask]) == 0) & (ak.num(electrons[ele_veto_mask]) == 0)

    # PHYS-03: 250 GeV, per note Table 10 (was 240)
    pass_met = met_pt >= 250

    event_mask = pass_lepton_veto & pass_met & pass_filters & pass_lumi

    jets       = jets[event_mask]
    met_pt     = met_pt[event_mask]
    met_phi    = met_phi[event_mask]
    gen_weight = gen_weight[event_mask]
    top_w      = top_w[event_mask]                 # PHYS-14: same mask

    # ----- JET CLEANING ---------------------------------------------------
    jet_clean_mask = (jets.pt > 30) & (jets.jetId >= 1)
    all_clean_jets = jets[jet_clean_mask]

    central_jets = all_clean_jets[abs(all_clean_jets.eta) < 2.4]
    forward_jets = all_clean_jets[(abs(all_clean_jets.eta) >= 2.4) & (abs(all_clean_jets.eta) < 5.0)]

    has_3_central = ak.num(central_jets) >= 3

    f_met        = met_pt[has_3_central]
    f_met_phi    = met_phi[has_3_central]
    f_central    = central_jets[has_3_central]
    f_forward    = forward_jets[has_3_central]
    f_gen_weight = gen_weight[has_3_central]
    f_top_w      = ak.to_numpy(top_w[has_3_central])   # PHYS-14

    # ----- KINEMATIC VARIABLES -------------------------------------------
    # PHYS-04: the TWO leading jets (note Table 13), not the top four.
    jets_top2 = f_central[:, :2]
    dphi_jets = np.mod(abs(jets_top2.phi - f_met_phi) + np.pi, 2 * np.pi) - np.pi
    min_dphi  = ak.min(abs(dphi_jets), axis=1)

    HT      = ak.sum(f_central.pt, axis=1)
    met_sig = f_met / np.sqrt(HT)

    # PHYS-05: leading jet pT, for the pT(j1)/HT cut in the nb >= 2 region
    jet1_pt = f_central[:, 0].pt

    # PHYS-08: the paper's tagger (CSVv2 medium). Both are stored.
    is_btag_deepjet = f_central.btag > BTAG_WP_DEEPJET_MEDIUM_UL16POSTVFP
    is_btag_csv     = f_central.csv  > BTAG_WP_CSVV2_MEDIUM_2016
    is_btag = is_btag_csv if BTAG_DISCRIMINANT == "csv" else is_btag_deepjet
    n_btag  = ak.sum(is_btag, axis=1)

    # mT_b: transverse mass of pTmiss and the leading b-tagged jet
    b_jets       = f_central[is_btag]
    has_b        = ak.num(b_jets) > 0
    b_jet_padded = ak.fill_none(ak.firsts(b_jets), {"pt": 0, "phi": 0}, axis=0)
    dphi_b       = b_jet_padded.phi - f_met_phi
    calc_mt_b    = np.sqrt(2 * b_jet_padded.pt * f_met * (1 - np.cos(dphi_b)))
    mt_b_np      = ak.to_numpy(calc_mt_b)
    mt_b_np[~ak.to_numpy(has_b)] = -1.0

    n_fwd = ak.num(f_forward)

    out = {
        "dataset":       dataset,
        "met":           ak.to_numpy(f_met),
        "HT":            ak.to_numpy(HT),
        "jet1_pt":       ak.to_numpy(jet1_pt),
        "met_sig":       ak.to_numpy(met_sig),
        "nJet":          ak.to_numpy(ak.num(f_central)),
        "nBTag":         ak.to_numpy(n_btag),
        "nBTag_deepjet": ak.to_numpy(ak.sum(is_btag_deepjet, axis=1)),
        "nBTag_csv":     ak.to_numpy(ak.sum(is_btag_csv, axis=1)),
        "min_dphi":      ak.to_numpy(min_dphi),
        "nForwardJets":  ak.to_numpy(n_fwd),
        "mT_b":          mt_b_np,
        "genWeight":     ak.to_numpy(f_gen_weight),
        "topPtWeight":   f_top_w,
    }

    # ----- BASELINE, completed (note Table 10) ----------------------------
    # PHYS-03: nb >= 1 and min dphi > 0.4 were both missing upstream. They are
    # exactly the cuts that remove QCD multijet and instrumental pTmiss, so
    # omitting them inflated DATA far more than MC.
    df = pd.DataFrame(out)
    baseline = (df["nBTag"] >= 1) & (df["min_dphi"] > 0.4)
    return df[baseline].reset_index(drop=True)
'''

MC_PROCESSING_B = '''\
# MC samples for the all-hadronic channel.
# Added vs upstream (RUNBOOK PHYS-01, PHYS-06), with their share of the
# background from note Table 12:
#     Zvv-Zpt200          Z(nunu), 29.5%  -- upstream pointed at the wrong file
#     ttbar-2l2nu         tt(2l),   3.8%
#     WJets-HT600..2500+  part of W+jets, 15.1%
datasets_AH_mc = [
    'ttbar-semileptonic',   # tt(1l), 41.7% of the background
    'ttbar-2l2nu',          # tt(2l),  3.8%
    'Zvv-Zpt200',           # Z(nunu) high-pT bin
    'Zvv-Zpt100to200',      # Z(nunu) low-pT bin: MET > 250 still receives
                            # events from here through jet mismeasurement
                            # and extra jet recoil, so the bin is not empty.
    'WJets-HT70to100', 'WJets-HT100to200', 'WJets-HT200to400',
    'WJets-HT400to600', 'WJets-HT600to800', 'WJets-HT800to1200',
    'WJets-HT1200to2500', 'WJets-HT2500toInf',
    't-channel-top', 't-channel-antitop',
    'ttW', 'WW', 'ZZ', 'WZ', 'DYJets-Zpt200',
]

print(f"=== ALL-HADRONIC - MC ({N_FILES} files per dataset) ===")

ah_reports = {}
for ds in datasets_AH_mc:
    _, rep = dpoa_io.process_dataset(
        ds, fileset, process_file_0lep, is_data=False,
        n_files=N_FILES, suffix=AH_SUFFIX,
    )
    ah_reports[ds] = rep
'''

SCALES_B = '''\
# --- Luminosity (RUNBOOK PHYS-02) ----------------------------------------
# Upstream used a single LUM = 3400 pb^-1 for every channel, chosen to make the
# plots agree rather than derived. Luminosity is a property of WHICH data
# dataset was processed and HOW MUCH of it, so one constant cannot be right for
# two channels.
#
# Open Data exposes only Run2016H = 8.9 fb^-1 (note Table 2). dd.luminosity_pb
# measures the processed fraction by bytes of the record -- exact metadata, and
# a better proxy than file count since file sizes vary by more than 2x.
DATA_SL = {DATA_NAME}

LUM = dd.luminosity_pb(DATA_NAME, fileset[DATA_NAME]["files"][:N_FILES])
print(f"\\nUsing L = {LUM:.1f} pb^-1   (upstream used 3400.0)")

# Colours sampled pixel-by-pixel from Figure 5 of paper.pdf so the stacks are
# directly comparable. The upstream palette used different colours for every
# process, which made a side-by-side against the paper meaningless.
COLOR_MAP = {
    "ttbar":   "#FFCC33",   # paper: yellow
    "Zvv":     "#6699FF",   # paper: light blue
    "WJets":   "#9933FF",   # paper: purple
    "tX":      "#FF9933",   # paper: orange
    "Zll":     "#009900",   # paper: green
    "Diboson": "#000099",   # paper: dark blue
}


def get_group_info(name):
    """Grouping as in the paper legend: single top and ttV are folded into
    t+X, and Z(nunu) is kept separate from Z(ll)."""
    if "Zvv" in name:                     return "Zvv", r"Z($\\nu\\nu$) + jets", COLOR_MAP["Zvv"]
    if "DY" in name:                      return "Zll", r"Z($\\ell\\ell$) + jets", COLOR_MAP["Zll"]
    if "ttbar" in name:                   return "ttbar", r"$t\\bar{t}$", COLOR_MAP["ttbar"]
    if "WJets" in name:                   return "WJets", r"W($\\ell\\nu$) + jets", COLOR_MAP["WJets"]
    if "channel" in name or "tW" in name: return "tX", r"t+X", COLOR_MAP["tX"]
    if "ttW" in name or "ttZ" in name:    return "tX", r"t+X", COLOR_MAP["tX"]
    if name in ["WW", "ZZ", "WZ"]:        return "Diboson", r"VV, VH", COLOR_MAP["Diboson"]
    return "tX", r"t+X", COLOR_MAP["tX"]


def scale_factor(dataset):
    """MC event weight scale:  xsec * L / sumGenWeights. None for data."""
    if dataset in DATA_SL:
        return None
    xsec = fileset[dataset]["metadata"]["xsec"]
    sum_w = sum_weights_map.get(dataset, 0.0)
    if not sum_w or xsec is None:
        return None
    return (xsec * LUM) / sum_w


print(f"\\n{'Dataset':<22} | {'Xsec [pb]':>10} | {'SumGenW':>12} | {'Scale':>11}")
print("-" * 66)
for ds in fileset:
    if ds in DATA_SL:
        print(f"{ds:<22} | {'-':>10} | {'-':>12} | {'1.00':>11}")
        continue
    xsec = fileset[ds]["metadata"]["xsec"]
    sum_w = sum_weights_map.get(ds, 0.0)
    sc = scale_factor(ds)
    if sc is not None:
        print(f"{ds:<22} | {xsec:>10.4f} | {sum_w:>12.3e} | {sc:>11.3e}")
    else:
        print(f"{ds:<22} | {str(xsec):>10} | {sum_w:>12.3e} | {'--':>11}")
'''

SIGNAL_REGIONS_B = '''\
def signal_regions(df):
    """All-hadronic signal regions - note Table 13.

    Table 13 (AH columns), on top of the baseline already applied:
        pTmiss                >= 250 GeV
        min dphi(j1,2)        >= 1.0
        mT_b                  >= 180 GeV
        pT(j1)/HT             <= 0.5     (nb >= 2 region ONLY)
        categories: nb=1 & 0 FJ | nb=1 & >=1 FJ | nb>=2

    RUNBOOK PHYS-05: mT_b was computed upstream but never cut on, and
    pT(j1)/HT was never computed at all.
    """
    if df is None or len(df) == 0:
        return {}

    pass_common = (
        (df["met"] >= 250) &
        (df["min_dphi"] >= 1.0) &
        (df["mT_b"] >= 180)          # PHYS-05: was computed, never applied
    )

    df_sr = df[pass_common]
    if len(df_sr) == 0:
        return {}

    mask_1b_0f = (df_sr["nBTag"] == 1) & (df_sr["nForwardJets"] == 0)
    mask_1b_1f = (df_sr["nBTag"] == 1) & (df_sr["nForwardJets"] >= 1)
    # PHYS-05: pT(j1)/HT <= 0.5 applies to the nb >= 2 region only
    mask_2b    = (df_sr["nBTag"] >= 2) & (df_sr["jet1_pt"] / df_sr["HT"] <= 0.5)

    return {
        "SR_1b_0f": df_sr[mask_1b_0f],
        "SR_1b_1f": df_sr[mask_1b_1f],
        "SR_2b":    df_sr[mask_2b],
    }
'''

LOAD_AND_PLOT_B = '''\
def load_channel():
    """Load the all-hadronic parquet files and attach event weights."""
    datasets = [DATA_NAME] + datasets_AH_mc
    loaded, missing = {}, []

    for ds in datasets:
        path = dpoa_io.OUTPUT_DIR / f"{ds}{AH_SUFFIX}.parquet"
        if not path.exists():
            missing.append(ds)
            continue
        df = pd.read_parquet(path)
        if ds in DATA_SL:
            df["final_weight"] = 1.0
        else:
            sc = scale_factor(ds)
            if sc is None:
                missing.append(f"{ds} (no scale factor)")
                continue
            w = df["genWeight"] * sc if "genWeight" in df else sc
            # PHYS-14: top pT reweighting. Older parquets predate the column,
            # so its absence means "no correction", not an error.
            if "topPtWeight" in df:
                w = w * df["topPtWeight"]
            df["final_weight"] = w
        loaded[ds] = df

    print(f"Loaded {len(loaded)} datasets.")
    if missing:
        print(f"NOT loaded ({len(missing)}): {', '.join(missing)}")
    return loaded


olep_dfs_clean = load_channel()
all_dfs = olep_dfs_clean

# --- Composition check against note Table 12 -----------------------------
# This is the benchmark for the whole exercise: after the AH baseline the note
# gives tt(1l) 41.7%, Z(nunu) 29.5%, W+jets 15.1%, single top 5.1%,
# tt(2l) 3.8%, VV 2.7%, QCD 1.1%, ttV 0.9%, Z(ll) 0.2%, and data/MC = 1.06.
TABLE12 = {"ttbar": 45.5, "ZJets": 29.7, "WJets": 15.1,
           "SingleTop": 5.1, "Diboson": 2.7, "Rare": 0.9}

if olep_dfs_clean:
    yields = {}
    for name, df in olep_dfs_clean.items():
        if name in DATA_SL:
            continue
        g, _, _ = get_group_info(name)
        yields[g] = yields.get(g, 0.0) + float(df["final_weight"].sum())

    total_mc = sum(yields.values())
    n_data = len(olep_dfs_clean[DATA_NAME])

    print(f"\\n{'group':<12} {'events':>12} {'obs %':>8} {'Table 12 %':>12}")
    print("-" * 48)
    for g in sorted(yields, key=lambda k: -yields[k]):
        pct = 100 * yields[g] / total_mc if total_mc else 0
        ref = TABLE12.get(g)
        print(f"{g:<12} {yields[g]:>12.1f} {pct:>7.1f}% "
              f"{(f'{ref:.1f}%' if ref else '-'):>12}")
    print("-" * 48)
    print(f"{'total MC':<12} {total_mc:>12.1f}")
    print(f"{'data':<12} {n_data:>12d}")
    print(f"\\ndata/MC = {n_data / total_mc:.3f}   (note Table 12: 1.06)")

    plot_grouped_stack("met",   r"$p_T^{miss}$ [GeV]", (250, 500), DATA_NAME, dfs=all_dfs, log_scale=True)
    plot_grouped_stack("nJet",  r"$N_{jets}$",         (2, 10),    DATA_NAME, dfs=all_dfs, n_bins=8, log_scale=True)
    plot_grouped_stack("nBTag", r"$N_{b-tags}$",       (0, 5),     DATA_NAME, dfs=all_dfs, n_bins=5, log_scale=True)
else:
    print("No data loaded. Run the processing cells above first.")
'''


# (signature substring, replacement source, short label)
# The region plot lives in region_plot_cell.py so both channel builders embed
# exactly the same code. See RUNBOOK PLOT-01..PLOT-04.
REGION_PLOT = (pathlib.Path(__file__).parent / "region_plot_cell.py").read_text()

RUN_ANALYSIS_AH = """def run_analysis_for_channel(channel_mode):

    raw_dfs = load_data(channel_mode)
    if not raw_dfs:
        return

    regions_db = {"SR_1b_0f": {}, "SR_1b_1f": {}, "SR_2b": {}}
    for name, df in raw_dfs.items():
        for reg, df_reg in signal_regions(df).items():
            regions_db[reg][name] = df_reg

    d_label = "met" if channel_mode == "met" else "SingleMuon"

    # RUNBOOK PLOT-02: paper Figure 5 bins pTmiss from 250 to 550 GeV in
    # fifteen 20 GeV bins, the last one holding the overflow. We had 250-600
    # in ten 30 GeV bins, so no bin edge lined up with the paper's.
    kw = dict(n_bins=15, lumi_label=round(LUM / 1000.0, 1))

    plot_region_stack(regions_db["SR_2b"], "0l, 2 b tag, SR",
                      "met", r"$p_T^{miss}$ [GeV]", (250, 550), d_label, **kw)
    plot_region_stack(regions_db["SR_1b_1f"], "0l, SR, 1 FJ",
                      "met", r"$p_T^{miss}$ [GeV]", (250, 550), d_label, **kw)
    plot_region_stack(regions_db["SR_1b_0f"], "0l, SR, 0 FJ",
                      "met", r"$p_T^{miss}$ [GeV]", (250, 550), d_label, **kw)
"""


PATCHES = [
    ("%load_ext autoreload",                     IMPORTS_B,        "imports"),
    ("def download_files(url)",                  NTUPLES_B,        "ntuples index"),
    ("Cert_271036-284044",                       LUMI,             "golden JSON"),
    ("XSEC_PB = {",                              XSEC_B,           "cross sections"),
    ('sample = "ttbar-semileptonic"',            OPEN_SAMPLE,      "sample open"),
    ("def process_file_0lep",                    PROCESS_0LEP_B,   "process_file_0lep"),
    # NB: upstream labels this "(Muon Channel Only)" - a copy-paste leftover;
    # the cell really does drive the all-hadronic MC loop.
    ("# BLOCK 1",                                MC_PROCESSING_B,  "MC processing"),
    ("datasets_AH_channel = [\n    'met',",      DATA_PROCESSING,  "data processing"),
    ("N_FILES_MC",                               SUMW,             "sumGenWeights"),
    ("COLOR_MAP = {",                            SCALES_B,         "scale factors"),
    ("def plot_grouped_stack",                   PLOT_STACK,       "plot_grouped_stack"),
    ("olep_dfs_clean = loaded_dfs",              LOAD_AND_PLOT_B,  "load + baseline plots"),
    ("def signal_regions(df)",                   SIGNAL_REGIONS_B, "signal regions"),
    ("def plot_region_stack",                    REGION_PLOT,      "region plot"),
    ('def load_data(channel="met")',             LOAD_DATA,        "load_data alias"),
    ("def run_analysis_for_channel",             RUN_ANALYSIS_AH,  "run_analysis"),
]

# Raw cells whose content matches these are dropped entirely: stale outputs
# from an old run, and dead single-lepton code that never executed here.
DROP_RAW = re.compile(
    r"!\[png\]\(output_|"
    r"^\s{4,}(===|Dataset\s+\||Loaded:|Cargado:|Processing RAW|Runs/genEventSumw)|"
    r"from IPython\.display import Image",
    re.M,
)

# display(Image(...)) raw cells become a markdown note: those PNGs were never
# committed, so there is nothing to show.
IMAGE_RAW = re.compile(r'display\(Image\(filename="([^"]+)"\)\)')


def _new_id() -> str:
    """A fresh cell id. nbformat >= 4.5 requires one on every cell."""
    _new_id.counter += 1
    return f"gen-{_new_id.counter:04d}"


_new_id.counter = 0


def main() -> int:
    if not SOURCE.exists():
        print(f"ERROR: source notebook not found at {SOURCE}", file=sys.stderr)
        return 1

    nb = json.loads(SOURCE.read_text())
    cells = nb["cells"]
    print(f"Source: {SOURCE.name} ({len(cells)} cells)")

    out_cells = []
    applied: set[str] = set()
    dropped_raw = dropped_empty = converted = 0

    for cell in cells:
        src = "".join(cell["source"])
        kind = cell["cell_type"]

        # --- raw cells: drop noise, keep prose ----------------------------
        if kind == "raw":
            m = IMAGE_RAW.search(src)
            if m:
                out_cells.append({
                    "cell_type": "markdown",
                    "id": _new_id(),
                    "metadata": {},
                    "source": [
                        f"> **Reference figure `{m.group(1)}` is not included "
                        f"in this repository.**\n",
                        "> It is a screenshot of a table from the paper and "
                        "carries no physics; see `paper.pdf`.\n",
                    ],
                })
                converted += 1
                continue
            if DROP_RAW.search(src) or not src.strip():
                dropped_raw += 1
                continue
            out_cells.append({
                "cell_type": "markdown",
                "id": cell.get("id") or _new_id(),
                "metadata": {},
                "source": cell["source"],
            })
            converted += 1
            continue

        # --- empty code cells ---------------------------------------------
        if kind == "code" and not src.strip():
            dropped_empty += 1
            continue

        # --- code cells: patch the plumbing -------------------------------
        if kind == "code":
            for sig, replacement, label in PATCHES:
                if sig in src and label not in applied:
                    cell = dict(cell)
                    cell["source"] = replacement.splitlines(keepends=True)
                    applied.add(label)
                    break

        cell = dict(cell)
        if cell["cell_type"] == "code":
            # The verbatim plotting cells hardcode `lumi=3.4` in the CMS label,
            # a leftover from when LUM was a fixed 3400 pb^-1. The label would
            # otherwise state a luminosity the plot was not normalised to.
            src = "".join(cell["source"]).replace(
                "lumi=3.4", "lumi=round(LUM / 1000.0, 1)")
            cell["source"] = src.splitlines(keepends=True)
            cell["outputs"] = []
            cell["execution_count"] = None
        out_cells.append(cell)

    missing = [label for _, _, label in PATCHES if label not in applied]
    if missing:
        # Fail loudly. A patch that silently finds no cell leaves the original
        # broken plumbing in place, which is exactly what this script exists to
        # remove -- and the notebook would still look freshly generated.
        print(f"ERROR: these patches found no matching cell: {', '.join(missing)}",
              file=sys.stderr)
        print("The upstream notebook has changed; update the signatures in PATCHES.",
              file=sys.stderr)
        return 1

    nb["cells"] = out_cells
    nb["metadata"]["kernelspec"] = {
        "display_name": "Python 3 (ipykernel)",
        "language": "python",
        "name": "python3",
    }

    # Validate before writing: catches a malformed notebook here rather than
    # as an opaque failure when someone opens it. Every cell carries an "id",
    # as nbformat >= 4.5 requires.
    nbformat.validate(nbformat.from_dict(nb))
    OUT.write_text(json.dumps(nb, indent=1))

    n_code = sum(1 for c in out_cells if c["cell_type"] == "code")
    n_md = sum(1 for c in out_cells if c["cell_type"] == "markdown")
    print(f"Applied {len(applied)}/{len(PATCHES)} computational patches.")
    print(f"Dropped {dropped_raw} stale raw cells and {dropped_empty} empty code cells; "
          f"converted {converted} raw cells to markdown.")
    print(f"Wrote {OUT}: {len(out_cells)} cells ({n_code} code, {n_md} markdown)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
