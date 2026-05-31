---
name: injector-magnet-scan
description: Scan a quadrupole magnet through the LCLS copper injector surrogate model (cuinj API) and plot beam sizes or emittances vs quad strength. Supports custom scans or replaying historical MATLAB emittance scans from this repo.
disable-model-invocation: false
allowed-tools: Read Bash WebFetch
---

# Magnet Scan — LCLS Copper Injector Surrogate Model

Scan a quadrupole magnet through a range of values using the LCLS copper injector surrogate model, then plot predicted beam properties vs magnet strength.

## When to use

When the user wants to:
- Scan a quad magnet and see predicted beam sizes, emittances, or bunch length
- Run a historical MATLAB scan through the surrogate model
- Compare model predictions across a range of magnet settings

## API Reference

**Base URL:** `https://ard-modeling-service.slac.stanford.edu/cuinj`

**Key endpoints:**
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/inputs` | GET | List input variables with defaults and ranges |
| `/outputs` | GET | List output variables |
| `/predict/batch` | POST | Run batch prediction |

**Batch payload format:**
```json
{"inputs_list": [{"QUAD:IN20:525:BACT": -3.0}, {"QUAD:IN20:525:BACT": -2.0}]}
```
Only the scanning variable needs to be specified per sample — omitted inputs use their model defaults.

**Batch response format:**
```json
{"outputs_list": [{"OTRS:IN20:571:XRMS": 275.4, ...}, ...], "batch_size": 2}
```

## Model Inputs (quadrupole magnets available for scanning)

| Input PV (API name) | Default | Range |
|---------------------|---------|-------|
| `QUAD:IN20:121:BACT` | -0.0015 | [-0.021, 0.021] |
| `QUAD:IN20:122:BACT` | -0.0007 | [-0.021, 0.021] |
| `QUAD:IN20:361:BACT` | -2.0006 | [-4.318, -1.080] |
| `QUAD:IN20:371:BACT` | 2.0006 | [1.091, 4.310] |
| `QUAD:IN20:425:BACT` | -1.0808 | [-7.560, -1.081] |
| `QUAD:IN20:441:BACT` | -0.1794 | [-1.078, 7.560] |
| `QUAD:IN20:511:BACT` | 2.8522 | [-1.079, 7.558] |
| `QUAD:IN20:525:BACT` | -3.2184 | [-7.558, -1.080] |

Other (non-quad) model inputs:

| Input PV | Default | Range | Constant? |
|----------|---------|-------|-----------|
| `CAMR:IN20:186:R_DIST` | 423.87 | [210.2, 500.0] | No |
| `Pulse_length` | 1.855 | [1.818, 7.272] | No |
| `FBCK:BCI0:1:CHRG_S` | 0.25 | [0.25, 0.25] | Yes |
| `SOLN:IN20:121:BACT` | 0.478 | [0.377, 0.498] | No |
| `ACCL:IN20:300:L0A_ADES` | 58.0 | [58.0, 58.0] | Yes |
| `ACCL:IN20:300:L0A_PDES` | -9.536 | [-25.0, 10.0] | No |
| `ACCL:IN20:400:L0B_ADES` | 70.0 | [70.0, 70.0] | Yes |
| `ACCL:IN20:400:L0B_PDES` | 9.856 | [-25.0, 10.0] | No |

## Model Outputs (available for plotting)

| Output PV | Description |
|-----------|-------------|
| `OTRS:IN20:571:XRMS` | Horizontal beam size (μm) |
| `OTRS:IN20:571:YRMS` | Vertical beam size (μm) |
| `sigma_z` | Bunch length (m) |
| `norm_emit_x` | Normalized horizontal emittance (m·rad) |
| `norm_emit_y` | Normalized vertical emittance (m·rad) |

## Procedure

### Step 1 — Identify the scan source

Determine whether the user wants:
- **Custom scan**: User specifies a quad, min, max, and number of steps. Other inputs use model defaults.
- **MATLAB scan**: User references a historical scan by date/time. The quad values come from the `.mat` file, and other model inputs come from `pv_data.json`.

### Step 2 — Collect scan parameters

**For a custom scan:**
- Ask which quad to scan (show the quad table above with ranges)
- Ask for min, max, and number of steps (suggest the model's valid range)
- Ask which output(s) to plot

**For a MATLAB scan:**
- Match the user's date/time description to a file in `matlab_scans/`. Files are named: `Emittance-scan-OTRS_IN20_571-YYYY-MM-DD-HHMMSS.mat`
  - Example: "6/21/2020 at 8:39 am" → `Emittance-scan-OTRS_IN20_571-2020-06-21-083923.mat`
- The scanning quad in all these files is `QUAD:IN20:525` (extract from `data['quadName']` to confirm)
- Load quad values from the `.mat` file: `scipy.io.loadmat(path)['data'][0]['quadVal'][0].flatten()`
- Load corresponding PV settings from `pv_data.json` using the filename as key

### Step 3 — Build the batch payload

For each quad value in the scan, build an input dict. 

**Custom scan:**
```python
import numpy as np
quad_values = np.linspace(min_val, max_val, num_steps)
inputs_list = [{scan_quad_pv: float(v)} for v in quad_values]
```

**MATLAB scan with pv_data context:**
```python
import json, scipy.io, numpy as np

