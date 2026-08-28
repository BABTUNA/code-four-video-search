from c4search.evaluate import is_hit, score_query, summarize, tiou


def test_tiou():
    assert tiou((0, 10), (5, 15)) == 5 / 15
    assert tiou((0, 10), (20, 30)) == 0.0


def test_hit_by_midpoint_even_when_tiou_low():
    prediction = {"video": "v", "t_start": 9.0, "t_end": 11.0}
    truths = [{"video": "v", "start": 0.0, "end": 60.0}]
    assert is_hit(prediction, truths)  # tiny span inside a long truth


def test_hit_requires_same_video():
    prediction = {"video": "other", "t_start": 5.0, "t_end": 10.0}
    assert not is_hit(prediction, [{"video": "v", "start": 0.0, "end": 60.0}])


def test_summarize_counts_abstention_both_ways():
    results = [
        score_query({"query": "a", "type": "easy",
                     "truth": [{"video": "v", "start": 0, "end": 10}]},
                    [{"video": "v", "t_start": 2, "t_end": 8}]),
        score_query({"query": "b", "type": "no_answer", "truth": []}, []),
        score_query({"query": "c", "type": "hard",
                     "truth": [{"video": "v", "start": 50, "end": 60}]}, []),
    ]
    summary = summarize(results)
    assert summary["hit@1"] == 0.5
    assert summary["abstention_acc"] == 1.0
    assert summary["false_abstain"] == 1
