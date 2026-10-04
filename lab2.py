# ============================================================
# SECTION 1: IMPORTS
# ============================================================

import argparse
import csv
import heapq
import random
import time
from math import inf
from pathlib import Path
from statistics import median
from typing import Callable, Dict, List, Optional, Tuple


# ============================================================
# SECTION 2: CENTRAL EXPERIMENT CONFIGURATION
# ============================================================

# Every shortest-path experiment starts from this vertex.
SOURCE_VERTEX = 0

# Dijkstra requires non-negative edge weights.
MIN_EDGE_WEIGHT = 1
MAX_EDGE_WEIGHT = 100

# Number of independent timing trials per graph and implementation.
TRIAL_COUNT = 3
MINIMUM_TIMED_CPU_SECONDS = 0.05
MAX_TIMING_REPETITIONS = 4096

# Default full vertex-scaling experiment.
VERTEX_COUNTS = [100, 200, 400, 800, 1600, 3200]

# Smaller configurations for a quick run that checks the full pipeline.
QUICK_VERTEX_COUNTS = [100, 200, 400]
QUICK_EDGE_COUNTS = [999, 2000, 5000]

# Fixed-vertex edge-scaling experiment.
EDGE_EXPERIMENT_VERTEX_COUNT = 1000
EDGE_COUNTS = [999, 2000, 5000, 10000, 50000, 250000, 999000]
EDGE_EXPERIMENT_SEED = 20261010

# Approximate density:
#
#     density = number_of_edges /
#               (number_of_vertices * (number_of_vertices - 1))
#
# The graph is directed and does not contain self-loops.
GRAPH_DENSITIES = {
    "sparse": 0.01,
    "medium": 0.10,
    "dense": 0.50,
}

# A different fixed seed is used for each graph-density family.
# Fixed seeds allow the same graphs to be regenerated.
GRAPH_SEEDS = {
    "sparse": 20261001,
    "medium": 20261002,
    "dense": 20261003,
}

# Output file containing every raw timing trial.
RESULTS_FILE = Path(__file__).resolve().parent / "dijkstra_results.csv"
QUICK_RESULTS_FILE = Path(__file__).resolve().parent / \
    "dijkstra_results_quick.csv"


# ============================================================
# SECTION 3: TYPE DEFINITIONS
# ============================================================

# An edge is represented as:
#
#     (source_vertex, destination_vertex, edge_weight)
#
# Example:
#
#     (0, 1, 10)
#
# means that there is a directed edge from vertex 0 to vertex 1
# with weight 10.
Edge = Tuple[int, int, int]

# An adjacency list stores:
#
#     adjacency_list[u] = [(v, weight), ...]
#
AdjacencyList = List[List[Tuple[int, int]]]

# An adjacency matrix stores:
#
#     adjacency_matrix[u][v] = edge weight
#
AdjacencyMatrix = List[List[float]]


# ============================================================
# SECTION 4: CALCULATE THE NUMBER OF EDGES
# ============================================================

def calculate_edge_count(
    number_of_vertices: int,
    density: float,
) -> int:
    """
    Calculate how many directed edges a graph should contain.

    Parameters
    ----------
    number_of_vertices:
        Total number of vertices in the graph.

    density:
        Approximate fraction of possible directed edges.
        For example, 0.01 means approximately 1% density.

    Returns
    -------
    int
        Number of directed edges.

    Explanation
    -----------
    A directed graph without self-loops has:

        V * (V - 1)

    possible directed edges.

    We require at least V - 1 edges so that the generator
    can create a path from vertex 0 to every other vertex.
    """
    if number_of_vertices < 1:
        raise ValueError("number_of_vertices must be at least 1")

    if not 0 < density <= 1:
        raise ValueError("density must be greater than 0 and at most 1")

    possible_edges = number_of_vertices * (number_of_vertices - 1)

    requested_edges = int(density * possible_edges)

    minimum_edges_for_reachability = max(
        0,
        number_of_vertices - 1,
    )

    return max(
        minimum_edges_for_reachability,
        requested_edges,
    )


