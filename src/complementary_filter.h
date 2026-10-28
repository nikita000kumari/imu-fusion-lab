// Portable code: no PC-only or Arduino-only calls, so the SAME file runs on a laptop
// (for tests) and later on an ESP32. Units: gyro in deg/s, dt in seconds.
#pragma once
#include <cmath>

namespace imu {

constexpr float kRadToDeg = 57.29577951308232f;

// Averages gyro readings taken while the device is still -> the gyro "bias".
class GyroCalibrator {
public:
    void addSample(float gx, float gy, float gz) { sx_ += gx; sy_ += gy; sz_ += gz; ++n_; }
    int count() const { return n_; }
    float biasX() const { return n_ ? static_cast<float>(sx_ / n_) : 0.0f; }
    float biasY() const { return n_ ? static_cast<float>(sy_ / n_) : 0.0f; }
    float biasZ() const { return n_ ? static_cast<float>(sz_ / n_) : 0.0f; }

private:
    double sx_ = 0, sy_ = 0, sz_ = 0;  // double: summing thousands of floats loses precision
    int n_ = 0;
};

// angle = alpha * (angle + gyro*dt) + (1 - alpha) * accel_angle
class ComplementaryFilter {
public:
    ComplementaryFilter(float alpha, float rollSign, float pitchSign)
        : alpha_(alpha), rollSign_(rollSign), pitchSign_(pitchSign) {}

    // gx, gy must already have the bias subtracted.
    void update(float ax, float ay, float az, float gx, float gy, float dt) {
        const float rollAcc = std::atan2(ay, az) * kRadToDeg;
        const float pitchAcc = std::atan2(-ax, std::sqrt(ay * ay + az * az)) * kRadToDeg;
        if (!started_) {  // first sample: start from the accelerometer angle
            roll_ = rollAcc;
            pitch_ = pitchAcc;
            started_ = true;
            return;
        }
        roll_ = alpha_ * (roll_ + rollSign_ * gx * dt) + (1.0f - alpha_) * rollAcc;
        pitch_ = alpha_ * (pitch_ + pitchSign_ * gy * dt) + (1.0f - alpha_) * pitchAcc;
    }

    float roll() const { return roll_; }
    float pitch() const { return pitch_; }

private:
    float alpha_, rollSign_, pitchSign_;
    float roll_ = 0.0f, pitch_ = 0.0f;
    bool started_ = false;
};

}  // namespace imu
