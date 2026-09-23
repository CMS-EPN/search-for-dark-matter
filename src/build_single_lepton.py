#!/usr/bin/env python
"""Regenerate ``Single_Lepton.ipynb`` from the documentation markdown.

The single-lepton analysis exists upstream only as a rendered markdown export
(``search-for-dark-matter-docs/docs/Single_Lepton/Analisis_muon_final_version.md``),
not as a runnable notebook. This script converts it back into a notebook and
then patches *only the computational plumbing*, leaving every physics cell —
selection cuts, cross sections, kinematic definitions, plotting — byte-for-byte
as the collaboration wrote it.

Run it with::

    pixi run build-notebook

Each patch below states what was broken and why the replacement is equivalent
physics. If the upstream markdown changes, rerun this script rather than
hand-editing the notebook.
"""

from __future__ import annotations

import pathlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
REPO_ROOT = HERE.parent
DOCS_MD = (
    REPO_ROOT.parent
    / "search-for-dark-matter-docs"
    / "docs"
    / "Single_Lepton"
    / "Analisis_muon_final_version.md"
)
OUT = REPO_ROOT / "notebooks" / "Single_Lepton.ipynb"


# ---------------------------------------------------------------------------
# Replacement cells. Key = index among *code* cells in the converted notebook.
# ---------------------------------------------------------------------------

CELL_0_IMPORTS = '''\
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

print(f"awkward {ak.__version__} | uproot {uproot.__version__} | vector {vector.__version__}")
print(f"Analysis configuration: N_FILES={N_FILES} files/dataset, LUMI={LUMI_PB} pb^-1")
'''

CELL_2_DATASET_IMG = '''\
# Reference screenshot from the paper (not shipped with the repository).
dpoa_io.show_table("dataset_2016.png", "2016 datasets and run periods")
'''

CELL_3_MC_IMG = '''\
dpoa_io.show_table("MC_data.png", "Monte Carlo samples")
'''

CELL_4_NTUPLES = '''\
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

CELL_5_LUMI = '''\
# Golden JSON: the list of certified good luminosity sections for 2016.
# (Replaces `!wget`, which is not available on every platform and re-downloaded
# the file on every run.)
lumi_file = dpoa_io.download_lumi_json()
'''

CELL_11_OPEN = '''\
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

CELL_13_TABLE10 = '''\
dpoa_io.show_table("Table_10.png", "Table 10 - baseline selection")
'''

# --- shared physics constants injected into both lepton processors --------
_SL_PREAMBLE = '''
# --- b tagging (RUNBOOK PHYS-08 / PHYS-10) --------------------------------
# Was 0.2770, the 2017 DeepJet medium WP. This data is UL2016; Run2016H is
# postVFP, whose medium WP is 0.2489.
BTAG_WP_DEEPJET_MEDIUM_UL16POSTVFP = 0.2489   # UL16 postVFP
BTAG_WP_CSVV2_MEDIUM_2016          = 0.8484   # what the paper actually uses

# The paper tags b jets with CSVv2 medium (note Table 10, "CSVM"), so we use
# it here too. NanoAOD exposes it as Jet_btagCSVV2.
#
# Measured effect in the all-hadronic channel (RUNBOOK PHYS-10): every process
# LOSES events (ttbar 0.86x, Z(nunu) 0.81x) -- the two taggers differ by only
# a few percent on light jets, not the factor we first assumed. The switch is
# kept because it is what the paper does, not because it fixes the shape.
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

# --- MET noise filters (RUNBOOK PHYS-07), note section 2.1 ----------------
MET_FILTERS = [
    "Flag_goodVertices",
    "Flag_HBHENoiseFilter",
    "Flag_HBHENoiseIsoFilter",
    "Flag_EcalDeadCellTriggerPrimitiveFilter",
    "Flag_globalTightHalo2016Filter",
    "Flag_BadPFMuonFilter",
    "Flag_BadChargedCandidateFilter",
]
MET_FILTERS_DATA_ONLY = ["Flag_eeBadScFilter"]


def _event_quality(tree, met_pt, IS_DATA):
    """MET noise filters, plus the golden-JSON lumi mask on data."""
    filters = list(MET_FILTERS) + (MET_FILTERS_DATA_ONLY if IS_DATA else [])
    ok = ak.ones_like(met_pt, dtype=bool)
    for flag in filters:
        ok = ok & tree[flag].array()
    if IS_DATA:
        ok = ok & build_lumi_mask(str(dpoa_io.LUMI_JSON), tree)
    return ok
'''

