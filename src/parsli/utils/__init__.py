from __future__ import annotations

import math


def expend_range(current_range, new_range):
    if current_range is None:
        return new_range

    return [
        min(current_range[0], new_range[0]),
        max(current_range[1], new_range[1]),
    ]


def to_precision(float_value, precision=3):
    precision_factor = math.pow(10, precision)
    int_value = int(float_value * precision_factor)
    return int_value / precision_factor
