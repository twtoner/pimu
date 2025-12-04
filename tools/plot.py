#!/usr/bin/env python3
"""Live plotter for IMU packets streamed through the Pi IMU server."""

from __future__ import annotations

import argparse
from collections import deque
from itertools import chain
from typing import Deque, Dict, List

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from pimu.client import ImuReader


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ip",
        default="127.0.0.1",
        help="IP address for the Pi IMU server (default: %(default)s)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5555,
        help="Port for the Pi IMU server (default: %(default)s)",
    )
    parser.add_argument(
        "--max-points",
        type=int,
        default=2000,
        help="Maximum number of samples retained per trace (default: %(default)s)",
    )
    parser.add_argument(
        "--window",
        type=float,
        default=5.0,
        help="Width of the time window to display in seconds (default: %(default)s)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    reader = ImuReader(args.ip, args.port)

    xs: Deque[float] = deque(maxlen=args.max_points)
    traces: Dict[str, Deque[float]] = {
        key: deque(maxlen=args.max_points)
        for key in ("ax", "ay", "az", "gx", "gy", "gz", "lag")
    }

    fig, axes = plt.subplots(3, 1, sharex=True, figsize=(12, 9))
    fig.suptitle("IMU Live Data")

    accel_lines: List = []
    gyro_lines: List = []
    lag_lines: List = []

    accel_labels = ("ax", "ay", "az")
    gyro_labels = ("gx", "gy", "gz")

    # NOTE: removed animated=True; we'll also use blit=False below so axes update
    for label in accel_labels:
        (line,) = axes[0].plot([], [], label=label)
        accel_lines.append(line)
    axes[0].set_ylabel("Accel (m/s^2)")
    axes[0].legend(loc="upper left")

    for label in gyro_labels:
        (line,) = axes[1].plot([], [], label=label)
        gyro_lines.append(line)
    axes[1].set_ylabel("Gyro (deg/s)")
    axes[1].legend(loc="upper left")

    (lag_line,) = axes[2].plot([], [], label="Lag (local - sensor)")
    lag_lines.append(lag_line)
    axes[2].set_ylabel("Lag (s)")
    axes[2].set_xlabel("Local timestamp (s)")
    axes[2].legend(loc="upper left")

    axis_groups = (
        (axes[0], accel_labels),
        (axes[1], gyro_labels),
        (axes[2], ("lag",)),
    )

    artists = tuple(chain(accel_lines, gyro_lines, lag_lines))
    last_ts = 0.0

    def init():
        for line in artists:
            line.set_data([], [])
        axes[0].set_xlim(0, args.window)
        return artists

    def update(_frame: int):
        nonlocal last_ts
        sample = reader.last_data
        if not sample.recv_ts or sample.recv_ts <= last_ts:
            return artists
        last_ts = sample.recv_ts

        xs.append(sample.recv_ts)
        traces["ax"].append(sample.ax)
        traces["ay"].append(sample.ay)
        traces["az"].append(sample.az)
        traces["gx"].append(sample.gx)
        traces["gy"].append(sample.gy)
        traces["gz"].append(sample.gz)
        traces["lag"].append(sample.recv_ts - sample.sensor_ts)

        x_vals = tuple(xs)
        y_vals = {label: tuple(traces[label]) for label in traces}

        # Determine window indices (only plot / autoscale visible window)
        if x_vals:
            xmax = x_vals[-1]
            xmin = xmax - args.window
            axes[-1].set_xlim(xmin, xmax)

            # indices of points in the visible window
            window_idx = [i for i, t in enumerate(x_vals) if t >= xmin]
        else:
            window_idx = []

        def windowed(series):
            if not window_idx:
                return []
            return [series[i] for i in window_idx if i < len(series)]

        # Update line data
        for label, line in zip(accel_labels, accel_lines):
            line.set_data(x_vals, y_vals[label])

        for label, line in zip(gyro_labels, gyro_lines):
            line.set_data(x_vals, y_vals[label])

        lag_lines[0].set_data(x_vals, y_vals["lag"])

        # Autoscale y for each axis group based on visible window
        for ax, labels in axis_groups:
            series = []
            for label in labels:
                series.extend(windowed(y_vals[label]))
            if not series:
                continue
            y_min = min(series)
            y_max = max(series)
            span = y_max - y_min
            padding = span * 0.1 if span else max(abs(y_min) * 0.1, 1e-3)
            ax.set_ylim(y_min - padding, y_max + padding)

        return artists

    plt.tight_layout()
    anim = FuncAnimation(
        fig,
        update,
        init_func=init,
        interval=50,
        blit=False,           # <- let Matplotlib redraw axes so y-limits update
        cache_frame_data=False,
    )
    plt.show()

    _ = anim


if __name__ == "__main__":
    main()