# ============================================================
# SECTION 5: GENERATE A REPRODUCIBLE GRAPH
# ============================================================

def generate_connected_graph(
    number_of_vertices: int,
    number_of_edges: int,
    random_seed: int,
    minimum_edge_weight: int = MIN_EDGE_WEIGHT,
    maximum_edge_weight: int = MAX_EDGE_WEIGHT,
) -> List[Edge]:
    """
    Generate a reproducible directed weighted graph.

    Parameters
    ----------
    number_of_vertices:
        Number of vertices in the graph.

        Vertices are labelled:

            0, 1, 2, ..., number_of_vertices - 1

    number_of_edges:
        Total number of directed edges in the graph.

        An edge is represented as:

            (source_vertex, destination_vertex, edge_weight)

    random_seed:
        Fixed seed used to reproduce the same graph.

    minimum_edge_weight:
        Smallest possible non-negative edge weight.

    maximum_edge_weight:
        Largest possible edge weight.

    Returns
    -------
    list of Edge
        A list containing exactly `number_of_edges` edges.

    Notes
    -----
    The function first creates a directed path:

        0 → 1 → 2 → 3 → ...

    This ensures that every vertex is reachable from vertex 0.
    It then adds random edges until the requested number is reached.
    """
    if number_of_vertices < 1:
        raise ValueError("number_of_vertices must be at least 1")

    maximum_possible_edges = (
        number_of_vertices * (number_of_vertices - 1)
    )

    minimum_required_edges = max(
        0,
        number_of_vertices - 1,
    )

    if number_of_edges < minimum_required_edges:
        raise ValueError(
            "number_of_edges is too small to connect all vertices "
            "from source vertex 0"
        )

    if number_of_edges > maximum_possible_edges:
        raise ValueError(
            "number_of_edges is too large for a directed graph "
            "without self-loops"
        )

    if minimum_edge_weight < 0:
        raise ValueError(
            "minimum_edge_weight must be non-negative"
        )

    if minimum_edge_weight > maximum_edge_weight:
        raise ValueError(
            "minimum_edge_weight cannot be greater than "
            "maximum_edge_weight"
        )

    if number_of_vertices == 1:
        return []

    random_generator = random.Random(random_seed)
    possible_edges = number_of_vertices * (number_of_vertices - 1)
    selected_edge_ids = random_generator.sample(
        range(possible_edges),
        number_of_edges,
    )

    # Encode each non-self directed edge as one integer in [0, V * (V - 1)).
    # Replace any missing path edges so every vertex stays reachable from 0.
    path_edge_ids = {
        source_vertex * (number_of_vertices - 1) + source_vertex
        for source_vertex in range(number_of_vertices - 1)
    }
    selected_flags = bytearray(possible_edges)
    for edge_id in selected_edge_ids:
        selected_flags[edge_id] = 1

    missing_path_ids = [
        edge_id for edge_id in path_edge_ids
        if not selected_flags[edge_id]
    ]
    missing_count = len(missing_path_ids)
    for position in range(len(selected_edge_ids) - 1, -1, -1):
        if missing_count == 0:
            break
        if selected_edge_ids[position] not in path_edge_ids:
            selected_edge_ids[position] = missing_path_ids[missing_count - 1]
            missing_count -= 1

    edges = []
    for edge_id in selected_edge_ids:
        source_vertex = edge_id // (number_of_vertices - 1)
        destination_offset = edge_id % (number_of_vertices - 1)
        destination_vertex = destination_offset
        if destination_vertex >= source_vertex:
            destination_vertex += 1

        edge_weight = random_generator.randint(
            minimum_edge_weight,
            maximum_edge_weight,
        )
        edges.append((source_vertex, destination_vertex, edge_weight))

    return edges


# ============================================================
# SECTION 6: CONVERT EDGES INTO AN ADJACENCY MATRIX
# ============================================================

