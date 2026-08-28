from pathlib import Path

import c4search.extractors  # noqa: F401  (registers extractors)
from c4search.extractors.diarize import officer_speaker, speaker_for
from c4search.ingest import annotate_speakers
from c4search.models import Doc
from c4search.store import Store

TURNS = [
    {"start": 0.0, "end": 10.0, "speaker": "S0", "role": "officer"},
    {"start": 12.0, "end": 20.0, "speaker": "S1", "role": "other"},
]


def test_officer_is_the_loudest_speaker():
    # S0 speaks near the mic (louder LUFS), S1 farther away.
    loudness = [[t, -20.0] for t in range(0, 10)] + [[t, -35.0] for t in range(12, 20)]
    assert officer_speaker(TURNS, loudness) == "S0"


def test_single_speaker_gets_no_officer_call():
    loudness = [[t, -20.0] for t in range(0, 10)]
    assert officer_speaker(TURNS[:1], loudness) is None


def test_speaker_for_picks_max_overlap():
    assert speaker_for(8.0, 14.0, TURNS)["speaker"] == "S0"
    assert speaker_for(13.0, 19.0, TURNS)["speaker"] == "S1"
    assert speaker_for(10.5, 11.5, TURNS) is None


def test_annotate_speakers_labels_transcripts(tmp_path):
    store = Store(tmp_path)
    store.add_docs([
        Doc("video_1", 1.0, 3.0, "transcript", "roll down your window"),
        Doc("video_1", 0.0, 10.0, "speaker_turn", "officer speaking",
            extra={"speaker": "S0", "role": "officer"}),
    ])
    annotate_speakers(store, "video_1")
    (_, transcript), = store.docs("video_1", "transcript")
    assert transcript.extra["role"] == "officer"
