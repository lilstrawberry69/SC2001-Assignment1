#!/usr/bin/env python3
"""
SC2001 Project 1: Hybrid Merge Sort + Insertion Sort

Implements:
(a) Hybrid sort with threshold S
(b) Random dataset generation
(c) Empirical analysis of comparisons and CPU time
(d) Comparison against original Merge Sort
"""

# Tested with Python 3.x.
# Comparison-counting convention: count only data-key comparisons such as
# "a[i] <= a[j]" and "a[j] <= key". Index checks, loop bounds, assignments,
# and copying are not counted. Seeds, trials, and sizes are configurable at
# the top of this file.

import time
import random
import argparse
import shutil
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ============================================================================
# Configuration variables (used in experiments)
# ============================================================================

# S: threshold for switching to Insertion Sort in hybrid algorithm.
S_DEFAULT = 32

# X: maximum value for random integers. All keys are in [1, X].
X_MAX = 10_000_000

# Seeds for reproducible random data generation.
SEED_GROWTH = 20260901
SEED_THRESHOLD = 20260902
SEED_OPTIMAL_BASE = 20260903
SEED_COMPARE = 20260904

# Sizes for growth experiment (c)(i).
SIZES_FULL = [1_000, 10_000, 100_000, 1_000_000, 10_000_000]
SIZES_SMALL = [1_000, 10_000, 100_000]

# Sizes for optimal-S experiment (c)(iii).
OPTIMAL_SIZES_FULL = [100_000, 1_000_000, 10_000_000]
OPTIMAL_SIZES_SMALL = [5_000, 20_000, 100_000]

# Threshold values to test in experiments (c)(ii) and (c)(iii).
THRESHOLDS = [1, 2, 4, 8, 12, 16, 24, 32, 48, 64, 96, 128]
OPTIMAL_THRESHOLDS = [4, 8, 12, 16, 24, 32, 48, 64, 96]

# Number of trials per configuration.
# Full runs use multiple trials so plots can report medians; small runs are
# intentionally quick smoke tests and use one trial.
TRIALS_FULL = 3
TRIALS_SMALL = 1

# Experiment size for threshold sweep (c)(ii).
N_THRESHOLD_FULL = 1_000_000
N_THRESHOLD_SMALL = 20_000

# Experiment size for final comparison (d).
N_COMPARE_FULL = 10_000_000
N_COMPARE_SMALL = 100_000


# ============================================================================
# Core sorting algorithms
# ============================================================================

def insertion_sort(a, left, right, counters, trace=False):
    """
    In-place insertion sort on a[left..right], counting key comparisons.

    Parameters:
        a: list of integers to sort
        left: left index of the subarray to sort
        right: right index of the subarray to sort
        counters: dict with key "comparisons" to count key comparisons
        trace: if True, print each key comparison for debugging
    """
    for i in range(left + 1, right + 1):
        key = a[i]
        j = i - 1

        while j >= left:
            # Count only data-key comparisons; index checks are not counted.
            counters["comparisons"] += 1
            if trace:
                print(f"compare: a[{j}]={a[j]} <= key={key} ?")

            if a[j] <= key:
                break

            a[j + 1] = a[j]
            j -= 1

        a[j + 1] = key


def merge_ranges(a, temp, left, mid, right, counters, trace=False):
    """
    Merge two sorted runs a[left..mid] and a[mid+1..right] into temp, then copy back.

    Parameters:
        a: list of integers (both runs are already sorted)
        temp: temporary list of same length as a
        left: left index of the first run
        mid: right index of the first run
        right: right index of the second run
        counters: dict with key "comparisons" to count key comparisons
        trace: if True, print each key comparison for debugging
    """
    i, j, k = left, mid + 1, left

    while i <= mid and j <= right:
        # Count only data-key comparisons; index checks are not counted.
        counters["comparisons"] += 1
        if trace:
            print(f"compare: a[{i}]={a[i]} <= a[{j}]={a[j]} ?")

        if a[i] <= a[j]:
            temp[k] = a[i]
            i += 1
        else:
            temp[k] = a[j]
            j += 1

        k += 1

    while i <= mid:
        temp[k] = a[i]
        i += 1
        k += 1

    while j <= right:
        temp[k] = a[j]
        j += 1
        k += 1

    for p in range(left, right + 1):
        a[p] = temp[p]


