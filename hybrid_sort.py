def merge_sort(arr, S, metrics=None):
    """Hybrid merge-insertion sort tracking comparisons and swaps."""
    if metrics is None:
        metrics = {"comparisons": 0, "swaps": 0}

    if len(arr) <= S:
        insert_sort(arr, metrics)
        return arr, metrics

    mid = len(arr) // 2
    left, _ = merge_sort(arr[:mid], S, metrics)
    right, _ = merge_sort(arr[mid:], S, metrics)

    return merge(left, right, metrics), metrics


def merge(left, right, metrics):
    result = []
    i = j = 0
    len_left, len_right = len(left), len(right)

    while i < len_left and j < len_right:
        metrics["comparisons"] += 1
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result += left[i:]
    result += right[j:]
    return result


def insert_sort(arr, metrics):
    for i in range(1, len(arr)):
        j = i - 1
        while j >= 0:
            metrics["comparisons"] += 1
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                metrics["swaps"] += 1
                j -= 1
            else:
                break
    return arr