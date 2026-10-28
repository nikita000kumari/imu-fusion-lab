"""Turn gyro rates into mouse movement. Same steps a firmware would do."""


class CursorMapper:
    def __init__(self, gain, deadzone_dps, smoothing, x_sign, y_sign):
        self.gain, self.dz, self.beta = gain, deadzone_dps, smoothing
        self.sx_sign, self.sy_sign = x_sign, y_sign
        self.fx = self.fy = 0.0      # smoothed rates
        self.cx = self.cy = 0.0      # leftover fractions of a pixel

    @staticmethod
    def _deadzone(rate, dz):
        return 0.0 if abs(rate) < dz else rate

    def update(self, rate_x, rate_y, dt):
        """rate_x / rate_y in deg/s (bias already removed). Returns whole-pixel (dx, dy)."""
        rx = self._deadzone(self.sx_sign * rate_x, self.dz)
        ry = self._deadzone(self.sy_sign * rate_y, self.dz)
        self.fx = self.beta * self.fx + (1 - self.beta) * rx      # exponential smoothing
        self.fy = self.beta * self.fy + (1 - self.beta) * ry
        self.cx += self.gain * self.fx * dt
        self.cy += self.gain * self.fy * dt
        dx, dy = int(self.cx), int(self.cy)       # a USB/BLE mouse sends whole numbers
        self.cx -= dx                              # keep the remainder so slow motion is not lost
        self.cy -= dy
        return dx, dy
