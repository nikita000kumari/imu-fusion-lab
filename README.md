# IMU Sensor Fusion Lab

Estimating pitch and roll from accelerometer and gyroscope data using a complementary filter in portable C++, with Python analysis and a comparison against other filters.

Built as groundwork for a wearable BLE air-mouse on ESP32 (MPU6050 + BLE HID).

> **Status:** In progress. Hardware port to ESP32 not yet done.

## Why this project

- The accelerometer gives a stable angle reference but is noisy.
- The gyroscope is smooth but drifts when integrated over time.
- A complementary filter combines both with very little compute, which suits a small microcontroller.

## Data

- Recorded with a phone IMU using Phyphox / Sensor Logger.
- `data/still.csv`: phone lying flat for 60 s (used to measure noise and gyro bias)
- `data/tilt.csv`: slow pitch and roll motion for [__] s (used to test the filter)
- Sample rate: [__] Hz

## Method

**1. Gyro bias calibration:** average the gyro readings from `still.csv` and subtract this offset.

**2. Angles from accelerometer**

```
roll_acc  = atan2(ay, az)
pitch_acc = atan2(-ax, sqrt(ay^2 + az^2))
```

**3. Complementary filter**

```
angle = alpha * (angle + gyro * dt) + (1 - alpha) * angle_acc
```

- `dt` is computed from the CSV timestamps, not assumed constant.
- Gyro data converted from rad/s to deg/s where needed.
- The filter is a small C++ class with no PC-specific dependencies, so it can be copied to an ESP32 sketch.

**Known limitation:** yaw cannot be corrected with an accelerometer, because gravity does not change when rotating about the vertical axis. This filter gives pitch and roll only. For the air-mouse, yaw motion would use gyro rate directly.




**Conclusion:** [Write 2-3 lines in your own words on why the complementary filter is enough for an air-mouse.]

## Repository structure

```
imu-fusion-lab/
├── data/        # recorded CSV files
├── src/         # C++ filter implementation
├── analysis/    # Python scripts and plots
├── tests/       # unit tests
└── README.md
```

## How to run

```bash
# C++ filter
g++ -std=c++17 src/main.cpp -o fusion
./fusion data/tilt.csv > output.csv

# Plots
pip install numpy pandas matplotlib
python analysis/plot.py
```
## Skills used

C++, Python, sensor calibration, sensor fusion, signal analysis, data visualization
