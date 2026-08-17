"""Ingestion: parse TLE/CSV/text catalog files into Ariadne's unified state representation."""

from ariadne.ingest.tle import load_tle_file, parse_tle_text

__all__ = ["load_tle_file", "parse_tle_text"]
