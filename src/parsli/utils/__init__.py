from __future__ import annotations


def expend_range(current_range, new_range):
    if current_range is None:
        return new_range

    return [
        min(current_range[0], new_range[0]),
        max(current_range[1], new_range[1]),
    ]
