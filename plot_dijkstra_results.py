"""Summarize Dijkstra trials and create separate (a), (b), and (c) figures."""

import matplotlib.pyplot as plt
import argparse
import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib
from matplotlib.ticker import FuncFormatter, LogLocator

matplotlib.use("Agg")


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = BASE_DIR / "dijkstra_results.csv"
DEFAULT_SUMMARY = BASE_DIR / "dijkstra_summary.csv"
DEFAULT_FIGURES = BASE_DIR / "figures"
CHART_BG = "#F4EADF"
PLOT_BG = "#F8F0E8"
GRID_COLOR = "#B9B2AA"
TEXT_COLOR = "#111111"
BLUE = "#3656A8"
RED = "#D83A2E"
ORANGE = "#E38A2F"
GRAY = "#77716B"
FONT = "DejaVu Sans"
LINE_WIDTH = 3.0
MARKER_SIZE = 7
IMPLEMENTATIONS = {
    "matrix_array": "Matrix + array",
    "adjacency_list_heap": "Adjacency list + min-heap",
}
COLORS = {
    "matrix_array": BLUE,
    "adjacency_list_heap": ORANGE,
}
VERTEX_PALETTE = (BLUE, RED, ORANGE, "#5C8D89", GRAY, "#548235")
VERTEX_COLORS = {
    100: BLUE,
    200: RED,
    400: ORANGE,
    800: "#5C8D89",
    1600: GRAY,
    3200: "#548235",
}
COUNT_FIELDS = (
    "minimum_scan_checks",
    "matrix_neighbour_checks",
    "edge_scans",
    "heap_pushes",
    "heap_pops",
    "stale_heap_pops",
    "successful_relaxations",
)
FAMILIES = ("sparse", "medium", "dense")


def style_axis(axis):
    axis.set_facecolor(PLOT_BG)
    axis.grid(axis="y", color=GRID_COLOR, linewidth=0.8, alpha=0.55)
    axis.grid(axis="x", visible=False)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.spines["left"].set_visible(False)
    axis.spines["bottom"].set_color(GRID_COLOR)
    axis.tick_params(axis="both", length=0, colors=TEXT_COLOR, pad=7)
    axis.set_axisbelow(True)
    for label in axis.get_xticklabels() + axis.get_yticklabels():
        label.set_fontname(FONT)
        label.set_color(TEXT_COLOR)


def runtime_unit(seconds_values):
    positive_values = [value for value in seconds_values if value > 0]
    smallest = min(positive_values)
    if smallest < 0.001:
        return 1_000_000, "us"
    if smallest < 1:
        return 1_000, "ms"
    return 1, "s"


def format_runtime_axis(axis, unit, logarithmic=False):
    axis.set_ylabel(f"Median CPU time ({unit})", color=TEXT_COLOR,
                    labelpad=10, fontname=FONT)
    if logarithmic:
        axis.set_yscale("log")
        axis.yaxis.set_major_locator(LogLocator(base=10, subs=(1, 2, 5)))
    axis.yaxis.set_major_formatter(
        FuncFormatter(lambda value, _: f"{value:,.0f}")
    )


def add_header(fig, title, subtitle):
    fig.text(0.06, 0.965, title, ha="left", va="top",
             fontsize=19, fontweight="bold", color=TEXT_COLOR,
             fontname=FONT)
    fig.text(0.06, 0.903, subtitle, ha="left", va="top",
             fontsize=9.5, color=GRAY, fontname=FONT)


def style_line(axis, x_values, y_values, color, label):
    return axis.plot(
        x_values, y_values, color=color, linewidth=LINE_WIDTH,
        marker="o", markersize=MARKER_SIZE, markerfacecolor=color,
        markeredgecolor=PLOT_BG, markeredgewidth=1.2,
        solid_capstyle="round", solid_joinstyle="round", alpha=0.95,
        label=label,
    )[0]


def _median_field(rows, field):
    values = [float(row[field])
              for row in rows if row[field] not in (None, "")]
    return statistics.median(values) if values else ""


