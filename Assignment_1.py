def merge_sort(arr, S): #S is the value we are testing to finding out how far down we should split
    if len(arr) <= S:
        insert_sort(arr) #adjusted this base case to perform insertion sort
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)
def merge(left, right):
    result = []
    i = 0
    j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j+=1
    result += left[i:]
    result += right[j:]
    return result
def insert_sort(arr):
    for i in range(1,len(arr) - 1):
        j = i -1
        while j >= 0 and arr[j] > arr[j+1]:
            temp = arr[j]
            arr[j] = arr[j+1]
            arr[j+1] = temp
            j -=1
    