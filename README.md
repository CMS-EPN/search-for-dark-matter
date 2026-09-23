# Search for dark matter produced in association with top quarks — CMS Open Data

A reproducible re-implementation of the CMS analysis
[*Search for dark matter produced in association with a single top quark or a top quark pair in proton–proton collisions at √s = 13 TeV*](paper.pdf)
using [CMS Open Data](https://opendata.cern.ch/) from 2016.

Part of the **CERN DPOA** collaboration effort to make the analysis runnable by anyone.

---

## Quick start

You need **one** tool: [pixi](https://pixi.sh). It installs the entire scientific
stack — including the XRootD client needed to stream CMS Open Data — into a
folder inside this repository. It touches nothing else on your system.

```bash
# 1. install pixi (once, any Linux machine)
curl -fsSL https://pixi.sh/install.sh | bash

# 2. clone and enter
git clone git@github.com:CMS-EPN/search-for-dark-matter.git
cd search-for-dark-matter

# 3. start JupyterLab — dependencies install automatically on first run
pixi run lab
```

Open <http://localhost:8888/lab> and run **`Single_Lepton.ipynb`** or
**`All_Hadronic.ipynb`** top to bottom. That is the whole setup: no `pip
install`, no conda environment to activate, no system package to add.

If this is your first time running it, read the step-by-step guide below —
it explains what each stage does, how long it takes, and what to do when
something fails. If you have run it before, this is all you need.

> Tested on Linux x86-64. The lockfile pins that platform; other platforms
> (macOS included) are untested and may need `pixi.toml` adjusted.

---

## Step-by-step guide

No prior setup is assumed beyond a Linux machine and a network connection.
If anything fails, jump to [Troubleshooting](#troubleshooting).

### Step 0 — Install pixi (once per machine)

```bash
curl -fsSL https://pixi.sh/install.sh | bash
```

Open a new terminal (or run `source ~/.bashrc`) so `pixi` is on your `PATH`,
then check it:

```bash
pixi --version
```

You do **not** need conda, a virtualenv, or `pip install` anything — and in
particular, do not try to install the dependencies with pip. The XRootD
client required to read `root://` URLs is not practically pip-installable,
and its absence is the single most common reason this analysis fails to
download data.

### Step 1 — Get the code

```bash
git clone git@github.com:CMS-EPN/search-for-dark-matter.git
cd search-for-dark-matter
```

### Step 2 — Start JupyterLab

```bash
pixi run lab
```

The **first** run downloads and installs the environment (~1.2 GB, a few
minutes). Every later run starts immediately. When it is ready you will see:

```
Jupyter Server 2.x is running at:
http://localhost:8888/lab
```

Open that URL. Everything — the environment, the package cache, Jupyter's own
config — is written inside the repository folder, so nothing lands on your
home partition.

### Step 3 — Pick a notebook

| Notebook | Channel | Paper section |
|---|---|---|
| `Single_Lepton.ipynb` | 1 lepton (muon **and** electron) | 4.1, 4.3.1 |
| `All_Hadronic.ipynb` | 0 leptons | 4.2, 4.3.2 |

They are independent — run either first. Both write their results to
`output_raw/`, under different filenames, so they do not interfere.

> The notebooks in `upstream/` are the original versions, kept for reference.
> Do not run those.

### Step 4 — Check it works before the long run

The full analysis streams 20 ROOT files per dataset and takes hours. Verify
the whole notebook executes first, using a single file per dataset:

```bash
pixi run smoke-sl     # single-lepton, ~15 min
pixi run smoke-ah     # all-hadronic, ~15 min
```

Each runs the notebook headlessly end to end and fails loudly if any cell
raises. A clean run ends with `[NbConvertApp] Writing ... bytes`. The plots
produced this way are statistically meaningless — one file is far too little
data — but they prove the machinery works.

The smoke run leaves one-file results in `output_raw/`. That is safe: the
cache records how many files each result came from, so the real run in Step
5 detects them as stale and reprocesses rather than silently reusing them.

### Step 5 — Run the analysis

In JupyterLab, open the notebook and use **Run ▸ Run All Cells**. What
happens, in order:

**5a. Setup (seconds).** Imports load the scientific stack and `dpoa_io`,
`dpoa_workshop` loads the dataset registry (which CMS Open Data records to
read), `build_ntuples` fetches the ROOT-file list per dataset into
`ntuples.json`, and the 2016 golden JSON (certified luminosity) downloads.
Expect roughly `met`: 32 files, `SingleMuon`: 82, `ttbar-semileptonic`: 138.
If a dataset shows **0 files**, its index URL is stale — the run continues
but that background will be missing, and the cell says so.

**5b–5c. Cross sections and a first real test (seconds).** Builds `fileset`
(dataset ↔ cross section ↔ data/MC flag) and opens one file over XRootD to
print its event count. If that works, downloads work.

**5d. Event processing — the long part.** For each dataset, the notebook
streams the first `N_FILES` ROOT files, applies the selection, and writes
surviving events to `output_raw/`:

```
=== MUON CHANNEL - MC (20 files per dataset) ===
  ttbar-semileptonic: 20/20 files ok, 214,560 events -> ttbar-semileptonic_raw.parquet
  ttW: 12/12 files ok, 5,040 events -> ttW_raw.parquet
```

Read the `N/M files ok` column — failed files are listed with the reason. A
dataset where every file fails stops the notebook on purpose: a silently
empty background is worse than an error.

| Notebook | Datasets | Approximate wall time |
|---|---|---|
| `Single_Lepton.ipynb` | 12 MC + 2 data, **two** channels | 3–5 hours |
| `All_Hadronic.ipynb` | 11 MC + 1 data, one channel | 1.5–3 hours |

This is measured on a good connection and varies a lot with network speed —
the step is almost entirely I/O against CERN. **You can stop and resume**:
results are cached per dataset, so re-running skips whatever already
completed.

**5e. Normalisation (~10–20 min).** `sum_gen_weights` reads
`Runs/genEventSumw` from the same files to compute the MC weight
`w = xsec × L / sumGenWeights`, then prints a scale-factor table. Nothing
should be flagged `<-- HIGH`, and no row should say `ERROR (SumW=0)`.

**5f. The plots.** Fast — reads the cached parquet files. `Single_Lepton.ipynb`
produces `mT_W`, `met`, `nJet`, `nBTag` for the muon and electron channels,
then `met` per signal region (`SR_1b_0f`, `SR_1b_1f`, `SR_2b`) and control
region. `All_Hadronic.ipynb` produces the same baseline distributions and
signal regions for the 0-lepton channel. Every plot is a stacked MC
histogram with data overlaid as black points, in CMS style.

### Where the output goes

```
output_raw/
├── .manifest.json                       # how many files each result used
├── ttbar-semileptonic_raw.parquet       # single-lepton, muon
├── ttbar-semileptonic_electron_raw.parquet
└── ttbar-semileptonic_0lep_raw.parquet  # all-hadronic
```

Plots render inline in the notebook. To save one to disk, replace
`plt.show()` with `plt.savefig("name.pdf")` in the plotting cell, or
right-click the image in JupyterLab.

### Changing the configuration

Both knobs live at the top of `dpoa_io.py`:

```python
N_FILES: int = 20        # files per dataset
LUMI_PB: float = 3400.0  # integrated luminosity, pb^-1
```

`N_FILES` drives both event processing and the `sumGenWeights` sum — they
must agree, which is why it is one constant. For a quicker, noisier run:

```bash
DPOA_N_FILES=5 pixi run lab
```

### A caveat about the all-hadronic plots

The all-hadronic figures **will not match the paper**, and that is not a bug
in the code — it is a set of known problems in the analysis inputs, listed
under [Known issues in the physics](#known-issues-in-the-physics). In short:
`Zvv` points at the wrong sample, `TTToHadronic` is disabled, QCD multijet is
absent, and several signal-region cuts from Table 1 are not applied. Fixing
those is a physics decision for the collaboration, so the notebooks
reproduce the original behaviour faithfully rather than quietly diverging
from it. The single-lepton plots are much closer to the paper because that
channel depends far less on the broken samples.

---

## What is in here

| File | What it is |
|---|---|
| `Single_Lepton.ipynb` | **The single-lepton analysis** (muon + electron): baseline plots, signal regions, control regions. Generated by `build_single_lepton.py`. |
| `All_Hadronic.ipynb` | **The all-hadronic (0-lepton) analysis.** Generated by `build_all_hadronic.py`. |
| `RUNBOOK.md` | **Every change made to the upstream analysis**, split into computational (COMP) and physics (PHYS), each with its justification and source. Read this to review or revert a specific change. |
| `dpoa_datasets.py` | Physics inputs: dataset records, cross sections with provenance, per-dataset luminosity. |
| `dpoa_workshop.py` | Upstream dataset registry: maps dataset names to CMS Open Data file indexes. |
| `dpoa_io.py` | Computational helpers — downloads, XRootD retries, parallel processing, normalisation bookkeeping. **Contains no physics.** |
| `build_single_lepton.py` | Regenerates `Single_Lepton.ipynb` from the docs markdown. |
| `build_all_hadronic.py` | Regenerates `All_Hadronic.ipynb` from `upstream/All_Hadronic_20files.ipynb`. |
| `region_plot_cell.py` | The signal-region plot, shared verbatim by both builders and embedded into both notebooks. Kept in one file so a fix cannot land in one channel and miss the other. |
| `make_report.py` | Internal tool used to build `comparacion.pdf` (paper / before / corrected). Not part of reproducing the analysis — it needs paper-figure screenshots and a sibling docs checkout that are not included here. |
| `run_analysis.sh` | Runs the notebooks end to end, **resuming automatically after a network drop**. Use this rather than calling `nbconvert` by hand. |
| `upstream/` | The original notebooks, kept for provenance. **Not meant to be run.** |
| `paper.pdf` | The published CMS paper. |
| `comparacion.pdf` | Visual comparison: paper vs. before vs. corrected, for every channel and region. |

> Both notebooks are **generated**. Lasting edits belong in the corresponding
> `build_*.py`, not in the `.ipynb` — `pixi run build` overwrites them.

Not included: `analysisis_notes.pdf`, the CMS analysis note this work also
draws on. It is collaboration-internal, not public like the paper — ask a
DPOA mentor for a copy if you need it; it is not required to run the
notebooks.

### Where the physics lives

Every selection cut, cross section, b-tagging working point and kinematic
definition is **in the notebook**, in plain sight, exactly as the
collaboration wrote it. `dpoa_io.py` deliberately contains none of it — it
only handles networking and bookkeeping. If you want to change the analysis,
you edit the notebook, never the helper module.

---

## How it runs

1. **Build the file index.** `dpoa_io.build_ntuples()` fetches the
   `file_index.txt` list for every dataset from opendata.cern.ch and caches
   it in `ntuples.json`. Delete that file (or pass `force=True`) to refresh.
2. **Process events.** Each NanoAOD file is streamed over XRootD from
   `root://eospublic.cern.ch/`. Nothing is stored locally except the results.
3. **Cache results.** Selected events are written to `output_raw/`, with a
   suffix per channel: `_raw` (single-lepton muon), `_electron_raw`
   (single-lepton electron), `_0lep_raw` (all-hadronic). Re-running reuses
   the cache instead of re-downloading — pass `overwrite=True` to force
   reprocessing.
4. **Normalise and plot.** MC is scaled by `xsec × L / sumGenWeights`.

The cache records how many files each parquet was built from, in
`output_raw/.manifest.json`. If you smoke-test with `DPOA_N_FILES=1` and
then run for real with 20, the stale one-file results are detected and
reprocessed rather than silently reused.

---

## Requirements

- Linux x86-64 (the lockfile pins this platform)
- ~2 GB disk for the environment, plus space for `output_raw/`
- A network connection that can reach `opendata.cern.ch` and
  `eospublic.cern.ch` on the XRootD port (1094)

Everything — the environment, the package cache, Jupyter's config — is
written inside this repository, so nothing lands on your home partition.

---

## Reproducibility

`pixi.lock` pins every package to an exact version, build and hash. Two
people running `pixi run lab` a year apart get byte-identical environments.
Commit the lockfile; never edit it by hand. To upgrade a dependency, change
`pixi.toml` and run `pixi install`, which rewrites the lock.

---

## Known issues in the physics

These are **not** fixed here — they are analysis decisions for the
collaboration, and the notebook reproduces the original behaviour faithfully.
They are recorded so nobody rediscovers them the hard way.

- **`Zvv` points at the wrong dataset.** In `dpoa_workshop.py`, the `Zvv`
  entry resolves to `ggH_HToSSTo4l_lowctau_MH-500_MS-150` — a
  long-lived-particle signal sample — while being assigned the Z→νν cross
  section of 77.3 pb. The real sample is CMS Open Data record **74910**
  (`ZJetsToNuNu_Zpt-200toInf_BPSFilter`, UL16 NanoAODv9), with record 74908
  for the Zpt-100to200 bin. Z→νν is the dominant background at high pᵀᵐⁱˢˢ in
  the all-hadronic channel.
- **Major backgrounds are missing.** `TTToHadronic` (record 67841) and
  `TTTo2L2Nu` (record 67801) are commented out in `dpoa_workshop.py`. QCD
  multijet is absent entirely; Open Data provides `QCD_Pt_*` UL16 samples,
  not the `QCD_HT_*` binning the paper used.
- **The W+jets tail stops at HT-600.** Records 69731, 69735, 69723 and 69727
  cover HT-600 to HT-2500+ and are not registered, though that tail is what
  matters at pᵀᵐⁱˢˢ > 250 GeV.
- **The luminosity is a fitted number.** `LUMI_PB = 3400.0` was chosen to
  make data and MC agree, not derived. The comment in the original notebook
  says `(20/82)*8900`, but 82 is the *SingleMuon* file count; the `met`
  dataset has 32 files in total.
- **All-hadronic selection deviates from the paper.** Table 1 of the paper
  uses the two leading jets for `min∆φ(j1,2, pᵀᵐⁱˢˢ)`, while the notebook
  uses the top four; `mᵦᵀ > 180 GeV` is computed but never applied; and
  `pT(j1)/HT < 0.5` for the nb≥2 category is never computed. Triggers, MET
  filters and the golden-JSON luminosity mask are never applied
  (`build_lumi_mask` is imported but unused).

For everything that **has** been fixed, with justification and source, see
[RUNBOOK.md](RUNBOOK.md).

---

## Troubleshooting

**`pixi: command not found`**
Open a new terminal after installing, or `source ~/.bashrc`.

**`OSError: Failed to open file ... [3011] Unable to open file`**
The cached file paths are stale. Delete `ntuples.json` and re-run the index
cell to fetch current paths.

**Downloads fail with `root://` URLs and you are not using pixi**
A plain `pip install` environment cannot read XRootD URLs — the client is not
practically pip-installable. This is the single most common setup failure.
Use `pixi run lab`.

**`ModuleNotFoundError: No module named 'dpoa_io'`**
The kernel's working directory is not the repository root. Start Jupyter
with `pixi run lab` from inside the repo.

**A dataset reports `all N file(s) failed`**
Check you can reach `eospublic.cern.ch` on port 1094. `dpoa_io` already
retries four times with exponential backoff, so a hard failure usually means
the redirector is unreachable rather than merely busy. CERN occasionally
takes it down for maintenance — try again later.

**Plots are empty or a background is missing**
Look for the `NOT loaded (...)` line printed by the loading cell. It names
every dataset that had no parquet file or no usable scale factor.

**It is taking forever**
Lower `N_FILES`. With `DPOA_N_FILES=5` you get usable shapes in roughly a
quarter of the time, at the cost of statistical precision.

**I edited a notebook and lost my changes**
Both notebooks are *generated*. `pixi run build-sl` and `pixi run build-ah`
overwrite them. Put lasting edits in `build_single_lepton.py` or
`build_all_hadronic.py`, not in the `.ipynb`.

**I changed the signal-region plot and only one channel picked it up**
It no longer works that way: the plot lives in `region_plot_cell.py` and
both builders embed the same file. Edit that, then rebuild both notebooks.

**Downloads fail with "could not open root://... after 6 attempts"**
Two different causes look identical from the notebook. Tell them apart:

```bash
python -c "import XRootD; print('xrootd OK')"
timeout 10 bash -c 'exec 3<>/dev/tcp/eospublic.cern.ch/1094' && echo "port 1094 OK" || echo "port 1094 BLOCKED"
```

- **`ModuleNotFoundError: XRootD`** — the environment is wrong. This is what
  a plain `pip install` gives you: uproot cannot speak `root://` without the
  XRootD bindings, which are not on PyPI for most platforms. Use the pixi
  environment (`pixi run lab`), which pulls xrootd from conda-forge.
- **`port 1094 BLOCKED`** — your *network* is blocking XRootD. Many
  corporate, hotel and some home/ISP networks drop everything outside the
  usual web ports; nothing in this repository can work around it. Connect
  through an academic network or VPN (eduVPN) and try again. A useful
  control: port 443 to the same host should connect in well under a second
  (`timeout 10 bash -c 'exec 3<>/dev/tcp/eospublic.cern.ch/443' && echo "443 OK"`).
  If 443 answers instantly and 1094 times out, it is the network, not this
  code. Also check IPv6 — `eospublic.cern.ch` publishes both A and AAAA
  records, and a network with broken IPv6 fails even when IPv4 is healthy
  (`getent ahosts eospublic.cern.ch`).

You do not need to start over: every dataset already processed is cached in
`output_raw/`, and `./run_analysis.sh` retries automatically and resumes
from the cache — once the connection is back it carries on where it stopped.