def load_summary(input_file):
    with input_file.open(newline="", encoding="utf-8") as csv_file:
        raw_rows = list(csv.DictReader(csv_file))
    if not raw_rows:
        raise ValueError(f"No raw trial rows found in {input_file}.")
    if any(row["correct"].lower() != "true" for row in raw_rows):
        raise ValueError("At least one raw result is marked incorrect.")

    groups = defaultdict(list)
    for row in raw_rows:
        key = (
            row["experiment"],
            row["graph_family"],
            row["implementation"],
            int(row["number_of_vertices"]),
            int(row["number_of_edges"]),
            float(row["density"]),
        )
        groups[key].append(row)

    summary = []
    for key, rows in groups.items():
        experiment, family, implementation, vertices, edges, density = key
        result = {
            "experiment": experiment,
            "graph_family": family,
            "implementation": implementation,
            "number_of_vertices": vertices,
            "number_of_edges": edges,
            "density": density,
            "trial_count": len({int(row["trial"]) for row in rows}),
            "median_cpu_seconds": statistics.median(
                float(row["cpu_seconds"]) for row in rows
            ),
            "median_wall_seconds": statistics.median(
                float(row["wall_seconds"]) for row in rows
            ),
        }
        result.update({field: _median_field(rows, field)
                      for field in COUNT_FIELDS})
        summary.append(result)

    summary.sort(key=lambda row: (
        row["experiment"],
        row["graph_family"],
        row["number_of_vertices"],
        row["implementation"],
    ))
    return summary


def write_summary(rows, summary_file):
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    with summary_file.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _reference_scale(points, feature):
    ratios = [
        float(row["median_cpu_seconds"]) / feature(row)
        for row in points
        if float(row["median_cpu_seconds"]) > 0
    ]
    return statistics.median(ratios)


def _scaled_reference(points, feature):
    scale = _reference_scale(points, feature)
    return [scale * feature(row) for row in points]


def _finish_figure(fig, output_dir, filename):
    fig.tight_layout(rect=(0.03, 0.04, 0.98, 0.84))
    fig.patch.set_facecolor(CHART_BG)
    fig.savefig(output_dir / filename, dpi=240, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)


def plot_vertex_scaling(rows, output_dir, implementation):
    points_by_family = {
        family: sorted(
            [row for row in rows
             if row["experiment"] == "vertex_scaling"
             and row["graph_family"] == family
             and row["implementation"] == implementation],
            key=lambda row: row["number_of_vertices"],
        )
        for family in FAMILIES
    }
    if not any(points_by_family.values()):
        return

    all_points = [row for points in points_by_family.values()
                  for row in points]
    factor, unit = runtime_unit(
        [row["median_cpu_seconds"] for row in all_points]
    )
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8))
    for axis, family in zip(axes, FAMILIES):
        style_axis(axis)
        points = points_by_family[family]
        vertices = [row["number_of_vertices"] for row in points]
        times = [row["median_cpu_seconds"] * factor for row in points]
        style_line(
            axis, vertices, times, COLORS[implementation],
            "Empirical median CPU time",
        )
        if implementation == "matrix_array":
            def feature(row):
                return row["number_of_vertices"] ** 2
            reference_label = "Scaled O(V^2) reference"
            scale = _reference_scale(points, feature)
            density = points[0]["density"]
            reference_vertices = [
                vertices[0] + (vertices[-1] - vertices[0]) * step / 199
                for step in range(200)
            ]
            reference_values = [
                scale * vertex_count ** 2 * factor
                for vertex_count in reference_vertices
            ]
        else:
            def feature(row):
                return (
                    row["number_of_vertices"] + row["number_of_edges"]
                ) * math.log2(row["number_of_vertices"])
            reference_label = "Scaled O((V+E) log V) reference"
            scale = _reference_scale(points, feature)
            density = points[0]["density"]
            reference_vertices = [
                vertices[0] + (vertices[-1] - vertices[0]) * step / 199
                for step in range(200)
            ]
            reference_values = [
                scale
                * (vertex_count
                   + density * vertex_count * (vertex_count - 1))
                * math.log2(vertex_count)
                * factor
                for vertex_count in reference_vertices
            ]
        axis.plot(
            reference_vertices, reference_values,
            linestyle="--", linewidth=1.8,
            color="#555555", label=reference_label,
        )
        axis.set_title(
            f"{family.title()} (density {points[0]['density']:.2f})",
            color=TEXT_COLOR, fontname=FONT)
        axis.set_xlabel("Vertices |V|", color=TEXT_COLOR, labelpad=10,
                        fontname=FONT)
        axis.set_ylim(bottom=0)
    format_runtime_axis(axes[0], unit)
    axes[0].legend(frameon=False, fontsize=8)
    part = "a" if implementation == "matrix_array" else "b"
    add_header(
        fig,
        f"PART ({part.upper()}): {IMPLEMENTATIONS[implementation].upper()} VS VERTEX COUNT",
        "Empirical medians and scaled asymptotic reference; vertices are evenly spaced",
    )
    filename = "a_01_matrix_runtime_vs_vertices.png" if implementation == "matrix_array" else "b_01_heap_runtime_vs_vertices.png"
    _finish_figure(fig, output_dir, filename)


