#!/usr/bin/env python3
"""Create presentation-ready charts from the SC2001 experiment results."""

import pandas as pd
import numpy as np
from matplotlib.patches import Patch
import matplotlib.pyplot as plt
from pathlib import Path

import matplotlib
matplotlib.use("Agg")


BASE_DIR = Path(__file__).resolve().parent
INPUT = BASE_DIR / "results.csv"
OUT = BASE_DIR / "figures"
OUT.mkdir(exist_ok=True, parents=True)


# Shared visual theme.
CHART_BG = "#F4EADF"
PLOT_BG = "#F8F0E8"
GRID_COLOR = "#B9B2AA"
TEXT_COLOR = "#111111"
BLUE = "#3656A8"
RED = "#D83A2E"
YELLOW = "#F4DB67"
ORANGE = "#E38A2F"
GRAY = "#77716B"

FONT = "DejaVu Sans"
LINE_WIDTH = 3.0
MARKER_SIZE = 7
NEAR_OPTIMAL_TOLERANCE_PCT = 2.0


def style_axis(ax):
    """Apply the shared infographic styling to one axes object."""
    ax.set_facecolor(PLOT_BG)
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.8, alpha=0.55)
    ax.grid(axis="x", visible=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(GRID_COLOR)
    ax.tick_params(axis="both", length=0, colors=TEXT_COLOR, pad=7)
    ax.set_axisbelow(True)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontname(FONT)
        label.set_color(TEXT_COLOR)


def format_large_number(value):
    """Format a count compactly for chart annotations."""
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:.0f}"


def format_seconds(value):
    """Format CPU seconds without hiding small measured values."""
    return f"{value:.3f}s"


def add_value_labels(ax, bars, values, formatter=format_large_number):
    """Place compact values above a collection of bars."""
    for bar, value in zip(bars, values):
        ax.annotate(
            formatter(value),
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 6),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
            color=TEXT_COLOR,
            fontname=FONT,
        )


def style_line(ax, x, y, color, label):
    """Plot measured values with consistent rounded line styling."""
    return ax.plot(
        x,
        y,
        color=color,
        linewidth=LINE_WIDTH,
        marker="o",
        markersize=MARKER_SIZE,
        markerfacecolor=color,
        markeredgecolor=PLOT_BG,
        markeredgewidth=1.2,
        solid_capstyle="round",
        solid_joinstyle="round",
        alpha=0.95,
        label=label,
    )[0]


def finish_figure(fig, filename):
    """Apply figure-level typography and save a slide-friendly PNG."""
    fig.patch.set_facecolor(CHART_BG)
    fig.savefig(
        OUT / filename,
        dpi=240,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )
    plt.close(fig)


def add_header(fig, title, subtitle, y=0.965):
    """Add the large title and quiet dynamic subtitle used by each chart."""
    fig.text(
        0.06,
        y,
        title,
        ha="left",
        va="top",
        fontsize=19,
        fontweight="bold",
        color=TEXT_COLOR,
        fontname=FONT,
    )
    fig.text(
        0.06,
        y - 0.062,
        subtitle,
        ha="left",
        va="top",
        fontsize=9.5,
        color=GRAY,
        fontname=FONT,
    )


def add_legend(fig, handles, labels, y=0.035):
    """Add a clean bottom legend with rectangular color swatches."""
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, y),
        ncol=max(1, min(len(labels), 3)),
        frameon=False,
        handlelength=1.3,
        handletextpad=0.5,
        columnspacing=1.5,
        fontsize=9,
        labelcolor=TEXT_COLOR,
        prop={"family": FONT},
    )


def add_takeaway(fig, text, y=0.005):
    fig.text(
        0.06,
        y,
        text,
        ha="left",
        va="bottom",
        fontsize=9,
        color=TEXT_COLOR,
        fontname=FONT,
    )