def edges_to_adjacency_matrix(
    number_of_vertices: int,
    edges: List[Edge],
) -> AdjacencyMatrix:
    """
    Convert an edge list into an adjacency matrix.

    Matrix meaning:

        matrix[u][v] = weight
        matrix[u][v] = infinity if no edge exists

    The diagonal is set to zero because the distance from
    a vertex to itself is zero.
    """
    matrix: AdjacencyMatrix = [
        [inf] * number_of_vertices
        for _ in range(number_of_vertices)
    ]

    if any(edge_weight < 0 for _, _, edge_weight in edges):
        raise ValueError("Dijkstra requires non-negative edge weights")

    for vertex in range(number_of_vertices):
        matrix[vertex][vertex] = 0

    for source_vertex, destination_vertex, edge_weight in edges:
        # If duplicate edges ever occur, keep the lighter edge.
        if edge_weight < matrix[source_vertex][destination_vertex]:
            matrix[source_vertex][destination_vertex] = edge_weight

    return matrix


# ============================================================
# SECTION 7: CONVERT EDGES INTO AN ADJACENCY LIST
# ============================================================

def edges_to_adjacency_list(
    number_of_vertices: int,
    edges: List[Edge],
) -> AdjacencyList:
    """
    Convert an edge list into an adjacency list.

    Example:

        adjacency_list[0] = [(1, 10), (2, 3)]

    means that vertex 0 has:
        - an edge to vertex 1 with weight 10
        - an edge to vertex 2 with weight 3
    """
    adjacency_list: AdjacencyList = [
        []
        for _ in range(number_of_vertices)
    ]

    if any(edge_weight < 0 for _, _, edge_weight in edges):
        raise ValueError("Dijkstra requires non-negative edge weights")

    for source_vertex, destination_vertex, edge_weight in edges:
        adjacency_list[source_vertex].append(
            (
                destination_vertex,
                edge_weight,
            )
        )

    return adjacency_list


# ============================================================
# SECTION 8: DIJKSTRA — ADJACENCY MATRIX + ARRAY
# ============================================================

def dijkstra_matrix_array(
    adjacency_matrix: AdjacencyMatrix,
    source_vertex: int,
    collect_statistics: bool = True,
    validate_weights: bool = True,
) -> Tuple[List[float], List[Optional[int]], Dict[str, int]]:
    """
    Run Dijkstra using:

        - an adjacency matrix
        - an array-based minimum search

    The algorithm repeatedly scans every vertex to find the
    unvisited vertex with the smallest known distance.

    Expected time complexity:

        O(V²)

    Expected space complexity:

        O(V²)
    """
    number_of_vertices = len(adjacency_matrix)
    if not 0 <= source_vertex < number_of_vertices:
        raise ValueError("source_vertex is outside the graph")
    if validate_weights and any(
        edge_weight < 0
        for row in adjacency_matrix
        for edge_weight in row
        if edge_weight != inf
    ):
        raise ValueError("Dijkstra requires non-negative edge weights")

    distances = [inf] * number_of_vertices
    previous_vertex: List[Optional[int]] = [
        None
    ] * number_of_vertices

    visited = [False] * number_of_vertices

    statistics = {
        "minimum_scan_checks": 0,
        "matrix_neighbour_checks": 0,
        "successful_relaxations": 0,
    }

    distances[source_vertex] = 0

    # --------------------------------------------------------
    # SECTION 8A: Repeatedly select the closest vertex
    # --------------------------------------------------------

    for _ in range(number_of_vertices):
        closest_vertex = None
        smallest_distance = inf

        # Array-based priority queue:
        # scan all vertices to find the minimum.
        for vertex in range(number_of_vertices):
            if collect_statistics:
                statistics["minimum_scan_checks"] += 1

            if (
                not visited[vertex]
                and distances[vertex] < smallest_distance
            ):
                smallest_distance = distances[vertex]
                closest_vertex = vertex

        # No reachable unvisited vertex remains.
        if closest_vertex is None:
            break

        visited[closest_vertex] = True

        # ----------------------------------------------------
        # SECTION 8B: Relax every matrix entry in the row
        # ----------------------------------------------------

        for neighbour_vertex in range(number_of_vertices):
            if collect_statistics:
                statistics["matrix_neighbour_checks"] += 1

            edge_weight = adjacency_matrix[
                closest_vertex
            ][neighbour_vertex]

            if edge_weight == inf:
                continue

            if visited[neighbour_vertex]:
                continue

            candidate_distance = (
                distances[closest_vertex]
                + edge_weight
            )

            if candidate_distance < distances[neighbour_vertex]:
                distances[neighbour_vertex] = candidate_distance
                previous_vertex[neighbour_vertex] = closest_vertex
                if collect_statistics:
                    statistics["successful_relaxations"] += 1

    return distances, previous_vertex, statistics


