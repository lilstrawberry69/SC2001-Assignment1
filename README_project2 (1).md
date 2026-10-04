# Project 2: Dijkstra's Algorithm with Two Representations

## 1. Project overview

This project studies how the representation of a weighted graph and the priority queue used by Dijkstra's algorithm affect performance.

Two implementations are compared:

| Implementation | Graph representation | Priority queue | Expected time |
|---|---|---|---|
| Part (a) | Adjacency matrix | Array-based minimum search | \(O(V^2)\) |
| Part (b) | Adjacency list | Binary min-heap | \(O((V+E)\log V)\) |

Here:

- \(V=|V|\) is the number of vertices.
- \(E=|E|\) is the number of directed weighted edges.

The project then compares the implementations under sparse, medium-density, and dense graph conditions.

Dijkstra's algorithm is valid because all generated edge weights are non-negative.

---

## 2. Research questions

The project answers three questions:

1. How does the matrix-and-array implementation scale as \(V\) and \(E\) change?
2. How does the adjacency-list-and-heap implementation scale as \(V\) and \(E\) change?
3. Which implementation is better for sparse, medium-density, and dense graphs?

The final answer is expected to depend on graph density, graph size, memory availability, and implementation overhead. The heap/list implementation is not assumed to be faster in every circumstance.

---

## 3. Graph terminology

The input graph is:

\[
G=(V,E).
\]

### Vertices

A vertex is a node in the graph. If there are 100 vertices, they are labelled:

```text
0, 1, 2, ..., 99
```

### Edges

An edge is a directed connection with a weight:

```python
(source_vertex, destination_vertex, edge_weight)
```

For example:

```python
(0, 2, 3)
```

means:

> Vertex 0 has a directed edge to vertex 2 with weight 3.

The graph does not contain self-loops. Therefore, the maximum possible number of directed edges is:

\[
V(V-1).
\]

### Density

For a directed graph without self-loops:

\[
\text{density}=
\frac{E}{V(V-1)}.
\]

The experiments use approximate densities:

```text
Sparse:  0.01
Medium:  0.10
Dense:   0.50
```

---

## 4. Graph generation

Graphs are generated with a fixed random seed so that the same graph can be reproduced.

The generator first creates a directed path:

```text
0 → 1 → 2 → ... → V - 1
```

This ensures every vertex is reachable from source vertex 0. Additional random edges are then added until the requested number of edges is reached.

The graph is therefore guaranteed to be source-reachable from vertex 0. It is not necessarily strongly connected: a path may exist from vertex 0 to every vertex without a path existing in the reverse direction.

### Graph-generation parameters

```python
SOURCE_VERTEX = 0
MIN_EDGE_WEIGHT = 1
MAX_EDGE_WEIGHT = 100
```

All edge weights are positive, which satisfies Dijkstra's non-negative-weight requirement.

---

## 5. Reproducibility settings

The project uses separate seeds for graph-density families:

```python
GRAPH_SEEDS = {
    "sparse": 20261001,
    "medium": 20261002,
    "dense": 20261003,
}
```

The fixed-
\(V\) edge experiment uses:

```python
EDGE_EXPERIMENT_SEED = 20261010
```

For each graph configuration, the seed is combined deterministically with the vertex count or edge-count setting. The exact seed is saved in the raw CSV.

Using a fixed seed means the graph can be regenerated with the same:

- Number of vertices.
- Number of edges.
- Weight range.
- Random-number generator.
- Seed.

---

## 6. Graph representations

### 6.1 Adjacency matrix

The matrix stores a value for every possible pair of vertices:

```text
matrix[u][v] = edge weight from u to v
matrix[u][v] = infinity if no edge exists
matrix[u][u] = 0
```

The matrix uses:

\[
O(V^2)
\]

space.

It provides direct access to a potential edge, but it also requires the algorithm to inspect non-edges.

### 6.2 Adjacency list

The adjacency list stores only existing outgoing edges:

```text
adjacency_list[u] = [(v, weight), ...]
```

For example:

```python
adjacency_list[0] = [(1, 10), (2, 3)]
```

The adjacency list uses:

\[
O(V+E)
\]

space.

It is usually more suitable for sparse graphs because it does not store absent edges.

---

## 7. Common Dijkstra algorithm

Both implementations use the same shortest-path logic:

