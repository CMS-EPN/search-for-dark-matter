"""
dpoa_datasets — physics inputs: which samples, which cross sections, how much luminosity.

Unlike ``dpoa_io`` (pure plumbing), this module holds *physics* numbers. Every
value carries its provenance, so a reader can check it against the source:

  * "notes Table 6"  -> Table 6 of ``analysisis_notes.pdf`` (the CMS analysis
    note's list of simulated samples and cross sections)
  * "notes Table 2"  -> the per-run-period integrated luminosities
  * "derived"        -> computed here from other quoted numbers; the derivation
    is written out. These are the only numbers not taken from a CMS source, and
    they are flagged so they can be replaced when a better value is available.

The upstream registry in ``dpoa_workshop.py`` is left untouched; this module
layers corrections and additions on top of it.
"""

from __future__ import annotations

import json

import requests

__all__ = [
    "RUN2016H_LUMI_PB",
    "EXTRA_RECORDS",
    "XSEC_PB",
    "DATA_RECORDS",
    "build_registry",
    "dataset_byte_fraction",
    "luminosity_pb",
]

_API = "https://opendata.cern.ch/api/records"
_TIMEOUT = 60


# ---------------------------------------------------------------------------
# Luminosity
# ---------------------------------------------------------------------------
# notes Table 2: the 2016 run periods and their integrated luminosities. CMS
# Open Data for this analysis only exposes Run2016H, which is 8.9 fb^-1.
#
# The analysis note quotes 35.9 fb^-1 for the full 2016 dataset; every cut-flow
# and figure in the note is at that luminosity. We only have Run2016H, and only
# a fraction of its files, so our yields are correspondingly smaller.
RUN2016H_LUMI_PB: float = 8900.0

# Open Data record ids for the three primary datasets, used to work out what
# fraction of each we actually processed.
DATA_RECORDS: dict[str, int] = {
    "met": 30559,
    "SingleMuon": 30563,
    "SingleElectron": 30562,
}


# ---------------------------------------------------------------------------
# Samples missing from, or wrong in, the upstream registry
# ---------------------------------------------------------------------------
# Each entry is an Open Data record id whose NANOAODSIM file index we resolve
# through the API. Using record ids rather than hard-coded file_index URLs means
# a renamed index cannot silently produce an empty dataset.
EXTRA_RECORDS: dict[str, int] = {
    # --- THE important one -------------------------------------------------
    # The upstream 'Zvv' entry resolves to ggH_HToSSTo4l_lowctau_MH-500_MS-150,
    # a long-lived-particle SIGNAL sample, while being given the Z->nunu cross
    # section. Per notes Table 12, Z(nunu)+jets is 10079.71 of 34214.64 total
    # background events after the AH baseline -- 29%, the second largest
    # background in the channel. Getting it wrong is the single biggest reason
    # the all-hadronic stack sits far below the data.
    "Zvv-Zpt200": 74910,       # ZJetsToNuNu_Zpt-200toInf_BPSFilter UL16 NanoAODv9
    "Zvv-Zpt100to200": 74908,  # ZJetsToNuNu_Zpt-100to200_BPSFilter

    # --- dileptonic ttbar: 1292.85/34214.64 = 3.8% of the AH background -----
    "ttbar-2l2nu": 67801,      # TTTo2L2Nu

    # --- the W+jets tail, which is what survives pTmiss > 250 GeV -----------
    # W+jets is 5160.62/34214.64 = 15% of the AH background. The upstream
    # registry stops at HT-400to600.
    "WJets-HT600to800": 69731,
    "WJets-HT800to1200": 69735,
    "WJets-HT1200to2500": 69723,
    "WJets-HT2500toInf": 69727,

    # --- diboson: WZ was missing entirely ---------------------------------
    # notes Table 6 lists five WZ decay modes summing to 30.26 pb. The upstream
    # registry has WW and ZZ but no WZ at all, so the "VV, VH" stack was short
    # of a third of its content -- visible in the paper's Figure 5, where the
    # dark blue band is much larger than ours.
    "WZ": 72754,               # WZ_TuneCP5 inclusive, UL16 NanoAODv9
}