def plot_vertex_comparison(rows, output_dir):
    points_all = [row for row in rows if row["experiment"] == "vertex_scaling"]
    if not points_all:
        return
    factor, unit = runtime_unit(
        [row["median_cpu_seconds"] for row in points_all]
    )
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8), sharey=True)
    for axis, family in zip(axes, FAMILIES):
        style_axis(axis)
        for implementation, label in IMPLEMENTATIONS.items():
            points = sorted(
                [row for row in rows
                 if row["experiment"] == "vertex_scaling"
                 and row["graph_family"] == family
                 and row["implementation"] == implementation],
                key=lambda row: row["number_of_vertices"],
            )
            if points:
                style_line(
                    axis,
                    [row["number_of_vertices"] for row in points],
                    [row["median_cpu_seconds"] * factor for row in points],
                    COLORS[implementation], label,
                )
        axis.set_title(f"{family.title()} graphs", color=TEXT_COLOR,
                       fontname=FONT)
        axis.set_xlabel("Vertices |V|", color=TEXT_COLOR, labelpad=10,
                        fontname=FONT)
    format_runtime_axis(axes[0], unit, logarithmic=True)
    axes[0].legend(frameon=False, fontsize=8)
    add_header(fig, "PART (C): IMPLEMENTATION RUNTIME COMPARISON",
               "Both implementations use the same graph at each vertex count")
    _finish_figure(fig, output_dir, "c_01_comparison_runtime_vs_vertices.png")


def plot_edge_scaling(rows, output_dir, implementation):
    points = sorted(
        [row for row in rows
         if row["experiment"] == "edge_scaling"
         and row["implementation"] == implementation],
        key=lambda row: row["number_of_edges"],
    )
    if not points:
        return
    edges = [row["number_of_edges"] for row in points]
    factor, unit = runtime_unit(
        [row["median_cpu_seconds"] for row in points]
    )
    times = [row["median_cpu_seconds"] * factor for row in points]
    fig, axis = plt.subplots(figsize=(8.5, 5.2))
    style_axis(axis)
    style_line(
        axis, edges, times, COLORS[implementation],
        "Empirical median CPU time",
    )
    if implementation == "matrix_array":
        def feature(row):
            return row["number_of_vertices"] ** 2
        reference_label = "Scaled O(V^2) reference"
    else:
        def feature(row):
            return (
                row["number_of_vertices"] + row["number_of_edges"]
            ) * math.log2(row["number_of_vertices"])
        reference_label = "Scaled O((V+E) log V) reference"
    axis.plot(
        edges, [value * factor
                for value in _scaled_reference(points, feature)],
        linestyle="--", linewidth=1.8, color="#555555",
        label=reference_label,
    )
    axis.set_xscale("log")
    axis.set_xlabel("Edges |E| (fixed |V| = 1000)", color=TEXT_COLOR,
                    labelpad=10, fontname=FONT)
    format_runtime_axis(axis, unit)
    axis.set_ylim(bottom=0)
    axis.legend(frameon=False)
    part = "a" if implementation == "matrix_array" else "b"
    add_header(
        fig,
        f"PART ({part.upper()}): {IMPLEMENTATIONS[implementation].upper()} VS EDGE COUNT",
        "Fixed |V| = 1000; dashed curve is a scaled complexity reference",
    )
    filename = "a_02_matrix_runtime_vs_edges.png" if implementation == "matrix_array" else "b_02_heap_runtime_vs_edges.png"
    _finish_figure(fig, output_dir, filename)


