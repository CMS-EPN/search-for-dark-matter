# Runbook — every change made to the upstream analysis

**Purpose.** This repository takes the DPOA collaboration's original notebooks
and makes them run reproducibly. Every deviation from the upstream code is
recorded here so a physicist can review the physics without reading diffs, and
so anything can be reverted.

**How to read this.** Changes are grouped into two classes, and the distinction
matters:

| Class | Meaning | Who should review |
|---|---|---|
| **COMP** | Computational. Changes *how* the code runs. The selected events and the numbers are identical. | Computing |
| **PHYS** | Physics. Changes *which* events are selected or *how* they are weighted. The numbers change. | **Physics — needs sign-off** |

Every entry states: what changed, why, the source that justifies it, how to
verify it, and how to revert it.

**Upstream reference.** The original notebooks are preserved untouched in
`upstream/`. The single-lepton original is the markdown export in
`../search-for-dark-matter-docs/docs/Single_Lepton/`.

**Source abbreviations.**
- *paper* — `paper.pdf`, CMS-EXO-18-010
- *note* — `analysisis_notes.pdf`, the CMS analysis note (tables cited by number)
- *record N* — CMS Open Data record `https://opendata.cern.ch/record/N`

---

## Status

| Phase | What | State |
|---|---|---|
| A | Reproduce the upstream plots faithfully, verify the pipeline end to end | ✅ **GREEN** — 2026-09-03 |
| B | Apply the PHYS changes and converge on the paper | ✅ **applied** (PHYS-01…14) |
| C | Make our histograms comparable to the paper's at all | ✅ **applied** (PLOT-01…05) |
| D | Single-lepton channel with the same corrections | ✅ **done** — 2026-09-07 |

**Where it stands** — all-hadronic, full 20-file run, 28/28 cells, 0 errors:

| | upstream | now | note Table 12 |
|---|---:|---:|---:|
| data/MC | ~10 | **1.34** | 1.06 |

Background composition after the baseline:

| group | now | Table 12 | ratio |
|---|---:|---:|---:|
| tt̄ | 59.1 % | 45.5 % | 1.3 |
| **Z(νν)** | **24.1 %** | **29.7 %** | **0.81** |
| W+jets | 13.9 % | 15.1 % | 0.9 |
| VV, VH | 1.0 % | 2.7 % | 0.4 |

**Single lepton** — full 20-file run, 35/35 cells, 0 errors, against note Table 11:

| | muon | electron | Table 11 |
|---|---:|---:|---:|
| data/MC | **1.075** | **0.942** | 1.118 |
| tt̄(2ℓ) | 93.3 % | 94.2 % | 61.4 % |
| t+X | 0.5 % | 0.5 % | 14.1 % |

The per-process breakdown of what is left, and which named input would supply
each piece, is in Part 4 (all-hadronic) and Part 6 (single lepton). Everything
still open is a specific missing input, listed in Part 3 as [OPEN-1]…[OPEN-6] —
**that list is what to ask the collaboration for.**
| diboson | 0.6 % | 2.7 % | 0.2 |
| tt̄V | 0.2 % | 0.9 % | 0.2 |

**This is the decisive test flagged in [OPEN-1].** That entry predicted: *"if the
observed fraction lands near 5 %, the BPSFilter pairing is wrong and 4.201 pb is
the value."* It landed at **4.5 %**.

Z(νν) is short by a factor of ~6.6, and 4.201 / 0.7333 = 5.73 — consistent
within the statistics of a single-file test. Every other background being
*proportionally* low while tt̄ is high is the expected signature of one large
component missing from the denominator.

**Full-statistics result (20 files, all 7 Z→νν files): Z is still 4.6 %.**
Identical to the 1-file test, so this is systematic, not statistical. The
`0.7333 pb` pairing is confirmed wrong.

**But 4.201 pb does not close the gap either.** Scaling Z by 5.73 gives ~21.6 %
against the 29.7 % required, and leaves data/MC at ~1.33. Comparing *absolute*
yields, rescaled from note Table 12 to our 4.907 fb⁻¹, shows the problem is not
only Z:

| group | observed | expected | obs/exp |
|---|---:|---:|---:|
| tt̄ | 5030 | 2128 | 2.36 |
| W+jets | 1404 | 705 | 1.99 |
| Z+jets | 319 | 1387 | **0.23** |
| single top | 130 | 239 | 0.54 |
| **data** | **11229** | **4953** | **2.27** |

**The data is 2.3× high too**, which no cross section can explain. There are at
least two independent problems. Do not tune the Z cross section until the data
excess is understood — that would be fitting one error to hide another, which is
exactly what the upstream `LUM = 3400` did.

**Phase A evidence** (run preserved in `runs/`):

| | Single_Lepton | All_Hadronic |
|---|---|---|
| exit code | 0 | 0 |
| cells executed | 35/35 | 28/28 |
| plots | 16 | 7 |
| errors | 0 | 0 |
| ROOT files read | 432/432 | 216/216 |
| network failures | **0** | **0** |

Wall time 1 h 50 min for 648 files.

Reproduction of the upstream output confirmed two independent ways:

1. **Exact event count.** The upstream notebook's stored output reads
   `Saved: output_raw/SingleMuon_raw.parquet with 25932 events`; this run
   reports `SingleMuon: 20/20 files ok, 25,932 events`.
2. **Plots match.** `m_T^W` and `N_b-tags` (muon channel) and `SR 2b` p_T^miss
   (all-hadronic) compared against the committed reference PNGs in
   `search-for-dark-matter-docs/docs/` — identical bin contents, axes and
   scales. Only the legend column order differs, a cosmetic mplhep difference.

**No PHYS change has been applied yet.** Everything in the PHYS section is a
proposal with its justification, awaiting (a) Phase A finishing and (b) physics
sign-off. The COMP changes are all applied and verified.

---

# Part 1 — COMP: computational changes (applied)

These do not change any physics result. Each was verified by running the
notebooks end to end.

### COMP-01 · Pinned, reproducible environment

**Was:** a `pip install uproot awkward numpy matplotlib vector hist mplhep dpoa_workshop`
cell inside the notebook.

**Now:** `pixi.toml` + `pixi.lock`, conda-forge, linux-64, Python 3.11. One
command: `pixi run lab`.

**Why:** the pip environment cannot read `root://` URLs — the XRootD client is
not practically pip-installable. This was the reported "download error". The
lockfile pins every package to an exact build and hash.

**Verify:** `pixi run lab` on a clean clone; the sample-inspection cell opens a
file over XRootD.

**Revert:** delete `pixi.toml`/`pixi.lock`.

---

### COMP-02 · Failures are reported instead of silently swallowed

**Was:**
```python
def process_file_muon(...):
    try:
        ...
    except Exception as e:
        print(f"Error procesando {filename}: {e}")
        return None
```
and the caller did `df = pd.DataFrame(data_dict)`.

**Now:** the processing functions do not catch their own exceptions;
`dpoa_io.process_dataset` catches, counts and reports them per file, and raises
if *every* file in a dataset failed.

**Why — this is the most consequential COMP change.** `pd.DataFrame(None)`
returns an empty DataFrame, not an error. A file that failed to download was
therefore **indistinguishable from a file with no selected events**. The dataset
would be written with fewer events than it should have, while `sumGenWeights`
was still computed over all 20 files — so the affected background was silently
scaled wrong, with no message anywhere.

**Verify:** the processing cells print `N/M files ok` per dataset. `M - N` is
the number that failed, and each is listed with its error.

**Revert:** restore the `try/except` in the notebook cell.

---

### COMP-03 · One `N_FILES` constant instead of two

**Was:** `N_FILES = 20` in the processing cell and `N_FILES_MC = 10` in the
`sumGenWeights` cell (in `All_Hadronic.ipynb`; the two happened to agree in
`All_Hadronic2.ipynb`).

**Now:** both read `dpoa_io.N_FILES`.

**Why:** the MC weight is `σ · L / sumGenWeights`. If the events come from 20
files and the denominator from 10, every MC sample is normalised by a
denominator that does not correspond to the events being normalised — here, a
factor of 2. **This was a live bug in `All_Hadronic.ipynb`.**