```text
1. Set the source distance to 0.
2. Set all other distances to infinity.
3. Select the unsettled vertex with the smallest distance.
4. Mark it as settled.
5. Relax its outgoing edges.
6. Repeat until no reachable unsettled vertex remains.
```

Relaxing an edge means checking whether travelling through the current vertex produces a shorter path:

\[
\text{candidate distance}
=
\text{distance}[u]+w(u,v).
\]

If the candidate is smaller than the current distance to \(v\), update the distance and predecessor.

The shortest-distance output of both implementations must match for every graph.

---

## 8. Part (a): matrix plus array

### Implementation change

The abstract Dijkstra operation is:

```text
u ← unsettled vertex with smallest distance
for each neighbour v of u:
    relax (u, v)
```

With an adjacency matrix and array, it becomes:

```text
u ← scan all V vertices to find the minimum
for v = 0 to V - 1:
    inspect matrix[u][v]
    if an edge exists:
        relax (u, v)
```

The implementation records:

- `minimum_scan_checks`
- `matrix_neighbour_checks`
- `successful_relaxations`

### Time-complexity derivation

#### Minimum selection

There are up to \(V\) selections. Each selection scans \(V\) vertices:

\[
V\times O(V)=O(V^2).
\]

#### Matrix row scanning

For each selected vertex, the algorithm scans a complete matrix row of length \(V\):

\[
V\times O(V)=O(V^2).
\]

#### Total

\[
T_{\text{matrix}}(V,E)
=
O(V^2)+O(V^2)
=
O(V^2).
\]

A more general expression is \(\Theta(V^2+E)\), which simplifies to \(\Theta(V^2)\) for a matrix-based implementation because \(E\leq V(V-1)\).

Space complexity:

\[
O(V^2).
\]

### Part (a) experiments

#### A1: vary V at fixed density

Use the default larger vertex list:

```python
VERTEX_COUNTS = [100, 200, 400, 800, 1600, 3200]
```

Run three graph families:

```text
Sparse:  E ≈ 0.01V(V−1)
Medium:  E ≈ 0.10V(V−1)
Dense:   E ≈ 0.50V(V−1)
```

This varies both \(V\) and \(E\), but keeps density approximately constant. It answers:

> How does the implementation scale as the graph grows within each density family?

Expected result:

> Runtime follows approximately \(V^2\) for all density families because the matrix scans \(V^2\) positions regardless of how many actual edges exist.

#### A2: vary E at fixed V

Use:

```text
V = 1000
E = 999, 2,000, 5,000, 10,000, 50,000, 250,000, 999,000
```

This isolates the effect of edge count while \(V\) remains fixed.

Expected result:

> Matrix runtime should remain comparatively stable because the dominant work is determined by \(V^2\), not only by the number of existing edges.

---

## 9. Part (b): adjacency list plus min-heap

### Implementation change

The abstract Dijkstra operation is:

```text
u ← unsettled vertex with smallest distance
for each neighbour v of u:
    relax (u, v)
```

With an adjacency list and min-heap, it becomes:

```text
(distance, u) ← remove minimum from heap
if entry is stale:
    skip it
for each actual (v, weight) in adjacency_list[u]:
    relax (u, v)
if distance improves:
    push new entry into heap
```

Python's `heapq` does not directly support decrease-key. The implementation uses lazy deletion: improved entries are inserted, and outdated entries are skipped later.

The implementation records:

- `edge_scans`
- `heap_pushes`
- `heap_pops`
- `stale_heap_pops`
- `successful_relaxations`

### Time-complexity derivation

#### Heap insertion

When a distance improves, the new `(distance, vertex)` pair is inserted into the binary min-heap. A heap insertion costs:

\[
O(\log V).
\]

Successful relaxations are associated with graph edges, so the heap-update contribution is bounded by:

\[
O(E\log V).
\]

#### Heap extraction

The algorithm repeatedly removes the smallest heap entry. Each heap removal costs:

\[
O(\log V).
\]

The standard analysis accounts for up to \(O(V)\) meaningful vertex extractions and additional stale entries created by lazy deletion. This gives a contribution bounded by:

\[
O(V\log V)+O(E\log V).
\]

#### Edge processing

The adjacency list stores only existing edges. Across all processed vertices, the algorithm examines the outgoing edges:

\[
O(E).
\]

#### Total

Combining the components:

\[
\begin{aligned}
T_{\text{heap}}(V,E)
&=O(V\log V) \\
&\quad+O(E\log V) \\
&\quad+O(E) \\
&=O((V+E)\log V).
\end{aligned}
\]

