def insertion_sort(a, left, right):
    for i in range(left + 1, right + 1):
        key = a[i]
        j = i - 1
        while j >= left and a[j] > key:
            a[j + 1] = a[j]
            j = j - 1
        a[j + 1] = key


def merge_ranges(a, temp, left, mid, right):
    i = left
    j = mid + 1
    k = left
    while i <= mid and j <= right:
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


def hybrid_recursive(a, temp, left, right, S):
    if left >= right:
        return
    if right - left + 1 <= S:
        insertion_sort(a, left, right)
        return
    mid = left + (right - left) // 2
    hybrid_recursive(a, temp, left, mid, S)
    hybrid_recursive(a, temp, mid + 1, right, S)
    merge_ranges(a, temp, left, mid, right)


def hybrid_sort(a, S):
    if len(a) <= 1:
        return
    temp = [0] * len(a)
    hybrid_recursive(a, temp, 0, len(a) - 1, S)

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
