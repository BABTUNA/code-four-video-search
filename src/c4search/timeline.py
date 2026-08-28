"""Small helpers for spans on a video's absolute timeline."""


def overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def merge_runs(labels: list[str], times: list[float], gap: float) -> list[tuple[float, float, str]]:
    """Collapse per-sample labels into (start, end, label) spans.

    Consecutive samples with the same label join one span while they are at
    most `gap` seconds apart; empty labels break runs and are dropped.
    """
    spans = []
    for label, time in zip(labels, times):
        if not label:
            continue
        if spans and spans[-1][2] == label and time - spans[-1][1] <= gap:
            spans[-1] = (spans[-1][0], time, label)
        else:
            spans.append((time, time, label))
    return spans