if not INPUT.exists():
    raise FileNotFoundError(
        f"Expected results file at {INPUT}. Run the sorting experiment first."
    )

df = pd.read_csv(INPUT)
if not df["sorted"].all():
    raise ValueError("At least one sorting run failed validation")

summary = (df.groupby(["experiment", "algorithm", "n", "S"], as_index=False)
             .agg(comparisons=("comparisons", "median"),
                  cpu_seconds=("cpu_seconds", "median"),
                  wall_seconds=("wall_seconds", "median"),
                  trial_count=("trial", "nunique")))
summary.to_csv(BASE_DIR / "summary.csv", index=False)
trial_count = int(df["trial"].nunique())
trial_note = ("Preliminary data: one trial per configuration"
              if trial_count == 1
              else f"Median of {trial_count} trials per configuration")

# (c)(i): comparisons vs n
growth = summary[summary.experiment == "growth"].sort_values("n")
if not growth.empty:
    x = growth["n"].to_numpy(float)
    y = growth["comparisons"].to_numpy(float)
    growth_s_values = growth["S"].unique()
    growth_s = ", ".join(str(int(value)) for value in growth_s_values)

    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    style_axis(ax)
    measured = style_line(ax, x, y, BLUE, "Measured hybrid sort")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Input size, n", color=TEXT_COLOR, labelpad=10,
                  fontname=FONT)
    ax.set_ylabel("Key comparisons", color=TEXT_COLOR, labelpad=10,
                  fontname=FONT)

    handles = [measured]
    labels = ["Measured hybrid sort"]
    if len(x) >= 2 and np.all(y > 0):
        basis = x * np.log2(x)
        fit_a, fit_b = np.polyfit(basis, y, 1)
        fitted = ax.plot(
            x,
            fit_a * basis + fit_b,
            color=ORANGE,
            linewidth=2.0,
            linestyle=(0, (5, 4)),
            solid_capstyle="round",
            label="Linear fit to n log2(n)",
        )[0]
        handles.append(fitted)
        labels.append("Linear fit to n log2(n)")

    add_header(fig, "KEY COMPARISONS VS INPUT SIZE",
               f"Hybrid sort, tested S = {growth_s}  |  {trial_note}")
    add_legend(fig, handles, labels)
    add_takeaway(
        fig, "Takeaway: measured comparisons follow an approximately n log n trend.")
    fig.subplots_adjust(left=0.10, right=0.97, top=0.78, bottom=0.22)
    finish_figure(fig, "01_comparisons_vs_n.png")

