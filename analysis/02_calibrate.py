"""STEP 5 - Gyro bias, noise, and drift from the STILL recording.
Run:  python analysis/02_calibrate.py
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import config
import fusion

still = pd.read_csv(config.PROCESSED / "still_clean.csv")
dt, t = still.dt.iloc[0], still.t.to_numpy()

bias = fusion.gyro_bias(still)
print("gyro bias (deg/s):  gx=%.4f  gy=%.4f  gz=%.4f" % tuple(bias))

if abs(still.ax.mean()) > abs(still.az.mean()) or still.az.mean() < 0:
    print("WARNING: gravity is not mostly on +Z. Was the phone flat, screen up, and still?")

roll_acc, pitch_acc = fusion.accel_angles(still.ax, still.ay, still.az)
print("accel angle noise (std, deg):  roll=%.3f  pitch=%.3f" % (roll_acc.std(), pitch_acc.std()))

rows = {}
fig, axs = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
for ax_plot, axis in zip(axs, ("gx", "gy", "gz")):
    raw = still[axis].to_numpy()
    before = fusion.gyro_only(raw, dt)
    after = fusion.gyro_only(raw - bias[("gx", "gy", "gz").index(axis)], dt)
    d_before = np.polyfit(t, before, 1)[0] * 60
    d_after = np.polyfit(t, after, 1)[0] * 60
    rows[axis] = (d_before, d_after)
    ax_plot.plot(t, before, label=f"no calibration ({d_before:+.2f} deg/min)")
    ax_plot.plot(t, after, label=f"calibrated ({d_after:+.3f} deg/min)")
    ax_plot.set_ylabel(f"{axis} integrated (deg)"); ax_plot.legend(loc="upper left")
axs[-1].set_xlabel("time (s)")
fig.suptitle("Gyro-only angle on a still phone (drift before / after calibration)")

print("\ndrift of gyro-only angle, deg/min:")
for k, (b, a) in rows.items():
    print(f"  {k}: before {b:+.3f}   after {a:+.3f}")
print("(After calibration, the leftover drift comes from temperature and noise.)")

fusion.save_cal({"bias_dps": bias.tolist(),
                 "accel_noise_deg": {"roll": float(roll_acc.std()), "pitch": float(pitch_acc.std())},
                 "drift_dpm_before": {k: v[0] for k, v in rows.items()},
                 "drift_dpm_after": {k: v[1] for k, v in rows.items()}})
config.save_and_show(fig, "02_gyro_drift.png")
