"""Edit the paths and numbers in this file. Everything else reads from here."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PROCESSED = DATA / "processed"
PLOTS = ROOT / "analysis" / "plots"
BUILD = ROOT / "build"

# ---- 1. YOUR RECORDINGS (edit these file names) --------------------------------
# If your app saved accel and gyro in ONE file, put the same path in both lines.
STILL_ACCEL = DATA / "still_accel.csv"
STILL_GYRO = DATA / "still_gyro.csv"
MOTION_ACCEL = DATA / "motion_accel.csv"
MOTION_GYRO = DATA / "motion_gyro.csv"

# Unit of the gyro in your files: "rad/s" (Phyphox, Sensor Logger) or "deg/s"
GYRO_UNIT = "rad/s"

# ---- 2. FILTER SETTINGS ---------------------------------------------------------
ALPHAS = [0.90, 0.96, 0.99]   # values compared in the plots (step 6)
ALPHA = 0.98                  # value used for the cursor and the C++ check

# ---- 3. CURSOR SETTINGS (step 8) ------------------------------------------------
# Which gyro axis moves the cursor, and in which direction (+1 or -1).
# Phone flat in your hand, screen up:
#   gy = tilt left/right edge   gx = tilt top/bottom edge   gz = turn left/right
X_FROM, X_SIGN = "gy", +1
Y_FROM, Y_SIGN = "gx", -1
GAIN = 12.0          # pixels per degree of rotation (sensitivity)
DEADZONE_DPS = 3.0   # ignore rotation slower than this (deg/s) -> no creeping
SMOOTHING = 0.80     # 0 = no smoothing, closer to 1 = smoother but laggier


def save_and_show(fig, name):
    PLOTS.mkdir(parents=True, exist_ok=True)
    fig.savefig(PLOTS / name, dpi=150, bbox_inches="tight")
    print(f"saved plot: analysis/plots/{name}")
    if not os.environ.get("NO_SHOW"):
        import matplotlib.pyplot as plt
        plt.show()
