"""Tests for ariadne.ingest.txt."""

from ariadne.ingest.txt import parse_txt_text
from ariadne.models.state_vector import Frame


def test_parses_required_fields_only():
    text = "2026-01-01T00:00:00Z 7000 0 0 0 7.5 0\n"
    states, warnings = parse_txt_text(text)

    assert warnings == []
    assert len(states) == 1
    assert states[0].position.tolist() == [7000.0, 0.0, 0.0]
    assert states[0].frame == Frame.ECI
    assert states[0].norad_id is None


def test_parses_optional_trailing_norad_id():
    text = "2026-01-01T00:00:00Z 7000 0 0 0 7.5 0 25544\n"
    states, warnings = parse_txt_text(text)

    assert warnings == []
    assert states[0].norad_id == 25544


def test_blank_lines_and_comments_are_skipped():
    text = "# a comment\n\n2026-01-01T00:00:00Z 7000 0 0 0 7.5 0\n   \n"
    states, warnings = parse_txt_text(text)

    assert len(states) == 1
    assert warnings == []


def test_wrong_field_count_is_collected_as_a_warning():
    text = "2026-01-01T00:00:00Z 7000 0 0 0 7.5\n2026-01-01T00:01:00Z 7001 0 0 0 7.4 0\n"
    states, warnings = parse_txt_text(text)

    assert len(states) == 1
    assert len(warnings) == 1
    assert "line 1" in warnings[0]


def test_non_numeric_field_is_collected_as_a_warning():
    text = "2026-01-01T00:00:00Z not-a-number 0 0 0 7.5 0\n"
    states, warnings = parse_txt_text(text)

    assert states == []
    assert len(warnings) == 1


def test_naive_epoch_is_rejected():
    text = "2026-01-01T00:00:00 7000 0 0 0 7.5 0\n"
    states, warnings = parse_txt_text(text)

    assert states == []
    assert "naive" in warnings[0]