# NOTE ON TTToHadronic (record 67841): deliberately NOT included. It is absent
# from notes Table 6, and notes Table 12 has no fully-hadronic ttbar row -- the
# AH background is tt(1l) (42%) and tt(2l) (3.8%). With no genuine pTmiss,
# fully-hadronic ttbar behaves like QCD multijet, which is only 367.51/34214.64
# = 1.1% of the AH background and is killed by min dphi(j1,2, pTmiss) > 0.4.
# Adding it would depart from the published analysis, not converge on it.


# ---------------------------------------------------------------------------
# Cross sections [pb]
# ---------------------------------------------------------------------------
XSEC_PB: dict[str, float] = {
    # ----- top quark ------------------------------------ notes Table 6 -----
    "ttbar-semileptonic": 364.35,   # TTToSemilepton
    "ttbar-2l2nu":         87.31,   # TTTo2L2Nu
    "t-channel-top":      136.02,   # ST_t-channel_top
    "t-channel-antitop":   80.95,   # ST_t-channel_antitop

    # ----- rare top ------------------------------------- notes Table 6 -----
    "ttW":                  0.2043,  # TTWJetsToLNu

    # ----- W+jets, HT-binned ---------------------------- notes Table 6 -----
    # The note's table lists HT-800To1200 as 1.329 and HT-1200To2500 as 5.501,
    # which is the pair swapped: the cross section must fall with increasing HT.
    # The standard CMS values (used here) are 5.501 and 1.329 respectively.
    # The note's HT-200To400 entry reads 1345 -- a copy of the HT-100To200 row;
    # the standard value is 359.7, which is what the upstream notebook uses too.
    "WJets-HT70to100":   1372.0,
    "WJets-HT100to200":  1345.0,
    "WJets-HT200to400":   359.7,
    "WJets-HT400to600":    48.91,
    "WJets-HT600to800":    12.05,
    "WJets-HT800to1200":    5.501,
    "WJets-HT1200to2500":   1.329,
    "WJets-HT2500toInf":    0.0322,

    # ----- diboson, inclusive --------------------------- notes Table 6 -----
    # The note lists exclusive decay modes; these are the standard inclusive
    # NNLO values, matching the inclusive samples Open Data provides.
    # Sum of the note's WW modes = 113.9, of its ZZ modes = 15.88: consistent.
    "WW": 118.7,
    "ZZ":  16.6,
    "WZ":  47.13,   # inclusive NNLO; the note's exclusive modes sum to 30.26

    # ----- Z + jets -------------------------------- XSDB (CMS official) ----
    # Source: XSDB, queried 2026-09-03, process_name=ZJetsToNuNu_Zpt.*
    # It returns TWO entries per pT bin, and choosing between them is the single
    # most consequential number in this analysis (Z->nunu is 29.7% of the AH
    # background per note Table 12):
    #
    #     ZJetsToNuNu_Zpt-200toInf_BPSFilter_TuneCP5    0.7333 pb
    #     ZJetsToNuNu_Zpt-200toInf_TuneCUETP8M1         4.201  pb
    #
    # We use 4.201. The evidence, in order:
    #
    # 1. MEASURED EVENT WEIGHTS. Reading the Runs tree of the Open Data sample
    #    (record 74910) gives, over its 7 files:
    #        Events = 453,967 ; genEventCount = 453,967 ; genEventSumw = 23,817
    #        => mean genWeight = 0.0525,  and 1/0.0525 = 19.0
    #    An unfiltered LO madgraphMLM sample has mean genWeight exactly 1.0
    #    (verified on WJets-HT400to600: 652,621 events, sumw 652,621, <w> = 1.0000).
    #    The BPS filter's acceptance is therefore already folded into the
    #    per-event weights, so sumGenWeights represents the FILTERED yield and
    #    must be paired with the UNFILTERED cross section.
    #
    # 2. AGREEMENT WITH THE PUBLISHED CUT-FLOW. note Table 12 gives
    #    Z(nunu) = 8716.14 events at 35.9 fb^-1 after the AH baseline. Scaled to
    #    our 4.907 fb^-1 that is 1191 events.
    #        with 0.7333 pb  ->   262 events  = 0.22x  (4.5x too low)
    #        with 4.201  pb  ->  1501 events  = 1.26x
    #
    # KNOWN RESIDUAL: 4.201 overshoots by 26%. Three unmodelled effects each
    # push that way and are not corrected here:
    #   * tune differs (CUETP8M1 vs the sample's CP5);
    #   * the paper uses HT-binned Z+jets, Open Data only pT(Z)-binned, so the
    #     phase-space coverage is not identical;
    #   * the NLO/LO k-factors the note applies to V+jets as a function of boson
    #     pT (note section 2.3.1) are not applied here at all.
    # Treat the Z->nunu normalisation as good to tens of percent, not better.
    "Zvv-Zpt200":      4.201,
    "Zvv-Zpt100to200": 35.99,   # same reasoning; the BPSFilter entry is 5.002 pb

    # Source: XSDB, queried 2026-09-03 with  process_name=DYJetsToLL_M-50_Zpt.*
    #
    #   DYJetsToLL_M-50_Zpt-200toInf_BPSFilter_TuneCP5_13TeV-madgraphMLM-pythia8
    #       cross_section = 0.393 pb  (total_uncertainty 0.001155, LO)
    #       DAS: .../RunIISummer20UL16MiniAOD-106X_mcRun2_asymptotic_v13-v1
    #
    # This row is UL16 -- the exact campaign of the Open Data sample, so no
    # cross-campaign inference is needed here.
    #
    # The upstream notebooks use 1.27 pb: too high by a factor of 3.2. That
    # affects Z/gamma*+jets in BOTH channels, not just all-hadronic.
    #
    # Bonus check on the Z->nunu value above: XSDB lists this same DY process at
    # 0.393 pb for UL16 and 0.3919 pb for UL17 -- a 0.3% difference. That
    # confirms empirically that these cross sections do not depend on the
    # data-taking campaign, which is what justified taking the UL17 number for
    # ZJetsToNuNu_Zpt-200toInf_BPSFilter (no UL16 row exists in XSDB).
    "DYJets-Zpt200":  0.393,
}