**Verify:** the config line printed by the first cell; both cells report the
same file count.

---

### COMP-04 · One luminosity constant instead of three

**Was:** `LUM` set in three separate cells — `(20/82)*8900 = 2170.7`, `35.9`,
and `3400.0` inside `load_data`.

**Now:** a single `dpoa_io.LUMI_PB`.

**Why:** the baseline plots and the signal-region plots were normalised to
**different luminosities** in the same notebook. Note this is a COMP change
only — it makes one value apply consistently. Whether that value is *correct*
is **PHYS-02** below.

**Verify:** grep for `LUM` — one definition.

---

### COMP-05 · Per-channel output files (silent cross-contamination)

**Was:** both channels wrote `output_raw/<dataset>_raw.parquet`.

**Now:** `_raw` (SL muon), `_electron_raw` (SL electron), `_0lep_raw` (AH).

**Why:** the all-hadronic and single-lepton selections keep **different events
from the same datasets** but wrote to the same filename. Running one notebook
after the other made the second reuse the first's events. Every plot in the
second channel would have been built from the wrong selection, with no error.

**Verify:** `ls output_raw/` shows three distinct suffixes.

---

### COMP-06 · Result cache is invalidated when `N_FILES` changes

**Was:** no caching (everything re-downloaded every run).

**Now:** results cached per dataset; `output_raw/.manifest.json` records how
many files each was built from, and a mismatch triggers reprocessing.

**Why:** caching is needed to make a multi-hour run resumable. Without the
manifest, a quick `DPOA_N_FILES=1` smoke test would poison a subsequent full
run: the 1-file parquet would be reused while `sumGenWeights` was computed over
20 files.

**Verify:** run with `DPOA_N_FILES=1`, then with 20 — the log says
`cache was built from 1 file(s), now asking for 20 - reprocessing`.

---

### COMP-07 · Robust file-index fetching

**Was:** `paths = [ln.split()[0] for ln in r.text.splitlines()]` with no status
check.

**Now:** `dpoa_io._fetch_index` checks the HTTP status, rejects HTML responses,
and validates that every path looks like a ROOT URI.

**Why:** a stale index URL returns a 404 **HTML page**, which the original code
parsed into a path list beginning `<!DOCTYPE`. The failure surfaced much later
as a confusing `FileNotFoundError` on a nonsense filename. Reproduced during
this work.

---

### COMP-08 · XRootD retries

**Now:** `dpoa_io.open_events` retries 4× with exponential backoff.