# Load quad scan values from .mat
mat = scipy.io.loadmat(f"matlab_scans/{filename}")
quad_values = mat['data'][0]['quadVal'][0].flatten()

# Load other PV settings from pv_data.json
with open('pv_data.json') as f:
    pv_data = json.load(f)
pv_settings = pv_data[filename]

# Map pv_data.json keys (BCTRL) → API keys (BACT)
# Also map L0A_PDES/L0B_PDES which have same name in both
PV_TO_API = {
    "SOLN:IN20:121:BCTRL": "SOLN:IN20:121:BACT",
    "QUAD:IN20:121:BCTRL": "QUAD:IN20:121:BACT",
    "QUAD:IN20:122:BCTRL": "QUAD:IN20:122:BACT",
    "QUAD:IN20:361:BCTRL": "QUAD:IN20:361:BACT",
    "QUAD:IN20:371:BCTRL": "QUAD:IN20:371:BACT",
    "QUAD:IN20:425:BCTRL": "QUAD:IN20:425:BACT",
    "QUAD:IN20:441:BCTRL": "QUAD:IN20:441:BACT",
    "QUAD:IN20:511:BCTRL": "QUAD:IN20:511:BACT",
    "QUAD:IN20:525:BCTRL": "QUAD:IN20:525:BACT",
    "ACCL:IN20:300:L0A_PDES": "ACCL:IN20:300:L0A_PDES",
    "ACCL:IN20:400:L0B_PDES": "ACCL:IN20:400:L0B_PDES",
}

# Build base settings (exclude non-model PVs and the scanning quad)
scan_quad_api = "QUAD:IN20:525:BACT"
base_inputs = {}
for pv_key, value in pv_settings.items():
    if pv_key in PV_TO_API:
        api_key = PV_TO_API[pv_key]
        if api_key != scan_quad_api:
            base_inputs[api_key] = value

# Build batch: each sample has base settings + one quad value
inputs_list = [{**base_inputs, scan_quad_api: float(v)} for v in quad_values]
```

### Step 4 — Run batch prediction

```python
import requests

response = requests.post(
    "https://ard-modeling-service.slac.stanford.edu/cuinj/predict/batch",
    json={"inputs_list": inputs_list}
)
response.raise_for_status()
results = response.json()
```

### Step 5 — Extract output values

```python
outputs_list = results["outputs_list"]
# Extract desired output(s) as arrays
output_values = {
    key: [sample[key] for sample in outputs_list]
    for key in outputs_to_plot  # e.g. ["OTRS:IN20:571:XRMS", "OTRS:IN20:571:YRMS"]
}
```

### Step 6 — Plot output(s) vs magnet

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(8, 5))
for output_name, values in output_values.items():
    ax.plot(quad_values, values, 'o-', label=output_name)

ax.set_xlabel(f"{scan_quad_pv} (kG)")
ax.set_ylabel("Model Output")
ax.set_title(f"Surrogate Model: Output vs {scan_quad_pv}")
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("scan_result.png", dpi=150)
plt.show()
```

## Example prompts and how to handle them

**"Scan QUAD:IN20:525 from -7 to -1 in 20 steps and plot beam sizes"**
→ Custom scan. Use `QUAD:IN20:525:BACT` with `np.linspace(-7, -1, 20)`. Plot `OTRS:IN20:571:XRMS` and `OTRS:IN20:571:YRMS`.

**"Run the scan from 6/21/2020 at 8:39 am through the injector model and show me the beamsizes vs the scanning quad"**
→ MATLAB scan. File: `Emittance-scan-OTRS_IN20_571-2020-06-21-083923.mat`. Load quad values from `.mat`, load other inputs from `pv_data.json`, scan quad is `QUAD:IN20:525:BACT`, plot `OTRS:IN20:571:XRMS` and `OTRS:IN20:571:YRMS`.

**"Show me emittance vs QUAD:IN20:511 across its full range"**
→ Custom scan. Use range [-1.079, 7.558] from model metadata, default to ~30 steps. Plot `norm_emit_x` and `norm_emit_y`.

## Important notes

- The API uses `BACT` suffix for magnet PVs. The `pv_data.json` file uses `BCTRL`. Map between them.
- `pv_data.json` contains `CAMR:IN20:186:XRMS` and `CAMR:IN20:186:YRMS` — these are measured beam sizes from the VCC camera, NOT model inputs. Do not pass them to the API. (The model input `CAMR:IN20:186:R_DIST` is a different quantity — the laser spot radius on the cathode.)
- When using MATLAB scan context, any PV in `pv_data.json` that doesn't map to a model input should be skipped.
- Always validate that quad scan values are within the model's valid range. Warn the user if values are out of range.
- The `pv_data.json` `ACCL:IN20:400:L0B_PDES` values (typically -2.5) differ from the model default (9.856). This is expected — use the pv_data value for MATLAB scans.