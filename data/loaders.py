import os
import re
import json
from dataclasses import dataclass

import numpy as np
import scipy.io


@dataclass
class ScanData:
    """Extracted beam measurement data from a single emittance scan .mat file.

    Attributes:
        quadvals: Quadrupole magnet setpoints [kG/m].
        xrms: Horizontal beam sizes [m].
        yrms: Vertical beam sizes [m].
        xrms_err: Horizontal beam size uncertainties [m].
        yrms_err: Vertical beam size uncertainties [m].
        twiss: Flattened Twiss parameter array (shape 4×2×7 flattened to 56).
        twissstd: Flattened Twiss parameter uncertainties (same shape as twiss).
        twiss0: Initial Twiss parameters used by MATLAB fitter [beta_x, alpha_x, beta_y, alpha_y, ...].
    """

    quadvals: np.ndarray
    xrms: np.ndarray
    yrms: np.ndarray
    xrms_err: np.ndarray
    yrms_err: np.ndarray
    twiss: np.ndarray
    twissstd: np.ndarray
    twiss0: np.ndarray


def find_scan_files(scans_dir: str) -> list[str]:
    """Return sorted list of .mat filenames matching the emittance scan pattern."""
    regex = r"^Emittance-scan-OTRS_IN20_571-202[0-9]-[0-9]{2}-[0-9]{2}-[0-9]{6}\.mat$"
    filenames = [
        f.name for f in os.scandir(scans_dir) if re.match(regex, f.name)
    ]
    return sorted(filenames)


def load_scan(scans_dir: str, filename: str) -> ScanData:
    """Load a single .mat file and return extracted beam data.

    Beam sizes and errors are converted from μm (as stored) to meters.

    Raises ValueError if twiss data cannot be extracted.
    """
    mat = scipy.io.loadmat(os.path.join(scans_dir, filename))
    mat_data = mat["data"][0]

    num_steps = mat_data["beam"][0].shape[0]
    quadvals = mat_data["quadVal"][0].flatten()

    xrms, yrms, xrms_err, yrms_err = [], [], [], []
    method_idx = 0
    for j in range(num_steps):
        beam_j = mat_data["beam"][0][j, 0+method_idx]
        xrms.append(beam_j["stats"][0, 2])
        yrms.append(beam_j["stats"][0, 3])
        xrms_err.append(beam_j["statsStd"][0, 2])
        yrms_err.append(beam_j["statsStd"][0, 3])

    xrms = np.array(xrms) * 1e-6
    yrms = np.array(yrms) * 1e-6
    xrms_err = np.array(xrms_err) * 1e-6
    yrms_err = np.array(yrms_err) * 1e-6

    try:
        twiss = mat_data["twiss"][0].flatten()
    except (KeyError, IndexError, ValueError) as e:
        raise ValueError(f"Cannot extract twiss data from {filename}") from e

    twissstd = mat_data["twissstd"][0].flatten()
    twiss0 = mat_data["twiss0"][0].flatten()

    return ScanData(
        quadvals=quadvals,
        xrms=xrms,
        yrms=yrms,
        xrms_err=xrms_err,
        yrms_err=yrms_err,
        twiss=twiss,
        twissstd=twissstd,
        twiss0=twiss0,
    )


def load_config(config_dir: str = "LCLS_OTR2") -> dict:
    """Load beamline_info.json and return config dict expected by EmitCalc.

    The returned dict has the structure {"beamline_info": {...}} containing
    quad length [m], beam energy [MeV], Twiss0, and R-matrices.
    """
    fname = os.path.join(config_dir, "beamline_info.json")
    with open(fname) as f:
        return {"beamline_info": json.load(f)}