**Why:** the public `eospublic.cern.ch` redirector intermittently drops
connections. One transient failure previously cost a whole dataset (via
COMP-02's silent path).

---

### COMP-09 · Parallel file processing

**Was:** a serial `for f in files:` loop.

**Now:** `ThreadPoolExecutor`, 4 workers.

**Why:** the workload is almost entirely network I/O and uproot releases the
GIL while waiting. Bounded at 4 to stay polite to the redirector.

**Note:** results are order-independent (each file is processed separately and
the frames concatenated), so this does not change any output.

---

### COMP-10 · `!wget` replaced with Python

**Why:** `wget` is not present on every platform, it re-downloaded the golden
JSON on every run, and its failures are invisible inside Jupyter.

---

### COMP-11 · Missing reference figures no longer abort a "Run All"

**Was:** five `display(Image(filename="Table_10.png"))` cells.

**Now:** `dpoa_io.show_table(...)`, which prints a note if the file is absent.

**Why:** those PNGs were never committed, so every one raised
`FileNotFoundError` and stopped the notebook. They are screenshots of tables
from the paper and carry no physics.

---

### COMP-12 · Notebooks are generated, not hand-edited

**Now:** `pixi run build-sl` / `build-ah` regenerate the notebooks from
`upstream/` and the docs markdown. Each patch is a named block in
`build_single_lepton.py` / `build_all_hadronic.py` with a comment saying what
was wrong.

**Why:** it keeps the upstream physics auditable — the build scripts verify that
14 (SL) and 16 (AH) physics code cells are passed through byte-identical.

**Caution:** editing the `.ipynb` directly is lost on the next build.

---

### COMP-13 · Dead cells removed from the all-hadronic notebook

**Removed:** three trailing "troubleshooting" code cells. One referenced an
undefined `file_paths` (`NameError`); the other two reset `N_FILES = 3` and
re-ran the whole processing loop. All three broke a "Run All". They are notes,
now markdown.

Also removed: `raw` cells holding stored outputs from an old run, and dead
single-lepton code the AH notebook carried but never executed.

---

### COMP-14 · Plot functions take their data explicitly

**Was:** `plot_grouped_stack` read a module-level `all_dfs` global that a later
cell reassigned to the electron dictionary.

**Now:** an explicit `dfs=` argument (still defaulting to `all_dfs`).

**Why:** re-running an earlier cell silently plotted a different channel.

### COMP-15 · Network drops abort a run that could simply resume

**What happened, three times.** A run pulls tens of gigabytes from the CERN
XRootD redirector over several hours. `dpoa_io` already retries each file six
times with exponential backoff (~310 s in total, COMP-08), but an outage longer
than that fails every file of a dataset, `process_dataset` raises, and the whole
notebook aborts — discarding hours of work that was, in fact, already saved.

    RuntimeError: WJets-HT800to1200: all 20 file(s) failed.
    First error: could not open root://eospublic.cern.ch//... after 6 attempts

Nothing was wrong with the code: the connection came back a minute later
(226 ms RTT to `eospublic`), and every dataset processed before the drop was
still sitting in `output_raw/` as a valid parquet file.

**The fix is not more retries.** Stretching the per-file backoff far enough to
ride out a multi-minute outage would also make every genuine failure — a
deleted file, a bad path — take that long to surface, which is exactly the
silent-slowness COMP-02 was written against.

Since every processed dataset is cached and the cache is keyed on `N_FILES`
(COMP-06), **re-running the notebook resumes where it stopped**. So the correct
response to an abort is to run it again. `run_analysis.sh` does that: up to
`MAX_ATTEMPTS` (default 8) attempts per notebook, with a `COOLDOWN` (default
120 s) between them to let the link recover, reporting how many datasets are
cached after each failure.

**Retrying blindly is not enough, as the next outage showed.** The first version
simply re-ran the notebook, and when the network went down for good it spent
about fifteen minutes per attempt rediscovering that every file open times out —
three attempts, three quarters of an hour, to learn something a single TCP
connection answers in ten seconds.

It now checks that `eospublic.cern.ch:1094` is reachable *before* spending an
attempt, and otherwise waits, probing once a minute (`PORT_WAIT`, default four
hours). Two consequences: an attempt is only consumed when there is a real
chance of it succeeding, and the run restarts within a minute of the connection
returning instead of up to fifteen.

It also reports *which* kind of failure it is, because the two need different
responses from the person running it:

    --- XRootD (eospublic.cern.ch:1094) is not reachable.
    --- but port 443 to the same host answers: this is a network/firewall
    --- block on port 1094, not an outage at CERN. See README.md.

That distinction was measured, not assumed: port 443 to the same IP connected in
**0.19 s** while port 1094 **timed out after 12 s**. A silent timeout is a
firewall dropping packets; a server refusing would answer fast. IPv6 was
independently broken on the same network — port 443 succeeded over IPv4 and
failed over IPv6 — and `eospublic.cern.ch` publishes both A and AAAA records, so
a client preferring IPv6 fails for a second, unrelated reason.

    ./run_analysis.sh Single_Lepton All_Hadronic
    MAX_ATTEMPTS=12 COOLDOWN=300 ./run_analysis.sh Single_Lepton

This matters beyond our own convenience: the project is meant to be run by
anyone. A four-hour job that has to be babysat, and that throws away its work
on any network hiccup, is not something a physicist elsewhere can realistically
reproduce.

It also keeps the `systemd-inhibit` guard that an earlier run needed after the
laptop suspended mid-dataset.

### Note on runtime — measured, not guessed

A full reprocess of the single-lepton channel takes about four hours. Two
measurements pin down why, and rule out the obvious fixes:

| | |
|---|---|
| Kernel CPU | **18 %** of one core |
| Sustained network | **44 Mbit/s** |
| Adding 6 more download streams alongside the running job | total fell to **14 Mbit/s** |

It is network-bound, and the path to `eospublic` is already saturated — adding
parallelism makes it *slower*, so raising `MAX_WORKERS` would not help. That
was tested rather than assumed.

The one real saving available is structural: the muon and electron processors
each download the same 20 MC samples independently, so **half the bytes
transferred are a duplicate**. A single pass writing both channels' outputs
would roughly halve the wall time. Not done here — it is a refactor of the
processing plumbing, and it was not worth the risk of introducing a bug into a
pipeline that is currently converging. Recorded as a COMP item for later.

---

# Part 2 — PHYS: physics changes (applied)

Each still needs physics review — "applied" means the code does it, not that a
physicist has signed it off. Ordered by expected impact. PHYS-10 … PHYS-14 came
later and are written up in Part 4, where each carries its measured effect.

**The benchmark.** Note Table 12 is a cut-flow with absolute yields at
35.9 fb⁻¹. After the AH baseline it gives, as a fraction of total background:
tt̄(1ℓ) 41.7 %, **Z(νν) 29.5 %**, W+jets 15.1 %, single top 5.1 %, tt̄(2ℓ) 3.8 %,
VV 2.7 %, QCD 1.1 %, tt̄V 0.9 %, Z(ℓℓ) 0.2 % — and **data/MC = 1.06**.

When this list was written data/MC was ≈ 7–10. It is now 1.22. The fractions
above are how each fix was checked.

---

### PHYS-01 · `Zvv` points at an unrelated signal sample

**Impact: largest.** Z(νν) is **29.5 %** of the all-hadronic background.

**Is:** `dpoa_workshop.py` maps `Zvv` to
`ggH_HToSSTo4l_lowctau_MH-500_MS-150_ctauS-100` — a long-lived-particle
**signal** sample (932 events in its first file) — while assigning it the Z→νν
cross section 77.3 pb.

That 77.3 is recognisable as note Table 6's `ZJetsToNuNu HT-200To400` = 77.67 pb,
so the intent was clearly Z→νν; the file index simply points elsewhere.

**Symptom:** the spiky, near-empty blue `Z/γ*+Jets` band in the AH plots — a
handful of events carrying enormous weights.

**Proposed:** use **record 74910**,
`ZJetsToNuNu_Zpt-200toInf_BPSFilter_TuneCP5` UL16 NanoAODv9 (7 files, 453 967
events). Record 74908 is the Zpt-100to200 bin and contributes nothing above
p_T^miss > 250 GeV.

**Open question — the cross section.** Not published in the record metadata,
and note Table 6 is HT-binned where Open Data is p_T(Z)-binned, so the two are
not interchangeable. See **[OPEN-1]** below. Interim value in
`dpoa_datasets.py` is derived from the DY sample by branching ratio (× 2.974)
and labelled as derived.

**Verify:** Z(νν) should come out at 29.5 % of the AH background after the
baseline selection.

---

### PHYS-02 · Luminosity is a fudged constant, wrong in both directions

**Is:** `LUM = 3400.0 pb⁻¹` for every channel — chosen to make the plots agree,
not derived. The original comment reads `(20/82)*8900`, but 82 is the
*SingleMuon* file count, applied to the *MET* channel, which has 32 files.

**Why it is wrong in principle:** luminosity is a property of *which* data
dataset you processed and *how much* of it. One constant cannot be right for
two channels.

**Proposed:** Open Data exposes only Run2016H = 8.9 fb⁻¹ (note Table 2).
Measure the processed fraction by **bytes** of the record — exact metadata, and
a much better proxy than file count since file sizes vary by more than 2×:

| Dataset | Files | Fraction | L [pb⁻¹] | vs 3400 |
|---|---:|---:|---:|---|
| `met` (AH) | 20/32 | 0.5514 | **4907** | MC was 31 % too low |
| `SingleMuon` | 20/82 | 0.2663 | **2370** | MC was 43 % too high |
| `SingleElectron` | 20/80 | 0.3254 | **2896** | MC was 17 % too high |

**Assumption to review:** bytes ∝ recorded luminosity, i.e. all files in a
primary dataset have similar event content. A physicist may prefer summing
`Runs`-tree entries, or the golden-JSON lumi sections actually present.

**Implemented in:** `dpoa_datasets.luminosity_pb()`.

---

### PHYS-03 · Baseline selection is missing cuts — note Table 10

| Baseline | Note Table 10 | Code | Effect of the omission |
|---|---|---|---|
| n_b | **≥ 1** | not applied | keeps b-free events the paper excludes |
| p_T^miss (AH) | **≥ 250 GeV** | 240 | |
| p_T^miss (SL) | **≥ 160 GeV** | 150 | |
| min∆φ(j₁,₂) (AH) | **> 0.4** | not applied | QCD and instrumental p_T^miss not suppressed |

**Why this matters more than it looks:** `n_b ≥ 1` and `min∆φ > 0.4` are exactly
the cuts that remove QCD multijet and fake p_T^miss. Both inflate **data** far
more than MC, so omitting them is a large part of the data/MC ≈ 7–10.

**Note:** the p_T^miss changes are *tightenings* of what is already stored, so
they need no reprocessing. `n_b ≥ 1` likewise. `min∆φ` does — see PHYS-04.

---

### PHYS-04 · min∆φ uses four jets instead of two (all-hadronic)

**Is:** `process_file_0lep` minimises ∆φ over the **top four** central jets:
```python
jets_top4 = f_central[:, :4]
```

**Paper:** min∆φ(**j₁,₂**, p_T^miss) — the **two** leading jets (paper Table 1,
note Table 13). The single-lepton function already uses the top two.

**Why it matters:** a minimum over more jets is always ≤ the minimum over
fewer, so the same numerical cut is systematically **tighter** than the paper's.

**Requires reprocessing** of the all-hadronic channel.

---

### PHYS-05 · Signal-region cuts computed but never applied — note Table 13

| Cut | AH | SL | Status |
|---|---|---|---|
| min∆φ(j₁,₂) | ≥ 1.0 | ≥ 1.2 | AH ok; SL uses **0.5** |
| m_T^b | ≥ 180 GeV | ≥ 180 GeV | **computed, never applied** |
| p_T(j₁)/H_T | ≤ 0.5, n_b ≥ 2 only | — | **never computed** |
| m_T | — | ≥ 160 GeV | not applied |
| m_T2^W | — | ≥ 200 GeV | **not implemented** |

`p_T(j₁)/H_T` needs the leading-jet p_T, which is not currently stored →
reprocessing.

**m_T2^W is a known gap.** It requires a kinematic minimisation over jet-lepton
assignments (note ref. [41]) and is not implemented. The single-lepton signal
regions therefore cannot apply Table 13 in full. Flagged for physics decision.

---

### PHYS-06 · Missing background samples

| Sample | Share of AH background | Record |
|---|---:|---|
| W+jets HT-600→2500+ | part of the 15.1 % | 69731, 69735, 69723, 69727 |
| `TTTo2L2Nu` | 3.8 % | 67801 |

**Deliberately NOT added — `TTToHadronic` (record 67841).** It is absent from
note Table 6, and note Table 12 has **no fully-hadronic tt̄ row**: the AH
background is tt̄(1ℓ) and tt̄(2ℓ). Without genuine p_T^miss, fully-hadronic tt̄
behaves like QCD multijet — 1.1 % of the background, and removed by
min∆φ > 0.4. Adding it would depart from the published analysis.

*(An earlier draft of this work wrongly called `TTToHadronic` a major missing
background. Note Table 12 shows otherwise; recorded here so the error is not
repeated.)*

**QCD multijet also not added:** 1.1 % of the background, and Open Data ships
`QCD_Pt_*` rather than the `QCD_HT_*` binning the note used.

---

### PHYS-07 · Triggers, MET filters and golden JSON never applied

Note §2.1 requires, on data and simulation: `HBHENoiseFilter`,
`HBHENoiseIsoFilter`, `ECALDeadCellFilter`, `GlobalTightHalo2016Filter`,
`BadPFMuonFilter`, `BadChargedHadronFilter`; and on data only `EEBadScFilter`,
`BadMuons`, `DuplicateMuons`. Plus the golden-JSON good-lumi list.

**None are applied.** `build_lumi_mask` is imported and never called.

**Why the MET filters matter here specifically:** they exist to remove
*instrumental* p_T^miss. Every event they should have removed lands in the data
histogram at high p_T^miss — precisely the region these plots show. This is a
strong candidate for a large part of the remaining data excess.

---

### PHYS-08 · b-tagging working point is the 2017 value

**Is:** `Jet_btagDeepFlavB > 0.2770` — the DeepJet **medium** working point for
**2017**.

**Should be:** the data is UL2016 and Run2016H is *postVFP*, whose DeepJet
medium working point is **0.2489**.

**Also:** the paper uses **CSVv2 medium**, which NanoAOD exposes as
`Jet_btagCSVV2`, not DeepJet. Changing discriminator changes efficiency and
mistag rate, so this needs a physics decision rather than a mechanical edit.

---

### PHYS-09 · The all-hadronic "control region" is not in the paper

**Is:** `filter_cr_wlnu` selects 0 leptons, n_b = 0, n_jet ≥ 3, and is labelled
`AH0lWR`.

**Note Table 14** defines the AH control regions as `AH1eTR`, `AH1mTR`,
`AH1eWR`, `AH1mWR`, `AH2eZR`, `AH2mZR` — **all requiring one or two leptons**.
`AH0lWR` does not exist, and no 0-lepton control region does.

**Consequence:** these regions cannot be built from the MET dataset at all. They
need SingleElectron and SingleMuon, i.e. a cross-channel restructuring.

---

# Part 3 — Open questions for the collaboration

### [OPEN-1] Cross section for `ZJetsToNuNu_Zpt-200toInf_BPSFilter` (UL16)

**Status: CLOSED.** Both values obtained from XSDB on 2026-09-03 via a CMS account.

Needed for PHYS-01, the single largest correction.

**Answer (XSDB, queried 2026-09-03 via a CMS account, `process_name=ZJetsToNuNu_Zpt.*`):**

| process_name | σ [pb] | unc. | accuracy | campaign |
|---|---:|---:|---|---|
| `ZJetsToNuNu_Zpt-200toInf_BPSFilter_TuneCP5` | **0.7333** | 0.006806 | LO | UL17 |
| `ZJetsToNuNu_Zpt-100to200_BPSFilter_TuneCP5` | **5.002** | 0.04655 | LO | UL17 |
| `ZJetsToNuNu_Zpt-200toInf_TuneCUETP8M1` | 4.201 | 0.004064 | LO | Summer16 |
| `ZJetsToNuNu_Zpt-100to200_TuneCUETP8M1` | 35.99 | 0.03419 | LO | Summer16 |

The Open Data UL16 sample (record 74910) is
`ZJetsToNuNu_Zpt-200toInf_BPSFilter_TuneCP5_13TeV-madgraphMLM-pythia8` — an
exact `process_name` match to the first row, filter and tune included. **Use
0.7333 pb.**

Two traps worth recording:

- **Do not use 4.201 pb.** It is the same p_T(Z) bin but a different tune
  (CUETP8M1) and *no BPS filter*. Pairing it with this sample's
  `sumGenWeights` would overestimate Z→νν by ~5.7×.
- XSDB lists the BPSFilter rows under **UL17**, not UL16. A cross section does
  not depend on the data-taking year — same √s, generator, tune and gridpack —
  so it carries over. This is an inference, small but not zero, and is flagged
  in `dpoa_datasets.py`.

**Remaining tension — resolve empirically.** 453 967 events at 0.7333 pb is an
equivalent luminosity of **619 fb⁻¹**, i.e. 17× the full 2016 dataset. That is
unusually generous for a background sample, which is mild evidence against the
BPSFilter pairing. The decisive test is note Table 12: Z(νν) must come out at
**29.5 %** of the AH background. If the observed fraction lands near 5 %, the
pairing is wrong and 4.201 pb is the value.

**DY cross section — also answered.** `process_name=DYJetsToLL_M-50_Zpt.*` gives:

| process_name | σ [pb] | campaign |
|---|---:|---|
| `DYJetsToLL_M-50_Zpt-200toInf_BPSFilter_TuneCP5` | **0.393** | **UL16** |
| `DYJetsToLL_M-50_Zpt-200toInf_BPSFilter_TuneCP5` | 0.3919 | UL17 |
| `DYJetsToLL_M-50_Zpt-150toInf_TuneCUETP8M1` | 18.36 | Summer16 |

The first row is UL16 — the exact campaign of the Open Data sample, so no
cross-campaign inference is needed. **Use 0.393 pb.** The upstream notebooks use
**1.27 pb**, too high by a factor of 3.2, affecting Z/γ*+jets in *both* channels.

This also settles the inference flagged above for Z→νν: the same DY process is
listed at 0.393 (UL16) and 0.3919 (UL17), a 0.3 % difference. Cross sections
here do not depend on the campaign, so taking the UL17 number for
`ZJetsToNuNu_Zpt-200toInf_BPSFilter` (which has no UL16 row) is justified.

The 619 fb⁻¹ equivalent-luminosity oddity noted above still stands as the one
open check, and is settled empirically by the Table 12 comparison.

### [OPEN-2] Should the analysis follow the paper, or stay faithful to upstream?

Applying the PHYS changes makes the plots closer to the paper but no longer a
faithful reproduction of the DPOA notebooks. Recommendation: keep both — the
upstream behaviour is preserved in `upstream/` and regenerable, so PHYS changes
can be applied to the main notebooks without losing it.

### [OPEN-3] m_T2^W (PHYS-05) — the largest cut in the SL selection

Not implemented; it needs a kinematic minimisation over jet-lepton assignments.

**Measured cost, from note Table 11:** it removes 84 % of the SL background on
its own (17 489 → 2 713, ×0.16) — more than every other signal-region cut
combined — and it is selective: ×9.3 on tt̄(2ℓ), which is 61 % of this channel's
background, against ×1.7 on W+jets. See Part 6.

Without it our SL signal regions are several times too full, overwhelmingly with
tt̄(2ℓ). Is an approximation acceptable, or should the region be reported as
explicitly incomplete?

### [OPEN-4] V+jets NLO/LO k-factors — the biggest thing we cannot derive

The note (section *Corrections for MC samples*) says the W+jets and Z+jets
samples are corrected with electroweak and QCD NLO/LO k-factors computed with
MG5_aMC@NLO v2.2.2 as a function of generated boson p_T. The table itself is
not in the note.

**Why this one matters most.** After PHYS-13 fixed the Z(nu nu) cross section,
the two processes still short against Table 12 are exactly the two these
k-factors act on: Z(nu nu) at 21.9 % against 29.7 %, W+jets at 12.6 % against
15.1 %. They are LO samples being corrected toward NLO, so the factors are
above 1 for most of the p_T range — the right direction and the right
processes.

**What we need:** the numerical k-factor tables (or the ROOT file they are
stored in) as a function of generated boson p_T, for both the QCD and the
electroweak part, for W+jets and Z+jets.

Guessing at values would move the plots toward the paper for the wrong reason,
so nothing is applied. This is left as a documented gap rather than a fudge.

---

### [OPEN-5] VH is missing from the diboson group

The paper's stack labels that group "VV, VH". Ours contains WW, WZ and ZZ and
nothing else, so VH is absent. Table 12 puts the group at 2.7 % of the
background; we have 0.9 %.

**What we could not establish.** A name search of the Open Data portal for VH
samples (`ZH_HToBB`, `WplusH`, `WminusH`, `VHToNonbb`, `GluGluHToBB`, …) in
RunIISummer20UL16 NanoAODv9 returned nothing. **That is not evidence of
absence**: the same search returns zero hits for `TTToSemiLeptonic`, a sample
this analysis demonstrably reads every run. The portal's free-text search does
not reliably index MC dataset names, so the question of whether UL16 VH samples
are published cannot be settled this way.

The one UL16 Higgs-related record the search did surface is
`HTo2LongLivedTo2mu2jets_MH-125_...` (records 41334 / 41335) — which is, as it
happens, precisely the long-lived-particle signal sample that upstream had
mistakenly wired in as Z→νν (PHYS-01). It is not VH and is not relevant here.

**What we need from the collaboration:** the record IDs of the UL16 VH samples,
if they are published; or confirmation that they are not, in which case this
component stays documented as unreproducible from Open Data.

---

# Part 4 — Convergence log (all-hadronic)

Each row is one change, its justification, and the measured effect. The
benchmark throughout is note Table 12 (AH cut-flow at 35.9 fb⁻¹), rescaled to
our 4.907 fb⁻¹.

| # | Change | data/MC | Z(νν) share |
|---|---|---:|---:|
| — | upstream | ~10 | ~0 % (wrong sample) |
| 1 | PHYS-01..08 applied (see Part 2) | 1.615 | 4.6 % |
| 2 | + CSVv2 b-tagging, + WZ, + Z(νν) low-pT bin | 1.485 | 4.6 % |
| 3 | + corrected Z(νν) cross section | **1.217** | **21.9 %** |
| — | **note Table 12** | **1.06** | **29.7 %** |

### PHYS-10 · b-tagging switched to CSVv2 medium — and my reasoning for it was wrong

**Change:** `Jet_btagCSVV2 > 0.8484` instead of `Jet_btagDeepFlavB > 0.2489`.
Both counts are now stored in the parquet (`nBTag_csv`, `nBTag_deepjet`) so the
choice can be revisited without reprocessing.

**Justification:** note Table 10 specifies "CSVM". This is what the paper uses.

**The prediction I made was wrong, and it is worth recording.** I argued that
because Z(νν)+jets and W+jets contain almost no real b quarks, they enter the
n_b ≥ 1 region only through mistagged light jets, and that CSVv2's higher
mistag rate would therefore raise them sharply while leaving tt̄ untouched.

Measured on the same events:

| Sample | DeepJet | CSVv2 | ratio |
|---|---:|---:|---:|
| tt̄ semileptonic | 55 938 | 48 172 | 0.86 |
| tt̄ dileptonic | 20 830 | 17 796 | 0.85 |
| Z(νν) | 35 379 | 28 827 | **0.81** |

Every process goes *down*, and Z(νν) goes down slightly *more* than tt̄ — the
opposite of the prediction. The two taggers differ by only ~5 % on light jets
here, not the factor of 3 I assumed. The change is kept because it is what the
paper does, but it does **not** explain the Z(νν) deficit.

### PHYS-11 · WZ was missing from the diboson stack

**Change:** added `WZ_TuneCP5` inclusive, Open Data record **72754**, σ = 47.13 pb.

**Justification:** note Table 6 lists three diboson processes — WW, WZ, ZZ. The
upstream registry had WW and ZZ only. The five WZ decay modes in the note sum
to 30.26 pb, comparable to WW and ZZ combined, which is why the dark blue
"VV, VH" band in the paper's Figure 5 is much larger than ours was.

**Effect:** diboson share 0.9 % → 1.1 % (note Table 12: 2.7 %).

### PHYS-12 · Z(νν) low-pT bin added

**Change:** added `ZJetsToNuNu_Zpt-100to200_BPSFilter`, record **74908**.

**Justification:** reconstructed p_T^miss is not identical to generator-level
p_T(Z) — jet mismeasurement and extra-jet recoil migrate events upward — so the
100–200 GeV bin is not empty above the 250 GeV cut.

### PHYS-13 · Z(νν) cross section: use the unfiltered value

**Change:** `Zvv-Zpt200` 0.7333 pb → **4.201 pb** (and the 100–200 bin
5.002 → 35.99 pb). Both are XSDB values; the change is *which* XSDB row to pair
with the Open Data sample.

**This is the single largest correction in the whole exercise**, and the
reasoning is worth stating in full because the two candidate numbers differ by
5.7× and both are official.

XSDB returns two entries per p_T(Z) bin:

| process_name | σ [pb] |
|---|---:|
| `ZJetsToNuNu_Zpt-200toInf_BPSFilter_TuneCP5` | 0.7333 |
| `ZJetsToNuNu_Zpt-200toInf_TuneCUETP8M1` | 4.201 |

The Open Data sample (record 74910) is the **BPSFilter** one, so the obvious
choice — and the one used in change #2 above — is 0.7333. It gives Z(νν) at
4.6 % against the 29.7 % the paper requires.

**Direct measurement settles it.** Reading the `Runs` tree of record 74910:

| Sample | Events | genEventSumw | mean genWeight |
|---|---:|---:|---:|
| `ZJetsToNuNu_Zpt-200toInf_BPSFilter` | 453 967 | 23 817 | **0.0525** |
| `WJetsToLNu_HT-400To600` (unfiltered) | 652 621 | 652 621 | **1.0000** |

An unfiltered LO madgraphMLM sample carries mean genWeight exactly 1. This one
carries 0.0525, and 1/0.0525 = 19.0. **The filter's acceptance is already folded
into the per-event weights.** Since the MC weight is
`σ · L · genWeight / Σ genWeight`, and Σ genWeight already carries the filter,
the σ to pair with it is the *unfiltered* one.

Cross-check against note Table 12, which gives Z(νν) = 8716.14 events at
35.9 fb⁻¹, i.e. 1191 at our 4.907 fb⁻¹:

| σ used | Z(νν) events | vs. expected |
|---|---:|---:|
| 0.7333 pb | 262 | 0.22× |
| **4.201 pb** | **1501** | **1.26×** |

**Known residual: 4.201 overshoots by 26 %.** Three uncorrected effects all push
that way, and none is a bug:
- the tune differs (CUETP8M1 vs the sample's CP5);
- the paper uses HT-binned Z+jets, Open Data only p_T(Z)-binned, so phase-space
  coverage is not identical;
- the NLO/LO k-factors the note applies to V+jets as a function of boson p_T
  (note §2.3.1) are **not applied here at all**.

Treat the Z→νν normalisation as good to tens of percent, not better.

### PHYS-14 · Top p_T reweighting — the one MC correction the note fully specifies

**The problem it addresses.** tt̄ sits at 62.8 % of the all-hadronic background
against the note's 45.5 % (Table 12). Part 4 closed with "no MC corrections are
applied at all" as the leading suspect. Of the corrections the note lists —
b-tagging, pileup, lepton ID, trigger, V+jets NLO k-factors, top p_T — exactly
**one** is written down completely enough to reproduce from the note alone.

**What the note says** (section *Corrections for MC samples*):

> The generated top p_T spectrum in tt̄ MC appears to be harder than
> observation. […] For each top in a simulated tt̄ event, a scale factor is
> computed by ρ(p_T) = exp(0.0615 − 0.0005·p_T), where p_T is taken at matrix
> element level. The event weight is given by the geometric mean […]

    rho(pT) = exp(0.0615 - 0.0005 * pT)
    w       = sqrt(rho(pT_top1) * rho(pT_top2))

**Implementation.** The two generated tops are the last copies of the top quark
in `GenPart` (`|pdgId| == 6`, statusFlags bit 13). Events without exactly two
such tops get weight 1, which covers every non-tt̄ sample.

The `GenPart_*` branches are only read for datasets whose name starts with
`ttbar`; reading them for all 22 samples would add bandwidth for a weight that
is identically 1.

**Measured, on `TTToSemiLeptonic` (1 233 000 events):**

| quantity | value |
|---|---:|
| ⟨w⟩ over all events | **1.0005** |
| ⟨w⟩ for p_T^miss > 250 GeV | **0.890** |
| range of w | 0.440 – 1.063 |
| events with exactly two generated tops | 100 % |
| ⟨w⟩ on `WW` (control: no tops) | 1.0000 |

So it is **normalisation-preserving but not shape-preserving** — which is the
whole point. It leaves the inclusive tt̄ cross section alone and removes ~11 %
of tt̄ *specifically in the signal region*, because the signal region selects
the boosted tail the correction suppresses.

**Choice of top definition, checked rather than assumed.** Using the
hard-process copies (statusFlags bit 7) instead of the last copies (bit 13)
gives the same weight to four decimal places, and both give exactly two tops in
100 % of events. The choice does not matter here.

**Expected effect.** ~11 % less tt̄ in the signal regions, so tt̄ moves from
62.8 % toward roughly 59 %, with every other process's share rising to match.
Real, in the right direction, and **not sufficient on its own** — closing
62.8 % → 45.5 % needs about a factor 0.6 on tt̄ relative to the rest. The
remainder has to come from the corrections below.

**One implementation bug, and the change it prompted.** The first version
computed the weight as a plain numpy array and then filtered it by hand. The
processors mask events in two stages — an event mask (lepton veto, p_T^miss),
then a jet-multiplicity mask — and the first version applied only the second.
The run died with

    IndexError: boolean index did not match indexed array along axis 0;
    size of axis is 1233000 but size of corresponding boolean axis is 5150

i.e. the weight was still at full file length while everything else had already
been filtered. The fix was not just to add the missing line: `top_w` is now an
`ak.Array`, so it is masked with exactly the same syntax as `genWeight` on
exactly the same lines. A parallel array carried through a selection by
different syntax is a bug waiting to happen; carried by identical syntax, it is
obvious when a mask is missing.

Worth noting the failure mode was loud. `process_dataset` reports per-file
failures and raises when every file fails, so this surfaced as an immediate
hard error rather than as silently wrong weights — which is the behaviour
COMP-02 was added for.

**Backward compatibility.** The weight is stored per event as a `topPtWeight`
column. Parquet files written before this change do not have the column, and
its absence is read as "no correction" rather than as an error, so only the two
tt̄ samples need reprocessing.

### PHYS-14, measured

Full 20-file all-hadronic run, 28/28 cells, 0 errors.

| group | before | after | factor | % before | % after | Table 12 |
|---|---:|---:|---:|---:|---:|---:|
| tt̄ | 4333.5 | 3698.8 | **0.854** | 62.8 % | **59.1 %** | 45.5 % |
| Z(νν) | 1508.4 | 1508.4 | 1.000 | 21.9 % | **24.1 %** | 29.7 % |
| W+jets | 870.0 | 870.0 | 1.000 | 12.6 % | **13.9 %** | 15.1 % |
| t+X | 116.8 | 116.8 | 1.000 | 1.7 % | 1.9 % | — |
| VV, VH | 64.1 | 64.1 | 1.000 | 0.9 % | 1.0 % | 2.7 % |
| **total MC** | **6895.9** | **6261.2** | | | | |
| **data/MC** | **1.217** | **1.340** | | | | **1.06** |

**The prediction held.** The gap analysis said tt̄ had to be multiplied by 0.83
to reach Table 12. The note's formula, applied to the generated top spectrum,
delivers **0.854** — within 3 % of the required factor, and derived entirely
from the note without any tuning against the target.

**Every composition row moved toward Table 12**, and none moved away.

**And data/MC got worse: 1.217 → 1.340.** This is not a regression and it is not
a surprise. The correction only *removes* tt̄ events; the corrections that would
*add* events back — the V+jets k-factors of [OPEN-4] and the missing VH of
[OPEN-5] — are precisely the ones we cannot apply. The gap analysis said the
total had to grow by 1.15× while tt̄'s share fell; we have applied the half that
shrinks and not the half that grows, so the total fell.

The right way to read this pair of numbers: **composition is the diagnostic
that responds to what we fixed, and normalisation is the one still waiting on
what we are missing.** Reporting only data/MC would have made a correct change
look like a mistake.

### What closure would look like

Applying, on top of the measured result, the factors the gap analysis implies
for the two missing inputs — Z(νν) ×1.56, W+jets ×1.37, VV/VH ×3.33:

| | projected | paper |
|---|---:|---:|
| data/MC | **1.108** | 1.06 |
| tt̄ | **48.8 %** | 45.5 % |
| Z(νν) | **31.1 %** | 29.7 % |
| W+jets | **15.7 %** | 15.1 % |

**This is arithmetic, not a result, and it must not be quoted as one.** The
factors were derived from Table 12 in the first place, so landing near Table 12
is circular by construction. It demonstrates one thing only, and that thing is
still worth having: the residual disagreement is *consistent* with exactly two
named missing inputs, and needs no third unknown effect to explain it. The
magnitudes required (1.2–1.6 for V+jets) also sit inside the range published
NLO/LO k-factors actually take, which is a weak but real independent check.

The honest current state remains **data/MC = 1.34 with tt̄ at 59.1 %**. Nothing
above changes that number.

### The other MC corrections, and why they are not applied

| Correction | Status | Why |
|---|---|---|
| Top p_T reweighting | **applied** | formula given in full in the note |
| V+jets NLO/LO k-factors | **not applied** | the note says they are computed with MG5_aMC@NLO as a function of generated boson p_T, but does not tabulate them; they live in CMS-internal files |
| b-tagging scale factors | not applied | per-jet, per-flavour tables from the BTV POG (method 1a) |
| Lepton ID / iso / tracking SFs | not applied | EGAMMA / MUON POG tag-and-probe tables |
| Trigger scale factors | not applied | measured per p_T, η |
| Pileup reweighting | not applied | needs the data pileup profile |

The V+jets k-factors are the ones that would matter most here: they act on
W+jets and Z(νν), the two processes that are still short against Table 12, and
they raise LO samples toward NLO. Applying them without the actual table would
be guessing, which is worse than the documented gap. **This is the single
biggest thing the collaboration could supply that we cannot derive**, and it is
recorded as [OPEN-4].

### What the ratio panel rules out

Adding the Data/Bkg panel (paper Figure 5 has one; the upstream plots did not)
showed the ratio is **flat** across p_T^miss, not sloped. That kills the
hypothesis carried through most of this work — that the residual disagreement
came from Open Data being the UL2016 reconstruction while the paper used the
2016 legacy reprocessing, with a different MET calibration. A calibration
difference distorts the *shape*; a flat ratio means the shape is right and only
the normalisation is off.

### Hypotheses tested and rejected, with numbers

| Hypothesis | Measured effect | Verdict |
|---|---:|---|
| Missing MET triggers | 0.64 % of events at p_T^miss > 250 | rejected |
| Missing MET noise filters | 0.05–1.8 % | rejected |
| b-tagger mistag rate | −19 %, wrong direction | rejected |
| UL vs legacy MET calibration | ratio is flat | rejected |
| Z(νν) cross section pairing | **4.55×** | **confirmed** |

### Where the remaining gap actually is, per process

Rather than describing the residual as one number (data/MC = 1.22 against 1.06),
it is worth asking what each process would have to be multiplied by to land on
note Table 12. The answer turns out to name a specific missing correction in
every row.

Target total = data / 1.06 = 8392 / 1.06 = **7917** events, against our 6896:
everything together has to grow by 1.15×, while tt̄'s *share* falls.

| Process | now | needed | factor | what would supply it |
|---|---:|---:|---:|---|
| tt̄ | 4333.5 | 3602.2 | **0.83** | top p_T reweighting, measured at **0.89** — covers most of it |
| Z(νν) | 1508.4 | 2351.3 | **1.56** | V+jets NLO/LO k-factor |
| W+jets | 870.0 | 1195.5 | **1.37** | V+jets NLO/LO k-factor |
| VV, VH | 64.1 | 213.8 | **3.33** | **VH is absent from our stack entirely** |

Three things follow, and none of them is "the analysis is wrong somewhere we
have not looked":

1. **tt̄** needs 0.83 and PHYS-14 delivers 0.89. That single correction, which
   the note writes out in full, accounts for roughly two thirds of the tt̄
   excess on its own.

2. **Z(νν) and W+jets** need 1.56 and 1.37. QCD NLO/LO k-factors for V+jets at
   high boson p_T are typically in the 1.2–1.5 range — the right magnitude, on
   exactly the two processes the note says they are applied to. This is
   [OPEN-4], and it is now quantified rather than merely suspected.

3. **The diboson group needs 3.33**, too large for a k-factor. Our group
   holds only WW, WZ and ZZ, while the paper's is labelled "**VV, VH**", so the
   VH contribution — a Higgs produced with a vector boson and decaying to b
   quarks, a genuine b-tagged high-p_T^miss background — is not in our stack at
   all. Recorded as [OPEN-5].

   Worth keeping in proportion, though: this row is the *smallest* absolute
   term. It is 150 events out of 7917, against +843 for Z(νν), +326 for W+jets
   and −731 for tt̄. It should be fixed, but it is not what is driving the
   1.22.

The useful conclusion is that the remaining disagreement is no longer
mysterious. It decomposes into one correction we have applied, one we cannot
derive from the note, and one missing sample.

### What is still open

- **data/MC = 1.217** against the paper's 1.06.
- **tt̄ at 62.8 %** against 45.5 % — the largest remaining discrepancy.
- **No MC corrections are applied at all**: b-tagging, pileup, lepton and
  trigger scale factors, and the V+jets NLO k-factors. The paper applies all of
  them, and they act mostly on the V+jets and tt̄ normalisations — exactly where
  the residual sits.
- **No global fit.** The paper's backgrounds are normalised by a simultaneous
  fit across all control regions; ours are pure simulation at fixed cross
  section. Its figures are labelled "post-fit" for that reason, so an exact
  match was never reachable without implementing the fit.

---

---

# Part 5 — PLOT: the histograms themselves were not comparable

Parts 2–4 are about the *physics*. This part is about something narrower and,
for anyone eyeballing the comparison, more misleading: even where the numbers
were right, our plots and the paper's could not be laid side by side, because
they were not the same histogram. Four separate mismatches, all of them
visible, none of them physics.

These were found by cropping the six panels of Figure 4 (single lepton, page
16) and the three of Figure 5 (all hadronic, page 17) out of `paper.pdf` at
300 dpi and reading the axes and stack off the pixels, rather than trusting the
figure captions.

The plot function now lives in one file, `region_plot_cell.py`, which both
build scripts embed into their notebook. It used to be duplicated as a
one-line string literal in each builder, so a fix to one silently left the
other behind.

### PLOT-01 · Stacking order was by yield; the paper's is fixed

**What we did.** `plot_region_stack` sorted the processes by yield, smallest
on top.

**What the paper does.** Figures 4 and 5 stack in a fixed order, bottom first:

    VV/VH → t+X → tt̄ → W(ℓν) → Z(νν) → Z(ℓℓ)

**Why it matters more than it sounds.** In the all-hadronic channel the two
orders happen to agree, so this went unnoticed. In the single-lepton channel
they do not: tt̄ is by far the largest process there (~75 % of the SR), so
yield-sorting drops it to the *bottom* of the stack, while the paper keeps it
third from the bottom, above VV/VH and t+X. The identical set of numbers
produces a picture with a completely different silhouette. This is a large
part of why the single-lepton comparison "looked nothing alike" even where
the yields were close.

**Fix.** `PAPER_STACK_ORDER`, applied to whichever groups are present.

### PLOT-02 · Binning did not match, so no bin edge lined up

|  | ours (before) | paper |
|---|---|---|
| All hadronic | 250–600 GeV, 10 bins of 30 GeV | **250–550 GeV, 15 bins of 20 GeV** |
| Single lepton | 160–600 GeV, 10 bins of 44 GeV | **160–520 GeV, 9 bins of 40 GeV** |

Not one bin edge was shared with the paper in either channel. Two histograms
binned differently cannot be compared bin by bin at all — only their integrals
mean anything — so every visual comparison up to this point was reading
differences that were partly just rebinning.

Bin edges were measured from the marker positions in the cropped panels
(all hadronic: markers at 260, 280, …, 540; single lepton: 180, 220, …, 500).

### PLOT-03 · The last bin is an overflow bin

Both captions say so explicitly: *"The last bin contains overflow events."*
We were dropping everything above the axis maximum instead.

The visible consequence: in the paper the rightmost bin **rises** above its
neighbour (all the high-p_T^miss tail piles into it); in ours it **fell away**.
That single bin was the most conspicuous shape difference in the whole
comparison, and it was not physics at all.

**Fix.** Values are clipped to just below the top edge before filling, for both
data and MC, so the last bin accumulates the tail exactly as the paper's does.

### PLOT-04 · Axis ranges left the panels differently scaled

The y-axis ceiling was computed per plot as `max(counts) × 300`, so each panel
chose its own decades and no two of our own plots shared a vertical scale.

**Copying the paper's absolute axis range would have been the wrong fix.** Open
Data gives us 2.4–4.9 fb⁻¹ against the paper's 35.9, so our stacks sit roughly
an order of magnitude lower. Pinning the paper's limits would push our
histogram into the bottom of a mostly empty frame and make the comparison look
*worse* than it is, for a reason that has nothing to do with the analysis.

What is copied instead is the paper's **proportions**: the limits are fixed
multiples of the stack peak — 3.5 decades below it, 2 above it for the legend —
read off Figures 4 and 5. Every panel in a channel now has the same dynamic
range as every other, and the same as the paper's, without pretending we have
its luminosity.

### PLOT-05 · The legend disagreed with the stack it described

The legend was built from whatever order matplotlib handed back, reversed. That
turned out to be *bottom-up* — VV/VH first, Z(ℓℓ) last — while the paper's runs
top-down from the top of the stack: Data, Z(ℓℓ), Z(νν), W(ℓν), tt̄, t+X, VV/VH.

So a reader matching legend entries to coloured bands top-to-bottom was reading
our stack in the opposite order to the paper's, on plots whose whole purpose is
side-by-side comparison.

The legend is now built explicitly from the same `order` list that draws the
stack, reversed once. It cannot drift from the stack again, because both come
from the same variable rather than from a library's return-value ordering.

### Also in this pass

The region labels now read as the paper's do (`0l, SR, 0 FJ`, `1mu, 2 b tag,
SR`, …) instead of our own shorthand (`SR 1b 0f`), so a panel can be matched
to its counterpart without a lookup table. The CMS luminosity label is passed
in explicitly per channel rather than being derived inside the plot function
from whichever luminosity happened to be largest.

### What this does *not* change

Nothing here moves a single event. These are presentation fixes: the yields,
the composition percentages and the data/MC ratios reported in Part 4 are all
unchanged. They matter because until they were fixed, we were comparing
against the paper by eye through four layers of distortion, and every judgement
of "these look different" was partly measuring our own plotting.

# Part 6 — The single-lepton benchmark, and what we already know will not match

The all-hadronic convergence had note **Table 12** as its yardstick. The
single-lepton channel has **Table 11**, and reading it before looking at our
plots settles two things in advance.

### What Table 11 says, after the full SL selection

| process | events | share |
|---|---:|---:|
| **tt̄(2ℓ)** | 772.81 | **61.4 %** |
| W+jets | 185.79 | 14.8 % |
| t+X | 177.17 | 14.1 % |
| tt̄+V | 52.73 | 4.2 % |
| VV, VH | 44.00 | 3.5 % |
| **tt̄(1ℓ)** | 20.77 | **1.7 %** |
| Z(ℓℓ) | 2.88 | 0.2 % |
| Z(νν) | 1.52 | 0.1 % |
| **total** | **1257.68** | |
| **data** | **1406** | **data/MC = 1.118** |

**The dominant background is dileptonic tt̄, not semileptonic — by 37 to 1.**
That inverts the naive expectation for a one-lepton final state, and it is a
direct consequence of the M_T > 160 GeV requirement: in genuine one-lepton tt̄
the transverse mass has a Jacobian edge at the W mass, so the cut removes it
almost entirely. What survives is tt̄ where *two* leptons were produced and one
was lost, carrying real missing energy from the second neutrino.

Two consequences for us. First, Z(νν) — the process that dominated the
all-hadronic channel and cost the most work to get right — is **0.1 %** here and
essentially irrelevant. Second, our plots group both tt̄ samples into one
`ttbar` entry, which hides the structure that matters most in this channel.

### [OPEN-3] is not a detail — it is the largest cut in the selection

The signal regions require **M_T2^W > 200 GeV**, which we do not implement: it
needs a kinematic minimisation over jet-lepton assignments. Table 11 puts a
number on what that omission costs:

| cut | total background | factor |
|---|---:|---:|
| after M_T | 17 489.14 | |
| after **M_T2^W** | 2 713.20 | **×0.16** |
| after min∆φ | 1 659.28 | ×0.61 |
| after M_T^b | 1 257.68 | ×0.76 |

**M_T2^W alone removes 84 % of the background — 6.4×, more than every other
signal-region cut combined.** And it is selective in exactly the worst way for
us:

| process | ×, from M_T2^W |
|---|---:|
| tt̄(2ℓ) | **9.3** |
| W+jets | 1.7 |

So the one cut we cannot apply is the one that suppresses the process that
dominates this channel, by a factor of nine, while barely touching the others.

**What this means for the plots.** Our single-lepton signal regions will hold
several times more background than the paper's, overwhelmingly tt̄. That is
*expected, quantified, and documented* — not a new discrepancy to investigate,
and not something the corrections of Parts 2–5 can fix. Any comparison of SL
yields against Figure 4 has to be read with this in mind; the *shape* of the
p_T^miss distribution remains meaningful, the normalisation does not.

This is now the single most valuable thing the collaboration could help with for
the SL channel, alongside [OPEN-4]: either an implementation of M_T2^W, or
agreement that the SL regions are reported as explicitly incomplete.

### The single-lepton result, and the sample it points at

Full run, 35/35 cells, 14 plots, 0 errors. Composition after the complete signal
selection (M_T2^W excepted), against note Table 11:

| process | muon | electron | Table 11 |
|---|---:|---:|---:|
| tt̄(2ℓ) | 93.3 % | 94.2 % | 61.4 % |
| W+jets | 3.9 % | 3.3 % | 14.8 % |
| tt̄(1ℓ) | **1.6 %** | 1.3 % | **1.7 %** |
| VV, VH | 0.6 % | 0.7 % | 3.5 % |
| **t+X** | **0.5 %** | **0.5 %** | **14.1 %** |
| Z(νν) | **0.1 %** | 0.1 % | **0.1 %** |
| Z(ℓℓ) | 0.0 % | 0.0 % | 0.2 % |
| **data/MC** | **1.075** | **0.942** | **1.118** |

Two rows land essentially exactly: tt̄(1ℓ) at 1.6 % against 1.7 %, and Z(νν) at
0.1 % against 0.1 %. Both are numbers that only come out right if the selection,
the cross sections and the normalisation are all correct, so the machinery is
working. data/MC is also close — closer than the all-hadronic channel's.

**The outlier is t+X: 0.5 % against 14.1 %, a factor of 28.**

### PHYS-15 · Three single-top samples and three tt̄V samples are missing

Note **Table 6** lists five single-top samples. The registry has two:

| sample | σ (pb) | present |
|---|---:|---|
| ST t-channel top | 136.02 | ✅ |
| ST t-channel antitop | 80.95 | ✅ |
| **ST tW top** | **35.85** | ❌ |
| **ST tW antitop** | **35.85** | ❌ |
| ST s-channel | 3.36 | ❌ |
| TTWJetsToLNu | 0.2043 | ✅ (as `ttW`) |
| TTWJetsToQQ | 0.4062 | ❌ |
| TTZToQQ | 0.5297 | ❌ |
| TTZToLLNuNu | 0.2529 | ❌ |

**tW is the one that matters, and this region is the reason.** The signal
selection requires a lepton, p_T^miss > 160 and M_T > 160 GeV. In t-channel
single top there is one W, so M_T has its Jacobian edge at the W mass and the
M_T cut removes it — the same mechanism that reduces tt̄(1ℓ) to 1.7 %. tW
produces a top *and* a second W: two neutrinos, real missing energy, and a
b jet. It survives exactly where t-channel does not.

So the paper's t+X in this region is largely tW, and we have none of it. That
accounts for the factor 28 without needing any other explanation, and it is
consistent with the all-hadronic channel, where t+X is 1.9 % against Table 12's
5.1 % — also low, but only by a factor 2.7, because with no lepton requirement
t-channel still contributes.

**Availability could not be established.** A portal search for `ST tW top`,
`ST tW antitop`, `TTZToLLNuNu` and `TTWJetsToQQ` in UL16 NanoAODv9 returned
nothing — but the same search returns nothing for `TTToSemiLeptonic`, which this
analysis reads on every run, so the free-text index cannot be trusted for MC
dataset names. Recorded as [OPEN-6]: **we need the record IDs**, exactly as for
Zvv, WZ and the low-p_T Z bin, all of which were fixed the moment the record was
known.

### What the single-lepton channel now needs, in order

1. **[OPEN-6] the tW record IDs** — one factor-28 row, mechanically understood.
2. **[OPEN-3] M_T2^W** — removes 84 % of the background and 9.3× of tt̄(2ℓ),
   which is why tt̄(2ℓ) sits at 93 % instead of 61 %.
3. **[OPEN-4] the V+jets k-factors** — W+jets at 3.9 % against 14.8 %; the same
   missing correction as the all-hadronic channel, in the same direction.

None of these is a defect in the code. Each is a specific, named input that is
either not published in the note or not yet located in Open Data.

## Change index

| ID | Class | Title | Applied |
|---|---|---|---|
| COMP-01 | COMP | Pinned reproducible environment | ✅ |
| COMP-02 | COMP | Failures reported, not swallowed | ✅ |
| COMP-03 | COMP | One `N_FILES` constant | ✅ |
| COMP-04 | COMP | One luminosity constant | ✅ |
| COMP-05 | COMP | Per-channel output files | ✅ |
| COMP-06 | COMP | Cache invalidated on `N_FILES` change | ✅ |
| COMP-07 | COMP | Robust file-index fetching | ✅ |
| COMP-08 | COMP | XRootD retries | ✅ |
| COMP-09 | COMP | Parallel file processing | ✅ |
| COMP-10 | COMP | `!wget` replaced with Python | ✅ |
| COMP-11 | COMP | Missing figures do not abort | ✅ |
| COMP-12 | COMP | Notebooks generated from build scripts | ✅ |
| COMP-13 | COMP | Dead cells removed | ✅ |
| COMP-14 | COMP | Plot functions take data explicitly | ✅ |
| COMP-15 | COMP | Runs resume after a network drop | ✅ |
| PHYS-01 | PHYS | `Zvv` → real Z→νν sample |✅ |
| PHYS-02 | PHYS | Per-dataset luminosity |✅ |
| PHYS-03 | PHYS | Missing baseline cuts (Table 10) |✅ |
| PHYS-04 | PHYS | min∆φ over 2 jets, not 4 |✅ |
| PHYS-05 | PHYS | Unapplied signal-region cuts (Table 13) |✅ |
| PHYS-06 | PHYS | Missing background samples |✅ |
| PHYS-07 | PHYS | Triggers, MET filters, golden JSON |✅ |
| PHYS-08 | PHYS | b-tagging working point |✅ |
| PHYS-09 | PHYS | AH control region not in the paper |✅ |
| PHYS-14 | PHYS | Top p_T reweighting (note formula) | ✅ |
| PLOT-01 | PLOT | Paper stacking order, not yield order | ✅ |
| PLOT-02 | PLOT | Paper binning (AH 250–550/20, SL 160–520/40) | ✅ |
| PLOT-03 | PLOT | Last bin holds the overflow | ✅ |
| PLOT-04 | PLOT | Fixed axis ranges per channel | ✅ |
| PLOT-05 | PLOT | Legend order matches the stack and the paper | ✅ |
| PHYS-15 | PHYS | tW / s-channel / ttV samples missing (identified) | ⬜ needs record IDs |
