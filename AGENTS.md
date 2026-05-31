# AGENTS.md

## What this codebase does

Compares transverse beam emittance results computed by two systems:

1. **MATLAB emittance tool** — the legacy analysis that produced the `.mat` scan files
   (results are embedded in the files as pre-computed Twiss parameters).
2. **slac-measurements** — the Python replacement under validation.

The notebook iterates over 49 quad-scan datasets from LCLS injector screen
OTRS:IN20:571, runs the Python emittance fit, and prints a side-by-side table
with percent differences against the MATLAB baseline.

### Scientific context

A *quad scan* measures transverse emittance by varying a quadrupole magnet's
strength and recording beam sizes on a downstream screen. Fitting σ² vs k
(focusing strength) yields the beam matrix, from which geometric emittance and
Twiss parameters (α, β, γ) are extracted. Multiplying by relativistic γ gives
the normalized emittance (an invariant under acceleration).

BMAG (beta mismatch) quantifies how far the measured optics deviate from the
design lattice at the observation point. BMAG = 1 means perfect match.

---

## Key packages

| Package | Role | Status | Notes |
|---------|------|--------|-------|
| `slac-measurements` | Emittance calculation backend | **Active** (github.com/slaclab/slac-measurements) | Replaces pyemittance |
| `pyemittance` | Previous emittance backend | **Unmaintained** | Removed from this repo; do not reintroduce |
| `scipy` | .mat file I/O, optimization | Stable | Used by both this code and slac-measurements internals |

---

## Units conventions

| Quantity | Internal unit | Config/file unit | Conversion |
|----------|--------------|------------------|------------|
| Beam size (xrms, yrms) | meters | μm (in .mat files) | ×1e-6 on load |
| Quad setpoint (BDES) | kG | kG | none |
| Beam energy | eV | eV | none |
| Normalized emittance | m·rad (output) | mm·mrad (slac-measurements internal) | ×1e-6 |
| Geometric emittance | mm·mrad (slac-measurements) | — | normalized = geometric × γ |
| BMAG | dimensionless | dimensionless | none |
| Quad length (Lquad) | meters | meters | none |
| R-matrix elements | dimensionless / meters | stored as flat 4-element list [R11, R12, R21, R22] | reshape to 2×2 |
| Design Twiss (β) | meters | meters | none |
| Design Twiss (α) | dimensionless | dimensionless | none |

---

## Data directory structure

```
matlab_scans/
  Emittance-scan-OTRS_IN20_571-YYYY-MM-DD-HHMMSS.mat   (49 files)
    └─ data.beam                — structured array shape (n_steps, 7_methods)
         .beam[step, method]['stats']    — numeric (1, 6): [..., [2]=xrms(μm), [3]=yrms(μm), ...]
         .beam[step, method]['statsStd'] — same layout, uncertainties
    └─ data.quadVal                               — BDES setpoints [kG]
    └─ data.twiss / twissstd                      — MATLAB fitted Twiss (shape 4×2×7 flattened)
         Emittance values are stored in m·rad (×1e6 → mm·mrad)
    └─ data.twiss0                                — initial Twiss used by MATLAB fitter
    └─ data.rMatrix[step]                         — per-step 6×6 R-matrices from physics model

LCLS_OTR2/
  beamline_info.json
    └─ Lquad:  quad effective length [m]
    └─ energy: beam energy [eV]
    └─ Twiss0: [emit_x, emit_y, beta_x, beta_y, alpha_x, alpha_y]
    └─ rMatx:  [R11, R12, R21, R22] quad-to-screen transport (x-plane)
    └─ rMaty:  [R11, R12, R21, R22] quad-to-screen transport (y-plane)

data/
  __init__.py
  loaders.py         — find_scan_files(), load_scan(), load_config(), ScanData

analysis/
  __init__.py
  emittance.py       — compute_emittance() wrapping slac-measurements
  comparison.py      — extract_matlab_results(), format_comparison(), print_comparison()
```

---

## Twiss array indexing

The `twiss`/`twissstd` arrays are flattened from shape `(4 quantities, 2 planes, 7 methods)`:

```
flat_index = quantity × 14 + plane × 7 + method
```

| Quantity (axis 0) | Index |
|-------------------|-------|
| Normalized emittance | 0 |
| Alpha | 1 |
| Beta | 2 |
| BMAG | 3 |

| Plane (axis 1) | Index |
|-----------------|-------|
| x | 0 |
| y | 1 |

The codebase currently extracts **method 0** (Gaussian) in both `loaders.py` and `comparison.py`.

---

## Known limitations

- **R-matrix mismatch**: `beamline_info.json` stores a simple drift matrix
  `[1, 2.26, 0, 1]`. The MATLAB tool uses per-step R-matrices from a full
  physics model (stored in `data.rMatrix`). This causes significant BMAG
  disagreement, especially in the y-plane where the optics between the quad
  and screen are not drift-like.

- **No uncertainty from slac-measurements**: The package does not propagate
  beam size measurement errors. `xrms_err`/`yrms_err` are loaded but unused.

- **BMAG reporting**: slac-measurements returns bmag per quad step. We report
  `min(bmag)` which is only meaningful when the transport model is correct
  (all steps should give similar bmag with correct R-matrices).

---

## Commands

### Run the notebook

```bash
cd /Users/smiskov/SLAC/agentic-coding-workshop
jupyter lab emittance_matlab_pyemittance_matv7_3.ipynb
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Verify module imports

```bash
python -c "from data.loaders import find_scan_files, load_scan, load_config"
python -c "from analysis.emittance import compute_emittance"
python -c "from analysis.comparison import extract_matlab_results, print_comparison"
```

### Run a quick smoke test (single file)

```bash
python -c "
from data.loaders import find_scan_files, load_scan, load_config
from analysis.emittance import compute_emittance
from analysis.comparison import extract_matlab_results, format_comparison

config = load_config()
scan = load_scan('matlab_scans/', find_scan_files('matlab_scans/')[0])
result = compute_emittance(scan.quadvals, scan.xrms, scan.yrms, scan.xrms_err, scan.yrms_err, config)
if result:
    matlab = extract_matlab_results(scan.twiss, scan.twissstd)
    print(format_comparison(find_scan_files('matlab_scans/')[0], result, matlab))
"
```

---

## Items to note

1. **Note on beam size methods** (1-indexed in MATLAB): 1=Gaussian, 2=Asymmetric Gaussian, 3=Super Gaussian, 4=RMS raw, 5=RMS cut peak, 6=RMS cut area, 7=RMS floor The code now uses method 0 for simplicty. Typically, operators plot method 2 or 5.

2. **Twiss0 field ordering**: in `beamline_info`, the `twiss0` ordering `[e_x, e_y, beta_x, beta_y, alpha_x, alpha_y]`