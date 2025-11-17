"""
Shared pytest configuration and fixtures for backend tests.

Provides common test fixtures, database setup, and test utilities.
"""

import os
import sys
from pathlib import Path

import pytest

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set test environment variables
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/saltbitter_test")
os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
os.environ["ENVIRONMENT"] = "test"


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment before running tests."""
    # Ensure test database exists
    print("\n🧪 Setting up test environment...")
    yield
    print("\n✅ Test environment cleaned up")
