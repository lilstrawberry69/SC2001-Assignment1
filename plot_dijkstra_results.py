"""Summarize Dijkstra trials and create separate (a), (b), and (c) figures."""

import matplotlib.pyplot as plt
import argparse
import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter

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
# One entry per vertex-scaling panel: (key, experiment, graph_family).
# PANELS is filled from the data in main(): the fixed-degree sweep first
# (key "sparse"), then every fixed-density family ordered by its density.
PANELS = []
PANEL_PALETTE = (BLUE, RED, ORANGE, "#5C8D89", "#548235", GRAY)


def discover_panels(rows):
    panels = []
    if any(row["experiment"] == "vertex_scaling_fixed_degree"
           for row in rows):
        panels.append(("sparse", "vertex_scaling_fixed_degree", None))
    densities = defaultdict(list)
    for row in rows:
        if row["experiment"] == "vertex_scaling":
            densities[row["graph_family"]].append(row["density"])
    for family in sorted(
        densities, key=lambda name: statistics.median(densities[name])
    ):
        panels.append((family, "vertex_scaling", family))
    return panels


def panel_color(panel):
    return PANEL_PALETTE[PANELS.index(panel) % len(PANEL_PALETTE)]


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


def format_runtime_axis(axis, unit, logarithmic=False, show_label=True):
    if show_label:
        axis.set_ylabel(f"Median CPU time ({unit})", color=TEXT_COLOR,
                        labelpad=10, fontname=FONT)
    if logarithmic:
        axis.set_yscale("log")
        axis.yaxis.set_major_locator(LogLocator(base=10, subs=(1, 2, 5)))
    axis.yaxis.set_major_formatter(
        FuncFormatter(lambda value, _: f"{value:,.0f}")
    )


HEADER_INCHES = 0.77


