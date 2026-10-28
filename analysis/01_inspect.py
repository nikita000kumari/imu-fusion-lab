"""STEP 4 - Load your recordings, check them, and plot the raw data.
Run:  python analysis/01_inspect.py
"""
import numpy as np
import matplotlib.pyplot as plt
import config
import imu_io

config.PROCESSED.mkdir(parents=True, exist_ok=True)

runs = [("still", config.STILL_ACCEL, config.STILL_GYRO),
        ("motion", config.MOTION_ACCEL, config.MOTION_GYRO)]

for name, acc_file, gyro_file in runs:
    df, info = imu_io.load_imu(acc_file, gyro_file, config.GYRO_UNIT)
    df.to_csv(config.PROCESSED / f"{name}_clean.csv", index=False)

    mag = np.sqrt(df.ax**2 + df.ay**2 + df.az**2)
    print(f"\n=== {name} ===")
    print(f"samples: {info['samples']}   rate: {info['rate_hz']:.1f} Hz   duration: {info['duration_s']:.1f} s")
    print(f"accel columns used: {info['accel_cols']}")
    print(f"gyro  columns used: {info['gyro_cols']}")
    print(f"mean |accel| = {mag.mean():.3f}   (should be ~9.8 if m/s^2, ~1.0 if in g)")
    print(f"gyro std (deg/s): gx={df.gx.std():.3f} gy={df.gy.std():.3f} gz={df.gz.std():.3f}")

    fig, ax = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    for k in ("ax", "ay", "az"):
        ax[0].plot(df.t, df[k], label=k, lw=0.8)
    ax[0].set_ylabel("accelerometer"); ax[0].legend(loc="upper right")
    for k in ("gx", "gy", "gz"):
        ax[1].plot(df.t, df[k], label=k, lw=0.8)
    ax[1].set_ylabel("gyroscope (deg/s)"); ax[1].set_xlabel("time (s)")
    ax[1].legend(loc="upper right")
    fig.suptitle(f"Raw data - {name}")
    config.save_and_show(fig, f"01_raw_{name}.png")
