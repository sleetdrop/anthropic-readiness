"""SSE meaning is independent of application read boundaries."""

import random
from itertools import pairwise

from anthropic_readiness.models import DecodeTail
from anthropic_readiness.sse import SSEDecoder

BODY = "\ufeff: comment\r\nevent: greeting\r\ndata: 你好\r\ndata: world\r\nid: x\r\nretry: 123\r\n\r\ndata: next\r\r".encode()


def decode(chunks: list[bytes]) -> tuple[list[tuple[str, str, str, int | None]], DecodeTail]:
    decoder = SSEDecoder(1024, 20)
    frames = []
    for index, chunk in enumerate(chunks):
        frames.extend(decoder.feed(chunk, float(index)))
    return [(f.event, f.data, f.id, f.retry) for f in frames], decoder.finish()


def test_all_single_split_positions_preserve_frames() -> None:
    expected = decode([BODY])
    assert len(expected[0]) == 2
    for split in range(len(BODY) + 1):
        assert decode([BODY[:split], BODY[split:]]) == expected
    randomizer = random.Random(173)
    for _ in range(30):
        points = sorted({0, len(BODY), *[randomizer.randrange(len(BODY)) for _ in range(12)]})
        assert decode([BODY[a:b] for a, b in pairwise(points)]) == expected


def test_utf8_and_crlf_across_reads() -> None:
    assert decode([bytes([b]) for b in BODY]) == decode([BODY])
    assert decode([BODY])[0][0][1] == "你好\nworld"


def test_multiline_data_uses_newline() -> None:
    assert decode([b"data: a\ndata: b\n\n"])[0][0][1] == "a\nb"


def test_bom_comments_and_bare_fields() -> None:
    frames, tail = decode(["\ufeff: hi\ndata\nid\n\n".encode()])
    assert frames == [("message", "", "", None)]
    assert not tail.pending_data


def test_unknown_fields_are_ignored() -> None:
    assert decode([b"unknown: x\nretry: invalid\nid: bad\x00id\ndata: a\n\n"])[0] == [
        ("message", "a", "", None)
    ]


def test_eof_does_not_dispatch_partial_event() -> None:
    frames, tail = decode([b"data: unfinished\n"])
    assert frames == []
    assert tail.pending_data
    assert not decode([b": comment"])[1].pending_data


def test_event_limits_bound_pending_data() -> None:
    decoder = SSEDecoder(10, 1)
    assert decoder.feed(b"data: " + b"x" * 10000, 0) == []
    assert decoder.finish().limit_kind == "max_event_bytes"
    decoder = SSEDecoder(100, 1)
    assert len(decoder.feed(b"data: a\n\ndata: b\n\n", 0)) == 1
    assert decoder.finish().limit_kind == "max_events"


def test_invalid_utf8_is_separate_from_incomplete_reads() -> None:
    assert decode([b"data: \xff\n\n"])[1].encoding_errors > 0
    assert decode([b"data: \xe4", b"\xbd\xa0\n\n"])[1].encoding_errors == 0
    assert decode([b"data: \xe4"])[1].encoding_errors > 0


def test_id_and_retry_persist_but_event_name_resets() -> None:
    frames, _ = decode([b"id: x\nretry: 12\nevent: first\ndata: a\n\ndata: b\n\n"])
    assert frames == [("first", "a", "x", 12), ("message", "b", "x", 12)]
