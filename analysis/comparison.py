from dataclasses import dataclass

import numpy as np


@dataclass
class MatlabResults:
    """MATLAB-computed emittance and BMAG results for a single scan.

    Attributes:
        emitx: Normalized horizontal emittance [m·rad].
        emitx_err: Uncertainty on emitx [m·rad].
        emity: Normalized vertical emittance [m·rad].
        emity_err: Uncertainty on emity [m·rad].
        bmagx: Horizontal BMAG (beta mismatch) [dimensionless].
        bmagx_err: Uncertainty on bmagx [dimensionless].
        bmagy: Vertical BMAG [dimensionless].
        bmagy_err: Uncertainty on bmagy [dimensionless].
    """

    emitx: float
    emitx_err: float
    emity: float
    emity_err: float
    bmagx: float
    bmagx_err: float
    bmagy: float
    bmagy_err: float


def extract_matlab_results(twiss: np.ndarray, twissstd: np.ndarray) -> MatlabResults:
    """Extract MATLAB emittance/bmag values from the flattened twiss arrays.

    The twiss array has logical shape (4 quantities × 2 planes × 7 methods),
    flattened to length 56. We extract method-0 results at known indices.
    """
    method_idx = 5
    return MatlabResults(
        emitx=twiss[0+method_idx],
        emitx_err=twissstd[0+method_idx],
        emity=twiss[7+method_idx],
        emity_err=twissstd[7+method_idx],
        bmagx=twiss[42+method_idx],
        bmagx_err=twissstd[42+method_idx],
        bmagy=twiss[49+method_idx],
        bmagy_err=twissstd[49+method_idx],
    )


def _pct_diff(a: float, b: float) -> str:
    """Format percent difference (a vs b) as a signed string."""
    if b == 0:
        return "  N/A"
    pct = (a - b) / abs(b) * 100
    return f"{pct:+5.1f}"


def format_comparison(filename: str, pyemit: dict, matlab: MatlabResults) -> str:
    """Build a formatted comparison table of slac-measurements vs MATLAB results.

    Args:
        filename: Scan filename for the header.
        pyemit: Output dict from compute_emittance() with keys
                'norm_emit_x/y' [m·rad], 'screen_bmagx/y' [dimensionless].
        matlab: Extracted MATLAB results.

    Returns:
        Multi-line string with a side-by-side comparison table.
    """
    sep = "━" * 70

    rows = [
        (
            "emit_x [μm]",
            pyemit["norm_emit_x"] / 1e-6,
            matlab.emitx / 1e-6,
            matlab.emitx_err / 1e-6,
        ),
        (
            "emit_y [μm]",
            pyemit["norm_emit_y"] / 1e-6,
            matlab.emity / 1e-6,
            matlab.emity_err / 1e-6,
        ),
        (
            "bmag_x",
            pyemit["screen_bmagx"],
            matlab.bmagx,
            matlab.bmagx_err,
        ),
        (
            "bmag_y",
            pyemit["screen_bmagy"],
            matlab.bmagy,
            matlab.bmagy_err,
        ),
    ]

    lines = [
        sep,
        f"  {filename}",
        sep,
        f"  {'':14s} {'slac-meas':>10s}  {'MATLAB':>16s}  {'Δ (%)':>6s}",
    ]

    for label, py_val, ml_val, ml_err in rows:
        py_str = f"{py_val:6.2f}"
        ml_str = f"{ml_val:6.2f} ± {ml_err:.2f}"
        pct = _pct_diff(py_val, ml_val)
        lines.append(f"  {label:14s} {py_str:>10s}  {ml_str:>16s}  {pct:>6s}")

    lines.append("")
    return "\n".join(lines)


def print_comparison(filename: str, pyemit: dict, matlab: MatlabResults) -> None:
    """Print a formatted comparison table of pyemittance vs MATLAB results."""
    print(format_comparison(filename, pyemit, matlab))


def print_config(config: dict, twiss0_matlab: np.ndarray) -> None:
    """Print beamline configuration (call once, not per-scan).

    Args:
        config: Config dict with 'beamline_info' key.
        twiss0_matlab: Initial Twiss parameters from MATLAB [beta_x, alpha_x, ...].
    """
    info = config["beamline_info"]
    print("━" * 70)
    print("  Beamline Configuration")
    print("━" * 70)
    print(f"  {'PyEmit Twiss0:':18s}", [f"{e:.4E}" for e in info["Twiss0"]])
    print(f"  {'MATLAB Twiss0:':18s}", [f"{e:.4E}" for e in twiss0_matlab])
    print(f"  {'R-matrix x:':18s}", info["rMatx"])
    print(f"  {'R-matrix y:':18s}", info["rMaty"])
    print()
