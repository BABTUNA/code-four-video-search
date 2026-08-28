from pathlib import Path

from c4search.search.plan import doc_modalities, fallback_plan
from c4search.search.verify import adjust_for_darkness, parse_verdict, pick_frames


def test_parse_verdict_extracts_json_from_chatter():
    output = 'Sure! Here is my answer:\n{"description": "d", "elements": [], ' \
             '"match": "yes", "reason": "r"} hope that helps'
    verdict = parse_verdict(output)
    assert verdict["match"] == "yes"
    assert parse_verdict("no json here") is None
    assert parse_verdict('{"match": "maybe"}') is None


def test_dark_frames_soften_only_visibility_limited_nos():
    limited = {"match": "no", "reason": "not visible",
               "elements": [{"name": "handcuffs", "present": "unclear"}]}
    assert adjust_for_darkness(limited, night=True)["match"] == "unclear"
    assert adjust_for_darkness(limited, night=False)["match"] == "no"

    confident = {"match": "no", "reason": "nothing of the sort occurs",
                 "elements": [{"name": "gunshot", "present": "no"}]}
    assert adjust_for_darkness(confident, night=True)["match"] == "no"

    yes = {"match": "yes", "reason": "clear", "elements": []}
    assert adjust_for_darkness(yes, night=True)["match"] == "yes"


def test_pick_frames_samples_within_span(tmp_path):
    for index in range(1, 31):  # 0.5 fps: frames at 0,2,...,58s
        (tmp_path / f"{index:06d}.jpg").touch()
    picked = pick_frames(tmp_path, frame_fps=0.5, t_start=10.0, t_end=20.0)
    times = [(int(p.stem) - 1) / 0.5 for p in picked]
    assert times and all(10.0 <= t <= 20.0 for t in times)

    many = pick_frames(tmp_path, 0.5, 0.0, 58.0, count=8)
    assert len(many) == 8


def test_pick_frames_guarantees_evidence_peaks(tmp_path):
    for index in range(1, 31):
        (tmp_path / f"{index:06d}.jpg").touch()
    picked = pick_frames(tmp_path, 0.5, 0.0, 58.0, count=8, focus_times=[42.0])
    times = [(int(p.stem) - 1) / 0.5 for p in picked]
    assert len(picked) == 8
    assert any(abs(t - 42.0) <= 1.0 for t in times)


def test_fallback_plan_covers_all_modalities():
    plan = fallback_plan("find shouting")
    assert plan["sub_queries"][0]["role"] == "required"
    assert doc_modalities(plan["sub_queries"][0]) >= {"transcript", "frame",
                                                      "audio_window", "caption"}
