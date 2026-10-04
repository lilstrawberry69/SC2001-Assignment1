"""Dijkstra implementations for an adjacency matrix and adjacency list."""

import heapq
from math import inf


Distance = int | float
AdjacencyMatrix = list[list[Distance]]
AdjacencyList = list[list[tuple[int, Distance]]]


def dijkstra_matrix_array(adjacency_matrix, source_vertex):
    """Dijkstra with an adjacency matrix and array-based minimum search.

    Use ``inf`` in the matrix where no edge exists. Edge weights must be
    non-negative. Returns the shortest distances and predecessor of each
    vertex. Its running time is O(V^2).
    """
    number_of_vertices = len(adjacency_matrix)
    distances = [inf] * number_of_vertices
    previous_vertex: list[int | None] = [None] * number_of_vertices
    visited = [False] * number_of_vertices
    distances[source_vertex] = 0

    for _ in range(number_of_vertices):
        closest_vertex = None
        smallest_distance = inf

        for vertex in range(number_of_vertices):
            if not visited[vertex] and distances[vertex] < smallest_distance:
                smallest_distance = distances[vertex]
                closest_vertex = vertex

        if closest_vertex is None:
            break

        visited[closest_vertex] = True

        for neighbour_vertex in range(number_of_vertices):
            edge_weight = adjacency_matrix[closest_vertex][neighbour_vertex]
            if edge_weight == inf or visited[neighbour_vertex]:
                continue

            candidate_distance = distances[closest_vertex] + edge_weight
            if candidate_distance < distances[neighbour_vertex]:
                distances[neighbour_vertex] = candidate_distance
                previous_vertex[neighbour_vertex] = closest_vertex

    return distances, previous_vertex


def dijkstra_adjacency_list_heap(adjacency_list, source_vertex):
    """Dijkstra with adjacency lists and a binary min-heap.

    Each list entry is a ``(neighbour, weight)`` pair. Edge weights must be
    non-negative. Since ``heapq`` has no decrease-key operation, improved
    distances are pushed as new entries and stale entries are skipped.
    Returns the shortest distances and predecessor of each vertex. Its
    running time is O((V + E) log V) for a simple graph.
    """
    number_of_vertices = len(adjacency_list)
    distances = [inf] * number_of_vertices
    previous_vertex: list[int | None] = [None] * number_of_vertices
    distances[source_vertex] = 0
    priority_queue = [(0, source_vertex)]

    while priority_queue:
        current_distance, current_vertex = heapq.heappop(priority_queue)

        if current_distance != distances[current_vertex]:
            continue

        for neighbour_vertex, edge_weight in adjacency_list[current_vertex]:
            candidate_distance = current_distance + edge_weight
            if candidate_distance < distances[neighbour_vertex]:
                distances[neighbour_vertex] = candidate_distance
                previous_vertex[neighbour_vertex] = current_vertex
                heapq.heappush(
                    priority_queue,
                    (candidate_distance, neighbour_vertex),
                )

    return distances, previous_vertex