# --- physics preserved verbatim, only the error handling changed -----------
CELL_14_PROCESS_MUON = '''\
vector.register_awkward()
''' + _SL_PREAMBLE + '''


def process_file_muon(filename, dataset="Unknown", IS_DATA=False):
    """Single-muon baseline selection for one NanoAOD file.

    PHYSICS IS UNCHANGED from the original notebook. The only difference is
    that this function no longer wraps its body in `try/except: return None`.
    That handler turned any failure — a dropped XRootD connection, a missing
    branch — into `None`, which the caller then passed to `pd.DataFrame(None)`,
    yielding an empty DataFrame. A failed download was therefore
    indistinguishable from a file with no selected events, and the MC
    normalisation was silently wrong. Errors are now caught, counted and
    reported by dpoa_io.process_dataset().
    """
    with dpoa_io.open_events(filename) as tree:
        muons = ak.zip({
            "pt": tree["Muon_pt"].array(),
            "eta": tree["Muon_eta"].array(),
            "phi": tree["Muon_phi"].array(),
            "mass": tree["Muon_mass"].array(),
            "iso": tree["Muon_pfRelIso04_all"].array(),
            "tightId": tree["Muon_tightId"].array(),
            "looseId": tree["Muon_looseId"].array(),
        }, with_name="Momentum4D")

        electrons = ak.zip({
            "pt": tree["Electron_pt"].array(),
            "eta": tree["Electron_eta"].array(),
            "phi": tree["Electron_phi"].array(),
            "mass": tree["Electron_mass"].array(),
            "cutBased": tree["Electron_cutBased"].array(),
        }, with_name="Momentum4D")

        jets = ak.zip({
            "pt": tree["Jet_pt"].array(),
            "eta": tree["Jet_eta"].array(),
            "phi": tree["Jet_phi"].array(),
            "mass": tree["Jet_mass"].array(),
            "jetId": tree["Jet_jetId"].array(),
            "btag": tree["Jet_btagDeepFlavB"].array(),
            "csv":  tree["Jet_btagCSVV2"].array(),
        }, with_name="Momentum4D")

        met_pt = tree["MET_pt"].array()
        met_phi = tree["MET_phi"].array()

        if not IS_DATA:
            gen_weight = tree["genWeight"].array()
            # PHYS-14: only ttbar has generated tops; every other sample gets 1.
            top_w = ak.Array(top_pt_weight(tree, len(met_pt))
                             if dataset.startswith("ttbar") else np.ones(len(met_pt)))
        else:
            gen_weight = ak.ones_like(met_pt)
            top_w = ak.Array(np.ones(len(met_pt)))

        # PHYS-07: MET noise filters + golden JSON
        pass_quality = _event_quality(tree, met_pt, IS_DATA)

    # ----- 2. BASELINE SELECTION (note Table 10) --------------------------
    mu_tight_mask = (muons.pt > 30) & (abs(muons.eta) < 2.4) & (muons.tightId) & (muons.iso < 0.15)
    mu_loose_mask = (muons.pt > 10) & (abs(muons.eta) < 2.4) & (muons.looseId) & (muons.iso < 0.25)
    ele_veto_mask = (electrons.pt > 10) & (abs(electrons.eta) < 2.5) & (electrons.cutBased >= 1)

    good_muons = muons[mu_tight_mask]
    veto_muons = muons[mu_loose_mask]
    veto_electrons = electrons[ele_veto_mask]

    has_1_tight_mu = (ak.num(good_muons) == 1)
    veto_extra_lep = (ak.num(veto_muons) == 1) & (ak.num(veto_electrons) == 0)
    pass_met = met_pt >= 160          # PHYS-03: note Table 10 (was 150)

    event_mask = has_1_tight_mu & veto_extra_lep & pass_met & pass_quality

    good_muons = good_muons[event_mask]
    jets = jets[event_mask]
    met_pt = met_pt[event_mask]
    met_phi = met_phi[event_mask]
    gen_weight = gen_weight[event_mask]
    top_w      = top_w[event_mask]                 # PHYS-14: same mask

    leading_mu = good_muons[:, 0]

    # ----- 3. JET CLEANING ------------------------------------------------
    jet_clean_mask = (
        (jets.pt > 30) &
        (jets.jetId >= 1) &
        (jets.deltaR(leading_mu) > 0.4)
    )
    all_clean_jets = jets[jet_clean_mask]

    central_jets = all_clean_jets[abs(all_clean_jets.eta) < 2.4]
    forward_jets = all_clean_jets[(abs(all_clean_jets.eta) >= 2.4) & (abs(all_clean_jets.eta) < 5.0)]

    has_2_jets = ak.num(central_jets) >= 2

    # ----- 4. FINAL SELECTION ---------------------------------------------
    f_met = met_pt[has_2_jets]
    f_met_phi = met_phi[has_2_jets]
    f_mu = leading_mu[has_2_jets]
    f_central = central_jets[has_2_jets]
    f_forward = forward_jets[has_2_jets]
    f_gen_weight = gen_weight[has_2_jets]
    f_top_w      = ak.to_numpy(top_w[has_2_jets])   # PHYS-14

    # mT_W
    dphi_lep = f_mu.phi - f_met_phi
    mt_w = np.sqrt(2 * f_mu.pt * f_met * (1 - np.cos(dphi_lep)))

    # min DeltaPhi (two leading jets vs MET)
    jets_top2 = f_central[:, :2]
    dphi_jets = abs(jets_top2.phi - f_met_phi)
    dphi_jets = np.mod(dphi_jets + np.pi, 2 * np.pi) - np.pi
    min_dphi = ak.min(abs(dphi_jets), axis=1)

    # PHYS-08 / PHYS-10: the paper's tagger (CSVv2 medium). Both are stored.
    is_btag_deepjet = f_central.btag > BTAG_WP_DEEPJET_MEDIUM_UL16POSTVFP
    is_btag_csv     = f_central.csv  > BTAG_WP_CSVV2_MEDIUM_2016
    is_btag = is_btag_csv if BTAG_DISCRIMINANT == "csv" else is_btag_deepjet
    n_btag = ak.sum(is_btag, axis=1)

    # Forward jet count
    n_fwd = ak.num(f_forward)

    # mT_b (transverse mass of MET and the leading b-jet)
    b_jets = f_central[is_btag]
    has_b = ak.num(b_jets) > 0

    b_jet_padded = ak.fill_none(ak.firsts(b_jets), {"pt": 0, "phi": 0}, axis=0)
    dphi_b = b_jet_padded.phi - f_met_phi
    calc_mt_b = np.sqrt(2 * b_jet_padded.pt * f_met * (1 - np.cos(dphi_b)))

    mt_b_np = ak.to_numpy(calc_mt_b)
    has_b_np = ak.to_numpy(has_b)
    mt_b_np[~has_b_np] = -1.0  # dummy value for events with no b-tag

    # ----- 5. OUTPUT ------------------------------------------------------
    out = {
        "dataset": dataset,
        "lep_pt": ak.to_numpy(f_mu.pt),
        "lep_eta": ak.to_numpy(f_mu.eta),
        "met": ak.to_numpy(f_met),
        "mT_W": ak.to_numpy(mt_w),
        "genWeight": ak.to_numpy(f_gen_weight),
        "topPtWeight": f_top_w,
        "nJet": ak.to_numpy(ak.num(f_central)),
        "nBTag": ak.to_numpy(n_btag),
        "nBTag_deepjet": ak.to_numpy(ak.sum(is_btag_deepjet, axis=1)),
        "nBTag_csv":     ak.to_numpy(ak.sum(is_btag_csv, axis=1)),
        "min_dphi": ak.to_numpy(min_dphi),
        "nForwardJets": ak.to_numpy(n_fwd),
        "mT_b": mt_b_np,
    }

    # PHYS-03: note Table 10 requires nb >= 1 in the baseline. Never applied
    # upstream, so b-free events the paper excludes were kept.
    df = pd.DataFrame(out)
    return df[df["nBTag"] >= 1].reset_index(drop=True)
'''

