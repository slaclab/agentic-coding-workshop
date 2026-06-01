import logging

import numpy as np
from slac_measurements.emittance import normalize_emittance
from slac_measurements.emittance_measurement import compute_emit_bmag_quad_scan_machine_units

logger = logging.getLogger(__name__)

ELECTRON_MASS_EV = 0.511e6


def compute_emittance(
    quadvals: np.ndarray,
    xrms: np.ndarray,
    yrms: np.ndarray,
    xrms_err: np.ndarray,
    yrms_err: np.ndarray,
    config: dict,
    calc_bmag: bool = True,
) -> dict | None:
    """Run a quad-scan emittance calculation via slac-measurements.

    Args:
        quadvals: Quad magnet BDES setpoints [kG].
        xrms: Horizontal beam sizes [m].
        yrms: Vertical beam sizes [m].
        xrms_err: Horizontal beam size uncertainties [m] (unused by slac-measurements).
        yrms_err: Vertical beam size uncertainties [m] (unused by slac-measurements).
        config: Beamline config dict (from load_config) with keys
                Lquad [m], energy [eV], rMatx/rMaty (flat 4-element), Twiss0.
        calc_bmag: Whether to compute BMAG (requires design Twiss in config).

    Returns:
        Dict with keys:
            'norm_emit_x', 'norm_emit_y' [m·rad],
            'screen_bmagx', 'screen_bmagy' [dimensionless] (min over quad steps),
        or None if the fit fails (e.g. non-positive emittance).

    Note:
        slac-measurements does not propagate measurement uncertainties.
        The returned dict does not include error keys.
    """
    info = config["beamline_info"]

    # Fixed transport matrix model from JSON config.
    Rx = np.array(info["rMatx"], dtype=float)
    Ry = np.array(info["rMaty"], dtype=float)
    rmat = np.array(
        [
            [[Rx[0], Rx[1]], [Rx[2], Rx[3]]],
            [[Ry[0], Ry[1]], [Ry[2], Ry[3]]],
        ],
        dtype=float,
    )
    if calc_bmag:
        # Twiss0 layout: [emit_x, emit_y, beta_x, beta_y, alpha_x, alpha_y]
        twiss_design = np.array([
            [info["Twiss0"][2], info["Twiss0"][4]],  # [beta_x, alpha_x]
            [info["Twiss0"][3], info["Twiss0"][5]],  # [beta_y, alpha_y]
        ])
    else:
        twiss_design = None

    try:
        results = compute_emit_bmag_quad_scan_machine_units(
            quad_vals=[quadvals, quadvals],
            beamsizes=[xrms, yrms],
            q_len=info["Lquad"],
            rmat=rmat,
            energy=info["energy"],
            twiss_design=twiss_design,
        )
    except Exception as exc:
        logger.warning("Emittance fit failed: %s", exc)
        return None

    # results["emittance"] is geometric emittance in mm-mrad
    geom_emit_x = np.asarray(results["emittance"][0]).item()
    geom_emit_y = np.asarray(results["emittance"][1]).item()

    if geom_emit_x <= 0 or geom_emit_y <= 0:
        return None

    norm_emit_x = normalize_emittance(geom_emit_x, info["energy"]*1e-9)
    norm_emit_y = normalize_emittance(geom_emit_y, info["energy"]*1e-9)

    out = {
        "norm_emit_x": norm_emit_x * 1e-6,  # mm-mrad → m·rad
        "norm_emit_y": norm_emit_y * 1e-6,
    }

    if results["bmag"] is not None:
        out["screen_bmagx"] = float(np.min(results["bmag"][0]))
        out["screen_bmagy"] = float(np.min(results["bmag"][1]))
    else:
        out["screen_bmagx"] = np.nan
        out["screen_bmagy"] = np.nan

    return out