# (c)(ii): comparisons and CPU time vs S
threshold_rows = df[df.experiment == "threshold"].copy()
threshold = summary[summary.experiment == "threshold"].sort_values("S")
if not threshold.empty:
    threshold_n = int(threshold["n"].iloc[0])
    s_values = threshold["S"].astype(int).tolist()
    x_pos = np.arange(len(s_values))
    threshold_trial_count = int(threshold_rows["trial"].nunique())
    threshold_trial_note = (
        f"Fixed n = {threshold_n:,} | Preliminary: one timing run per threshold"
        if threshold_trial_count == 1
        else (
            f"Fixed n = {threshold_n:,} | CPU time shown as median across "
            f"{threshold_trial_count} trials per threshold"
        )
    )
    fig, axes = plt.subplots(2, 1, figsize=(10.5, 6.8), sharex=True)
    for ax in axes:
        style_axis(ax)
    comparison_values = threshold["comparisons"].to_numpy(float)
    cpu_values = threshold["cpu_seconds"].to_numpy(float)
    comparison_line = style_line(
        axes[0], x_pos, comparison_values, BLUE, "Key comparisons")
    time_line = style_line(
        axes[1], x_pos, cpu_values, RED, "CPU time")
    axes[0].set_ylabel("Key comparisons", color=TEXT_COLOR, fontname=FONT)
    axes[1].set_ylabel("CPU time (s)", color=TEXT_COLOR, fontname=FONT)
    axes[1].set_xlabel("Threshold, S", color=TEXT_COLOR, labelpad=10,
                       fontname=FONT)
    axes[0].set_title("KEY COMPARISONS VS THRESHOLD S", loc="left",
                      fontsize=11, fontweight="bold", color=TEXT_COLOR,
                      pad=12, fontname=FONT)
    axes[1].set_title("CPU TIME VS THRESHOLD S", loc="left",
                      fontsize=11, fontweight="bold", color=TEXT_COLOR,
                      pad=12, fontname=FONT)
    axes[1].set_xticks(x_pos)
    axes[1].set_xticklabels([str(value) for value in s_values],
                            rotation=45, ha="right")
    add_header(fig, "THRESHOLD S: COMPARISONS AND CPU TIME",
               threshold_trial_note, y=0.99)
    add_legend(fig, [comparison_line, time_line],
               ["Key comparisons", "CPU time"], y=0.015)
    lowest_index = int(np.argmin(cpu_values))
    lowest_s = s_values[lowest_index]
    lowest_note = (
        f"Lowest observed time, S = {lowest_s} (one run)"
        if threshold_trial_count == 1
        else f"Lowest measured median, S = {lowest_s}"
    )
    if threshold_trial_count >= 3:
        cpu_groups = threshold_rows.groupby("S")["cpu_seconds"]
        q1 = cpu_groups.quantile(0.25).reindex(s_values).to_numpy(float)
        q3 = cpu_groups.quantile(0.75).reindex(s_values).to_numpy(float)
        axes[1].errorbar(
            x_pos,
            cpu_values,
            yerr=np.vstack((cpu_values - q1, q3 - cpu_values)),
            fmt="none",
            ecolor=RED,
            elinewidth=1.0,
            capsize=3,
            alpha=0.55,
            zorder=2,
        )
    add_takeaway(fig, f"{lowest_note}  |  Larger S shifts work toward insertion sort.",
                 y=-0.015)
    fig.subplots_adjust(left=0.10, right=0.97, top=0.79,
                        bottom=0.17, hspace=0.48)
    finish_figure(fig, "02_effect_of_S.png")

