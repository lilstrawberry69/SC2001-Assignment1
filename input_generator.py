import random


def generate_array(size: int, max_x: int, distribution: str = "random") -> list[int]:
    """Generates an array bounded by [1, max_x], controlled by the caller."""
    if distribution == "random":
        return [random.randint(1, max_x) for _ in range(size)]

    elif distribution == "sorted":
        if size <= max_x:
            return list(range(1, size + 1))
        step = max_x / size
        return [int(1 + i * step) for i in range(size)]

    elif distribution == "reversed":
        if size <= max_x:
            return list(range(size, 0, -1))
        step = max_x / size
        return [int(max_x - i * step) for i in range(size)]

    else:
        raise ValueError(f"Unknown distribution: {distribution}")