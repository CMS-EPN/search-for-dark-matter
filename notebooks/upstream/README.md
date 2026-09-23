# Upstream notebooks (reference only — do not run)

These are the original notebooks as the collaboration wrote them, kept for
provenance and diffing. They are **not** the ones to run.

| File | Notes |
|---|---|
| `All_Hadronic_20files.ipynb` | Formerly `All_Hadronic2.ipynb`. 20 files/dataset, global `LUM = 35.9`. **Source for the generated `../All_Hadronic.ipynb`.** |
| `All_Hadronic_10files.ipynb` | Formerly `All_Hadronic.ipynb`. 10 files/dataset, global `LUM = (20/82)*8900`. Differs from the above in only 7 of 29 code cells. |

Both carry dead single-lepton code in `raw` cells that never executed, and
stored outputs from an old run.

The single-lepton analysis has no upstream notebook at all — its source is
`../../search-for-dark-matter-docs/docs/Single_Lepton/Analisis_muon_final_version.md`.

To regenerate the runnable notebooks from these sources:

```bash
pixi run build-ah        # -> ../All_Hadronic.ipynb
pixi run build-sl        # -> ../Single_Lepton.ipynb
```