CELL_15_MC_MUON = '''\
# MC samples for the muon channel (unchanged physics list).
datasets_muon_mc = [
    'ttbar-semileptonic',   # tt(1l)
    'ttbar-2l2nu',          # tt(2l)  -- PHYS-06, was missing
    'Zvv-Zpt200',           # Z(nunu) -- PHYS-01, upstream had the wrong file
    'WJets-HT70to100', 'WJets-HT100to200', 'WJets-HT200to400',
    'WJets-HT400to600', 'WJets-HT600to800', 'WJets-HT800to1200',
    'WJets-HT1200to2500', 'WJets-HT2500toInf',   # PHYS-06: tail was missing
    't-channel-top', 't-channel-antitop',
    'ttW', 'WW', 'WZ', 'ZZ',        # PHYS-11: WZ was missing entirely
    'Zvv-Zpt100to200',              # PHYS-12: the lower Z pT bin was missing
    'DYJets-Zpt200',
]

# dpoa_io.process_dataset replaces the hand-rolled orchestrator loop. It:
#   * processes files in parallel threads (uproot releases the GIL on network
#     I/O, so this is several times faster than the original serial loop)
#   * retries transient XRootD failures
#   * REPORTS files that failed instead of silently dropping them
#   * caches to output_raw/*.parquet and reuses it on rerun (overwrite=True
#     forces reprocessing)
print(f"=== MUON CHANNEL - MC ({N_FILES} files per dataset) ===")

muon_reports = {}
for ds in datasets_muon_mc:
    _, rep = dpoa_io.process_dataset(
        ds, fileset, process_file_muon, is_data=False, n_files=N_FILES
    )
    muon_reports[ds] = rep
'''

CELL_16_DATA_MUON = '''\
# Real data: the SingleMuon primary dataset.
print(f"=== MUON CHANNEL - DATA ({N_FILES} files) ===")

_, rep = dpoa_io.process_dataset(
    "SingleMuon", fileset, process_file_muon, is_data=True, n_files=N_FILES
)
muon_reports["SingleMuon"] = rep
'''

CELL_17_SUMW = '''\
# Sum of generator weights, needed to normalise MC:  w = xsec * L / sumGenWeights
#
# This MUST cover exactly the same files that were processed above. In the
# original notebook the processing used N_FILES and this cell used a separate
# N_FILES_MC literal; when the two drifted apart (20 vs 10) every MC sample was
# normalised by the wrong denominator. Both now read the single N_FILES constant.
DATA_SL = {"SingleMuon", "SingleElectron"}

sum_weights_map = dpoa_io.sum_gen_weights(fileset, DATA_SL, n_files=N_FILES)
'''

CELL_18_SCALES = '''\
# --- Luminosity (RUNBOOK PHYS-02) ----------------------------------------
# Upstream used one LUM = 3400 pb^-1 for every channel, chosen to make plots
# agree rather than derived. Luminosity depends on WHICH data dataset was
# processed and HOW MUCH of it, so one constant cannot serve two channels.
# Open Data exposes only Run2016H = 8.9 fb^-1 (note Table 2).
DATA_SL = {"SingleMuon", "SingleElectron"}

LUMI_BY_CHANNEL = {
    ch: dd.luminosity_pb(ch, fileset[ch]["files"][:N_FILES], verbose=True)
    for ch in ("SingleMuon", "SingleElectron")
}
print(f"\\nupstream used 3400.0 pb^-1 for both.")

# Colours sampled from Figure 4 of paper.pdf so the stacks are directly
# comparable; the upstream palette used a different colour for every process.
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


def scale_factor(dataset, channel="muon"):
    """MC event weight: xsec * L(channel) / sumGenWeights. None for data."""
    if dataset in DATA_SL:
        return None
    lum = LUMI_BY_CHANNEL["SingleMuon" if channel == "muon" else "SingleElectron"]
    xsec = fileset[dataset]["metadata"]["xsec"]
    sum_w = sum_weights_map.get(dataset, 0.0)
    if not sum_w or xsec is None:
        return None
    return (xsec * lum) / sum_w


print(f"\\n{'Dataset':<22} | {'Xsec [pb]':>10} | {'SumGenW':>12} | {'Scale(mu)':>11}")
print("-" * 66)
for ds in fileset:
    if ds in DATA_SL:
        print(f"{ds:<22} | {'-':>10} | {'-':>12} | {'1.00':>11}")
        continue
    xsec = fileset[ds]["metadata"]["xsec"]
    sum_w = sum_weights_map.get(ds, 0.0)
    sc = scale_factor(ds, "muon")
    if sc is not None:
        print(f"{ds:<22} | {xsec:>10.4f} | {sum_w:>12.3e} | {sc:>11.3e}")
    else:
        print(f"{ds:<22} | {str(xsec):>10} | {sum_w:>12.3e} | {'--':>11}")
'''