# (c)(iii): repeated CPU time vs S for each n
optimal = summary[summary.experiment == "optimal"].sort_values(["n", "S"])
optimal_rows = df[df.experiment == "optimal"].copy()
if not optimal.empty:
    group_counts = (optimal_rows.groupby(["n", "S"])["trial"]
                    .nunique())
    repeated_trials = bool(
        len(group_counts) > 0
        and group_counts.min() >= 3
        and group_counts.nunique() == 1
    )
    displayed_trial_counts = group_counts.to_numpy()
    if repeated_trials:
        optimal_status = (
            f"CPU time shown as median across {int(group_counts.iloc[0])} "
            "trials per threshold"
        )
    elif len(set(displayed_trial_counts)) == 1 and len(displayed_trial_counts):
        count = int(displayed_trial_counts[0])
        optimal_status = (
            "Preliminary: one timing run per threshold"
            if count == 1 else "Repeated trials below the three-trial IQR threshold"
        )
    else:
        optimal_status = "Mixed trial counts; see raw results"

    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    style_axis(ax)
    colors = [BLUE, RED, ORANGE, GRAY, "#5C8D89", "#9B59B6"]
    handles = []
    labels = []
    near_ranges = []
    annotation_offsets = [(8, 10), (0, -18), (-8, 10)]
    for series_index, (color, (n, group)) in enumerate(
            zip(colors, optimal.groupby("n"))):
        n_label = format_large_number(n)
        line = style_line(ax, group["S"], group["cpu_seconds"], color,
                          f"n = {n_label}")
        handles.append(line)
        labels.append(f"n = {n_label}")
        minimum = group.loc[group["cpu_seconds"].idxmin()]
        best_index = int(np.argmin(group["cpu_seconds"].to_numpy()))
        best_s = group["S"].astype(int).tolist()[best_index]
        slowdown = 100 * (group["cpu_seconds"] / minimum["cpu_seconds"] - 1)
        near_s = group.loc[slowdown <=
                           NEAR_OPTIMAL_TOLERANCE_PCT, "S"].astype(int)
        near_ranges.append((n_label, near_s.tolist()))
        ax.scatter(
            [minimum["S"]], [minimum["cpu_seconds"]], marker="*", s=125,
            color=YELLOW, edgecolor=TEXT_COLOR, linewidth=0.8, zorder=5,
        )
        if repeated_trials:
            best_note = f"Lowest measured median\nS = {best_s}"
        else:
            best_note = f"Lowest observed time\nS = {best_s} (one run)"
        ax.annotate(
            best_note,
            xy=(minimum["S"], minimum["cpu_seconds"]),
            xytext=annotation_offsets[series_index % len(annotation_offsets)],
            textcoords="offset points",
            ha="left" if series_index % 3 == 0 else "center",
            va="bottom" if series_index % 3 != 1 else "top",
            fontsize=8, color=TEXT_COLOR, fontname=FONT,
        )
        if repeated_trials:
            raw_group = optimal_rows[
                (optimal_rows["n"] == n) & (optimal_rows["S"].isin(group["S"]))
            ]
            q1 = raw_group.groupby("S")["cpu_seconds"].quantile(0.25)
            q3 = raw_group.groupby("S")["cpu_seconds"].quantile(0.75)
            medians = group.set_index("S")["cpu_seconds"]
            yerr = np.vstack((medians - q1, q3 - medians))
            ax.errorbar(
                group["S"], group["cpu_seconds"], yerr=yerr,
                fmt="none", ecolor=color, elinewidth=1.0, capsize=3,
                alpha=0.48, zorder=2,
            )
    ax.set_xlabel("Threshold, S", color=TEXT_COLOR, labelpad=10,
                  fontname=FONT)
    ax.set_ylabel("Median CPU time (s)", color=TEXT_COLOR, labelpad=10,
                  fontname=FONT)
    add_header(fig, "CPU TIME ACROSS THRESHOLD VALUES",
               f"{optimal_status}  |  Lowest measured median among tested thresholds")
    add_legend(fig, handles, labels)
    footnote = ("Marker = median CPU time; whisker = interquartile range"
                if repeated_trials else optimal_status)
    add_takeaway(fig, footnote)
    fig.subplots_adjust(left=0.10, right=0.97, top=0.78, bottom=0.22)
    optimal_best = (optimal.loc[optimal.groupby("n")["cpu_seconds"].idxmin()]
                    .sort_values("n").copy())
    optimal_best["near_optimal_S"] = [
        ", ".join(str(value) for value in values) for _, values in near_ranges
    ]
    optimal_best.to_csv(BASE_DIR / "optimal_thresholds.csv", index=False)
    finish_figure(fig, "03_optimal_S.png")

    # Relative slowdown makes close medians and near-optimal tested ranges visible.
    fig, slowdown_ax = plt.subplots(figsize=(10.5, 6.2))
    style_axis(slowdown_ax)
    slowdown_handles = []
    slowdown_labels = []
    for color, (n, group) in zip(colors, optimal.groupby("n")):
        best_cpu = group["cpu_seconds"].min()
        slowdown_pct = 100 * (group["cpu_seconds"] / best_cpu - 1)
        line = style_line(slowdown_ax, group["S"], slowdown_pct, color,
                          f"n = {format_large_number(n)}")
        slowdown_handles.append(line)
        slowdown_labels.append(f"n = {format_large_number(n)}")
    slowdown_ax.axhline(0, color=GRID_COLOR, linewidth=1.0)
    slowdown_ax.set_xlabel("Threshold, S", color=TEXT_COLOR, labelpad=10,
                           fontname=FONT)
    slowdown_ax.set_ylabel(
        "CPU slowdown relative to lowest measured median (%)",
        color=TEXT_COLOR, labelpad=10, fontname=FONT,
    )
    add_header(fig, "SENSITIVITY TO THRESHOLD S", optimal_status)
    add_legend(fig, slowdown_handles, slowdown_labels)
    add_takeaway(
        fig,
        "Thresholds close to 0% form a near-optimal region; larger slowdowns indicate a less robust choice.",
    )
    fig.subplots_adjust(left=0.12, right=0.97, top=0.78, bottom=0.22)
    finish_figure(fig, "03b_relative_slowdown.png")

    for n_label, values in near_ranges:
        prefix = "Preliminary near-minimum range" if not repeated_trials else (
            "Near-optimal tested range"
        )
        suffix = "; repeat trials required" if not repeated_trials else ""
        print(
            f"{prefix} for n={n_label} (within {NEAR_OPTIMAL_TOLERANCE_PCT:.0f}%): "
            f"S = {', '.join(str(value) for value in values)}{suffix}"
        )