# ============================================================
# SECTION 9: DIJKSTRA — ADJACENCY LIST + MIN-HEAP
# ============================================================

def dijkstra_adjacency_list_heap(
    adjacency_list: AdjacencyList,
    source_vertex: int,
    collect_statistics: bool = True,
    validate_weights: bool = True,
) -> Tuple[List[float], List[Optional[int]], Dict[str, int]]:
    """
    Run Dijkstra using:

        - an adjacency list
        - Python's binary min-heap

    Expected time complexity:

        O((V + E) log V)

    Expected space complexity:

        O(V + E)

    Python's heapq does not provide a direct decrease-key
    operation. Therefore, when a shorter distance is found,
    a new heap entry is inserted. Old entries are ignored
    when they are later removed.
    """
    number_of_vertices = len(adjacency_list)
    if not 0 <= source_vertex < number_of_vertices:
        raise ValueError("source_vertex is outside the graph")
    if validate_weights and any(
        edge_weight < 0
        for outgoing_edges in adjacency_list
        for _, edge_weight in outgoing_edges
    ):
        raise ValueError("Dijkstra requires non-negative edge weights")

    distances = [inf] * number_of_vertices
    previous_vertex: List[Optional[int]] = [
        None
    ] * number_of_vertices

    # Each heap item is:
    #
    #     (current_distance, vertex)
    #
    priority_queue = [
        (0, source_vertex)
    ]

    statistics = {
        "edge_scans": 0,
        "heap_pushes": 1,
        "heap_pops": 0,
        "stale_heap_pops": 0,
        "successful_relaxations": 0,
    }

    distances[source_vertex] = 0

    # --------------------------------------------------------
    # SECTION 9A: Repeatedly extract the closest vertex
    # --------------------------------------------------------

    while priority_queue:
        current_distance, current_vertex = (
            heapq.heappop(priority_queue)
        )

        if collect_statistics:
            statistics["heap_pops"] += 1

        # This entry is outdated.
        if current_distance != distances[current_vertex]:
            if collect_statistics:
                statistics["stale_heap_pops"] += 1
            continue

        # ----------------------------------------------------
        # SECTION 9B: Relax only existing outgoing edges
        # ----------------------------------------------------

        for (
            neighbour_vertex,
            edge_weight,
        ) in adjacency_list[current_vertex]:
            if collect_statistics:
                statistics["edge_scans"] += 1

            candidate_distance = (
                current_distance
                + edge_weight
            )

            if candidate_distance < distances[neighbour_vertex]:
                distances[neighbour_vertex] = candidate_distance
                previous_vertex[neighbour_vertex] = current_vertex
                if collect_statistics:
                    statistics["successful_relaxations"] += 1

                heapq.heappush(
                    priority_queue,
                    (
                        candidate_distance,
                        neighbour_vertex,
                    ),
                )
                if collect_statistics:
                    statistics["heap_pushes"] += 1

    return distances, previous_vertex, statistics


# ============================================================
# SECTION 10: RECONSTRUCT A SHORTEST PATH
# ============================================================

