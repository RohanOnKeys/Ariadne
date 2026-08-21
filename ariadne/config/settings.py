"""
config.settings

Environment-driven configuration for Ariadne (see `.env.example` for the
supported keys). Read once at import time from the process environment;
nothing here loads a `.env` file, if that's ever wanted, this is the
only module that needs to change.
"""

import os
from pathlib import Path

CACHE_DIR = Path(os.environ.get("CACHE_DIR", "./data/catalogs"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

SPACETRACK_USERNAME = os.environ.get("SPACETRACK_USERNAME") or None
SPACETRACK_PASSWORD = os.environ.get("SPACETRACK_PASSWORD") or None

CORS_ORIGINS = [
    origin.strip() for origin in os.environ.get("CORS_ORIGINS", "*").split(",") if origin.strip()
]