For connected graphs where \(E\geq V-1\), this is often simplified to:

\[
O(E\log V).
\]

Space complexity:

\[
O(V+E).
\]

### Part (b) experiments

Use exactly the same graph instances as Part (a).

#### B1: vary V at fixed density

```text
Densities: 0.01, 0.10, 0.50
V: 100, 200, 400, 800, 1600, 3200
```

Build the adjacency list from the same edge list used to build the matrix. Run three trials and report median CPU time.

#### B2: vary E at fixed V

```text
V = 1000
E = 999, 2,000, 5,000, 10,000, 50,000, 250,000, 999,000
```

Expected result:

> Runtime and edge scans should generally increase with \(E\), because the adjacency-list implementation processes existing edges and performs heap operations for improved distances.

---

## 10. Experimental methodology

For every graph configuration:

1. Generate one edge list with a fixed seed.
2. Convert the same edge list into an adjacency matrix and adjacency list.
3. Use the same source vertex and edge weights.
4. Run each implementation three times.
5. Time only the Dijkstra function.
6. Compare the returned distance arrays.
7. Save every raw trial to CSV.
8. Report median CPU time.

Graph generation and representation conversion are outside the timed region.

### Timing pipeline

```text
Generate edge list
        ↓
Build matrix and adjacency list
        ↓
Start timer
        ↓
Run Dijkstra
        ↓
Stop timer
        ↓
Validate distances
        ↓
Save raw trial
```

### Whiskers

Whiskers should be labelled explicitly as one of:

- Interquartile range (IQR), or
- Minimum-to-maximum trial range.

Do not call them confidence intervals unless a formal confidence interval is calculated.

---

## 11. Required figures

Do not show one graph per raw graph configuration. Aggregate the measurements into summary figures.

### Figure 1: runtime versus V

Create one three-panel figure:

```text
Sparse density | Medium density | Dense density
```

The default run uses:

```text
V = 100, 200, 400, 800, 1600, 3200
```

For Part (a), show:

- Matrix empirical median CPU time.
- Scaled \(O(V^2)\) theoretical reference.

For Part (b), generate a separate equivalent figure showing:

- Heap empirical median CPU time.
- Scaled \(O((V+E)\log V)\) theoretical reference.

Do not combine heap/list empirical runtime into the Part (a) or Part (b) figure. Use a separate Part (c) comparison figure for direct comparison.

The theoretical curves must be scaled references, not raw complexity values plotted directly as seconds:

```python
matrix_reference = scale_matrix * V_values**2
heap_reference = (
    scale_heap
    * (V_values + E_values)
    * np.log2(V_values)
)
```

Label them:

```text
Empirical median CPU time
Scaled O(V²) reference
Scaled O((V+E) log V) reference
```

### Figure 2: runtime versus E at fixed V

Use:

```text
V = 1000
E = 999, 2,000, 5,000, 10,000, 50,000, 250,000, 999,000
```

Generate separate figures:

- Part (a): matrix empirical runtime with a scaled \(O(V^2)\) horizontal reference.
- Part (b): heap empirical runtime with a scaled \(O((V+E)\log V)\) reference.

Then combine both empirical series only in the Part (c) comparison figure.

### Figure 3: speedup versus density

This belongs to Part (c).

For every matching graph configuration:

\[
\text{speedup}
=
\frac{T_{\text{matrix}}}{T_{\text{heap}}}.
\]

Use the median CPU time for each implementation.

Interpretation:

- Speedup greater than 1: adjacency list + heap is faster.
- Speedup less than 1: matrix + array is faster.
- Speedup close to 1: similar performance.

Add a horizontal reference line at speedup = 1.

### Figure 4: operation counts

Optional supporting figure:

- Matrix checks versus \(V^2\).
- Heap edge scans versus \(E\).
- Heap pushes and pops versus \(E\).

---

## 12. Part (c): direct comparison

Part (c) reuses the same graph configurations and results from Parts (a) and (b). It should not generate a separate unrelated graph set unless the crossover is unclear.

### Comparison table

| Graph type | \(V\) | \(E\) | Matrix median | Heap median | Faster |
|---|---:|---:|---:|---:|---|
| Sparse | ... | ... | ... | ... | ... |
| Medium | ... | ... | ... | ... | ... |
| Dense | ... | ... | ... | ... | ... |

