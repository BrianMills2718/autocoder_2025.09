"""Shared pytest fixtures"""
import pytest
import tempfile
from pathlib import Path

@pytest.fixture
def temp_output_dir():
    """Temporary directory for test outputs"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
