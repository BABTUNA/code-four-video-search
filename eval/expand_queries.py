"""Bootstrap labeled truth spans from the corpus's own transcripts and captions.

Each query is defined by keyword patterns. Truth candidates are discovered by
scanning EVERY transcript/caption Doc in the store - corpus-wide, so labels
are not biased toward what the search system can find - then merged and
padded. The output is an audit sheet a human ticks through before the spans
are trusted; this script proposes, it does not bless.

Usage:
    uv run python eval/expand_queries.py > eval/audit-sheet.md
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from c4search.store import Store  # noqa: E402

PAD_S = 10.0
MERGE_GAP_S = 45.0

# (query, type, [regex patterns], modalities to scan)
SPECS = [
    ("officer reads someone their rights", "easy",
     [r"right to remain silent", r"attorney", r"appointed"], ("transcript",)),
    ("officer orders the driver to step out of the vehicle", "easy",
     [r"step (out|outside)", r"out of the (car|vehicle)"], ("transcript",)),
    ("a person is being handcuffed", "hard",
     [r"handcuff", r"hands behind your back", r"cuff"], ("transcript", "caption")),
    ("a vehicle stopped at night", "hard",
     [r"traffic stop", r"pulled over", r"drive-thru"], ("caption",)),
    ("someone raises their voice", "hard",
     [r"raised voice", r"shout", r"yell"], ("caption", "vocal_arousal")),
]


def scan(store: Store, patterns: list[str], modalities: tuple[str, ...]):
    compiled = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    hits = []
    for modality in modalities:
        for _, doc in store.docs(modality=modality):
            if any(pattern.search(doc.text) for pattern in compiled):
                hits.append((doc.video_id, doc.t_start, doc.t_end, doc.text))
    return sorted(hits)


def merge_and_pad(hits):
    spans = []
    for video, start, end, text in hits:
        if spans and spans[-1][0] == video and start - spans[-1][2] <= MERGE_GAP_S:
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
    return f"{minutes}:{secs:02d}"


def main() -> None:
    store = Store(Path("data/index"))
    print("# Ground-truth audit sheet")
    print("\nOpen the video at the timestamp, watch ~20s, tick if it matches.\n")
    for query, kind, patterns, modalities in SPECS:
        print(f'## "{query}"  ({kind})')
        spans = merge_and_pad(scan(store, patterns, modalities))
        if not spans:
            print("- (no candidates found by scan)")
        for video, start, end, texts in spans:
            evidence = texts[0][:80].replace("\n", " ")
            print(f"- [ ] **{video} {hms(start)}-{hms(end)}** · \"{evidence}\"")
        print()


if __name__ == "__main__":
    main()