def plot_edge_comparison(rows, output_dir):
    all_points = [row for row in rows if row["experiment"] == "edge_scaling"]
    if not all_points:
        return
    factor, unit = runtime_unit(
        [row["median_cpu_seconds"] for row in all_points]
    )
    fig, axis = plt.subplots(figsize=(8.5, 5.2))
    style_axis(axis)
    for implementation, label in IMPLEMENTATIONS.items():
        points = sorted(
            [row for row in rows
             if row["experiment"] == "edge_scaling"
             and row["implementation"] == implementation],
            key=lambda row: row["number_of_edges"],
        )
        if points:
            style_line(
                axis,
                [row["number_of_edges"] for row in points],
                [row["median_cpu_seconds"] * factor for row in points],
                COLORS[implementation], label,
            )
    axis.set_xscale("log")
    axis.set_xlabel("Edges |E| (fixed |V| = 1000)", color=TEXT_COLOR,
                    labelpad=10, fontname=FONT)
    format_runtime_axis(axis, unit, logarithmic=True)
    axis.legend(frameon=False)
    add_header(fig, "PART (C): IMPLEMENTATION RUNTIME VS EDGE COUNT",
               "Same generated graphs and fixed vertex count for both implementations")
    _finish_figure(fig, output_dir, "c_02_comparison_runtime_vs_edges.png")


def plot_speedup(rows, output_dir):
    by_configuration = defaultdict(dict)
    for row in rows:
        if row["experiment"] != "vertex_scaling":
            continue
        key = (
            row["graph_family"],
            row["number_of_vertices"],
            row["number_of_edges"],
        )
        by_configuration[key][row["implementation"]] = row

    by_vertices = defaultdict(list)
    for (family, vertices, edges), implementations in by_configuration.items():
        if set(implementations) != set(IMPLEMENTATIONS):
            continue
        heap_time = implementations["adjacency_list_heap"]["median_cpu_seconds"]
        matrix_time = implementations["matrix_array"]["median_cpu_seconds"]
        if heap_time > 0:
            by_vertices[vertices].append((edges, matrix_time / heap_time))

    fig, axis = plt.subplots(figsize=(8.5, 5.2))
    style_axis(axis)
    for color_index, (vertices, points) in enumerate(sorted(by_vertices.items())):
        points.sort()
        style_line(
            axis,
            [edge_count / (vertices * (vertices - 1))
             for edge_count, _ in points],
            [speedup for _, speedup in points],
            VERTEX_COLORS.get(
                vertices,
                VERTEX_PALETTE[color_index % len(VERTEX_PALETTE)],
            ),
            f"|V|={vertices}",
        )
    axis.axhline(1.0, color=GRAY, linestyle="--", linewidth=1.3)
    axis.set_yscale("log")
    axis.set_xlabel("Graph density E / (V(V-1))", color=TEXT_COLOR,
                    labelpad=10, fontname=FONT)
    axis.set_ylabel("Speedup: matrix time / heap time", color=TEXT_COLOR,
                    labelpad=10, fontname=FONT)
    axis.legend(frameon=False, ncol=2, fontsize=8)
    add_header(fig, "PART (C): SPEEDUP BY DENSITY",
               "Matrix time / heap time; above 1 favors the adjacency-list heap")
    _finish_figure(fig, output_dir, "c_03_speedup_vs_density.png")