def hybrid_recursive(a, temp, left, right, S, counters, trace=False):
    """
    Recursive hybrid sort: switch to insertion sort when subarray size <= S.

    Parameters:
        a: list of integers to sort
        temp: temporary list for merging
        left: left index of current subarray
        right: right index of current subarray
        S: threshold for switching to insertion sort
        counters: dict with key "comparisons" to count key comparisons
        trace: if True, print comparisons for debugging
    """
    if left >= right:
        return

    if right - left + 1 <= S:
        insertion_sort(a, left, right, counters, trace=trace)
        return

    mid = left + (right - left) // 2

    hybrid_recursive(a, temp, left, mid, S, counters, trace=trace)
    hybrid_recursive(a, temp, mid + 1, right, S, counters, trace=trace)
    merge_ranges(a, temp, left, mid, right, counters, trace=trace)


def hybrid_sort(a, S, trace=False):
    """
    Hybrid Merge/Insertion sort.

    Parameters:
        a: list of integers to sort
        S: threshold for switching to insertion sort
        trace: if True, print comparison tracing for debugging

    Returns:
        dict with key "comparisons" and value = number of key comparisons
    """
    if S < 1:
        raise ValueError("S must be at least 1")

    counters = {"comparisons": 0}

    if not a:
        return counters

    temp = [0] * len(a)
    hybrid_recursive(a, temp, 0, len(a) - 1, S, counters, trace=trace)

    return counters


def merge_recursive(a, temp, left, right, counters):
    """
    Classic recursive Merge Sort.

    Parameters:
        a: list of integers to sort
        temp: temporary list for merging
        left: left index of current subarray
        right: right index of current subarray
        counters: dict with key "comparisons" to count key comparisons
    """
    if left >= right:
        return

    mid = left + (right - left) // 2

    merge_recursive(a, temp, left, mid, counters)
    merge_recursive(a, temp, mid + 1, right, counters)
    merge_ranges(a, temp, left, mid, right, counters)


def original_merge_sort(a):
    """
    Original Merge Sort implementation.

    Parameters:
        a: list of integers to sort

    Returns:
        dict with key "comparisons" and value = number of key comparisons
    """
    counters = {"comparisons": 0}

    if not a:
        return counters

    temp = [0] * len(a)
    merge_recursive(a, temp, 0, len(a) - 1, counters)

    return counters


# ============================================================================
# Data generation and measurement
# ============================================================================

def make_dataset(n, x, seed):
    """
    Generate n random integers in [1, x] using a seeded RNG.

    Parameters:
        n: number of integers to generate
        x: maximum value (inclusive)
        seed: seed for the random generator

    Returns:
        list of n random integers
    """
    rng = random.Random(seed)
    return [rng.randint(1, x) for _ in range(n)]


def measure(original, sort_function):
    """
    Run sort_function on a copy of original.
    Return comparisons, CPU time, wall time, and sortedness check.

    Parameters:
        original: list of integers to sort (will not be modified)
        sort_function: function that takes a list and returns a dict with "comparisons"

    Returns:
        dict with keys:
            "comparisons": number of key comparisons
            "cpu_seconds": CPU time used by the sort
            "wall_seconds": elapsed wall-clock time
            "sorted": True if result is sorted, False otherwise
    """
    working = original[:]

    cpu_start = time.process_time()
    wall_start = time.perf_counter()

    counters = sort_function(working)

    cpu_end = time.process_time()
    wall_end = time.perf_counter()

    return {
        "comparisons": counters["comparisons"],
        "cpu_seconds": cpu_end - cpu_start,
        "wall_seconds": wall_end - wall_start,
        "sorted": all(
            working[i] <= working[i + 1]
            for i in range(len(working) - 1)
        )
    }


def print_timing_diagnostics():
    """Print the clocks and trial policy used by the experiments."""
    cpu_clock = time.get_clock_info("process_time")
    wall_clock = time.get_clock_info("perf_counter")

    print("Timing diagnostics")
    print(
        f"CPU clock: {cpu_clock.implementation}, resolution={cpu_clock.resolution:g}s")
    print(
        f"Wall clock: {wall_clock.implementation}, resolution={wall_clock.resolution:g}s")
    print(
        f"Full-run trials per configuration: {TRIALS_FULL} (median in plotter)")
    print(f"Small-run trials per configuration: {TRIALS_SMALL}")
    print("Timed region: sort call only; copying and sortedness validation are excluded.")


