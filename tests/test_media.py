from pathlib import Path

from c4search.media import frame_time, parse_loudness


def test_frame_time_recovers_timestamps():
    assert frame_time(Path("000001.jpg"), fps=0.5) == 0.0
    assert frame_time(Path("000002.jpg"), fps=0.5) == 2.0
    assert frame_time(Path("000031.jpg"), fps=0.5) == 60.0


def test_parse_loudness_reads_ebur128_lines():
    stderr = "\n".join([
        "[Parsed_ebur128_0 @ 0x123] t: 0.099979  TARGET:-23 LUFS    "
        "M: -120.7 S:-120.7     I: -70.0 LUFS       LRA:   0.0 LU",
        "[Parsed_ebur128_0 @ 0x123] t: 1.09998   TARGET:-23 LUFS    "
        "M: -34.2 S:-120.7     I: -42.1 LUFS       LRA:   0.0 LU",
        "unrelated line",
    ])
    series = parse_loudness(stderr)
    assert len(series) == 2
    assert series[1] == [1.09998, -34.2]
