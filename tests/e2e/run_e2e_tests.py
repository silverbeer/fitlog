#!/usr/bin/env python3
"""
Standalone script to run E2E tests against the deployed Fitlog API.

This script can be run locally or in GitHub Actions to verify
the deployed API is working correctly.

Usage:
    python run_e2e_tests.py --api-url https://api.example.com/dev
    python run_e2e_tests.py --api-id 2054k0hh9j --region us-east-1
"""

import argparse
import os
import subprocess
import sys

import requests


def construct_api_url(api_id: str, region: str, stage: str = "dev") -> str:
    """Construct API Gateway URL from components"""
    return f"https://{api_id}.execute-api.{region}.amazonaws.com/{stage}"


def check_api_availability(api_url: str, timeout: int = 30) -> bool:
    """Check if the API is available and responding"""
    try:
        print(f"🔍 Checking API availability: {api_url}")
        response = requests.get(f"{api_url}/", timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                print(f"✅ API is healthy: {data.get('message', 'Unknown')}")
                return True
        print(f"⚠️ API responded but not healthy: {response.status_code}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ API not available: {e}")
        return False


def run_e2e_tests(api_url: str, verbose: bool = False) -> bool:
    """Run the E2E tests against the deployed API"""

    # Set environment variable for pytest
    os.environ["API_BASE_URL"] = api_url

    # Construct pytest command
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/e2e/test_api_endpoints.py",
        "-v" if verbose else "-q",
        "--tb=short",
        "-m",
        "e2e",
        "--no-header",
        "--color=yes",
    ]

    print(f"🧪 Running E2E tests against: {api_url}")
    print(f"📋 Command: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(cmd, check=False, capture_output=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        return False


def run_quick_smoke_test(api_url: str) -> bool:
    """Run a quick smoke test of key endpoints"""

    # Get API key from environment
    api_key = os.getenv("API_KEY")

    endpoints_to_test = [
        ("/", "GET", False),  # Public endpoint
        ("/test", "GET", True),  # Protected endpoint
        ("/runs", "GET", True),  # Protected endpoint
        ("/pushups", "GET", True),  # Protected endpoint
        ("/activities/status", "GET", True),  # Protected endpoint
    ]

    print(f"🚀 Running quick smoke test against: {api_url}")

    all_passed = True
    for endpoint, method, requires_auth in endpoints_to_test:
        try:
            url = f"{api_url}{endpoint}"
            headers = {}

            # Add API key for protected endpoints
            if requires_auth:
                if not api_key:
                    print(f"❌ {method:<4} {endpoint:<20} - No API key provided")
                    all_passed = False
                    continue
                headers["X-API-Key"] = api_key

            if method == "GET":
                response = requests.get(url, timeout=10, headers=headers)
            else:
                response = requests.post(url, timeout=10, headers=headers)

            if response.status_code == 200:
                print(f"✅ {method:<4} {endpoint:<20} - OK")
            else:
                print(f"❌ {method:<4} {endpoint:<20} - {response.status_code}")
                all_passed = False

        except Exception as e:
            print(f"❌ {method:<4} {endpoint:<20} - Error: {e}")
            all_passed = False

    return all_passed


def main():
    parser = argparse.ArgumentParser(
        description="Run E2E tests against deployed Fitlog API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test using full API URL
  python run_e2e_tests.py --api-url https://abc123.execute-api.us-east-1.amazonaws.com/dev

  # Test using API ID and region
  python run_e2e_tests.py --api-id abc123 --region us-east-1

  # Quick smoke test only
  python run_e2e_tests.py --api-id abc123 --region us-east-1 --smoke-only

  # Verbose output
  python run_e2e_tests.py --api-url https://api.example.com/dev --verbose
        """,
    )

    # URL specification (mutually exclusive)
    url_group = parser.add_mutually_exclusive_group(required=True)
    url_group.add_argument(
        "--api-url",
        help="Full API Gateway URL (e.g., https://abc123.execute-api.us-east-1.amazonaws.com/dev)",
    )
    url_group.add_argument(
        "--api-id", help="API Gateway ID (will construct URL with --region)"
    )

    # Additional options
    parser.add_argument(
        "--region",
        default="us-east-1",
        help="AWS region (default: us-east-1, used with --api-id)",
    )
    parser.add_argument(
        "--stage",
        default="dev",
        help="API Gateway stage (default: dev, used with --api-id)",
    )
    parser.add_argument(
        "--smoke-only",
        action="store_true",
        help="Run only quick smoke test, not full E2E suite",
    )
    parser.add_argument(
        "--skip-availability-check",
        action="store_true",
        help="Skip initial API availability check",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout for API availability check (default: 30s)",
    )

    args = parser.parse_args()

    # Determine API URL
    if args.api_url:
        api_url = args.api_url.rstrip("/")
    else:
        api_url = construct_api_url(args.api_id, args.region, args.stage)

    print(f"🎯 Target API: {api_url}")
    print()

    # Check API availability (unless skipped)
    if not args.skip_availability_check:
        if not check_api_availability(api_url, args.timeout):
            print("❌ API is not available. Exiting.")
            sys.exit(1)
        print()

    # Run tests
    if args.smoke_only:
        success = run_quick_smoke_test(api_url)
        test_type = "Smoke test"
    else:
        success = run_e2e_tests(api_url, args.verbose)
        test_type = "E2E tests"

    print()
    if success:
        print(f"🎉 {test_type} PASSED! API is working correctly.")
        sys.exit(0)
    else:
        print(f"💥 {test_type} FAILED! Check the output above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