def run_correctness_tests():
    """Run a small deterministic correctness check for merge and hybrid sort."""
    cases = [
        [],
        [1],
        [2, 2, 2],
        [1, 2, 3],
        [3, 2, 1],
        [4, 1, 3, 2],
    ]
    sort_variants = [
        ("original_merge_sort", original_merge_sort),
        ("hybrid_sort_S=1", lambda a: hybrid_sort(a, 1)),
        ("hybrid_sort_S=2", lambda a: hybrid_sort(a, 2)),
        ("hybrid_sort_S=4", lambda a: hybrid_sort(a, 4)),
    ]

    total = 0
    passed = 0

    for arr in cases:
        for _, sort_fn in sort_variants:
            total += 1
            working = arr[:]
            result = sort_fn(working)
            if sorted(working) != sorted(arr):
                raise AssertionError(
                    f"Sorting failed for {arr!r} with {sort_fn!r}")
            if result.get("comparisons", 0) < 0:
                raise AssertionError(f"Negative comparison count for {arr!r}")
            passed += 1

    print(
        f"Correctness tests passed: {passed}/{total} cases, 1 merge + 3 hybrid variants.")


def trace_hybrid_on_small_array():
    """Use trace mode on a 4-element example for teaching the hybrid algorithm."""
    a = [4, 1, 3, 2]
    result = hybrid_sort(a, S=2, trace=False)
    print(f"Final array: {a}")
    print(f"Total comparisons: {result['comparisons']}")


# ============================================================================
# Experiment runners
# ============================================================================

def run_growth(full, trials=None):
    """
    Experiment (c)(i): comparisons vs n with fixed S.

    Parameters:
        full: if True, use full range of sizes and trials; otherwise small subset

    Returns:
        list of result tuples
    """
    sizes = SIZES_FULL if full else SIZES_SMALL
    S = S_DEFAULT
    x = X_MAX
    trials = trials if trials is not None else (
        TRIALS_FULL if full else TRIALS_SMALL)

    rows = []

    for n in sizes:
        data = make_dataset(n, x, SEED_GROWTH + n)

        for trial in range(1, trials + 1):
            m = measure(data, lambda a, S=S: hybrid_sort(a, S))

            rows.append((
                "growth", "hybrid", n, S, SEED_GROWTH + n, trial,
                m["comparisons"], m["cpu_seconds"], m["wall_seconds"], m["sorted"]
            ))

            if not m["sorted"]:
                raise RuntimeError("Sorting failed")

    return rows


def run_threshold(full, trials=None):
    """
    Experiment (c)(ii): comparisons and CPU time vs S for fixed n.

    Parameters:
        full: if True, use large n and more trials; otherwise small subset

    Returns:
        list of result tuples
    """
    n = N_THRESHOLD_FULL if full else N_THRESHOLD_SMALL
    thresholds = THRESHOLDS
    x = X_MAX
    trials = trials if trials is not None else (
        TRIALS_FULL if full else TRIALS_SMALL)
    seed = SEED_THRESHOLD

    # Generate one base array for the complete threshold sweep. measure()
    # copies it before sorting, so every S and trial sees identical input data.
    base_data = make_dataset(n, x, seed)

    rows = []

    for S in thresholds:
        for trial in range(1, trials + 1):
            m = measure(base_data, lambda a, S=S: hybrid_sort(a, S))

            rows.append((
                "threshold", "hybrid", n, S, seed, trial,
                m["comparisons"], m["cpu_seconds"], m["wall_seconds"], m["sorted"]
            ))

            if not m["sorted"]:
                raise RuntimeError("Sorting failed")

    return rows


def run_optimal(full, trials=None):
    """
    Experiment (c)(iii): CPU time vs S for several n to select optimal S.

    Parameters:
        full: if True, use large sizes and more trials; otherwise small subset

    Returns:
        list of result tuples
    """
    sizes = OPTIMAL_SIZES_FULL if full else OPTIMAL_SIZES_SMALL
    thresholds = OPTIMAL_THRESHOLDS
    x = X_MAX
    trials = trials if trials is not None else (
        TRIALS_FULL if full else TRIALS_SMALL)

    rows = []

    for n in sizes:
        seed = SEED_OPTIMAL_BASE + n
        data = make_dataset(n, x, seed)

        for S in thresholds:
            for trial in range(1, trials + 1):
                m = measure(data, lambda a, S=S: hybrid_sort(a, S))

                rows.append((
                    "optimal", "hybrid", n, S, seed, trial,
                    m["comparisons"], m["cpu_seconds"], m["wall_seconds"], m["sorted"]
                ))

                if not m["sorted"]:
                    raise RuntimeError("Sorting failed")

    return rows


