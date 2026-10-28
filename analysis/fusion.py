"""Reference (Python) implementation. The C++ in src/ must give the same numbers."""
import json
import numpy as np
import config


def accel_angles(ax, ay, az):
    """Tilt angles from gravity. Result in degrees.
    roll  = rotation about the X axis (top/bottom edge of the phone goes up/down)
    pitch = rotation about the Y axis (left/right edge goes up/down)
    (Aircraft naming differs. Do not worry, only the axis matters.)"""
    roll = np.degrees(np.arctan2(ay, az))
    pitch = np.degrees(np.arctan2(-ax, np.sqrt(ay * ay + az * az)))
    return roll, pitch


def gyro_bias(still_df):
    return still_df[["gx", "gy", "gz"]].mean().to_numpy()


def gyro_only(rate, dt, start=0.0):
    """Integrate the gyro: angle += rate * dt  (this drifts!)"""
    return start + np.cumsum(rate * dt)


def complementary(acc_angle, rate, dt, alpha):
    """angle = alpha * (angle + rate*dt) + (1 - alpha) * accel_angle"""
    out = np.empty_like(acc_angle)
    angle = acc_angle[0]
    out[0] = angle
    for i in range(1, len(acc_angle)):
        angle = alpha * (angle + rate[i] * dt) + (1.0 - alpha) * acc_angle[i]
        out[i] = angle
    return out


def pick_sign(acc_angle, rate, dt):
    """Decide if the gyro axis points the same way as the accel angle (+1) or not (-1)."""
    k = max(1, int(round(0.1 / dt)))
    kernel = np.ones(k) / k
    d = np.gradient(np.convolve(acc_angle, kernel, mode="same"), dt)
    r = np.convolve(rate, kernel, mode="same")
    c = float(np.corrcoef(d, r)[0, 1])
    return (1 if c >= 0 else -1), c


def load_cal():
    p = config.PROCESSED / "calibration.json"
    if not p.exists():
        raise SystemExit("Run 02_calibrate.py first (calibration.json missing).")
    return json.loads(p.read_text())


def save_cal(cal):
    (config.PROCESSED / "calibration.json").write_text(json.dumps(cal, indent=2))
