# Agentic Coding Workshop Exercises

This repository contains materials for comparing beam emittance calculations between MATLAB and [pyemittance](https://github.com/slaclab/pyemittance) at SLAC's LCLS injector (OTR screen `OTRS:IN20:571`).

## Contents

- **`emittance_matlab_pyemittance_matv7_3.ipynb`** — Jupyter notebook that loads MATLAB emittance scan files, re-runs the analysis with pyemittance, and compares results (emittance, Twiss parameters, Bmag).
- **`matlab_scans/`** — MATLAB `.mat` files from emittance scans taken in 2020–2021.
- **`LCLS_OTR2/`** — Beamline optics/configuration for the OTR2 screen.
- **`pv_data.json`** — Machine PV snapshot data associated with individual scans. This is only needed for the optional exercise involving the LCLS injector surrogate model.
- **`requirements.txt`** — Python dependencies.

## Setup

Create and activate an isolated environment, then install dependencies.

**Using venv:**
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Using conda:**
```bash
conda create -n emittance python=3.11
conda activate emittance
pip install -r requirements.txt
```

## Running the Notebook

Open `emittance_matlab_pyemittance_matv7_3.ipynb` in an IDE such as VS Code or PyCharm and select the environment created above as the kernel. Running the notebook inside an IDE is required for AI coding agents (e.g. GitHub Copilot) to be able to read cell outputs and assist with the exercises.