def run_compare(full, chosen_S, trials=None):
    """
    Experiment (d): original Merge Sort vs hybrid on large dataset.

    Parameters:
        full: if True, use 10 million integers; otherwise smaller
        chosen_S: selected threshold value for hybrid sort

    Returns:
        list of result tuples
    """
    n = N_COMPARE_FULL if full else N_COMPARE_SMALL
    x = X_MAX
    trials = trials if trials is not None else (
        TRIALS_FULL if full else TRIALS_SMALL)
    seed = SEED_COMPARE

    data = make_dataset(n, x, seed)

    rows = []

    for algo_name, sort_fn in [
        ("merge", lambda a: original_merge_sort(a)),
        ("hybrid", lambda a: hybrid_sort(a, chosen_S))
    ]:
        for trial in range(1, trials + 1):
            m = measure(data, sort_fn)

            rows.append((
                "comparison", algo_name, n,
                1 if algo_name == "merge" else chosen_S,
                seed, trial,
                m["comparisons"], m["cpu_seconds"], m["wall_seconds"], m["sorted"]
            ))

            if not m["sorted"]:
                raise RuntimeError("Sorting failed")

    return rows


def run_all(full, chosen_S, trials=3):
    """
    Run all experiments.

    Parameters:
        full: if True, use full dataset sizes and trials
        chosen_S: selected threshold value for hybrid sort

    Returns:
        list of result tuples
    """
    rows = []
    rows.extend(run_growth(full, trials))
    rows.extend(run_threshold(full, trials))
    rows.extend(run_optimal(full, trials))
    rows.extend(run_compare(full, chosen_S, trials))
    return rows


# ============================================================================
# Main entry point
# ============================================================================

def preserve_preliminary_outputs():
    """Keep the first one-trial outputs before a later run overwrites them."""
    output_names = {
        "results.csv": "results_preliminary_one_trial.csv",
        "summary.csv": "summary_preliminary_one_trial.csv",
        "optimal_thresholds.csv": "optimal_thresholds_preliminary_one_trial.csv",
    }
    for source_name, backup_name in output_names.items():
        source = BASE_DIR / source_name
        backup = BASE_DIR / backup_name
        if source.exists() and not backup.exists():
            shutil.copy2(source, backup)


def parse_arguments():
    """Parse experiment mode, size selection, trial count, and hybrid S."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode", nargs="?", default="all",
        choices=["all", "growth", "threshold", "optimal", "compare",
                 "test", "diagnostics"],
    )
    size_group = parser.add_mutually_exclusive_group()
    size_group.add_argument("--small", action="store_true")
    size_group.add_argument("--full", action="store_true")
    parser.add_argument("--trials", type=int, default=None)
    parser.add_argument("--S", dest="chosen_S", type=int, default=S_DEFAULT)
    args = parser.parse_args()
    if args.trials is not None and args.trials < 1:
        parser.error("--trials must be at least 1")
    return args


def warn_about_comparison_variation(rows):
    """Report unexpected comparison-count variation across repeated trials."""
    grouped = {}
    for row in rows:
        key = (row[0], row[1], row[2], row[3], row[4])
        grouped.setdefault(key, set()).add(row[6])
    for key, values in grouped.items():
        if len(values) > 1:
            print(f"WARNING: comparisons vary for {key}: {sorted(values)}")


if __name__ == "__main__":
    args = parse_arguments()
    full = args.full
    trials = args.trials if args.trials is not None else (
        TRIALS_FULL if full else TRIALS_SMALL)

    if args.mode == "test":
        run_correctness_tests()
        raise SystemExit(0)

    if args.mode == "diagnostics":
        print_timing_diagnostics()
        raise SystemExit(0)

    if args.mode == "optimal":
        sizes = OPTIMAL_SIZES_FULL if full else OPTIMAL_SIZES_SMALL
        print(f"Mode: {'full' if full else 'small'}")
        print(f"n values: {sizes}")
        print(f"S values: {OPTIMAL_THRESHOLDS}")
        print(f"Seeds: {[SEED_OPTIMAL_BASE + n for n in sizes]}")
        print(f"Trials per (n, S): {trials}")

    rows = []

    if args.mode in ("growth", "all"):
        rows.extend(run_growth(full, trials))

    if args.mode in ("threshold", "all"):
        rows.extend(run_threshold(full, trials))

    if args.mode in ("optimal", "all"):
        rows.extend(run_optimal(full, trials))

    if args.mode in ("compare", "all"):
        rows.extend(run_compare(full, args.chosen_S, trials))

    for row in rows:
        if not row[9]:
            raise RuntimeError("Sorting failed")
    warn_about_comparison_variation(rows)
    preserve_preliminary_outputs()

    output_path = BASE_DIR / "results.csv"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(
            "experiment,algorithm,n,S,seed,trial,"
            "comparisons,cpu_seconds,wall_seconds,sorted\n"
        )

        for r in rows:
            f.write(",".join(str(v) for v in r) + "\n")

    print(f"Results written to {output_path}")
