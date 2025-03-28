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


def sort_fields(names):
    remaining = []
    group_count = 0
    groups = {
        "strike_slip": [],
        "dip_slip": [],
        "tensile_slip": [],
    }
    for name in names:
        k = "_".join(name.split("_")[:2])
        if k in groups:
            groups[k].append(name)
            groups[k].sort()
            group_count += 1
        else:
            remaining.append(name)
            remaining.sort()

    sorted_list = []
    while group_count:
        for v in groups.values():
            if len(v):
                sorted_list.append(v.pop(0))
                group_count -= 1
    sorted_list.extend(remaining)

    return sorted_list
