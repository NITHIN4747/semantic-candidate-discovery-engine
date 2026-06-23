"""
tests/test_cosine.py
====================
Unit tests for the cosine similarity engine.
RULE: Only uses Python stdlib — no numpy, no scipy.

Run with: python -m pytest tests/test_cosine.py -v
"""

import math
import sys
import os

# Allow running from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from rank import cosine_similarity


class TestCosineSimilarity:
    """Tests for the raw-loop cosine similarity function."""

    def test_identical_vectors_return_1(self):
        """Two identical vectors should have cosine similarity = 1.0"""
        vec = [1.0, 2.0, 3.0, 4.0]
        result = cosine_similarity(vec, vec)
        assert abs(result - 1.0) < 1e-9, f"Expected 1.0, got {result}"

    def test_opposite_vectors_return_minus_1(self):
        """Perfectly opposite vectors should return -1.0"""
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [-1.0, 0.0, 0.0]
        result = cosine_similarity(vec_a, vec_b)
        assert abs(result - (-1.0)) < 1e-9, f"Expected -1.0, got {result}"

    def test_orthogonal_vectors_return_0(self):
        """Perpendicular vectors should return 0.0"""
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [0.0, 1.0, 0.0]
        result = cosine_similarity(vec_a, vec_b)
        assert abs(result - 0.0) < 1e-9, f"Expected 0.0, got {result}"

    def test_zero_vector_returns_0(self):
        """A zero vector should return 0.0 safely (no division by zero)"""
        vec_a = [0.0, 0.0, 0.0]
        vec_b = [1.0, 2.0, 3.0]
        result = cosine_similarity(vec_a, vec_b)
        assert result == 0.0, f"Expected 0.0, got {result}"

    def test_known_value(self):
        """Manual calculation verification."""
        # a = [1, 2], b = [3, 4]
        # dot = 1*3 + 2*4 = 11
        # |a| = sqrt(5), |b| = sqrt(25) = 5
        # cos = 11 / (sqrt(5) * 5) = 11 / 11.180... ≈ 0.9839
        vec_a = [1.0, 2.0]
        vec_b = [3.0, 4.0]
        expected = 11.0 / (math.sqrt(5) * 5.0)
        result = cosine_similarity(vec_a, vec_b)
        assert abs(result - expected) < 1e-9, f"Expected {expected:.6f}, got {result:.6f}"

    def test_score_range(self):
        """Score must always be in [-1.0, 1.0]"""
        import random
        random.seed(42)
        for _ in range(100):
            vec_a = [random.uniform(-1, 1) for _ in range(384)]
            vec_b = [random.uniform(-1, 1) for _ in range(384)]
            score = cosine_similarity(vec_a, vec_b)
            assert -1.0 - 1e-9 <= score <= 1.0 + 1e-9, f"Score out of range: {score}"

    def test_no_numpy_used(self):
        """
        Ensure the cosine_similarity function does not use numpy.
        Checks executable lines only — ignores docstrings and comments.
        Sandbox constraint enforcement.
        """
        import inspect
        source_lines = inspect.getsource(cosine_similarity).splitlines()
        # Filter out comment lines and the docstring — only check real code lines
        code_lines = [
            ln for ln in source_lines
            if ln.strip() and
            not ln.strip().startswith("#") and
            not ln.strip().startswith('"""') and
            not ln.strip().startswith("'''")
        ]
        for line in code_lines:
            assert "import numpy" not in line, f"numpy import found in cosine_similarity: {line}"
            assert "numpy." not in line,       f"numpy usage found in cosine_similarity: {line}"
            assert " np." not in line,         f"np. alias usage found in cosine_similarity: {line}"


if __name__ == "__main__":
    # Allow running directly: python tests/test_cosine.py
    tests = TestCosineSimilarity()
    test_methods = [m for m in dir(tests) if m.startswith("test_")]
    passed = 0
    failed = 0
    for name in test_methods:
        try:
            getattr(tests, name)()
            print(f"  [PASS]  {name}")
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL]  {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"  [ERROR] {name}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed}/{passed+failed} tests passed")