def reconstruct_path(
    previous_vertex: List[Optional[int]],
    source_vertex: int,
    destination_vertex: int,
) -> List[int]:
    """
    Reconstruct a shortest path after Dijkstra completes.

    Example output:

        [0, 2, 1, 3]

    If the destination cannot be reached, return an empty list.
    """
    path = []
    current_vertex: Optional[int] = destination_vertex

    while current_vertex is not None:
        path.append(current_vertex)

        if current_vertex == source_vertex:
            path.reverse()
            return path

        current_vertex = previous_vertex[current_vertex]

    return []


# ============================================================
# SECTION 11: SMALL CORRECTNESS TEST
# ============================================================

def run_small_correctness_test() -> None:
    """
    Run both implementations on a hand-checkable graph.

    Expected shortest distances from vertex 0:

        vertex 0: distance 0
        vertex 1: distance 7
        vertex 2: distance 3
        vertex 3: distance 9
        vertex 4: distance 5
    """
    number_of_vertices = 5

    edges = [
        (0, 1, 10),
        (0, 2, 3),
        (1, 2, 1),
        (1, 3, 2),
        (2, 1, 4),
        (2, 3, 8),
        (2, 4, 2),
        (3, 4, 7),
        (4, 3, 9),
    ]

    matrix = edges_to_adjacency_matrix(
        number_of_vertices,
        edges,
    )

    adjacency_list = edges_to_adjacency_list(
        number_of_vertices,
        edges,
    )

    matrix_distances, _, _ = dijkstra_matrix_array(
        matrix,
        SOURCE_VERTEX,
    )

    heap_distances, _, _ = dijkstra_adjacency_list_heap(
        adjacency_list,
        SOURCE_VERTEX,
    )

    expected_distances = [
        0,
        7,
        3,
        9,
        5,
    ]

    assert matrix_distances == expected_distances
    assert heap_distances == expected_distances
    assert matrix_distances == heap_distances

    single_matrix = edges_to_adjacency_matrix(1, [])
    single_list = edges_to_adjacency_list(1, [])
    assert dijkstra_matrix_array(single_matrix, 0)[0] == [0]
    assert dijkstra_adjacency_list_heap(single_list, 0)[0] == [0]

    disconnected_edges = [(0, 1, 0), (2, 3, 4)]
    disconnected_matrix = edges_to_adjacency_matrix(4, disconnected_edges)
    disconnected_list = edges_to_adjacency_list(4, disconnected_edges)
    expected_disconnected = [0, 0, inf, inf]
    assert dijkstra_matrix_array(disconnected_matrix, 0)[
        0] == expected_disconnected
    assert dijkstra_adjacency_list_heap(disconnected_list, 0)[
        0] == expected_disconnected

    negative_edges = [(0, 1, -1)]
    for converter in (edges_to_adjacency_matrix, edges_to_adjacency_list):
        try:
            converter(2, negative_edges)
        except ValueError:
            pass
        else:
            raise AssertionError("Negative edge weights must be rejected")

    negative_matrix = [[0, -1], [inf, 0]]
    negative_list = [[(1, -1)], []]
    for algorithm, graph in (
        (dijkstra_matrix_array, negative_matrix),
        (dijkstra_adjacency_list_heap, negative_list),
    ):
        try:
            algorithm(graph, 0)
        except ValueError:
            pass
        else:
            raise AssertionError("Dijkstra must reject negative edge weights")

    print("Correctness and input-validation tests passed.")
    print(f"Hand-checkable distances: {matrix_distances}")


# ============================================================
# SECTION 12: TIMING ONE IMPLEMENTATION
# ============================================================

