"""
Global pytest conftest.py
Patches bcrypt to use 4 rounds during tests (vs 12 in production).
This cuts fixture setup time from ~6s to ~0.1s per test file with no security impact.
"""
import os

# Ensure isolated SQLite database is used during automated test runs
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_medcy.db"

import bcrypt
import pytest
from unittest.mock import patch

# ── Speed up bcrypt for ALL tests ──────────────────────────────────────────────
# bcrypt rounds=4 is still cryptographically valid and indistinguishable from
# rounds=12 at the API level — it's just much faster in CI / local test runs.
_ORIGINAL_GENSALT = bcrypt.gensalt


def _fast_gensalt(rounds: int = 12, prefix: bytes = b"2b") -> bytes:
    """Override bcrypt.gensalt to always use rounds=4 during testing."""
    return _ORIGINAL_GENSALT(rounds=4, prefix=prefix)


# Apply the monkey-patch for the duration of the test session
bcrypt.gensalt = _fast_gensalt

# Also patch it inside the security module so hash_password() picks it up
import app.utils.security as _security_module
_security_module.bcrypt.gensalt = _fast_gensalt
