#!/usr/bin/env python
"""Render Figs 3-6 (per-axis position + orientation) and Figs 7-8 (single
axis comparison with/without surface feedback) from CSVs produced by
record_experiment.py.

Plot style mimics the paper: estimate in orange overlaid on ground truth
in blue, with the optional `--baseline` series rendered in black for the
"with surface feedback" comparison.
"""
from __future__ import print_function

import argparse
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load(path):
    out = {}
    with open(path, "r") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            for k, v in row.items():
                out.setdefault(k, []).append(float(v))
    return out


def plot_six_panel(data, title, out_path):
    t = data["t"]
    fig, ax = plt.subplots(3, 2, figsize=(10, 8))
    ax[0, 0].plot(t, data["gt_x"], color="tab:blue", label="ground truth")
    ax[0, 0].plot(t, data["est_x"], color="tab:orange", label="estimate")
    ax[0, 0].set_ylabel("x [m]")

    ax[1, 0].plot(t, data["gt_y"], color="tab:blue")
    ax[1, 0].plot(t, data["est_y"], color="tab:orange")
    ax[1, 0].set_ylabel("y [m]")

    ax[2, 0].plot(t, data["gt_z"], color="tab:blue")
    ax[2, 0].plot(t, data["est_z"], color="tab:orange")
    ax[2, 0].set_ylabel("z [m]")
    ax[2, 0].set_xlabel("time [s]")

    ax[0, 1].plot(t, data["gt_roll"], color="tab:blue")
    ax[0, 1].plot(t, data["est_roll"], color="tab:orange")
    ax[0, 1].set_ylabel("roll [rad]")

    ax[1, 1].plot(t, data["gt_pitch"], color="tab:blue")
    ax[1, 1].plot(t, data["est_pitch"], color="tab:orange")
    ax[1, 1].set_ylabel("pitch [rad]")

    ax[2, 1].plot(t, data["gt_yaw"], color="tab:blue")
    ax[2, 1].plot(t, data["est_yaw"], color="tab:orange")
    ax[2, 1].set_ylabel("yaw [rad]")
    ax[2, 1].set_xlabel("time [s]")

    ax[0, 0].legend(loc="best")
    fig.suptitle(title)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    print("wrote", out_path)


def plot_axis_compare(with_data, no_fb_data, axis, title, out_path):
    fig, ax = plt.subplots(figsize=(9, 5))
    gt_key = "gt_" + axis
    est_key = "est_" + axis
    ax.plot(with_data["t"], with_data[gt_key],
            color="tab:blue", label="ground truth")
    if no_fb_data is not None:
        ax.plot(no_fb_data["t"], no_fb_data[est_key],
                color="tab:orange", label="estimate (no surface feedback)")
    ax.plot(with_data["t"], with_data[est_key],
            color="black", label="estimate (with surface feedback)")
    ax.set_xlabel("time [s]")
    ax.set_ylabel("%s [m]" % axis)
    ax.set_title(title)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    print("wrote", out_path)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", required=True, choices=["six", "compare"])
    p.add_argument("--csv", required=True)
    p.add_argument("--baseline", default=None,
                   help="(compare mode) CSV without surface feedback")
    p.add_argument("--axis", default="x")
    p.add_argument("--title", default="")
    p.add_argument("--out", required=True)
    args = p.parse_args()

    data = load(args.csv)
    if args.mode == "six":
        plot_six_panel(data, args.title, args.out)
    else:
        baseline = load(args.baseline) if args.baseline else None
        plot_axis_compare(data, baseline, args.axis, args.title, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