def measure_algorithm(
    algorithm: Callable[..., Tuple[List[float], List[Optional[int]], Dict[str, int]]],
    graph,
    source_vertex: int,
    trial_count: int,
) -> List[dict]:
    """Measure one implementation without graph setup or counter overhead."""
    _, _, operation_counts = algorithm(graph, source_vertex, True, True)

    def run_once():
        return algorithm(graph, source_vertex, False, False)

    repetitions = 1
    while True:
        calibration_start = time.process_time()
        for _ in range(repetitions):
            run_once()
        calibration_elapsed = time.process_time() - calibration_start
        if (
            calibration_elapsed >= MINIMUM_TIMED_CPU_SECONDS
            or repetitions >= MAX_TIMING_REPETITIONS
        ):
            break
        repetitions = min(repetitions * 2, MAX_TIMING_REPETITIONS)

    results = []
    distances: List[float] = []
    previous_vertex: List[Optional[int]] = []
    for trial_number in range(1, trial_count + 1):
        start_cpu_time = time.process_time()
        start_wall_time = time.perf_counter()
        for _ in range(repetitions):
            distances, previous_vertex, _ = run_once()

        cpu_seconds = (time.process_time() - start_cpu_time) / repetitions
        wall_seconds = (time.perf_counter() - start_wall_time) / repetitions
        results.append({
            "trial": trial_number,
            "cpu_seconds": cpu_seconds,
            "wall_seconds": wall_seconds,
            "timing_repetitions": repetitions,
            "distances": distances,
            "previous_vertex": previous_vertex,
            **operation_counts,
        })

    return results


def measure_matrix_algorithm(
    adjacency_matrix: AdjacencyMatrix,
    source_vertex: int,
    trial_count: int,
) -> List[dict]:
    return measure_algorithm(
        dijkstra_matrix_array,
        adjacency_matrix,
        source_vertex,
        trial_count,
    )


def measure_heap_algorithm(
    adjacency_list: AdjacencyList,
    source_vertex: int,
    trial_count: int,
) -> List[dict]:
    return measure_algorithm(
        dijkstra_adjacency_list_heap,
        adjacency_list,
        source_vertex,
        trial_count,
    )


# ============================================================
# SECTION 13: RUN ONE GRAPH EXPERIMENT
# ============================================================

def run_one_graph_experiment(
    experiment: str,
    graph_family: str,
    number_of_vertices: int,
    number_of_edges: int,
    random_seed: int,
) -> List[dict]:
    """Run both implementations on the same generated graph."""
    density = number_of_edges / (number_of_vertices * (number_of_vertices - 1))

    edges = generate_connected_graph(
        number_of_vertices=number_of_vertices,
        number_of_edges=number_of_edges,
        random_seed=random_seed,
        minimum_edge_weight=MIN_EDGE_WEIGHT,
        maximum_edge_weight=MAX_EDGE_WEIGHT,
    )

    matrix = edges_to_adjacency_matrix(
        number_of_vertices,
        edges,
    )

    adjacency_list = edges_to_adjacency_list(
        number_of_vertices,
        edges,
    )
    del edges

    matrix_results = measure_matrix_algorithm(
        matrix,
        SOURCE_VERTEX,
        TRIAL_COUNT,
    )

    heap_results = measure_heap_algorithm(
        adjacency_list,
        SOURCE_VERTEX,
        TRIAL_COUNT,
    )

    raw_rows = []
    for matrix_result, heap_result in zip(matrix_results, heap_results):
        if matrix_result["distances"] != heap_result["distances"]:
            raise AssertionError(
                "The two implementations returned different "
                "shortest-path distances."
            )

        common_fields = {
            "experiment": experiment,
            "graph_family": graph_family,
            "number_of_vertices": number_of_vertices,
            "number_of_edges": number_of_edges,
            "density": density,
            "random_seed": random_seed,
            "source_vertex": SOURCE_VERTEX,
            "correct": True,
        }
        raw_rows.append({
            **common_fields,
            "implementation": "matrix_array",
            "trial": matrix_result["trial"],
            "cpu_seconds": matrix_result["cpu_seconds"],
            "wall_seconds": matrix_result["wall_seconds"],
            "timing_repetitions": matrix_result["timing_repetitions"],
            "minimum_scan_checks": matrix_result["minimum_scan_checks"],
            "matrix_neighbour_checks": matrix_result[
                "matrix_neighbour_checks"
            ],
            "edge_scans": "",
            "heap_pushes": "",
            "heap_pops": "",
            "stale_heap_pops": "",
            "successful_relaxations": matrix_result[
                "successful_relaxations"
            ],
        })
        raw_rows.append({
            **common_fields,
            "implementation": "adjacency_list_heap",
            "trial": heap_result["trial"],
            "cpu_seconds": heap_result["cpu_seconds"],
            "wall_seconds": heap_result["wall_seconds"],
            "timing_repetitions": heap_result["timing_repetitions"],
            "minimum_scan_checks": "",
            "matrix_neighbour_checks": "",
            "edge_scans": heap_result["edge_scans"],
            "heap_pushes": heap_result["heap_pushes"],
            "heap_pops": heap_result["heap_pops"],
            "stale_heap_pops": heap_result["stale_heap_pops"],
            "successful_relaxations": heap_result[
                "successful_relaxations"
            ],
        })

    return raw_rows