# (d): original merge vs hybrid
comparison = summary[summary.experiment == "comparison"].copy()
if not comparison.empty:
    comparison = comparison.sort_values("algorithm")
    comparison_n = int(comparison["n"].max())
    hybrid_rows = comparison[comparison.algorithm == "hybrid"]
    hybrid_s = int(hybrid_rows["S"].iloc[0]) if not hybrid_rows.empty else None
    labels = [
        "Original\nMerge Sort" if algorithm == "merge"
        else f"Hybrid Sort\nS = {int(s)}"
        for algorithm, s in zip(comparison.algorithm, comparison.S)
    ]
    colors = [GRAY if algorithm == "merge" else BLUE
              for algorithm in comparison.algorithm]

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 5.9))
    for ax in axes:
        style_axis(ax)
    bars_comparison = axes[0].bar(labels, comparison["comparisons"],
                                  color=colors, width=0.55)
    bars_time = axes[1].bar(labels, comparison["cpu_seconds"],
                            color=colors, width=0.55)
    add_value_labels(axes[0], bars_comparison, comparison["comparisons"])
    add_value_labels(axes[1], bars_time,
                     comparison["cpu_seconds"], format_seconds)
    axes[0].set_title("KEY COMPARISONS", loc="left", fontsize=11,
                      fontweight="bold", color=TEXT_COLOR, pad=14,
                      fontname=FONT)
    axes[1].set_title("CPU TIME", loc="left", fontsize=11,
                      fontweight="bold", color=TEXT_COLOR, pad=14,
                      fontname=FONT)
    axes[0].set_ylabel("Key comparisons", color=TEXT_COLOR, fontname=FONT)
    axes[1].set_ylabel("Median CPU time (s)", color=TEXT_COLOR, fontname=FONT)
    axes[0].set_ylim(0, comparison["comparisons"].max() * 1.22)
    axes[1].set_ylim(0, comparison["cpu_seconds"].max() * 1.30)
    legend_handles = [
        Patch(facecolor=GRAY, label="Original Merge Sort"),
        Patch(facecolor=BLUE, label=(f"Hybrid Sort (S = {hybrid_s})"
                                     if hybrid_s is not None else "Hybrid Sort")),
    ]
    add_header(fig, "ORIGINAL MERGE SORT VS HYBRID",
               f"Comparison at n = {comparison_n:,}  |  {trial_note}")
    add_legend(fig, legend_handles, [handle.get_label()
               for handle in legend_handles])
    add_takeaway(
        fig, "Takeaway: CPU time and comparison count measure different performance costs.")
    fig.subplots_adjust(left=0.09, right=0.97, top=0.76,
                        bottom=0.24, wspace=0.28)
    finish_figure(fig, "04_merge_vs_hybrid.png")

print("Created summary.csv and charts in figures/")