# Branching ratios, kept for the DY <-> Z->nunu consistency check:
#   sigma(Z->nunu)/sigma(Z->ll, l=e,mu) = 0.2000 / (2 x 0.033632) = 2.974
# With the XSDB values above this predicts a DY BPSFilter Zpt-200toInf cross
# section of 0.7333 / 2.974 = 0.247 pb -- nowhere near the 1.27 pb in use.
BR_Z_TO_NUNU = 0.2000
BR_Z_TO_EE_OR_MUMU = 2 * 0.033632


# ---------------------------------------------------------------------------
# Registry construction
# ---------------------------------------------------------------------------
def _record_files(recid: int, timeout: int = _TIMEOUT) -> list[str]:
    """Return every ROOT file URI listed in an Open Data record's file indexes."""
    resp = requests.get(f"{_API}/{recid}", timeout=timeout)
    resp.raise_for_status()
    meta = resp.json()["metadata"]
    uris: list[str] = []
    for index in meta.get("_file_indices", []):
        for entry in index.get("files", []):
            uri = entry.get("uri")
            if uri and uri.endswith(".root"):
                uris.append(uri)
    if not uris:
        raise ValueError(f"record {recid} exposes no ROOT files")
    return uris


def build_registry(nanoaod_filenames: dict, verbose: bool = True) -> dict[str, list[str]]:
    """Upstream registry plus the corrected and added samples.

    The upstream ``Zvv`` key is *replaced*: it pointed at an unrelated signal
    sample. Everything else upstream is passed through unchanged.
    """
    out: dict[str, list[str]] = {}
    from dpoa_io import _fetch_index  # reuse the validating fetcher

    if verbose:
        print(f"{'Dataset':<24} {'Files':>6}  Source")
        print("-" * 62)

    for name, urls in nanoaod_filenames.items():
        if name == "Zvv":
            continue  # replaced below by Zvv-Zpt200
        paths: list[str] = []
        for url in urls:
            try:
                paths.extend(_fetch_index(url))
            except Exception as exc:  # noqa: BLE001
                if verbose:
                    print(f"  ! {name}: {exc}")
        out[name] = paths
        if verbose:
            print(f"{name:<24} {len(paths):>6}  upstream")

    for name, recid in EXTRA_RECORDS.items():
        try:
            out[name] = _record_files(recid)
            src = f"record {recid}"
        except Exception as exc:  # noqa: BLE001
            out[name] = []
            src = f"record {recid} FAILED: {exc}"
        if verbose:
            print(f"{name:<24} {len(out[name]):>6}  {src}")

    return out


