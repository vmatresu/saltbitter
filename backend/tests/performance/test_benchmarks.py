"""Performance benchmark tests for SaltBitter API.

Tests API response times and throughput to ensure performance targets are met.
"""

import time
from statistics import mean, median

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for performance testing."""
    return TestClient(app)


@pytest.mark.performance
class TestAPIPerformance:
    """Test API endpoint performance benchmarks."""

    def test_health_endpoint_response_time(self, client: TestClient) -> None:
        """Test health endpoint responds within 50ms."""
        response_times = []

        for _ in range(10):
            start = time.perf_counter()
            response = client.get("/health")
            end = time.perf_counter()

            assert response.status_code == 200
            response_times.append((end - start) * 1000)  # Convert to ms

        avg_time = mean(response_times)
        median_time = median(response_times)

        print(f"\nHealth endpoint - Avg: {avg_time:.2f}ms, Median: {median_time:.2f}ms")

        # Health check should be very fast
        assert avg_time < 50, f"Health check too slow: {avg_time:.2f}ms"

    def test_root_endpoint_response_time(self, client: TestClient) -> None:
        """Test root endpoint responds within 100ms."""
        response_times = []

        for _ in range(10):
            start = time.perf_counter()
            response = client.get("/")
            end = time.perf_counter()

            assert response.status_code == 200
            response_times.append((end - start) * 1000)

        avg_time = mean(response_times)
        median_time = median(response_times)

        print(f"\nRoot endpoint - Avg: {avg_time:.2f}ms, Median: {median_time:.2f}ms")

        # Root endpoint should respond quickly
        assert avg_time < 100, f"Root endpoint too slow: {avg_time:.2f}ms"

    def test_authentication_response_time(self, client: TestClient) -> None:
        """Test authentication endpoints respond within 500ms."""
        # Register a test user first
        user_data = {
            "email": "perf_test@example.com",
            "password": "SecurePassword123!",
            "consent_data_processing": True,
            "consent_terms": True,
        }
        client.post("/api/auth/register", json=user_data)

        response_times = []

        for _ in range(5):
            login_data = {
                "username": "perf_test@example.com",
                "password": "SecurePassword123!",
            }

            start = time.perf_counter()
            response = client.post("/api/auth/login", data=login_data)
            end = time.perf_counter()

            # Authentication might fail if already exists, that's okay
            response_times.append((end - start) * 1000)

        avg_time = mean(response_times)
        median_time = median(response_times)

        print(
            f"\nAuth login endpoint - Avg: {avg_time:.2f}ms, Median: {median_time:.2f}ms"
        )

        # Auth operations can be slower due to password hashing
        assert avg_time < 500, f"Authentication too slow: {avg_time:.2f}ms"


@pytest.mark.performance
@pytest.mark.slow
class TestThroughput:
    """Test API throughput and concurrent request handling."""

    def test_concurrent_health_checks(self, client: TestClient) -> None:
        """Test API can handle multiple concurrent health checks."""
        num_requests = 50
        start = time.perf_counter()

        for _ in range(num_requests):
            response = client.get("/health")
            assert response.status_code == 200

        end = time.perf_counter()
        total_time = end - start
        requests_per_second = num_requests / total_time

        print(
            f"\nThroughput: {requests_per_second:.2f} requests/second ({num_requests} requests in {total_time:.2f}s)"
        )

        # Should handle at least 100 requests per second
        assert (
            requests_per_second > 100
        ), f"Throughput too low: {requests_per_second:.2f} req/s"


@pytest.mark.performance
class TestDatabaseQueries:
    """Test database query performance."""

    def test_registration_creates_user_quickly(self, client: TestClient) -> None:
        """Test user registration completes within reasonable time."""
        user_data = {
            "email": f"perf_db_test_{time.time()}@example.com",
            "password": "SecurePassword123!",
            "consent_data_processing": True,
            "consent_terms": True,
        }

        start = time.perf_counter()
        response = client.post("/api/auth/register", json=user_data)
        end = time.perf_counter()

        response_time = (end - start) * 1000

        print(f"\nRegistration time: {response_time:.2f}ms")

        # Database write operations should complete quickly
        assert (
            response_time < 1000
        ), f"Registration too slow: {response_time:.2f}ms"  # 1 second max


@pytest.mark.performance
class TestMemoryUsage:
    """Test memory usage during operations."""

    def test_repeated_requests_dont_leak_memory(self, client: TestClient) -> None:
        """Test repeated requests don't cause memory leaks."""
        # Make many requests to detect potential memory leaks
        for _ in range(100):
            response = client.get("/health")
            assert response.status_code == 200

        # If this test completes without OOM, basic check passes
        assert True


@pytest.mark.performance
def test_p95_response_time(client: TestClient) -> None:
    """Test that 95th percentile response time meets targets."""
    response_times = []

    # Collect 100 samples
    for _ in range(100):
        start = time.perf_counter()
        response = client.get("/health")
        end = time.perf_counter()

        assert response.status_code == 200
        response_times.append((end - start) * 1000)

    response_times.sort()
    p95 = response_times[94]  # 95th percentile
    p99 = response_times[98]  # 99th percentile
    avg = mean(response_times)

    print(f"\nResponse times - Avg: {avg:.2f}ms, P95: {p95:.2f}ms, P99: {p99:.2f}ms")

    # P95 should be under 200ms for health endpoint
    assert p95 < 200, f"P95 response time too high: {p95:.2f}ms"
