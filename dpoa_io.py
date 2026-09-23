"""
dpoa_io — computational plumbing for the DPOA / CMS Open Data analysis.

This module contains **no physics**. Every selection cut, cross section and
kinematic definition stays in the notebook, where a physicist can read and
edit it. What lives here is the fragile infrastructure that has nothing to do
with the analysis itself:

  * fetching the CMS Open Data file indexes (with validation and retries)
  * opening ROOT files over XRootD (with retries on transient failures)
  * running a per-file processing function over a dataset, in parallel,
    and reporting failures instead of hiding them
  * reading ``genEventSumw`` using *exactly* the same file slice that was
    processed, so the normalisation cannot silently drift

Design rule: **fail loudly**. The original notebook wrapped every file in a
bare ``except Exception: return None``; the caller then did
``pd.DataFrame(None)``, which yields an empty DataFrame. A file that failed to
download was therefore indistinguishable from a file that legitimately
contained no events, and the resulting normalisation was silently wrong.
Here, failures are counted, reported, and raised if *everything* fails.
"""

from __future__ import annotations

import concurrent.futures as _futures
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import uproot

__all__ = [
    "N_FILES",
    "LUMI_PB",
    "OUTPUT_DIR",
    "LUMI_JSON",
    "build_ntuples",
    "download_lumi_json",
    "open_events",
    "process_dataset",
    "sum_gen_weights",
    "show_table",
    "ProcessReport",
]

# ---------------------------------------------------------------------------
# Configuration — single source of truth
# ---------------------------------------------------------------------------
# N_FILES is used BOTH when processing events AND when summing genEventSumw.
# In the original notebook these were two independent literals (N_FILES=20 in
# one cell, N_FILES_MC=10 in another), so the MC was normalised by the sum of
# weights of a different number of files than were actually processed.
# Keeping one constant makes that class of bug impossible.
#
# Override with the DPOA_N_FILES environment variable for a quick smoke test:
#     DPOA_N_FILES=1 pixi run smoke
N_FILES: int = int(os.environ.get("DPOA_N_FILES", 20))

# Integrated luminosity used to scale MC, in pb^-1.
# NOTE: this is the value inherited from the original analysis. It is a
# *physics* input and is left exactly as the collaboration set it.
LUMI_PB: float = 3400.0

OUTPUT_DIR = Path("output_raw")
NTUPLES_JSON = Path("ntuples.json")
LUMI_JSON = Path("Cert_271036-284044_13TeV_Legacy2016_Collisions16_JSON.txt")

_LUMI_URL = (
    "https://opendata.cern.ch/record/14220/files/"
    "Cert_271036-284044_13TeV_Legacy2016_Collisions16_JSON.txt"
)

# Network behaviour
HTTP_TIMEOUT = 60
# A multi-hour run must survive a brief network outage. 4 retries starting at
# 5 s gave up after ~75 s, which was enough for a mid-morning connectivity drop
# to abort a run that had already been going for an hour. 6 retries starting at
# 10 s keeps trying for ~5 minutes before giving up, and still fails eventually
# rather than hanging forever.
XROOTD_RETRIES = 6
XROOTD_BACKOFF = 10.0  # seconds, doubled each attempt (10+20+40+80+160 = 310 s)
MAX_WORKERS = 4  # be polite to the eospublic redirector


