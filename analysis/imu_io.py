"""Load accelerometer + gyroscope CSVs exported by Phyphox or Sensor Logger.

Both apps name their columns differently, so we find the time column and the
x/y/z columns by looking at the names. The result is resampled onto one
evenly spaced time grid so accel and gyro line up sample by sample.

Output columns:  t (s), dt (s), ax ay az (as in file), gx gy gz (deg/s)
"""
import re
import numpy as np
import pandas as pd


def _read(path):
    # sep=None lets pandas guess comma / semicolon / tab
    return pd.read_csv(path, sep=None, engine="python")


def _tokens(name):
    return re.findall(r"[a-z0-9]+", str(name).lower())


def _is_time_col(c):
    return "seconds_elapsed" in str(c).lower() or "time" in _tokens(c)


def _time_seconds(df):
    pick = next((c for c in df.columns if "seconds_elapsed" in str(c).lower()), None)
    if pick is None:
        pick = next((c for c in df.columns if "time" in _tokens(c)), df.columns[0])
    t = pd.to_numeric(df[pick], errors="coerce").to_numpy(float)
    if np.nanmedian(np.diff(t)) > 1e3:      # looks like nanoseconds
        t = t / 1e9
    return pick, t


def _axes(df, keyword):
    cols = [c for c in df.columns if not _is_time_col(c)]
    if keyword:
        sub = [c for c in cols if keyword in str(c).lower()]
        cols = sub or cols
    found = {}
    for ax in "xyz":
        match = [c for c in cols if ax in _tokens(c)]
        if not match:
            raise ValueError(f"Could not find an '{ax}' column. Columns are: {list(df.columns)}")
        found[ax] = match[0]
    return found


def _to_array(df, axes):
    return np.column_stack([pd.to_numeric(df[axes[k]], errors="coerce").to_numpy(float) for k in "xyz"])


def _clean(t, v):
    ok = np.isfinite(t) & np.isfinite(v).all(axis=1)
    t, v = t[ok], v[ok]
    t, idx = np.unique(t, return_index=True)   # sorted, no duplicate stamps
    return t, v[idx]


def load_imu(accel_path, gyro_path=None, gyro_unit="rad/s"):
    gyro_path = gyro_path or accel_path
    a, g = _read(accel_path), _read(gyro_path)
    ta_col, ta = _time_seconds(a)
    tg_col, tg = _time_seconds(g)
    a_axes, g_axes = _axes(a, "acc"), _axes(g, "gyro")
    ta, A = _clean(ta, _to_array(a, a_axes))
    tg, G = _clean(tg, _to_array(g, g_axes))

    t0, t1 = max(ta[0], tg[0]), min(ta[-1], tg[-1])
    if t1 <= t0:
        print("WARNING: accel and gyro files do not overlap in time. Assuming both "
              "started recording together. Record both sensors in the SAME run!")
        ta, tg = ta - ta[0], tg - tg[0]
        t0, t1 = 0.0, min(ta[-1], tg[-1])

    dt = float(np.median(np.diff(tg)))
    grid = np.arange(t0, t1, dt)
    out = pd.DataFrame({"t": grid - t0, "dt": dt})
    for i, k in enumerate("xyz"):
        out["a" + k] = np.interp(grid, ta, A[:, i])
    scale = 180.0 / np.pi if gyro_unit == "rad/s" else 1.0
    for i, k in enumerate("xyz"):
        out["g" + k] = np.interp(grid, tg, G[:, i]) * scale

    if gyro_unit == "rad/s" and np.nanpercentile(np.abs(G), 99) > 20:
        print("WARNING: gyro values are large for rad/s. If your file is in deg/s, "
              'set GYRO_UNIT = "deg/s" in config.py')

    info = {"rate_hz": 1.0 / dt, "duration_s": float(grid[-1] - grid[0]), "samples": len(grid),
            "accel_cols": a_axes, "gyro_cols": g_axes}
    return out, info