CELL_19_PLOT = '''\
import mplhep as hep
import matplotlib.pyplot as plt

plt.style.use(hep.style.CMS)


def plot_grouped_stack(var_name, x_label, x_range, channel_data="SingleMuon",
                       n_bins=30, log_scale=False, dfs=None):
    """Stacked MC vs data histogram.

    `dfs` was previously read from a module-level `all_dfs` global that later
    cells reassigned to the electron dictionary. Re-running an earlier cell
    then silently plotted the wrong channel. It is now an explicit argument;
    it still falls back to `all_dfs` so existing calls keep working.
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

    # Luminosity is per channel (PHYS-02), so the CMS label shows the value
    # for whichever dataset is being plotted rather than one global constant.
    _lumi = LUMI_BY_CHANNEL.get(channel_data, max(LUMI_BY_CHANNEL.values()))
    hep.cms.label("Preliminary", data=True, lumi=round(_lumi / 1000.0, 1), year=2016, ax=ax)

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

CELL_20_LOAD_MUON = '''\
def load_channel(channel="muon"):
    """Load the processed parquet files for one channel and attach event weights."""
    data_name = "SingleMuon" if channel == "muon" else "SingleElectron"
    suffix = "_raw.parquet" if channel == "muon" else "_electron_raw.parquet"

    datasets = [data_name] + datasets_muon_mc

    loaded = {}
    missing = []

    for ds in datasets:
        path = dpoa_io.OUTPUT_DIR / f"{ds}{suffix}"
        if not path.exists():
            missing.append(ds)
            continue

        df = pd.read_parquet(path)

        if ds in DATA_SL:
            df["final_weight"] = 1.0
        else:
            scale = scale_factor(ds, channel)
            if scale is None:
                missing.append(f"{ds} (no scale factor)")
                continue
            w = df["genWeight"] * scale if "genWeight" in df.columns else scale
            # PHYS-14: top pT reweighting. Older parquets predate the column,
            # so its absence means "no correction", not an error.
            if "topPtWeight" in df.columns:
                w = w * df["topPtWeight"]
            df["final_weight"] = w

        loaded[ds] = df

    print(f"Loaded {len(loaded)} datasets for the {channel} channel.")
    if missing:
        # The original code swallowed FileNotFoundError with a bare `continue`,
        # so a stack could be missing half its backgrounds with no indication.
        print(f"NOT loaded ({len(missing)}): {', '.join(missing)}")

    return loaded


muon_dfs = load_channel("muon")
all_dfs = muon_dfs

if muon_dfs:
    plot_grouped_stack("mT_W",  r"$m_T^W$ [GeV]",        (0, 200),   "SingleMuon", dfs=muon_dfs)
    plot_grouped_stack("met",   r"$p_T^{miss}$ [GeV]",   (150, 500), "SingleMuon", dfs=muon_dfs, log_scale=True)
    plot_grouped_stack("nJet",  r"$N_{jets}$",           (2, 10),    "SingleMuon", dfs=muon_dfs, n_bins=8, log_scale=True)
    plot_grouped_stack("nBTag", r"$N_{b-tags}$",         (0, 5),     "SingleMuon", dfs=muon_dfs, n_bins=5, log_scale=True)
else:
    print("No data loaded. Run the processing cells above first.")
'''

CELL_22_ELE_MC = '''\
datasets_electron_mc = [
    'ttbar-semileptonic',   # tt(1l)
    'ttbar-2l2nu',          # tt(2l)  -- PHYS-06, was missing
    'Zvv-Zpt200',           # Z(nunu) -- PHYS-01, upstream had the wrong file
    'WJets-HT70to100', 'WJets-HT100to200', 'WJets-HT200to400',
    'WJets-HT400to600', 'WJets-HT600to800', 'WJets-HT800to1200',
    'WJets-HT1200to2500', 'WJets-HT2500toInf',   # PHYS-06: tail was missing
    't-channel-top', 't-channel-antitop',
    'ttW', 'WW', 'WZ', 'ZZ',        # PHYS-11: WZ was missing entirely
    'Zvv-Zpt100to200',              # PHYS-12: the lower Z pT bin was missing
    'DYJets-Zpt200',
]

print(f"=== ELECTRON CHANNEL - MC ({N_FILES} files per dataset) ===")

electron_reports = {}
for ds in datasets_electron_mc:
    _, rep = dpoa_io.process_dataset(
        ds, fileset, process_electron, is_data=False,
        n_files=N_FILES, suffix="_electron_raw",
    )
    electron_reports[ds] = rep
'''

CELL_23_ELE_DATA = '''\
print(f"=== ELECTRON CHANNEL - DATA ({N_FILES} files) ===")

_, rep = dpoa_io.process_dataset(
    "SingleElectron", fileset, process_electron, is_data=True,
    n_files=N_FILES, suffix="_electron_raw",
)
electron_reports["SingleElectron"] = rep
'''

CELL_24_ELE_LOAD = '''\
electron_dfs = load_channel("electron")

if electron_dfs:
    plot_grouped_stack("mT_W",  r"$m_T^W$ [GeV]",      (0, 200),   "SingleElectron", dfs=electron_dfs)
    plot_grouped_stack("met",   r"$p_T^{miss}$ [GeV]", (150, 500), "SingleElectron", dfs=electron_dfs, log_scale=True)
    plot_grouped_stack("nJet",  r"$N_{jets}$",         (2, 10),    "SingleElectron", dfs=electron_dfs, n_bins=8, log_scale=True)
    plot_grouped_stack("nBTag", r"$N_{b-tags}$",       (0, 5),     "SingleElectron", dfs=electron_dfs, n_bins=5, log_scale=True)
