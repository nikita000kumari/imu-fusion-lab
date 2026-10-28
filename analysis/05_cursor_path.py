"""STEP 8a - Turn the recorded motion into a cursor path and plot it.
Run:  python analysis/05_cursor_path.py
Tune GAIN, DEADZONE_DPS, SMOOTHING, X_FROM/Y_FROM and the signs in config.py.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import config
import fusion
from cursor import CursorMapper

cal = fusion.load_cal()
bias = dict(zip(("gx", "gy", "gz"), cal["bias_dps"]))
motion = pd.read_csv(config.PROCESSED / "motion_clean.csv")
dt = motion.dt.iloc[0]

mapper = CursorMapper(config.GAIN, config.DEADZONE_DPS, config.SMOOTHING, config.X_SIGN, config.Y_SIGN)
rx = (motion[config.X_FROM] - bias[config.X_FROM]).to_numpy()
ry = (motion[config.Y_FROM] - bias[config.Y_FROM]).to_numpy()

moves = np.array([mapper.update(a, b, dt) for a, b in zip(rx, ry)])
x, y = np.cumsum(moves[:, 0]), np.cumsum(moves[:, 1])

fig, ax = plt.subplots(1, 2, figsize=(12, 5))
sc = ax[0].scatter(x, y, c=motion.t, s=3, cmap="viridis")
ax[0].invert_yaxis()            # screen coordinates: y grows downward
ax[0].set_aspect("equal"); ax[0].set_title("Cursor path (colour = time)")
fig.colorbar(sc, ax=ax[0], label="time (s)")
ax[1].plot(motion.t, rx, color="lightgray", label="raw rate X")
ax[1].plot(motion.t, moves[:, 0] / dt / config.GAIN, label="after deadzone + smoothing (x)")
ax[1].set_xlabel("time (s)"); ax[1].set_ylabel("deg/s"); ax[1].legend()
ax[1].set_title("Effect of dead zone and smoothing")
print(f"total cursor travel: x {x[-1]:+d}px, y {y[-1]:+d}px  (should end near where it started if you returned your hand)")
config.save_and_show(fig, "05_cursor_path.png")