def add_header(fig, title, subtitle):
    height = fig.get_figheight()
    fig.text(0.06, 1 - 0.17 / height, title, ha="left", va="top",
             fontsize=19, fontweight="bold", color=TEXT_COLOR,
             fontname=FONT)
    fig.text(0.06, 1 - 0.47 / height, subtitle, ha="left", va="top",
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
    fig.tight_layout(
        rect=(0.03, 0.04, 0.98, 1 - HEADER_INCHES / fig.get_figheight()))
    fig.patch.set_facecolor(CHART_BG)
    fig.savefig(output_dir / filename, dpi=240, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)


def panel_rows(rows, panel, implementation=None):
    """Summary rows for one vertex-scaling panel, ordered by vertex count."""
    _, experiment, family = panel
    return sorted(
        [row for row in rows
         if row["experiment"] == experiment
         and (family is None or row["graph_family"] == family)
         and (implementation is None
              or row["implementation"] == implementation)],
        key=lambda row: (row["number_of_vertices"], row["implementation"]),
    )


def panel_title(panel, points):
    key, experiment, _ = panel
    first = points[0]
    if experiment == "vertex_scaling_fixed_degree":
        degree = first["number_of_edges"] / first["number_of_vertices"]
        return f"Sparse (E = {degree:g}V)"
    name = key.replace("_", " ").title()
    return f"{name} (density {first['density']:.2f})"


def edges_for_vertices(panel, points):
    """Edge count as a function of |V| for the panel's graph family."""
    first = points[0]
    if panel[1] == "vertex_scaling_fixed_degree":
        degree = first["number_of_edges"] / first["number_of_vertices"]
        return lambda vertex_count: degree * vertex_count
    density = first["density"]
    return lambda vertex_count: density * vertex_count * (vertex_count - 1)


PANEL_COLUMNS = 3


def panel_grid(panel_count, **subplot_kwargs):
    """Create a grid with PANEL_COLUMNS columns and hide unused cells."""
    grid_rows = math.ceil(panel_count / PANEL_COLUMNS)
    fig, axes = plt.subplots(
        grid_rows, PANEL_COLUMNS, squeeze=False,
        figsize=(14, 4.4 * grid_rows + 0.6), **subplot_kwargs,
    )
    flat_axes = list(axes.flat)
    for unused_axis in flat_axes[panel_count:]:
        unused_axis.set_visible(False)
    return fig, flat_axes[:panel_count]


def plot_vertex_scaling(rows, output_dir, implementation):
    panels = [panel for panel in PANELS
              if panel_rows(rows, panel, implementation)]
    if not panels:
        return

    all_points = [row for panel in panels
                  for row in panel_rows(rows, panel, implementation)]
    factor, unit = runtime_unit(
        [row["median_cpu_seconds"] for row in all_points]
    )
    fig, axes = panel_grid(len(panels))
    for index, (axis, panel) in enumerate(zip(axes, panels)):
        style_axis(axis)
        points = panel_rows(rows, panel, implementation)
        vertices = [row["number_of_vertices"] for row in points]
        times = [row["median_cpu_seconds"] * factor for row in points]
        style_line(
            axis, vertices, times, COLORS[implementation],
            "Empirical median CPU time",
        )
        reference_vertices = [
            vertices[0] + (vertices[-1] - vertices[0]) * step / 199
            for step in range(200)
        ]
        if implementation == "matrix_array":
            def feature(row):
                return row["number_of_vertices"] ** 2
            reference_label = "Scaled O(V^2) reference"
            scale = _reference_scale(points, feature)
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
            edges_at = edges_for_vertices(panel, points)
            reference_values = [
                scale
                * (vertex_count + edges_at(vertex_count))
                * math.log2(vertex_count)
                * factor
                for vertex_count in reference_vertices
            ]
        axis.plot(
            reference_vertices, reference_values,
            linestyle="--", linewidth=1.8,
            color="#555555", label=reference_label,
        )
        axis.set_title(panel_title(panel, points),
                       color=TEXT_COLOR, fontname=FONT)
        axis.set_xlabel("Vertices |V|", color=TEXT_COLOR, labelpad=10,
                        fontname=FONT)
        axis.set_ylim(bottom=0)
        format_runtime_axis(axis, unit, show_label=index % PANEL_COLUMNS == 0)
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
    panels = [panel for panel in PANELS if panel_rows(rows, panel)]
    if not panels:
        return
    all_points = [row for panel in panels for row in panel_rows(rows, panel)]
    factor, unit = runtime_unit(
        [row["median_cpu_seconds"] for row in all_points]
    )
    fig, axes = panel_grid(len(panels), sharey=True)
    for index, (axis, panel) in enumerate(zip(axes, panels)):
        style_axis(axis)
        for implementation, label in IMPLEMENTATIONS.items():
            points = panel_rows(rows, panel, implementation)
            if points:
                style_line(
                    axis,
                    [row["number_of_vertices"] for row in points],
                    [row["median_cpu_seconds"] * factor for row in points],
                    COLORS[implementation], label,
                )
        axis.set_title(panel_title(panel, panel_rows(rows, panel)),
                       color=TEXT_COLOR, fontname=FONT)
        axis.set_xlabel("Vertices |V|", color=TEXT_COLOR, labelpad=10,
                        fontname=FONT)
        format_runtime_axis(axis, unit, logarithmic=True,
                            show_label=index % PANEL_COLUMNS == 0)
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


def plot_speedup_vs_vertices(rows, output_dir):
    """Matrix time / heap time against |V|, one line per graph family."""
    fig, axis = plt.subplots(figsize=(8.5, 5.2))
    style_axis(axis)
    all_vertices = set()
    for panel in PANELS:
        matrix = {row["number_of_vertices"]: row
                  for row in panel_rows(rows, panel, "matrix_array")}
        heap = {row["number_of_vertices"]: row
                for row in panel_rows(rows, panel, "adjacency_list_heap")}
        vertices = sorted(
            vertex_count for vertex_count in set(matrix) & set(heap)
            if heap[vertex_count]["median_cpu_seconds"] > 0
        )
        if not vertices:
            continue
        all_vertices.update(vertices)
        style_line(
            axis,
            vertices,
            [matrix[v]["median_cpu_seconds"] / heap[v]["median_cpu_seconds"]
             for v in vertices],
            panel_color(panel),
            panel_title(panel, panel_rows(rows, panel)),
        )
    if not all_vertices:
        plt.close(fig)
        return
    axis.axhline(1.0, color=GRAY, linestyle="--", linewidth=1.3)
    axis.set_xscale("log", base=2)
    axis.set_xticks(sorted(all_vertices))
    axis.xaxis.set_major_formatter(
        FuncFormatter(lambda value, _: f"{value:,.0f}"))
    axis.xaxis.set_minor_formatter(NullFormatter())
    axis.set_yscale("log")
    axis.yaxis.set_major_locator(LogLocator(base=10, subs=(1, 2, 5)))
    axis.yaxis.set_major_formatter(
        FuncFormatter(lambda value, _: f"{value:g}"))
    axis.yaxis.set_minor_formatter(NullFormatter())
    axis.set_xlabel("Vertices |V|", color=TEXT_COLOR, labelpad=10,
                    fontname=FONT)
    axis.set_ylabel("Speedup: matrix time / heap time", color=TEXT_COLOR,
                    labelpad=10, fontname=FONT)
    axis.legend(frameon=False, fontsize=8, loc="upper left",
                  bbox_to_anchor=(1.02, 1.0))
    add_header(fig, "PART (C): SPEEDUP BY VERTEX COUNT",
               "Matrix time / heap time; above 1 favors the heap, below 1 favors the matrix")
    _finish_figure(fig, output_dir, "c_04_speedup_vs_vertices.png")


def plot_operation_counts(rows, output_dir):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    for axis in axes:
        style_axis(axis)
    for panel in PANELS:
        matrix_points = panel_rows(rows, panel, "matrix_array")
        if matrix_points:
            style_line(
                axes[0],
                [row["number_of_vertices"] ** 2 for row in matrix_points],
                [float(row["minimum_scan_checks"])
                 + float(row["matrix_neighbour_checks"])
                 for row in matrix_points],
                panel_color(panel),
                panel[0].replace("_", " ").title(),
            )
    axes[0].text(
        0.97, 0.05, "Lines overlap: matrix work\ndepends only on |V|",
        transform=axes[0].transAxes, ha="right", va="bottom",
        fontsize=8, color=GRAY, fontname=FONT,
    )

    heap_points = sorted(
        [row for row in rows
         if row["experiment"] == "edge_scaling"
         and row["implementation"] == "adjacency_list_heap"],
        key=lambda row: row["number_of_edges"],
    )
    if heap_points:
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
    PANELS[:] = discover_panels(rows)
    write_summary(rows, arguments.summary)
    arguments.output_dir.mkdir(parents=True, exist_ok=True)
    plot_vertex_scaling(rows, arguments.output_dir, "matrix_array")
    plot_vertex_scaling(rows, arguments.output_dir, "adjacency_list_heap")
    plot_vertex_comparison(rows, arguments.output_dir)
    plot_edge_scaling(rows, arguments.output_dir, "matrix_array")
    plot_edge_scaling(rows, arguments.output_dir, "adjacency_list_heap")
    plot_edge_comparison(rows, arguments.output_dir)
    plot_speedup(rows, arguments.output_dir)
    plot_speedup_vs_vertices(rows, arguments.output_dir)
    plot_operation_counts(rows, arguments.output_dir)
    print(f"Saved {len(rows)} median configurations to {arguments.summary}")
    print(f"Saved figures to {arguments.output_dir}")


if __name__ == "__main__":
    main()