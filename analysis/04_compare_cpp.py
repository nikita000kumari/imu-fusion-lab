"""STEP 7 - Build the C++ filter, run it on the same data, and check it matches Python.
Run:  python analysis/04_compare_cpp.py      (needs g++ installed)
"""
import os
import shutil
import subprocess
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import config
import fusion

compiler = shutil.which("g++")
if not compiler:
    raise SystemExit("g++ not found. Install MinGW (Windows) or use WSL, then run again.")

cal = fusion.load_cal()
if "roll_sign" not in cal:
    raise SystemExit("Run 03_filter.py first (it finds the gyro signs).")

config.BUILD.mkdir(exist_ok=True)
exe = config.BUILD / ("fusion.exe" if os.name == "nt" else "fusion")
subprocess.run([compiler, "-O2", "-std=c++17", str(config.ROOT / "src" / "main.cpp"), "-o", str(exe)],
               check=True)

still_csv = config.PROCESSED / "still_clean.csv"
motion_csv = config.PROCESSED / "motion_clean.csv"
res = subprocess.run([str(exe), str(still_csv), str(motion_csv), str(config.ALPHA),
                      str(cal["roll_sign"]), str(cal["pitch_sign"])],
                     check=True, capture_output=True, text=True)
(config.PROCESSED / "cpp_output.csv").write_text(res.stdout)
print("C++", res.stderr.strip())

cpp = pd.read_csv(config.PROCESSED / "cpp_output.csv")
still = pd.read_csv(still_csv)
motion = pd.read_csv(motion_csv)
bias = fusion.gyro_bias(still)
print("py  bias:", " ".join(f"{b:.6f}" for b in bias))

dt = motion.dt.iloc[0]
r_acc, p_acc = fusion.accel_angles(motion.ax.to_numpy(), motion.ay.to_numpy(), motion.az.to_numpy())
py_roll = fusion.complementary(r_acc, cal["roll_sign"] * (motion.gx - bias[0]).to_numpy(), dt, config.ALPHA)
py_pitch = fusion.complementary(p_acc, cal["pitch_sign"] * (motion.gy - bias[1]).to_numpy(), dt, config.ALPHA)

d_roll = np.abs(py_roll - cpp.roll.to_numpy())
d_pitch = np.abs(py_pitch - cpp.pitch.to_numpy())
print(f"\nmax |Python - C++|  roll: {d_roll.max():.5f} deg   pitch: {d_pitch.max():.5f} deg")
print("PASS: C++ matches Python" if max(d_roll.max(), d_pitch.max()) < 0.01 else
      "FAIL: results differ - check signs, units, and the first-sample handling")

fig, ax = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
ax[0].plot(motion.t, py_roll, label="Python"); ax[0].plot(motion.t, cpp.roll, "--", label="C++")
ax[0].set_ylabel("roll (deg)"); ax[0].legend()
ax[1].plot(motion.t, d_roll, label="roll difference"); ax[1].plot(motion.t, d_pitch, label="pitch difference")
ax[1].set_ylabel("|Python - C++| (deg)"); ax[1].set_xlabel("time (s)"); ax[1].legend()
fig.suptitle("Python vs C++ filter output")
config.save_and_show(fig, "04_python_vs_cpp.png")