# ============================================================
# SECTION 14: SAVE RAW RESULTS TO CSV
# ============================================================

def save_results_to_csv(
    rows: List[dict],
    output_file: Path,
) -> None:
    """
    Save trial-level experiment results to a CSV file.
    """
    if not rows:
        return

    fieldnames = list(rows[0].keys())

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# SECTION 15: RUN THE FULL EXPERIMENT
# ============================================================

def run_experiment(
    vertex_counts: List[int],
    edge_counts: List[int],
    output_file: Path,
) -> None:
    """Run vertex-scaling and fixed-vertex edge-scaling experiments."""
    all_rows = []

    for graph_family, density in GRAPH_DENSITIES.items():
        for number_of_vertices in vertex_counts:
            number_of_edges = calculate_edge_count(number_of_vertices, density)
            random_seed = GRAPH_SEEDS[graph_family] + number_of_vertices
            print(
                f"Vertex scaling: {graph_family}, V={number_of_vertices}, "
                f"E={number_of_edges}, seed={random_seed}"
            )
            all_rows.extend(run_one_graph_experiment(
                "vertex_scaling",
                graph_family,
                number_of_vertices,
                number_of_edges,
                random_seed,
            ))

    for number_of_edges in edge_counts:
        random_seed = EDGE_EXPERIMENT_SEED + number_of_edges
        print(
            f"Edge scaling: V={EDGE_EXPERIMENT_VERTEX_COUNT}, "
            f"E={number_of_edges}, seed={random_seed}"
        )
        all_rows.extend(run_one_graph_experiment(
            "edge_scaling",
            "fixed_v",
            EDGE_EXPERIMENT_VERTEX_COUNT,
            number_of_edges,
            random_seed,
        ))

    save_results_to_csv(all_rows, output_file)
    print(
        f"Saved {len(all_rows)} raw trials from "
        f"{len(all_rows) // (2 * TRIAL_COUNT)} graph configurations to {output_file}"
    )


# ============================================================
# SECTION 16: PROGRAM ENTRY POINT
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark two Dijkstra implementations.")
    run_mode = parser.add_mutually_exclusive_group()
    run_mode.add_argument("--quick", action="store_true",
                          help="Run a reduced pipeline check.")
    run_mode.add_argument("--full", action="store_true",
                          help="Run the full configured experiments (default).")
    run_mode.add_argument("--test", action="store_true",
                          help="Run correctness tests only.")
    parser.add_argument("--output", type=Path,
                        help="Override the raw CSV output path.")
    arguments = parser.parse_args()

    run_small_correctness_test()
    if arguments.test:
        return

    if arguments.quick:
        vertex_counts = QUICK_VERTEX_COUNTS
        edge_counts = QUICK_EDGE_COUNTS
        default_output = QUICK_RESULTS_FILE
    else:
        vertex_counts = VERTEX_COUNTS
        edge_counts = EDGE_COUNTS
        default_output = RESULTS_FILE

    run_experiment(
        vertex_counts,
        edge_counts,
        arguments.output or default_output,
    )


if __name__ == "__main__":
    main()
