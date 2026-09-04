import matplotlib.pyplot as plt
import numpy as np

from hybrid_sort import merge_sort
from input_generator import generate_array

# ==========================================
# BENCHMARK CONFIGURATION
# ==========================================
# Set the maximum integer value allowed across all generated arrays
MAX_X = 10_000_000

# Insertion sort threshold S
S_THRESHOLD = 32

# Test input sizes (adjust range as needed for runtime feasibility)
TEST_SIZES = [1_000, 5_000, 10_000, 50_000, 100_000, 500_000, 1_000_000]

DISTRIBUTIONS = ["random", "sorted", "reversed"]


def run_benchmark(sizes=TEST_SIZES, max_x=MAX_X, s_threshold=S_THRESHOLD):
    results = {dist: [] for dist in DISTRIBUTIONS}

    print(f"=== Running Benchmark ===")
    print(f"Threshold (S) : {s_threshold}")
    print(f"Element Bounds: [1, {max_x:,}] (Max X = {max_x:,})")
    print("-" * 55)
    print(f"{'Size (N)':<12} | {'Distribution':<12} | {'Comparisons':<15}")
    print("-" * 55)

    for n in sizes:
        for dist in DISTRIBUTIONS:
            # Generate dataset enforcing max_x cap
            data = generate_array(size=n, distribution=dist, max_x=max_x)

            # Sanity verification of bounds
            assert max(data) <= max_x, f"Element exceeded max_x={max_x}!"
            assert min(data) >= 1, "Element below minimum 1!"

            # Run hybrid sort and record comparison metrics
            _, metrics = merge_sort(data, s_threshold)
            comps = metrics["comparisons"]
            results[dist].append(comps)

            print(f"{n:<12,d} | {dist:<12} | {comps:<15,d}")

    plot_results(sizes, results, s_threshold, max_x)


def plot_results(sizes, results, s_val, max_x):
    plt.figure(figsize=(10, 6))

    markers = {"random": "o", "sorted": "s", "reversed": "^"}
    for dist, comps in results.items():
        plt.plot(sizes, comps, marker=markers[dist], label=f"Actual ({dist.capitalize()})")

    # Theoretical O(N log2 N) baseline curve
    n_vals = np.array(sizes)
    theoretical_baseline = n_vals * np.log2(n_vals)
    scale_factor = results["random"][-1] / theoretical_baseline[-1]
    plt.plot(
        n_vals,
        theoretical_baseline * scale_factor,
        "--",
        color="gray",
        label="Reference: c * N log2(N)",
    )

    plt.title(f"Hybrid Merge Sort Comparisons vs. Array Size\n(S = {s_val}, Max X = {max_x:,})")
    plt.xlabel("Array Size (N)")
    plt.ylabel("Number of Comparisons")
    plt.xscale("log")
    plt.yscale("log")
    plt.grid(True, which="both", linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    run_benchmark()