def plot_operation_counts(rows, output_dir):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    for axis in axes:
        style_axis(axis)
    for family in FAMILIES:
        matrix_points = sorted(
            [row for row in rows
             if row["experiment"] == "vertex_scaling"
             and row["graph_family"] == family
             and row["implementation"] == "matrix_array"],
            key=lambda row: row["number_of_vertices"],
        )
        if matrix_points:
            style_line(
                axes[0],
                [row["number_of_vertices"] ** 2 for row in matrix_points],
                [float(row["minimum_scan_checks"])
                 + float(row["matrix_neighbour_checks"])
                 for row in matrix_points],
                {"sparse": BLUE, "medium": RED, "dense": ORANGE}[family],
                family.title(),
            )

        heap_points = sorted(
            [row for row in rows
             if row["experiment"] == "edge_scaling"
             and row["implementation"] == "adjacency_list_heap"],
            key=lambda row: row["number_of_edges"],
        )
        if family == "sparse" and heap_points:
            style_line(
                axes[1],
                [row["number_of_edges"] for row in heap_points],
                [float(row["edge_scans"]) for row in heap_points],
                COLORS["adjacency_list_heap"], "Measured edge scans",
            )
            axes[1].plot(
                [row["number_of_edges"] for row in heap_points],
                [row["number_of_edges"] for row in heap_points],
                linestyle="--", linewidth=1.8, color=GRAY,
                label="E reference",
            )
            style_line(
                axes[2],
                [row["number_of_edges"] for row in heap_points],
                [float(row["heap_pushes"]) for row in heap_points],
                BLUE, "Heap pushes",
            )
            axes[2].plot(
                [row["number_of_edges"] for row in heap_points],
                [float(row["heap_pops"]) for row in heap_points],
                marker="s", linestyle="--", linewidth=2.0,
                color=ORANGE, label="Heap pops",
            )

    axes[0].set_xlabel("V^2", color=TEXT_COLOR, fontname=FONT)
    axes[0].set_ylabel("Minimum scans + matrix-neighbour checks",
                       color=TEXT_COLOR, fontname=FONT)
    axes[0].set_title("MATRIX WORK", loc="left", fontweight="bold",
                      color=TEXT_COLOR, fontname=FONT)
    axes[1].set_xlabel("Edges |E|", color=TEXT_COLOR, fontname=FONT)
    axes[1].set_ylabel("Scanned edges", color=TEXT_COLOR, fontname=FONT)
    axes[1].set_title("HEAP EDGE WORK", loc="left", fontweight="bold",
                      color=TEXT_COLOR, fontname=FONT)
    axes[2].set_xlabel("Edges |E|", color=TEXT_COLOR, fontname=FONT)
    axes[2].set_ylabel("Heap operations", color=TEXT_COLOR, fontname=FONT)
    axes[2].set_title("HEAP QUEUE WORK", loc="left", fontweight="bold",
                      color=TEXT_COLOR, fontname=FONT)
    for axis in axes:
        axis.set_xscale("log")
        axis.set_yscale("log")
        axis.legend(frameon=False, fontsize=8)
    add_header(fig, "MEASURED OPERATION COUNTS",
               "Full-vertex matrix scans versus stored-edge and heap work")
    _finish_figure(fig, output_dir, "04_operation_counts.png")


def main():
    parser = argparse.ArgumentParser(
        description="Plot Dijkstra experiment results.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_FIGURES)
    arguments = parser.parse_args()

    rows = load_summary(arguments.input)
    write_summary(rows, arguments.summary)
    arguments.output_dir.mkdir(parents=True, exist_ok=True)
    plot_vertex_scaling(rows, arguments.output_dir, "matrix_array")
    plot_vertex_scaling(rows, arguments.output_dir, "adjacency_list_heap")
    plot_vertex_comparison(rows, arguments.output_dir)
    plot_edge_scaling(rows, arguments.output_dir, "matrix_array")
    plot_edge_scaling(rows, arguments.output_dir, "adjacency_list_heap")
    plot_edge_comparison(rows, arguments.output_dir)
    plot_speedup(rows, arguments.output_dir)
    plot_operation_counts(rows, arguments.output_dir)
    print(f"Saved {len(rows)} median configurations to {arguments.summary}")
    print(f"Saved figures to {arguments.output_dir}")


if __name__ == "__main__":
    main()
