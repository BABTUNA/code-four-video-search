import c4search.extractors  # noqa: F401  (registers extractors)
from c4search.extractors.caption import chunk_spans, events_to_docs


def test_chunk_spans_cover_the_video():
    assert chunk_spans(650.0, 300.0) == [(0.0, 300.0), (300.0, 600.0), (600.0, 650.0)]
    assert chunk_spans(120.0, 300.0) == [(0.0, 120.0)]


def test_events_become_absolute_and_clamped():
    events = [
        {"start_s": 10.0, "end_s": 25.0, "description": "officer approaches SUV",
         "tags": ["traffic stop"]},
        {"start_s": 290.0, "end_s": 400.0, "description": "beyond the chunk", "tags": []},
        {"start_s": 5.0, "end_s": 6.0, "description": "   ", "tags": []},
    ]
    docs = events_to_docs(events, "video_1", chunk_start=300.0, chunk_end=600.0,
                          cost=0.01)
    assert len(docs) == 2  # blank description dropped
    assert (docs[0].t_start, docs[0].t_end) == (310.0, 325.0)
    assert docs[0].extra["tags"] == ["traffic stop"]
    assert (docs[1].t_start, docs[1].t_end) == (590.0, 600.0)  # clamped into chunk
