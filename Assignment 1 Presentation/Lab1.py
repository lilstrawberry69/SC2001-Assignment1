def insertion_sort(a, left, right, counters, trace=False):
    for i in range(left + 1, right + 1):
        key = a[i]
        j = i - 1
        while j >= left:
            counters["comparisons"] += 1
            if trace:
                print(f"compare: a[{j}]={a[j]} > key={key} ?")
            if a[j] <= key:
                break
            a[j + 1] = a[j]
            j = j - 1
        a[j + 1] = key


def merge_ranges(a, temp, left, mid, right, counters, trace=False):
    i = left
    j = mid + 1
    k = left
    while i <= mid and j <= right:
        counters["comparisons"] += 1
        if trace:
            print(f"compare: a[{i}]={a[i]} <= a[{j}]={a[j]} ?")
        if a[i] <= a[j]:
            temp[k] = a[i]
            i = i + 1
        else:
            temp[k] = a[j]
            j = j + 1
        k = k + 1
    while i <= mid:
        temp[k] = a[i]
        i = i + 1
        k = k + 1
    while j <= right:
        temp[k] = a[j]
        j = j + 1
        k = k + 1
    for p in range(left, right + 1):
        a[p] = temp[p]


def hybrid_recursive(a, temp, left, right, S, counters, trace=False):
    if left >= right:
        return
    if right - left + 1 <= S:
        insertion_sort(a, left, right, counters, trace)
        return
    mid = left + (right - left) // 2
    hybrid_recursive(a, temp, left, mid, S, counters, trace)
    hybrid_recursive(a, temp, mid + 1, right, S, counters, trace)
    merge_ranges(a, temp, left, mid, right, counters, trace)


def hybrid_sort(a, S, trace=False):
    counters = {"comparisons": 0}
    if len(a) <= 1:
        return counters["comparisons"]
    temp = [0] * len(a)
    hybrid_recursive(a, temp, 0, len(a) - 1, S, counters, trace)
    return counters["comparisons"]


def merge_recursive(a, temp, left, right, counters, trace=False):
    if left >= right:
        return
    mid = left + (right - left) // 2
    merge_recursive(a, temp, left, mid, counters, trace)
    merge_recursive(a, temp, mid + 1, right, counters, trace)
    merge_ranges(a, temp, left, mid, right, counters, trace)


def original_mergesort(a, trace=False):
    counters = {"comparisons": 0}
    if len(a) <= 1:
        return counters["comparisons"]
    temp = [0] * len(a)
    merge_recursive(a, temp, 0, len(a) - 1, counters, trace)
    return counters["comparisons"]


def main():
    data = [17, 3, 14, 8, 19, 1, 12, 6, 10, 5,
            16, 2, 20, 9, 13, 4, 18, 7, 15, 11]
    threshold = 4

    hybrid_data = data[:]
    print(f"Original array ({len(data)} elements): {data}")
    print(f"\nHybrid sort trace (S={threshold}):")
    hybrid_comparisons = hybrid_sort(hybrid_data, threshold, trace=False)
    print(f"Sorted hybrid array: {hybrid_data}")
    print(f"Hybrid comparisons: {hybrid_comparisons}")

    merge_data = data[:]
    merge_comparisons = original_mergesort(merge_data)
    print(f"\nSorted original mergesort array: {merge_data}")
    print(f"Original mergesort comparisons: {merge_comparisons}")
    print(
        f"Comparison difference (hybrid - original): "
        f"{hybrid_comparisons - merge_comparisons}"
    )


if __name__ == "__main__":
    main()

# Works on one original array (in-place)
#   - Uses indices (left, right) on a single array `a`.
#   - No new lists are created during recursion.
#   - Insertion Sort and Merge both operate directly on `a`.

# previous version:
#   - Uses slicing: arr[:mid], arr[mid:].
#   - Each slice creates a new list.
#   - Recursive calls return new lists and merge builds another list.
#
# Why better:
#   - This version uses less memory (i think) by avoiding creating and copying many lists during the recursive call.
