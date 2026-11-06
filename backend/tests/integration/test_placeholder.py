"""Integration tests are added as domain endpoints arrive.

Phase 3 validates the health endpoints in ``tests/unit/test_health.py``; a live
MySQL connection is required for the readiness probe and is covered by the
compose smoke test in CI.
"""
