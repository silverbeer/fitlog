"""
End-to-end tests for the deployed Fitlog API.

These tests run against the actual deployed Lambda function via API Gateway
to ensure the deployment is working correctly in the cloud environment.
"""

import os
from datetime import datetime

import pytest
import requests


# Global fixtures available to all test classes
@pytest.fixture(scope="session")
def api_base_url() -> str:
    """Get the API base URL from environment variable"""
    base_url = os.getenv("API_BASE_URL")
    if not base_url:
        pytest.skip("API_BASE_URL environment variable not set")
    return base_url.rstrip("/")


@pytest.fixture(scope="session")
def client(api_base_url: str):
    """HTTP client configured for the deployed API"""
    return APIClient(api_base_url)


class APIClient:
    """HTTP client for testing the deployed API"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "User-Agent": "fitlog-e2e-tests/1.0"}
        )

    def get(self, endpoint: str, **kwargs):
        """Make GET request to API endpoint"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, **kwargs)
        return response

    def post(self, endpoint: str, data: dict = None, **kwargs):
        """Make POST request to API endpoint"""
        url = f"{self.base_url}{endpoint}"
        if data:
            kwargs["json"] = data
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
        timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
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

        # Should return a list of runs (may be empty)
        assert isinstance(data, list)

        # If there are runs, verify structure
        if data:
            run = data[0]
            assert "activity_id" in run
            assert "date" in run
            assert "duration" in run
            assert "distance_miles" in run
            assert "pace_per_mile" in run

    def test_create_run_endpoint(self, client: APIClient):
        """Test POST /runs endpoint"""
        run_data = {"duration": "00:30:15", "distance": 3.2, "date": "06/07/25"}

        response = client.post("/runs", data=run_data)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure for successful creation
        assert "message" in data
        assert "run" in data
        assert "Run created successfully" in data["message"]

        # Verify created run data
        created_run = data["run"]
        assert "activity_id" in created_run
        assert created_run["duration"] == run_data["duration"]
        assert created_run["distance_miles"] == run_data["distance"]
        assert "pace_per_mile" in created_run
        assert created_run["activity_id"] is not None

    def test_create_run_without_date(self, client: APIClient):
        """Test POST /runs endpoint without date (should default to today)"""
        run_data = {"duration": "00:25:30", "distance": 2.8}

        response = client.post("/runs", data=run_data)

        assert response.status_code == 200
        data = response.json()

        # Verify successful creation
        assert "message" in data
        assert "run" in data
        assert "Run created successfully" in data["message"]

        # Verify run was created with today's date
        created_run = data["run"]
        created_date = datetime.fromisoformat(created_run["date"])
        today = datetime.now().date()
        assert created_date.date() == today

    def test_create_run_invalid_duration(self, client: APIClient):
        """Test POST /runs with invalid duration format"""
        invalid_data = {"duration": "invalid_format", "distance": 3.0}

        response = client.post("/runs", data=invalid_data)
        assert response.status_code == 400  # Bad request for invalid duration

    def test_create_run_invalid_distance(self, client: APIClient):
        """Test POST /runs with invalid distance"""
        invalid_data = {"duration": "30:00:00", "distance": -1.0}

        response = client.post("/runs", data=invalid_data)
        assert response.status_code == 422  # Validation error for negative distance

    def test_get_runs_with_date_filter(self, client: APIClient):
        """Test GET /runs with date filtering"""
        # Test with date range parameters
        response = client.get(
            "/runs",
            params={"start_date": "2025-01-01", "end_date": "2025-12-31", "limit": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10  # Respect limit parameter


class TestPushupsEndpoints:
    """Test pushups-related endpoints"""

    def test_get_pushups_endpoint(self, client: APIClient):
        """Test GET /pushups endpoint"""
        response = client.get("/pushups")

        assert response.status_code == 200
        data = response.json()

        # Should return a list of pushup entries (may be empty)
        assert isinstance(data, list)

        # If there are pushups, verify structure
        if data:
            pushup = data[0]
            assert "date" in pushup
            assert "count" in pushup

    def test_create_pushup_endpoint(self, client: APIClient):
        """Test POST /pushups endpoint"""
        pushup_data = {"count": 100, "date": "06/07/25"}

        response = client.post("/pushups", data=pushup_data)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure for successful creation
        assert "message" in data
        assert "pushup" in data
        assert "Pushup entry created successfully" in data["message"]

        # Verify created pushup data
        created_pushup = data["pushup"]
        assert created_pushup["count"] == pushup_data["count"]
        assert "date" in created_pushup

    def test_create_pushup_without_date(self, client: APIClient):
        """Test POST /pushups endpoint without date"""
        pushup_data = {"count": 75}

        response = client.post("/pushups", data=pushup_data)

        assert response.status_code == 200
        data = response.json()

        # Verify successful creation
        assert "message" in data
        assert "pushup" in data
        assert "Pushup entry created successfully" in data["message"]

        # Verify pushup was created with today's date
        created_pushup = data["pushup"]
        created_date = datetime.fromisoformat(created_pushup["date"])
        today = datetime.now().date()
        assert created_date.date() == today

    def test_create_pushup_invalid_count(self, client: APIClient):
        """Test POST /pushups with invalid count"""
        invalid_data = {"count": -10}

        response = client.post("/pushups", data=invalid_data)
        assert response.status_code == 422  # Validation error for negative count

    def test_get_pushups_with_date_filter(self, client: APIClient):
        """Test GET /pushups with date filtering"""
        # Test with date range parameters
        response = client.get(
            "/pushups",
            params={"start_date": "2025-01-01", "end_date": "2025-12-31", "limit": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10  # Respect limit parameter


class TestActivitiesEndpoints:
    """Test activities-related endpoints"""

    def test_activity_status_endpoint(self, client: APIClient):
        """Test GET /activities/status endpoint"""
        response = client.get("/activities/status")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "message" in data
        assert "stats" in data
        assert "Activity status retrieved successfully" in data["message"]

        # Verify stats structure
        stats = data["stats"]
        assert "runs" in stats
        assert "pushups" in stats
        assert "period" in stats

        # Verify runs stats
        runs_stats = stats["runs"]
        assert "total" in runs_stats
        assert "total_distance" in runs_stats
        assert "avg_distance" in runs_stats
        assert isinstance(runs_stats["total"], int)
        assert isinstance(runs_stats["total_distance"], int | float)
        assert isinstance(runs_stats["avg_distance"], int | float)

        # Verify pushups stats
        pushups_stats = stats["pushups"]
        assert "total" in pushups_stats
        assert "total_count" in pushups_stats
        assert "avg_count" in pushups_stats
        assert isinstance(pushups_stats["total"], int)
        assert isinstance(pushups_stats["total_count"], int)
        assert isinstance(pushups_stats["avg_count"], int | float)

        # Verify period info
        period = stats["period"]
        assert "days" in period
        assert "start_date" in period
        assert "end_date" in period
        assert period["days"] == 30  # Default days

    def test_activity_status_custom_days(self, client: APIClient):
        """Test GET /activities/status with custom days parameter"""
        response = client.get("/activities/status", params={"days": 7})

        assert response.status_code == 200
        data = response.json()

        # Verify custom days parameter was used
        stats = data["stats"]
        period = stats["period"]
        assert period["days"] == 7


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_invalid_endpoint(self, client: APIClient):
        """Test that invalid endpoints return 404"""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_invalid_run_data(self, client: APIClient):
        """Test POST /runs with invalid data"""
        invalid_data = {"duration": "invalid", "distance": "not_a_number"}

        response = client.post("/runs", data=invalid_data)
        # Should return 422 for validation error or 400 for bad request
        assert response.status_code in [400, 422]

    def test_invalid_pushup_data(self, client: APIClient):
        """Test POST /pushups with invalid data"""
        invalid_data = {"count": "not_a_number"}

        response = client.post("/pushups", data=invalid_data)
        # Should return 422 for validation error
        assert response.status_code == 422

    def test_missing_required_fields_run(self, client: APIClient):
        """Test POST /runs with missing required fields"""
        incomplete_data = {"duration": "30:00:00"}  # Missing distance

        response = client.post("/runs", data=incomplete_data)
        assert response.status_code == 422  # Validation error

    def test_missing_required_fields_pushup(self, client: APIClient):
        """Test POST /pushups with missing required fields"""
        incomplete_data = {}  # Missing count

        response = client.post("/pushups", data=incomplete_data)
        assert response.status_code == 422  # Validation error


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


# Mark all tests in this file as e2e tests
pytestmark = pytest.mark.e2e