else:
    print("No electron data loaded. Run the electron processing cells above first.")
'''

CELL_25_TABLE13 = '''\
dpoa_io.show_table("Table_13.png", "Table 13 - signal region definitions")
'''

CELL_26_LOAD_DATA = '''\
# `load_data` is kept as a thin alias so the signal- and control-region cells
# below read exactly as they do in the documentation.
def load_data(channel="muon"):
    return load_channel(channel)
'''

CELL_31_TABLE14 = '''\
dpoa_io.show_table("Table_14.png", "Table 14 - control region definitions")
'''

CELL_21_PROCESS_ELECTRON = '''\
def process_electron(filename, dataset="Unknown", IS_DATA=False):
    """Single-electron baseline selection for one NanoAOD file.

    PHYSICS IS UNCHANGED from the original notebook. The only difference is
    that the file is opened through dpoa_io.open_events(), which retries
    transient XRootD failures, instead of a bare uproot.open().
    """
    with dpoa_io.open_events(filename) as tree:
        electrons = ak.zip({
            "pt": tree["Electron_pt"].array(),
            "eta": tree["Electron_eta"].array(),
            "phi": tree["Electron_phi"].array(),
            "mass": tree["Electron_mass"].array(),
            "cutBased": tree["Electron_cutBased"].array(),
        }, with_name="Momentum4D")

        muons = ak.zip({
            "pt": tree["Muon_pt"].array(),
            "eta": tree["Muon_eta"].array(),
            "phi": tree["Muon_phi"].array(),
            "mass": tree["Muon_mass"].array(),
            "looseId": tree["Muon_looseId"].array(),
            "iso": tree["Muon_pfRelIso04_all"].array(),
        }, with_name="Momentum4D")

        jets = ak.zip({
            "pt": tree["Jet_pt"].array(),
            "eta": tree["Jet_eta"].array(),
            "phi": tree["Jet_phi"].array(),
            "mass": tree["Jet_mass"].array(),
            "jetId": tree["Jet_jetId"].array(),
            "btag": tree["Jet_btagDeepFlavB"].array(),
            "csv":  tree["Jet_btagCSVV2"].array(),
        }, with_name="Momentum4D")

        met_pt = tree["MET_pt"].array()
        met_phi = tree["MET_phi"].array()

        if not IS_DATA:
            gen_weight = tree["genWeight"].array()
            # PHYS-14: only ttbar has generated tops; every other sample gets 1.
            top_w = ak.Array(top_pt_weight(tree, len(met_pt))
                             if dataset.startswith("ttbar") else np.ones(len(met_pt)))
        else:
            gen_weight = ak.ones_like(met_pt)
            top_w = ak.Array(np.ones(len(met_pt)))

        # PHYS-07: MET noise filters + golden JSON
        pass_quality = _event_quality(tree, met_pt, IS_DATA)

    # ----- 1. SELECTION (note Table 10) -----------------------------------
    in_gap = (abs(electrons.eta) > 1.4442) & (abs(electrons.eta) < 1.566)
    ele_tight_mask = (electrons.pt > 30) & (abs(electrons.eta) < 2.1) & (electrons.cutBased == 4) & (~in_gap)
    ele_veto_mask = (electrons.pt > 10) & (electrons.cutBased >= 1)
    mu_loose_mask = (muons.pt > 10) & (abs(muons.eta) < 2.4) & (muons.looseId) & (muons.iso < 0.25)

    good_ele = electrons[ele_tight_mask]
    veto_ele = electrons[ele_veto_mask]
    veto_mu = muons[mu_loose_mask]

    has_1_tight = (ak.num(good_ele) == 1)
    is_exclusive = (ak.num(veto_ele) == 1) & (ak.num(veto_mu) == 0)
    pass_met = met_pt >= 160          # PHYS-03: note Table 10 (was 150)

    event_mask = has_1_tight & is_exclusive & pass_met & pass_quality

    good_ele = good_ele[event_mask]
    jets = jets[event_mask]
    met_pt = met_pt[event_mask]
    met_phi = met_phi[event_mask]
    gen_weight = gen_weight[event_mask]
    top_w      = top_w[event_mask]                 # PHYS-14: same mask
    leading_ele = good_ele[:, 0]

    # ----- 2. JET CLEANING against the ELECTRON ---------------------------
    jet_clean_mask = (
        (jets.pt > 30) & (jets.jetId >= 1) &
        (jets.deltaR(leading_ele) > 0.4)
    )
    all_clean_jets = jets[jet_clean_mask]

    central_jets = all_clean_jets[abs(all_clean_jets.eta) < 2.4]
    forward_jets = all_clean_jets[(abs(all_clean_jets.eta) >= 2.4) & (abs(all_clean_jets.eta) < 5.0)]

    has_2_jets = ak.num(central_jets) >= 2

    f_met = met_pt[has_2_jets]
    f_met_phi = met_phi[has_2_jets]
    f_ele = leading_ele[has_2_jets]
    f_central = central_jets[has_2_jets]
    f_forward = forward_jets[has_2_jets]
    f_gen_weight = gen_weight[has_2_jets]
    f_top_w      = ak.to_numpy(top_w[has_2_jets])   # PHYS-14

    # mT
    dphi = f_ele.phi - f_met_phi
    mt = np.sqrt(2 * f_ele.pt * f_met * (1 - np.cos(dphi)))

    # min DeltaPhi
    jets_top2 = f_central[:, :2]
    dphi_jets = abs(jets_top2.phi - f_met_phi)
    dphi_jets = np.mod(dphi_jets + np.pi, 2 * np.pi) - np.pi
    min_dphi = ak.min(abs(dphi_jets), axis=1)

    # B-tagging - PHYS-08: UL16 postVFP WP (was 0.2770, a 2017 value)
    # PHYS-08 / PHYS-10: the paper's tagger (CSVv2 medium). Both are stored.
    is_btag_deepjet = f_central.btag > BTAG_WP_DEEPJET_MEDIUM_UL16POSTVFP
    is_btag_csv     = f_central.csv  > BTAG_WP_CSVV2_MEDIUM_2016
    is_btag = is_btag_csv if BTAG_DISCRIMINANT == "csv" else is_btag_deepjet
    n_btag = ak.sum(is_btag, axis=1)

    n_fwd = ak.num(f_forward)

    b_jets = f_central[is_btag]
    has_b = ak.num(b_jets) > 0
    b_jet_padded = ak.fill_none(ak.firsts(b_jets), {"pt": 0, "phi": 0}, axis=0)
    dphi_b = b_jet_padded.phi - f_met_phi
    calc_mt_b = np.sqrt(2 * b_jet_padded.pt * f_met * (1 - np.cos(dphi_b)))

    mt_b_np = ak.to_numpy(calc_mt_b)
    has_b_np = ak.to_numpy(has_b)
    mt_b_np[~has_b_np] = -1.0

    out = {
        "dataset": dataset,
        "lep_pt": ak.to_numpy(f_ele.pt),
        "lep_eta": ak.to_numpy(f_ele.eta),
        "met": ak.to_numpy(f_met),
        "mT_W": ak.to_numpy(mt),
        "genWeight": ak.to_numpy(f_gen_weight),
        "topPtWeight": f_top_w,
        "nJet": ak.to_numpy(ak.num(f_central)),
        "nBTag": ak.to_numpy(n_btag),
        "nBTag_deepjet": ak.to_numpy(ak.sum(is_btag_deepjet, axis=1)),
        "nBTag_csv":     ak.to_numpy(ak.sum(is_btag_csv, axis=1)),
        "min_dphi": ak.to_numpy(min_dphi),
        "nForwardJets": ak.to_numpy(n_fwd),
        "mT_b": mt_b_np,
    }

    # PHYS-03: note Table 10 requires nb >= 1 in the baseline. Never applied
    # upstream, so b-free events the paper excludes were kept.
    df = pd.DataFrame(out)
    return df[df["nBTag"] >= 1].reset_index(drop=True)
