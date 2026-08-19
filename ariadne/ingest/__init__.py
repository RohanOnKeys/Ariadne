"""Ingestion: parse TLE/CSV/text catalog files into Ariadne's unified state representation."""

from ariadne.ingest.csv import load_csv_file, parse_csv_text
from ariadne.ingest.sniff import IngestFormat, load_file, sniff_format
from ariadne.ingest.tle import load_tle_file, parse_tle_text
from ariadne.ingest.txt import load_txt_file, parse_txt_text

__all__ = [
    "load_tle_file",
    "parse_tle_text",
    "load_csv_file",
    "parse_csv_text",
    "load_txt_file",
    "parse_txt_text",
    "IngestFormat",
    "sniff_format",
    "load_file",
]
