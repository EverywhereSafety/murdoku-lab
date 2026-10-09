"""Task state, grading and the shared text/visual agent interface."""

from murdoku_lab.environment.state import Scratchpad
from murdoku_lab.environment.scoring import score_episode
from murdoku_lab.environment.actions import apply_structured_action


def environment_for(record, memory_path=None):
    from murdoku_lab.environment.vision import environment_for as create

    return create(record, memory_path)


__all__ = ["Scratchpad", "score_episode", "apply_structured_action", "environment_for"]