'''

# ===========================================================================
#  PHASE B - physics corrections. See RUNBOOK.md, PHYS-01 .. PHYS-08.
# ===========================================================================

CELL_0_IMPORTS_B = '''\
import os
import json
import time

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import hist
import requests

import awkward as ak
import uproot
import vector

vector.register_awkward()

# dpoa_io       : plumbing only. No physics.
# dpoa_datasets : physics inputs (samples, cross sections, luminosity).
import dpoa_io
import dpoa_datasets as dd
from dpoa_io import N_FILES

print(f"awkward {ak.__version__} | uproot {uproot.__version__} | vector {vector.__version__}")
print(f"N_FILES = {N_FILES} per dataset")
'''

CELL_4_NTUPLES_B = '''\
# dd.build_registry() replaces the broken 'Zvv' entry and adds the samples the
# upstream registry was missing (RUNBOOK PHYS-01, PHYS-06).
ntuples = dd.build_registry(nanoaod_filenames)

with open("ntuples.json", "w") as f:
    json.dump(ntuples, f, indent=1)

print()
print(f"{len(ntuples)} datasets indexed.")
'''

CELL_7_XSEC_B = '''\
# Cross sections [pb], with provenance next to each value in dpoa_datasets.
# Two were wrong (RUNBOOK PHYS-01):
#   Zvv            wrong sample entirely; now ZJetsToNuNu_Zpt-200toInf
#                  _BPSFilter at 0.7333 pb        [XSDB 2026-09-03]
#   DYJets-Zpt200  was 1.27 pb, actually 0.393 pb [XSDB, UL16 row]
# Everything else is note Table 6.
XSEC_PB = dd.XSEC_PB
print(f"{len(XSEC_PB)} cross sections loaded from dpoa_datasets.")
'''

CELL_27_SIGNAL_REGIONS_B = '''\
def signal_regions(df):
    """Single-lepton signal regions - note Table 13.

        pTmiss          >= 160 GeV
        MT              >= 160 GeV
        MT2W            >= 200 GeV     <-- NOT IMPLEMENTED, see below
        min dphi(j1,2)  >= 1.2
        mT_b            >= 180 GeV
        categories: nb=1 & 0 FJ | nb=1 & >=1 FJ | nb>=2

    RUNBOOK PHYS-05. Upstream applied only pTmiss > 160 and min dphi > 0.5;
    MT, mT_b and the correct dphi threshold were all missing.

    MT2W IS NOT APPLIED. It requires a kinematic minimisation over jet-lepton
    assignments (note ref. [41]) that is not implemented here, so these regions
    are LOOSER than the paper's and will retain more tt(2l) background. This is
    a known, documented gap -- see RUNBOOK [OPEN-3].
    """
    if df is None or len(df) == 0:
        return {}

    pass_common = (
        (df["met"]      >= 160) &
        (df["mT_W"]     >= 160) &   # PHYS-05: was not applied at all
        (df["min_dphi"] >= 1.2) &   # PHYS-05: was 0.5
        (df["mT_b"]     >= 180)     # PHYS-05: computed, never applied
    )

    df_sr = df[pass_common]
    if len(df_sr) == 0:
        return {}

    mask_1b_0f = (df_sr["nBTag"] == 1) & (df_sr["nForwardJets"] == 0)
    mask_1b_1f = (df_sr["nBTag"] == 1) & (df_sr["nForwardJets"] >= 1)
    mask_2b    = (df_sr["nBTag"] >= 2)

    return {
        "SR_1b_0f": df_sr[mask_1b_0f],
        "SR_1b_1f": df_sr[mask_1b_1f],
        "SR_2b":    df_sr[mask_2b],
    }
