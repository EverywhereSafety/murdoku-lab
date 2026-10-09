"""Training-only terminal shaping; strict task success stays independent."""

import math


def terminal_reward(score, total_characters, config=None):
    config = config or {}
    mode = config.get("mode", "strict")
    if mode == "strict":
        return float(score["solved"])
    if mode != "placement_shaped":
        raise ValueError("unknown Murdoku reward mode")
    weight = float(config.get("placement_weight", 0.2))
    if not math.isfinite(weight) or not 0 <= weight <= 1:
        raise ValueError("placement weight must lie in [0,1]")
    count = score["placement_cells_correct"]
    if total_characters <= 0 or not 0 <= count <= total_characters:
        raise ValueError("invalid placement count")
    # Use integer counts, not the display statistic rounded to four decimals.
    return weight * (count / total_characters) + (1 - weight) * float(score["solved"])
