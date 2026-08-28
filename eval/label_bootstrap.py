"""Propose ground-truth candidates for the labeled query set.

Reads query specs from eval/label_specs.yaml, scans the indexed corpus's
transcript/caption/audio Docs for pattern matches, merges nearby matches into
padded spans, and prints two things per query: a human audit checklist and a
ready-to-paste YAML truth block. A human watches ~20 seconds at each proposed
timestamp and keeps only the spans where the event really occurs - the scan
proposes, the audit decides.

Known bias, stated openly: proposals come from the corpus's own indexes, so an
event that no index captured cannot be proposed. Offset by hand-adding spans
found by watching (especially for visual- and audio-only queries).

Usage:
    uv run python eval/label_bootstrap.py > eval/audit-sheet.md
"""

import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from c4search.store import Store  # noqa: E402

PAD_S = 8.0        # context padding around merged matches
JOIN_GAP_S = 30.0  # matches closer than this belong to one event


def scan(store: Store, patterns: list[str], modalities: list[str]):
    compiled = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    hits = []
    for modality in modalities:
        for _, doc in store.docs(modality=modality):
            if any(pattern.search(doc.text) for pattern in compiled):
                hits.append((doc.video_id, doc.t_start, doc.t_end, doc.text))
    return sorted(hits)


def join_and_pad(hits):
    spans = []
    for video, start, end, text in hits:
        if spans and spans[-1][0] == video and start - spans[-1][2] <= JOIN_GAP_S:
            spans[-1][2] = max(spans[-1][2], end)
            spans[-1][3].append(text)
        else:
            spans.append([video, start, end, [text]])
    return [
        (video, max(0.0, start - PAD_S), end + PAD_S, texts)
        for video, start, end, texts in spans
    ]


def hms(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def main() -> None:
    store = Store(Path("data/index"))
    specs = yaml.safe_load(Path("eval/label_specs.yaml").read_text())["specs"]

    print("# Truth-span audit sheet")
    print("\nJump to each timestamp, watch about twenty seconds, and keep the")
    print("box only if the event is really there. Strike the rest.\n")
    for spec in specs:
        print(f'## "{spec["query"]}"  ({spec["type"]})')
        spans = join_and_pad(scan(store, spec["patterns"], spec["scan"]))
        if not spans:
            print("- (scan proposed nothing - label by watching, or drop)")
        for video, start, end, texts in spans:
            evidence = texts[0][:70].replace("\n", " ")
            print(f'- [ ] **{video} {hms(start)}-{hms(end)}** · "{evidence}"')
        print("\nTruth YAML for kept boxes:")
        print("```yaml")
        print(f"  - query: {spec['query']}")
        print(f"    type: {spec['type']}")
        print("    truth:")
        for video, start, end, _ in spans:
            print(f"      - {{video: {video}, start: {start:.0f}, end: {end:.0f}}}")
        print("```\n")


if __name__ == "__main__":
    main()
