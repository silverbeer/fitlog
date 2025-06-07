"""
End-to-end tests for the deployed Fitlog API.

These tests run against the actual deployed Lambda function via API Gateway
to ensure the deployment is working correctly in the cloud environment.
"""

import os
from datetime import datetime

import pytest
import requests


class TestDeployedAPI:
    """Test suite for the deployed Fitlog API"""

    @pytest.fixture(scope="class")
    def api_base_url(self) -> str:
        """Get the API base URL from environment variable"""
        base_url = os.getenv("API_BASE_URL")
        if not base_url:
            pytest.skip("API_BASE_URL environment variable not set")
        return base_url.rstrip('/')

    @pytest.fixture(scope="class")
    def client(self, api_base_url: str):
        """HTTP client configured for the deployed API"""
        return APIClient(api_base_url)


class APIClient:
    """HTTP client for testing the deployed API"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "fitlog-e2e-tests/1.0"
        })

    def get(self, endpoint: str, **kwargs):
        """Make GET request to API endpoint"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, **kwargs)
        return response

    def post(self, endpoint: str, data: dict = None, **kwargs):
        """Make POST request to API endpoint"""
        url = f"{self.base_url}{endpoint}"
        if data:
            kwargs['json'] = data
        response = self.session.post(url, **kwargs)
        return response


class TestHealthAndStatus:
    """Test health check and status endpoints"""

    def test_health_check_endpoint(self, client: APIClient):
        """Test the root health check endpoint"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "message" in data
        assert "status" in data
        assert "environment" in data
        assert "s3_bucket" in data
        assert "lambda_function" in data
        assert "timestamp" in data

        # Verify content
        assert "Fitlog API v2.0.0" in data["message"]
        assert data["status"] == "healthy"
        assert data["environment"] == "dev"
        assert data["s3_bucket"] == "fitlog-dev-data"
        assert "fitlog-dev-api" in data["lambda_function"]

        # Verify timestamp is recent (within last 5 minutes)
        timestamp = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
        now = datetime.now().astimezone()
        time_diff = abs((now - timestamp).total_seconds())
        assert time_diff < 300, f"Timestamp too old: {time_diff} seconds"

    def test_test_endpoint(self, client: APIClient):
        """Test the /test endpoint for GitHub Actions verification"""
        response = client.get("/test")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["test"] == "success"
        assert "GitHub Actions deployment working" in data["message"]
        assert "environment_vars" in data
        assert "lambda_context" in data

        # Verify environment variables are set correctly
        env_vars = data["environment_vars"]
        assert env_vars["ENVIRONMENT"] == "dev"
        assert env_vars["S3_BUCKET"] == "fitlog-dev-data"
        assert "s3://fitlog-dev-data/fitlog.db" in env_vars["DUCKDB_PATH"]

        # Verify Lambda context
        lambda_ctx = data["lambda_context"]
        assert "fitlog-dev-api" in lambda_ctx["function_name"]


class TestRunsEndpoints:
    """Test runs-related endpoints"""

    def test_get_runs_endpoint(self, client: APIClient):
        """Test GET /runs endpoint"""
        response = client.get("/runs")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "message" in data
        assert "data" in data
        assert "todo" in data

        # Verify content
        assert "DuckDB S3 implementation" in data["message"]
        assert isinstance(data["data"], list)
        assert isinstance(data["todo"], list)
        assert len(data["todo"]) > 0

    def test_create_run_endpoint(self, client: APIClient):
        """Test POST /runs endpoint"""
        run_data = {
            "duration": "30:15:00",
            "distance": 3.2,
            "date": "06/07/25"
        }

        response = client.post("/runs", data=run_data)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "message" in data
        assert "received_data" in data
        assert "todo" in data

        # Verify received data matches what we sent
        received = data["received_data"]
        assert received["duration"] == run_data["duration"]
        assert received["distance"] == run_data["distance"]
        assert received["date"] == run_data["date"]

    def test_create_run_without_date(self, client: APIClient):
        """Test POST /runs endpoint without date (should default to today)"""
        run_data = {
            "duration": "25:30:00",
            "distance": 2.8
        }

        response = client.post("/runs", data=run_data)

        assert response.status_code == 200
        data = response.json()

        # Verify date was set to today
        received = data["received_data"]
        today = datetime.now().strftime("%m/%d/%y")
        assert received["date"] == today


class TestPushupsEndpoints:
    """Test pushups-related endpoints"""

    def test_get_pushups_endpoint(self, client: APIClient):
        """Test GET /pushups endpoint"""
        response = client.get("/pushups")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "message" in data
        assert "data" in data
        assert "todo" in data

        # Verify content
        assert "DuckDB S3 implementation" in data["message"]
        assert isinstance(data["data"], list)
        assert isinstance(data["todo"], list)

    def test_create_pushup_endpoint(self, client: APIClient):
        """Test POST /pushups endpoint"""
        pushup_data = {
            "count": 100,
            "date": "06/07/25"
        }

        response = client.post("/pushups", data=pushup_data)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "message" in data
        assert "received_data" in data
        assert "todo" in data

        # Verify received data
        received = data["received_data"]
        assert received["count"] == pushup_data["count"]
        assert received["date"] == pushup_data["date"]

    def test_create_pushup_without_date(self, client: APIClient):
        """Test POST /pushups endpoint without date"""
        pushup_data = {
            "count": 75
        }

        response = client.post("/pushups", data=pushup_data)

        assert response.status_code == 200
        data = response.json()

        # Verify date was set to today
        received = data["received_data"]
        today = datetime.now().strftime("%m/%d/%y")
        assert received["date"] == today


class TestActivitiesEndpoints:
    """Test activities-related endpoints"""

    def test_activity_status_endpoint(self, client: APIClient):
        """Test GET /activities/status endpoint"""
        response = client.get("/activities/status")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "message" in data
        assert "status" in data
        assert "stats" in data
        assert "todo" in data

        # Verify stats structure
        stats = data["stats"]
        assert "total_runs" in stats
        assert "total_pushups" in stats
        assert "current_streak" in stats

        # Verify placeholder values
        assert isinstance(stats["total_runs"], int)
        assert isinstance(stats["total_pushups"], int)
        assert isinstance(stats["current_streak"], int)


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_invalid_endpoint(self, client: APIClient):
        """Test that invalid endpoints return 404"""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_invalid_run_data(self, client: APIClient):
        """Test POST /runs with invalid data"""
        invalid_data = {
            "duration": "invalid",
            "distance": "not_a_number"
        }

        response = client.post("/runs", data=invalid_data)
        # Should return 422 for validation error
        assert response.status_code == 422

    def test_invalid_pushup_data(self, client: APIClient):
        """Test POST /pushups with invalid data"""
        invalid_data = {
            "count": "not_a_number"
        }

        response = client.post("/pushups", data=invalid_data)
        # Should return 422 for validation error
        assert response.status_code == 422


class TestAPIPerformance:
    """Test API performance and reliability"""

    def test_health_check_response_time(self, client: APIClient):
        """Test that health check responds quickly"""
        import time

        start_time = time.time()
        response = client.get("/")
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 5.0, f"Health check too slow: {response_time:.2f}s"

    def test_multiple_concurrent_requests(self, client: APIClient):
        """Test handling multiple concurrent requests"""
        import concurrent.futures

        def make_request():
            return client.get("/")

        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            responses = [future.result() for future in futures]

        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"


# Pytest configuration for E2E tests
def pytest_configure(config):
    """Configure pytest for E2E tests"""
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test against deployed API"
    )


# Mark all tests in this file as e2e tests
pytestmark = pytest.mark.e2e