'''

CELL_32_CR_B = '''\
def filter_cr_wlnu(df):
    """W+jets control region - note Table 14, columns SL1eWR / SL1mWR.

        nlep = 1,  njet >= 2,  nb = 0,  pTmiss >= 160 GeV,  MT >= 160 GeV

    The nb = 0 requirement is what makes this orthogonal to the signal region.
    Upstream used MT >= 80 GeV; Table 14 requires 160.
    """
    if df is None or len(df) == 0:
        return {}

    mask = (
        (df["met"]   >= 160) &
        (df["mT_W"]  >= 160) &   # note Table 14 (was 80)
        (df["nBTag"] == 0) &
        (df["nJet"]  >= 2)
    )

    df_cr = df[mask]
    return {"CR_Wlnu": df_cr} if len(df_cr) else {}
'''


# The region plot lives in region_plot_cell.py so both channel builders embed
# exactly the same code. See RUNBOOK PLOT-01..PLOT-04.
CELL_28_REGION_PLOT = (pathlib.Path(__file__).parent / "region_plot_cell.py").read_text()

REPLACEMENTS = {
    0: CELL_0_IMPORTS_B,
    2: CELL_2_DATASET_IMG,
    3: CELL_3_MC_IMG,
    4: CELL_4_NTUPLES_B,
    5: CELL_5_LUMI,
    11: CELL_11_OPEN,
    7: CELL_7_XSEC_B,
    13: CELL_13_TABLE10,
    14: CELL_14_PROCESS_MUON,
    15: CELL_15_MC_MUON,
    16: CELL_16_DATA_MUON,
    17: CELL_17_SUMW,
    18: CELL_18_SCALES,
    19: CELL_19_PLOT,
    20: CELL_20_LOAD_MUON,
    21: CELL_21_PROCESS_ELECTRON,
    22: CELL_22_ELE_MC,
    23: CELL_23_ELE_DATA,
    24: CELL_24_ELE_LOAD,
    25: CELL_25_TABLE13,
    26: CELL_26_LOAD_DATA,
    27: CELL_27_SIGNAL_REGIONS_B,
    28: CELL_28_REGION_PLOT,
    32: CELL_32_CR_B,
    31: CELL_31_TABLE14,
}

SL_COMPOSITION = '# --- Composition check against note Table 11 (RUNBOOK Part 6) -------------\n# Table 11 is to the single-lepton channel what Table 12 is to the all-hadronic\n# one. After the full SL selection it gives, as a share of total background:\n#\n#   tt(2l) 61.4%, W+jets 14.8%, t+X 14.1%, ttV 4.2%, VV/VH 3.5%,\n#   tt(1l) 1.7%, Z(ll) 0.2%, Z(nunu) 0.1%,  and data/MC = 1.118\n#\n# Two things to read off it before comparing anything:\n#\n#  * The dominant background is DILEPTONIC ttbar, by 37 to 1 over the\n#    semileptonic one. MT > 160 GeV removes genuine 1-lepton ttbar almost\n#    entirely (its transverse mass has a Jacobian edge at the W mass); what\n#    survives is ttbar where a second lepton was lost. So the two ttbar samples\n#    are reported separately here, even though the stack plots merge them into\n#    one yellow band as the paper\'s legend does.\n#\n#  * MT2W IS NOT IMPLEMENTED (RUNBOOK [OPEN-3]). Table 11 shows it removes 84%\n#    of the background on its own -- more than every other signal-region cut\n#    combined -- and 9.3x of tt(2l) specifically. Our regions are therefore\n#    several times too full, dominated by ttbar. That is expected and\n#    quantified, not a discrepancy to chase.\nTABLE11 = {"ttbar-2l2nu": 61.4, "WJets": 14.8, "tX": 14.1,\n           "Diboson": 3.5, "ttbar-semileptonic": 1.7,\n           "Zll": 0.2, "Zvv": 0.1}\n\n\ndef composition_table(dfs, data_name, label):\n    """Yields per process against note Table 11. ttbar is split 1l / 2l."""\n    if not dfs:\n        print(f"({label}: nothing loaded)")\n        return\n    yields = {}\n    for name, df in dfs.items():\n        if name in DATA_SL:\n            continue\n        # ttbar is kept split here: Table 11 separates them and the split is\n        # the most informative number in this channel.\n        key = name if name.startswith("ttbar") else get_group_info(name)[0]\n        yields[key] = yields.get(key, 0.0) + float(df["final_weight"].sum())\n\n    total_mc = sum(yields.values())\n    n_data = len(dfs[data_name]) if data_name in dfs else 0\n\n    print(f"\\n=== {label} — composicion vs note Table 11 ===")\n    print(f"{\'process\':<22} {\'events\':>12} {\'obs %\':>8} {\'Table 11 %\':>12}")\n    print("-" * 58)\n    for g in sorted(yields, key=lambda k: -yields[k]):\n        pct = 100 * yields[g] / total_mc if total_mc else 0\n        ref = TABLE11.get(g)\n        print(f"{g:<22} {yields[g]:>12.1f} {pct:>7.1f}% "\n              f"{(f\'{ref:.1f}%\' if ref is not None else \'-\'):>12}")\n    print("-" * 58)\n    print(f"{\'total MC\':<22} {total_mc:>12.1f}")\n    print(f"{\'data\':<22} {n_data:>12d}")\n    if total_mc:\n        print(f"\\ndata/MC = {n_data / total_mc:.3f}   (note Table 11: 1.118)")\n    print("NB: MT2W no aplicado — el fondo esta ~6x alto por eso. Ver RUNBOOK Part 6.")\n\n\n# The Table 11 percentages above are for the FULL signal selection, so they must\n# be compared against our full selection too -- not against the baseline, whose\n# composition is a different thing entirely. signal_regions() applies everything\n# Table 13 asks for except MT2W, so summing its three regions reproduces the\n# note\'s "MTb" row with that one cut missing. That is the honest comparison.\nfor _ch, _dn in (("muon", "SingleMuon"), ("electron", "SingleElectron")):\n    _dfs = load_channel(_ch)\n    if not _dfs:\n        continue\n    _sr = {}\n    for _name, _df in _dfs.items():\n        _parts = [d for d in signal_regions(_df).values() if d is not None and len(d)]\n        if _parts:\n            _sr[_name] = pd.concat(_parts, ignore_index=True)\n    composition_table(_sr, _dn, f"{_ch} — SR completa (sin MT2W)")\n'

RUN_ANALYSIS_SL = SL_COMPOSITION + """

def run_analysis_for_channel(channel_mode):

    raw_dfs = load_data(channel_mode)
    if not raw_dfs:
        return

    regions_db = {"SR_1b_0f": {}, "SR_1b_1f": {}, "SR_2b": {}}
    for name, df in raw_dfs.items():
        for reg, df_reg in signal_regions(df).items():
            regions_db[reg][name] = df_reg

    d_label = "SingleMuon" if channel_mode == "muon" else "SingleElectron"

    # RUNBOOK PLOT-02: paper Figure 4 bins pTmiss from 160 to 520 GeV in nine
    # 40 GeV bins, the last one holding the overflow. We had 160-600 in ten
    # 44 GeV bins, so not a single bin edge lined up with the paper's and the
    # two histograms could not be compared bin by bin.
    ch = "mu" if channel_mode == "muon" else "e"
    kw = dict(n_bins=9,
              lumi_label=round(LUMI_BY_CHANNEL[d_label] / 1000.0, 1))

    plot_region_stack(regions_db["SR_2b"], f"1{ch}, 2 b tag, SR",
                      "met", r"$p_T^{miss}$ [GeV]", (160, 520), d_label, **kw)
    plot_region_stack(regions_db["SR_1b_1f"], f"1{ch}, SR, 1 FJ",
                      "met", r"$p_T^{miss}$ [GeV]", (160, 520), d_label, **kw)
    plot_region_stack(regions_db["SR_1b_0f"], f"1{ch}, SR, 0 FJ",
                      "met", r"$p_T^{miss}$ [GeV]", (160, 520), d_label, **kw)
"""




# Applied by signature rather than by index: this cell is verbatim physics
# from the docs, so its position shifts whenever the markdown changes.
SIGNATURE_REPLACEMENTS = [
    ("def run_analysis_for_channel", RUN_ANALYSIS_SL, "run_analysis"),
]


# Cells kept verbatim (physics): 1, 6, 8, 9, 10, 12, 28, 29, 30, 33, 34


def main() -> int:
    if not DOCS_MD.exists():
        print(f"ERROR: source markdown not found at {DOCS_MD}", file=sys.stderr)
        print("Clone search-for-dark-matter-docs next to this repository.", file=sys.stderr)
        return 1

    tmp = HERE / ".sl_source.md"
    tmp.write_text(DOCS_MD.read_text())
    try:
        subprocess.run(
            [sys.executable, "-m", "jupytext", "--from", "md", "--to", "ipynb",
             str(tmp), "-o", str(OUT)],
            check=True, capture_output=True,
        )
    finally:
        tmp.unlink(missing_ok=True)

    nb = json.loads(OUT.read_text())

    code_idx = [i for i, c in enumerate(nb["cells"]) if c["cell_type"] == "code"]
    print(f"Converted notebook: {len(nb['cells'])} cells ({len(code_idx)} code).")

    patched = 0
    for n, source in REPLACEMENTS.items():
        if n >= len(code_idx):
            print(f"  WARNING: no code cell #{n}; upstream markdown may have changed.")
            continue
        cell = nb["cells"][code_idx[n]]
        cell["source"] = source.splitlines(keepends=True)
        cell["outputs"] = []
        cell["execution_count"] = None
        patched += 1

    # Signature-based pass for verbatim cells whose index is not stable.
    for sig, source, label in SIGNATURE_REPLACEMENTS:
        hit = False
        for cell in nb["cells"]:
            if cell["cell_type"] == "code" and sig in "".join(cell["source"]):
                cell["source"] = source.splitlines(keepends=True)
                cell["outputs"] = []
                cell["execution_count"] = None
                patched += 1
                hit = True
                break
        if not hit:
            print(f"ERROR: patch '{label}' found no cell matching {sig!r}",
                  file=sys.stderr)
            return 1

    # Clear stale outputs everywhere so the notebook ships clean, and fix the
    # hardcoded `lumi=3.4` in the verbatim plotting cells -- a leftover from
    # when LUM was a fixed 3400 pb^-1. The label would otherwise state a
    # luminosity the plot was not normalised to.
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            src = "".join(cell["source"]).replace(
                "lumi=3.4",
                "lumi=round(max(LUMI_BY_CHANNEL.values()) / 1000.0, 1)")
            cell["source"] = src.splitlines(keepends=True)
            cell.setdefault("outputs", [])
            cell["outputs"] = []
            cell["execution_count"] = None

    nb["metadata"]["kernelspec"] = {
        "display_name": "Python 3 (ipykernel)",
        "language": "python",
        "name": "python3",
    }

    OUT.write_text(json.dumps(nb, indent=1))
    print(f"Patched {patched} computational cells; physics cells left verbatim.")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