### Interpretation

For sparse graphs:

\[
E\ll V^2.
\]

The adjacency-list/min-heap implementation is generally better because it stores and processes only existing edges.

For dense graphs:

\[
E\approx V^2.
\]

The matrix/array implementation may become competitive because it has direct indexed access and avoids heap-management overhead.

### Optional crossover experiment

If the initial results do not clearly show where performance changes, run a density sweep at fixed \(V\):

```text
V = 1000
Density = 0.001, 0.005, 0.01, 0.05,
          0.10, 0.25, 0.50, 0.75, 1.00
```

Plot:

\[
\frac{T_{\text{matrix}}}{T_{\text{heap}}}
\]

against density, with a horizontal line at 1. This shows the empirical crossover for this implementation and machine.

---

## 13. Running the project

### Quick correctness run

```bash
python dijkstra_project.py --quick
```

### Full experiment

The default/full run uses the larger vertex list:

```text
V = 100, 200, 400, 800, 1600, 3200
```

Run:

```bash
python dijkstra_project.py --full
```

### Plot results

```bash
python plot_dijkstra_results.py
```

Expected outputs:

```text
dijkstra_results.csv
dijkstra_summary.csv
figures/
```

The code should also support a correctness mode:

```bash
python dijkstra_project.py --test
```

---

## 14. Raw and summary data

### Raw CSV

Every trial is saved with fields including:

```text
implementation
graph_family
number_of_vertices
number_of_edges
density
random_seed
source_vertex
trial
cpu_seconds
wall_seconds
minimum_scan_checks
matrix_neighbour_checks
edge_scans
heap_pushes
heap_pops
stale_heap_pops
successful_relaxations
correct
```

### Summary CSV

The summary groups by:

```text
implementation
graph_family
number_of_vertices
number_of_edges
density
```

It reports:

- Median CPU time.
- Median wall time.
- Trial count.
- Median operation counts where appropriate.

---

## 15. Expected comparison

| Situation | Likely better implementation | Reason |
|---|---|---|
| Large sparse graph | Adjacency list + min-heap | Processes only existing edges and uses less memory |
| Dense graph | Matrix + array may be competitive | Predictable \(O(V^2)\) work and no heap overhead |
| Memory-constrained setting | Adjacency list + min-heap | Uses \(O(V+E)\) instead of \(O(V^2)\) space |
| Small graph | Either | Constant factors and Python overhead may dominate |

The empirical conclusion must be based on the measured results, not assumed in advance.

---

## 16. Limitations

- CPU runtime depends on Python version, processor, operating system, and background processes.
- Three trials provide useful but limited information about timing variability.
- Graphs are randomly generated, so results depend on the documented seeds.
- Graph generation guarantees reachability from source vertex 0, not strong connectivity.
- The heap implementation uses lazy deletion, which creates stale heap entries.
- Matrix storage becomes memory-intensive for large \(V\).
- Scaled theoretical curves illustrate growth and are not exact runtime predictions.
- Different constant factors can cause empirical results to differ from asymptotic expectations.

---

## 17. Suggested conclusion

> The matrix-and-array implementation has \(O(V^2)\) time and \(O(V^2)\) space because it scans all vertices and possible matrix neighbours. The adjacency-list/min-heap implementation has \(O((V+E)\log V)\) time and \(O(V+E)\) space because it processes only existing edges and uses logarithmic heap operations. Therefore, the heap/list version is generally preferable for large sparse graphs, while the matrix/array version can be competitive for dense or moderate-sized graphs. The final conclusion is based on controlled experiments using the same generated graphs, repeated trials, median timings, and matching shortest-path outputs.

---

## 18. Reproducibility checklist

- [ ] All edge weights are non-negative.
- [ ] Source vertex is documented.
- [ ] Vertex and edge settings are documented.
- [ ] Seeds are recorded for every graph configuration.
- [ ] Both implementations use the same edge list.
- [ ] Both implementations use the same source vertex.
- [ ] Graph conversion is outside timing.
- [ ] Three trials are run per configuration.
- [ ] Median CPU time is reported.
- [ ] Whiskers are labelled as IQR or min–max.
- [ ] Distance arrays match.
- [ ] Raw trials are saved.
- [ ] The default full run uses the larger vertex list.
- [ ] Theory curves are scaled and labelled as references.
- [ ] Conclusions distinguish asymptotic complexity from empirical runtime.