# ---------------------------------------------------------------------------
# Luminosity of the processed fraction
# ---------------------------------------------------------------------------
def dataset_byte_fraction(dataset: str, files_used: list[str],
                          timeout: int = _TIMEOUT) -> tuple[float, dict]:
    """Fraction of a data primary dataset covered by ``files_used``, by bytes.

    Returns ``(fraction, info)``.

    Why bytes and not file count: the upstream notebook assumed every file
    carries the same luminosity and wrote ``LUM = (20/82) * 8900`` -- where 82
    is moreover the *SingleMuon* file count, applied to the *MET* dataset (which
    has 32 files). File sizes vary by more than a factor of two, so counting
    files is a poor proxy. Bytes track the number of recorded events closely,
    and the per-file sizes are exact metadata from the Open Data record, so
    this costs one HTTP request and no extra event reading.
    """
    recid = DATA_RECORDS.get(dataset)
    if recid is None:
        raise KeyError(f"{dataset!r} is not a known data primary dataset")

    resp = requests.get(f"{_API}/{recid}", timeout=timeout)
    resp.raise_for_status()
    meta = resp.json()["metadata"]

    sizes: dict[str, int] = {}
    for index in meta.get("_file_indices", []):
        for entry in index.get("files", []):
            uri = entry.get("uri")
            if uri:
                sizes[uri] = int(entry.get("size", 0))

    total = sum(sizes.values())
    used = sum(sizes.get(f, 0) for f in files_used)
    missing = [f for f in files_used if f not in sizes]

    info = {
        "record": recid,
        "n_files_used": len(files_used),
        "n_files_total": len(sizes),
        "bytes_used": used,
        "bytes_total": total,
        "events_total": meta.get("distribution", {}).get("number_events"),
        "unmatched_files": missing,
    }
    return (used / total if total else 0.0), info


def luminosity_pb(dataset: str, files_used: list[str], verbose: bool = True) -> float:
    """Integrated luminosity, in pb^-1, of the processed slice of ``dataset``.

    ``L = (bytes processed / bytes in the whole Run2016H dataset) x 8900 pb^-1``

    This is a *per-dataset* quantity. The upstream notebooks used one global
    ``LUM`` for every channel, but the MET, SingleMuon and SingleElectron
    datasets have different file counts, so processing 20 files of each covers
    a different fraction of the same 8.9 fb^-1 in each case.
    """
    frac, info = dataset_byte_fraction(dataset, files_used)
    lumi = frac * RUN2016H_LUMI_PB

    if verbose:
        print(f"Luminosity for {dataset}:")
        print(f"  record {info['record']}, "
              f"{info['n_files_used']}/{info['n_files_total']} files")
        print(f"  {info['bytes_used'] / 1e9:.1f} / {info['bytes_total'] / 1e9:.1f} GB "
              f"= {frac:.4f} of Run2016H")
        print(f"  L = {frac:.4f} x {RUN2016H_LUMI_PB:.0f} pb^-1 = {lumi:.1f} pb^-1")
        if info["unmatched_files"]:
            print(f"  WARNING: {len(info['unmatched_files'])} processed file(s) "
                  f"are not in the record index; luminosity is underestimated.")

    return lumi