# ---------------------------------------------------------------------------
# 1. File index
# ---------------------------------------------------------------------------
def _fetch_index(url: str) -> list[str]:
    """Fetch one ``file_index.txt`` and return the ROOT paths it lists.

    Validates the response instead of blindly splitting whatever comes back.
    A 404 from opendata.cern.ch returns an HTML error page; the original
    ``download_files`` happily parsed that into a path list starting with
    ``<!DOCTYPE``, which then failed much later with a confusing
    ``FileNotFoundError`` on a nonsensical filename.
    """
    resp = requests.get(url, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()

    text = resp.text
    if "<!DOCTYPE" in text[:200] or "<html" in text[:200].lower():
        raise ValueError(f"index URL returned an HTML page, not a file index: {url}")

    paths = [ln.split()[0] for ln in text.splitlines() if ln.strip()]
    bad = [p for p in paths if not p.startswith(("root://", "/eos/", "http"))]
    if bad:
        raise ValueError(f"index contains {len(bad)} malformed path(s), e.g. {bad[0]!r}")
    return paths


def build_ntuples(nanoaod_filenames: dict, force: bool = False, verbose: bool = True) -> dict:
    """Build (or reuse) ``ntuples.json``: dataset -> list of ROOT file paths.

    Parameters
    ----------
    nanoaod_filenames
        The registry from ``dpoa_workshop``.
    force
        Re-download even if ``ntuples.json`` already exists. The index is
        cached because it is a few hundred HTTP requests that rarely change;
        rerunning the notebook should not repeat them.
    """
    if NTUPLES_JSON.exists() and not force:
        ntuples = json.loads(NTUPLES_JSON.read_text())
        if verbose:
            total = sum(len(v) for v in ntuples.values())
            print(f"Reusing {NTUPLES_JSON} ({len(ntuples)} datasets, {total} files).")
            print("Pass force=True to rebuild it from opendata.cern.ch.")
        return ntuples

    ntuples: dict[str, list[str]] = {}
    failures: list[str] = []

    if verbose:
        print(f"{'Dataset':<28} | {'Files':>6} | Status")
        print("-" * 55)

    for dataset, urls in nanoaod_filenames.items():
        all_paths: list[str] = []
        errs: list[str] = []
        for url in urls:
            try:
                all_paths.extend(_fetch_index(url))
            except Exception as exc:  # noqa: BLE001 - reported, not hidden
                errs.append(f"{url.rsplit('/', 1)[-1]}: {exc}")

        ntuples[dataset] = all_paths
        if errs:
            failures.extend(f"{dataset}: {e}" for e in errs)
        status = "ok" if not errs else f"{len(errs)} index(es) FAILED"
        if verbose:
            print(f"{dataset:<28} | {len(all_paths):>6} | {status}")

    NTUPLES_JSON.write_text(json.dumps(ntuples, indent=2))

    if verbose:
        print("-" * 55)
        print(f"Wrote {NTUPLES_JSON} with {len(ntuples)} datasets.")
        if failures:
            print(f"\n{len(failures)} index file(s) could not be read:")
            for f in failures:
                print(f"  - {f}")

    empty = [d for d, p in ntuples.items() if not p]
    if empty:
        print(f"\nWARNING: these datasets have NO files: {', '.join(empty)}")
        print("They will be skipped downstream; any plot using them will be incomplete.")

    return ntuples


def download_lumi_json(verbose: bool = True) -> Path:
    """Download the 2016 golden-JSON certification file.

    Replaces the notebook's ``!wget`` line, which depends on wget being
    installed, re-downloads on every run, and gives no usable error inside
    Jupyter when it fails.
    """
    if LUMI_JSON.exists() and LUMI_JSON.stat().st_size > 0:
        if verbose:
            print(f"{LUMI_JSON} already present ({LUMI_JSON.stat().st_size:,} bytes).")
        return LUMI_JSON

    resp = requests.get(_LUMI_URL, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    LUMI_JSON.write_bytes(resp.content)
    if verbose:
        print(f"Downloaded {LUMI_JSON} ({len(resp.content):,} bytes).")
    return LUMI_JSON


# ---------------------------------------------------------------------------
# 2. Robust ROOT access
# ---------------------------------------------------------------------------
def open_events(path: str, tree: str = "Events", retries: int = XROOTD_RETRIES):
    """``uproot.open`` with retries and exponential backoff.

    The public eospublic.cern.ch redirector intermittently drops connections;
    a single transient failure should not cost a whole dataset. Raises the
    last exception if every attempt fails.
    """
    delay = XROOTD_BACKOFF
    last: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return uproot.open(f"{path}:{tree}")
        except Exception as exc:  # noqa: BLE001
            last = exc
            if attempt < retries:
                time.sleep(delay)
                delay *= 2
    raise RuntimeError(f"could not open {path} after {retries} attempts") from last


# ---------------------------------------------------------------------------
# 3. Dataset processing
# ---------------------------------------------------------------------------
@dataclass
class ProcessReport:
    """What actually happened while processing a dataset."""

    dataset: str
    n_requested: int = 0
    n_ok: int = 0
    n_events: int = 0
    failures: list[tuple[str, str]] = field(default_factory=list)

    @property
    def n_failed(self) -> int:
        return len(self.failures)

    def summary(self) -> str:
        s = (
            f"{self.dataset}: {self.n_ok}/{self.n_requested} files ok, "
            f"{self.n_events:,} events"
        )
        if self.failures:
            s += f", {self.n_failed} FAILED"
        return s


MANIFEST = OUTPUT_DIR / ".manifest.json"


def _read_manifest() -> dict:
    if MANIFEST.exists():
        try:
            return json.loads(MANIFEST.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def _write_manifest(key: str, n_files: int) -> None:
    data = _read_manifest()
    data[key] = {"n_files": n_files}
    MANIFEST.parent.mkdir(exist_ok=True)
    MANIFEST.write_text(json.dumps(data, indent=1, sort_keys=True))


def process_dataset(
    dataset: str,
    fileset: dict,
    process_file,
    *,
    is_data: bool,
    n_files: int = N_FILES,
    suffix: str = "_raw",
    overwrite: bool = False,
    max_workers: int = MAX_WORKERS,
    verbose: bool = True,
) -> tuple[pd.DataFrame | None, ProcessReport]:
    """Run ``process_file`` over the first ``n_files`` files of ``dataset``.

    ``process_file(path, dataset=..., IS_DATA=...)`` must return a dict of
    equal-length arrays (the notebook's physics function). It should *not*
    swallow its own exceptions — this function handles and reports them.

    Files are processed in parallel threads (uproot releases the GIL while
    waiting on network I/O, so this is a large speedup over the original
    serial loop). Results are written to ``output_raw/<dataset><suffix>.parquet``
    and reused on subsequent runs unless ``overwrite=True``.
    """
    report = ProcessReport(dataset=dataset)
    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / f"{dataset}{suffix}.parquet"

    cache_key = f"{dataset}{suffix}"
    cached_n = _read_manifest().get(cache_key, {}).get("n_files")

    if out_path.exists() and not overwrite:
        # Only reuse the cache when it was built from the SAME number of files.
        # Otherwise a quick DPOA_N_FILES=1 smoke test would silently poison a
        # subsequent full run: the parquet would be reused and the MC scaled by
        # a sumGenWeights computed over 20 files it never saw.
        if cached_n == n_files:
            df = pd.read_parquet(out_path)
            report.n_events = len(df)
            report.n_ok = report.n_requested = -1
            if verbose:
                print(f"  {dataset}: reusing {out_path.name} ({len(df):,} events, "
                      f"{n_files} files). Pass overwrite=True to reprocess.")
            return df, report
        if verbose:
            was = "unknown" if cached_n is None else str(cached_n)
            print(f"  {dataset}: cache was built from {was} file(s), "
                  f"now asking for {n_files} - reprocessing.")

    if dataset not in fileset:
        if verbose:
            print(f"  {dataset}: not in fileset, skipping.")
        return None, report

    files = fileset[dataset]["files"][:n_files]
    report.n_requested = len(files)
    if not files:
        if verbose:
            print(f"  {dataset}: no files listed, skipping.")
        return None, report

    def _one(path: str):
        return process_file(path, dataset=dataset, IS_DATA=is_data)

    frames: list[pd.DataFrame] = []
    with _futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futs = {pool.submit(_one, f): f for f in files}
        for fut in _futures.as_completed(futs):
            path = futs[fut]
            try:
                result = fut.result()
            except Exception as exc:  # noqa: BLE001
                report.failures.append((path, f"{type(exc).__name__}: {exc}"))
                continue

            if result is None:
                report.failures.append((path, "processing function returned None"))
                continue

            frame = pd.DataFrame(result)
            report.n_ok += 1
            if len(frame):
                frames.append(frame)

    if report.failures and verbose:
        print(f"  {dataset}: {report.n_failed} file(s) failed:")
        for path, err in report.failures[:3]:
            print(f"      {path.rsplit('/', 1)[-1]}  ->  {err}")
        if report.n_failed > 3:
            print(f"      ... and {report.n_failed - 3} more")

    if report.n_ok == 0:
        raise RuntimeError(
            f"{dataset}: all {report.n_requested} file(s) failed. "
            f"First error: {report.failures[0][1] if report.failures else 'unknown'}"
        )

    if not frames:
        if verbose:
            print(f"  {report.summary()} (no events survived the selection)")
        return None, report

    full = pd.concat(frames, ignore_index=True)
    report.n_events = len(full)
    full.to_parquet(out_path, index=False)
    _write_manifest(cache_key, n_files)
    if verbose:
        print(f"  {report.summary()} -> {out_path.name}")
    return full, report


# ---------------------------------------------------------------------------
# 4. Normalisation inputs
# ---------------------------------------------------------------------------
def sum_gen_weights(
    fileset: dict,
    data_datasets: set[str],
    *,
    n_files: int = N_FILES,
    max_workers: int = MAX_WORKERS,
    verbose: bool = True,
) -> dict[str, float]:
    """Sum ``Runs/genEventSumw`` over the SAME file slice that was processed.

    ``n_files`` defaults to the module-level ``N_FILES``, the same constant
    used by :func:`process_dataset`. Do not pass a different value here unless
    you also changed it there — the ratio xsec*L/sumW is only meaningful when
    both refer to the same set of files.
    """
    # sumGenWeights reads the Runs tree of every file over the network. Nothing
    # about it changes between runs at a fixed n_files, so cache it: re-running
    # a notebook to regenerate plots otherwise re-reads a few hundred files.
    cache_path = OUTPUT_DIR / f".sumw_{n_files}.json"
    if cache_path.exists():
        cached = json.loads(cache_path.read_text())
        if set(cached) >= {k for k in fileset if k not in data_datasets}:
            if verbose:
                print(f"Reusing {cache_path.name} "
                      f"({len(cached)} datasets, n_files={n_files}).")
                print("Delete that file to recompute.")
            return {k: float(v) for k, v in cached.items()}

    sums: dict[str, float] = {}

    if verbose:
        print(f"{'Dataset':<28} | {'sumGenWeights':<16} | Files")
        print("-" * 58)

    for name, info in fileset.items():
        # Skip real data: either named explicitly by the caller, or flagged
        # is_data by construct_fileset (which covers datasets belonging to a
        # different channel, e.g. 'met' when running the single-lepton notebook).
        if name in data_datasets or info.get("metadata", {}).get("is_data"):
            sums[name] = 1.0
            if verbose:
                print(f"{name:<28} | {'(data)':<16} | -")
            continue

        files = info["files"][:n_files]
        if not files:
            sums[name] = 0.0
            if verbose:
                print(f"{name:<28} | {'NO FILES':<16} | 0")
            continue

        def _one(path: str) -> float:
            with open_events(path, tree="Runs") as runs:
                if "genEventSumw" not in runs:
                    return 0.0
                return float(np.sum(runs["genEventSumw"].array(library="np")))

        total = 0.0
        failed = 0
        with _futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            for fut in _futures.as_completed([pool.submit(_one, f) for f in files]):
                try:
                    total += fut.result()
                except Exception:  # noqa: BLE001
                    failed += 1

        sums[name] = total
        if verbose:
            note = f"{len(files)}" + (f" ({failed} failed)" if failed else "")
            print(f"{name:<28} | {total:<16.4e} | {note}")

    OUTPUT_DIR.mkdir(exist_ok=True)
    cache_path.write_text(json.dumps(sums, indent=1, sort_keys=True))

    zero = [
        k for k, v in sums.items()
        if v == 0.0
        and k not in data_datasets
        and not fileset[k].get("metadata", {}).get("is_data")
    ]
    if zero and verbose:
        print(f"\nWARNING: sumGenWeights is 0 for: {', '.join(zero)}")
        print("Those samples cannot be normalised and will be dropped from the stack.")

    return sums


# ---------------------------------------------------------------------------
# 5. Notebook helpers
# ---------------------------------------------------------------------------
def show_table(filename: str, caption: str = "") -> None:
    """Display a reference figure if present, otherwise say so and carry on.

    The docs notebook calls ``display(Image(filename="Table_10.png"))`` for a
    handful of screenshots of tables from the paper. Those PNGs were never
    committed, so every one of those cells raised ``FileNotFoundError`` and
    stopped a "Run All". They are illustrative only and carry no physics, so a
    missing file is a note, not an error.
    """
    from IPython.display import Image, display

    path = Path(filename)
    if path.exists():
        display(Image(filename=str(path)))
        return
    label = caption or filename
    print(f"[reference figure not included in the repository: {label}]")
    print("  This is a screenshot of a table from the paper; it carries no physics.")
    print("  See the corresponding table in paper.pdf.")
