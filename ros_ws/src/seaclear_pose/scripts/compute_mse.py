#!/usr/bin/env python
"""Read one or more CSVs produced by record_experiment.py and emit Tables
II/III/IV in the same format as the paper.

Usage:
    rosrun seaclear_pose compute_mse.py file1.csv [file2.csv ...] \
        [--labels lab1,lab2,...] [--out tables.txt]
"""
from __future__ import print_function

import argparse
import csv
import math
import os
import sys


def load(path):
    rows = []
    with open(path, "r") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            rows.append({k: float(v) for k, v in row.items()})
    return rows


def mse(rows, gt_key, est_key, angular=False):
    if not rows:
        return float("nan")
    s = 0.0
    n = 0
    for r in rows:
        d = r[est_key] - r[gt_key]
        if angular:
            d = math.atan2(math.sin(d), math.cos(d))
        s += d * d
        n += 1
    return s / n if n else float("nan")


def summarize(path):
    rows = load(path)
    cols = [
        ("X(m)",    "gt_x",     "est_x",     False),
        ("Y(m)",    "gt_y",     "est_y",     False),
        ("Z(m)",    "gt_z",     "est_z",     False),
        ("Roll",    "gt_roll",  "est_roll",  True),
        ("Pitch",   "gt_pitch", "est_pitch", True),
        ("Yaw",     "gt_yaw",   "est_yaw",   True),
    ]
    return [(name, mse(rows, gk, ek, ang)) for (name, gk, ek, ang) in cols]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("csvs", nargs="+")
    p.add_argument("--labels", default=None)
    p.add_argument("--out", default=None)
    args = p.parse_args()

    if args.labels:
        labels = args.labels.split(",")
    else:
        labels = [os.path.splitext(os.path.basename(c))[0] for c in args.csvs]
    if len(labels) != len(args.csvs):
        print("number of labels does not match number of csvs", file=sys.stderr)
        return 1

    headers = ["Configuration", "X(m)", "Y(m)", "Z(m)",
               "Roll(rad)", "Pitch(rad)", "Yaw(rad)"]
    lines = ["\t".join(headers)]
    for label, path in zip(labels, args.csvs):
        stats = summarize(path)
        cells = [label] + ["%g" % v for _, v in stats]
        lines.append("\t".join(cells))

    out = "\n".join(lines)
    print(out)
    if args.out:
        with open(args.out, "w") as fp:
            fp.write(out + "\n")
        print("wrote", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
