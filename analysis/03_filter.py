"""STEP 6 - Complementary filter: accel-only vs gyro-only vs filtered, for several alphas.
Run:  python analysis/03_filter.py
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import config
import fusion

cal = fusion.load_cal()
bias = np.array(cal["bias_dps"])
still = pd.read_csv(config.PROCESSED / "still_clean.csv")
motion = pd.read_csv(config.PROCESSED / "motion_clean.csv")
dt = motion.dt.iloc[0]


def prepare(df):
    roll_acc, pitch_acc = fusion.accel_angles(df.ax.to_numpy(), df.ay.to_numpy(), df.az.to_numpy())
    return roll_acc, pitch_acc, (df.gx - bias[0]).to_numpy(), (df.gy - bias[1]).to_numpy()


roll_acc, pitch_acc, gx, gy = prepare(motion)

# Do the gyro and accel angles point the same way? Find out from the data.
roll_sign, c1 = fusion.pick_sign(roll_acc, gx, dt)
pitch_sign, c2 = fusion.pick_sign(pitch_acc, gy, dt)
print(f"roll sign {roll_sign:+d} (corr {c1:+.2f})   pitch sign {pitch_sign:+d} (corr {c2:+.2f})")
if min(abs(c1), abs(c2)) < 0.5:
    print("WARNING: low correlation. Check the units/axes, or the motion was too small.")
cal["roll_sign"], cal["pitch_sign"] = roll_sign, pitch_sign
fusion.save_cal(cal)

s_roll_acc, s_pitch_acc, s_gx, s_gy = prepare(still)
fig, axs = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
results = []
for ax_plot, name, acc, rate, sign in ((axs[0], "roll", roll_acc, gx, roll_sign),
                                       (axs[1], "pitch", pitch_acc, gy, pitch_sign)):
    ax_plot.plot(motion.t, acc, color="lightgray", lw=1, label="accel only (noisy)")
    ax_plot.plot(motion.t, fusion.gyro_only(sign * rate, dt, acc[0]), "--", color="tab:red", lw=1,
                 label="gyro only (drifts)")
    for alpha in config.ALPHAS:
        ax_plot.plot(motion.t, fusion.complementary(acc, sign * rate, dt, alpha), lw=1.3,
                     label=f"complementary alpha={alpha}")
    ax_plot.set_ylabel(f"{name} (deg)"); ax_plot.legend(loc="upper right", fontsize=8)
axs[-1].set_xlabel("time (s)")
fig.suptitle("Accel vs gyro vs complementary filter")

# Numbers for the README, measured on the STILL recording (true angle does not move)
lines = ["| Signal | Jitter at rest, std (deg) | Time constant tau (s) |", "|---|---|---|",
         f"| accel only (roll) | {s_roll_acc.std():.3f} | - |"]
for alpha in config.ALPHAS + [config.ALPHA]:
    out = fusion.complementary(s_roll_acc, roll_sign * s_gx, dt, alpha)
    tau = alpha * dt / (1 - alpha)
    lines.append(f"| complementary alpha={alpha} (roll) | {out.std():.3f} | {tau:.2f} |")
table = "\n".join(lines)
print("\n" + table)
(config.ROOT / "analysis" / "results.md").write_text(table + "\n")
print("\nsaved table to analysis/results.md (paste it into your README)")
config.save_and_show(fig, "03_filter_comparison.png")
