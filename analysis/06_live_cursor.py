"""STEP 8b - Move the real cursor.

  python analysis/06_live_cursor.py --replay            safe test: prints the moves from your recording
  python analysis/06_live_cursor.py --replay --move     moves your real cursor from the recording
  python analysis/06_live_cursor.py --serve --move      live: the phone streams data to this laptop

--serve starts a tiny web server. Set your phone app (for example Sensor Logger's "push to
server" option, check its current settings) to POST to  http://<laptop-ip>:8000.
Phone and laptop must be on the same Wi-Fi. If nothing moves, add --debug to print the raw
messages and adjust parse_message() to match what your app really sends.

SAFETY: pyautogui fail-safe is ON. Slam the mouse into a screen corner to stop the script.
"""
import argparse
import json
import math
import socket
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import numpy as np
import pandas as pd

import config
import fusion
from cursor import CursorMapper

AXIS = {"gx": 0, "gy": 1, "gz": 2}


def make_mover(enabled):
    if not enabled:
        return lambda dx, dy: None
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0
    return lambda dx, dy: pyautogui.moveRel(dx, dy, _pause=False) if (dx or dy) else None


def new_mapper():
    return CursorMapper(config.GAIN, config.DEADZONE_DPS, config.SMOOTHING, config.X_SIGN, config.Y_SIGN)


def replay(move):
    bias = np.array(fusion.load_cal()["bias_dps"])
    motion = pd.read_csv(config.PROCESSED / "motion_clean.csv")
    dt = motion.dt.iloc[0]
    mapper, mover = new_mapper(), make_mover(move)
    print("replaying recording in real time... (Ctrl+C to stop)")
    start = time.perf_counter()
    for i, row in enumerate(motion.itertuples(index=False)):
        while time.perf_counter() < start + i * dt:
            time.sleep(0.0005)
        rate = np.array([row.gx, row.gy, row.gz]) - bias
        dx, dy = mapper.update(rate[AXIS[config.X_FROM]], rate[AXIS[config.Y_FROM]], dt)
        if move:
            mover(dx, dy)
        elif (dx or dy) and i % 10 == 0:
            print(f"t={row.t:6.2f}s  dx={dx:+d}  dy={dy:+d}")
    print("done")


class Engine:
    """Boot calibration (hold the phone still), then rates -> cursor moves."""

    def __init__(self, move, calib_seconds=2.0):
        self.mapper, self.mover = new_mapper(), make_mover(move)
        self.calib_seconds, self.samples = calib_seconds, []
        self.bias = self.t0 = self.last_t = None

    def handle(self, t, rate_dps):
        rate_dps = np.asarray(rate_dps, float)
        if self.t0 is None:
            self.t0 = t
            print(f"Calibrating for {self.calib_seconds:.0f} s - keep the phone still...")
        if self.bias is None:
            self.samples.append(rate_dps)
            if t - self.t0 >= self.calib_seconds:
                self.bias = np.mean(self.samples, axis=0)
                print("bias (deg/s):", np.round(self.bias, 4), "- move your hand now")
            self.last_t = t
            return
        dt = t - self.last_t
        self.last_t = t
        if dt <= 0 or dt > 0.5:       # skip duplicate or stalled packets
            return
        rate = rate_dps - self.bias
        dx, dy = self.mapper.update(rate[AXIS[config.X_FROM]], rate[AXIS[config.Y_FROM]], dt)
        self.mover(dx, dy)


def parse_message(msg):
    """Sensor Logger style: {"payload": [{"name": "gyroscope", "time": <ns>, "values": {"x":..,"y":..,"z":..}}]}
    Yields (time_in_seconds, [gx, gy, gz] in deg/s). Edit here if your app sends something else."""
    for item in msg.get("payload", []):
        if "gyro" not in str(item.get("name", "")).lower():
            continue
        v = item.get("values", {})
        t = float(item.get("time", time.time()))
        t = t / 1e9 if t > 1e12 else t
        rad = [float(v.get(k, 0.0)) for k in "xyz"]
        scale = 180.0 / math.pi if config.GYRO_UNIT == "rad/s" else 1.0
        yield t, [r * scale for r in rad]


def local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def serve(port, move, debug):
    engine = Engine(move)
    shown = {"n": 0}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            self.send_response(200)
            self.end_headers()
            if debug and shown["n"] < 3:
                shown["n"] += 1
                print("RAW:", body[:600])
            try:
                for t, rate in parse_message(json.loads(body)):
                    engine.handle(t, rate)
            except Exception as e:   # never crash the server on one bad packet
                print("could not parse a message:", e)

        def log_message(self, *args):
            pass

    print(f"Listening on http://{local_ip()}:{port}  (put this URL in your phone app)")
    try:
        HTTPServer(("0.0.0.0", port), Handler).serve_forever()
    except KeyboardInterrupt:
        print("stopped")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--replay", action="store_true")
    p.add_argument("--serve", action="store_true")
    p.add_argument("--move", action="store_true", help="actually move the cursor")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--debug", action="store_true")
    a = p.parse_args()
    if a.serve:
        serve(a.port, a.move, a.debug)
    elif a.replay:
        replay(a.move)
    else:
        p.print_help()
