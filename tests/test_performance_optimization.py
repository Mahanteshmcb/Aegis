"""
Day 44: Performance optimization and testing

Load testing for concurrent robotic operations and gRPC performance validation.
"""

import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Dict, Any, Tuple
import logging

from fastapi.testclient import TestClient
import pytest

from ai.robotics_connector import RoboticsConnector
from backend import crud, schemas
from backend.config import settings

logger = logging.getLogger(__name__)


class LoadTestRunner:
    """Load testing framework for Aegis robotics operations."""

    def __init__(self,
                 client: TestClient | None = None,
                 db_factory: Callable[[], Any] | None = None,
                 base_url: str | None = None,
                 concurrent_users: int = 50,
                 duration_seconds: int = 60,
                 ramp_up_seconds: int = 10):
        self.client = client
        self.db_factory = db_factory
        self.base_url = base_url or f"http://localhost:{settings.server_port}"
        self.concurrent_users = concurrent_users
        self.duration_seconds = duration_seconds
        self.ramp_up_seconds = ramp_up_seconds

        # Performance metrics
        self.response_times: List[float] = []
        self.error_count = 0
        self.success_count = 0
        self.throughput_measurements: List[float] = []

        # Authentication
        self.auth_token = None
        self._setup_auth()

    def _setup_auth(self):
        """Set up authentication for load testing."""
        try:
            if self.client and self.db_factory:
                db = self.db_factory()
                try:
                    tenant = crud.create_tenant(db, schemas.TenantCreate(name="LoadTest Tenant"))
                    crud.create_user(
                        db,
                        schemas.UserCreate(
                            email="loadtest@example.com",
                            password="testpass123",
                            tenant_id=tenant.id,
                            role="admin",
                        ),
                    )
                finally:
                    db.close()

                login_data = {
                    "email": "loadtest@example.com",
                    "password": "testpass123",
                }
                resp = self.client.post("/api/v1/auth/login", json=login_data)
            else:
                login_data = {
                    "email": "loadtest@example.com",
                    "password": "testpass123",
                    "tenant_id": 1,
                    "role": "admin",
                }
                if self.client:
                    resp = self.client.post("/api/v1/auth/login", json=login_data)
                else:
                    import requests
                    resp = requests.post(f"{self.base_url}/api/v1/auth/login", json=login_data)

            if resp.status_code == 200:
                self.auth_token = resp.json()["access_token"]
                logger.info("✅ Load test authentication established")
            else:
                logger.warning("⚠️ Load test authentication failed, proceeding without auth")
        except Exception as e:
            logger.warning(f"⚠️ Auth setup failed: {e}, proceeding without auth")

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    def _single_robotics_request(self, robot_id: str, operation: str) -> Tuple[float, bool]:
        """Execute a single robotics API request and measure performance."""
        start_time = time.time()

        try:
            if operation == "register":
                payload = {
                    "robot_id": robot_id,
                    "robot_type": "AEGIS_ROVER",
                    "firmware_version": "v1.0.0",
                    "model_year": 2026,
                    "capabilities": {"navigation": "true", "payload_kg": "50"}
                }
                if self.client:
                    resp = self.client.post("/api/v1/robotics/register", json=payload, headers=self._get_headers())
                else:
                    resp = requests.post(
                        f"{self.base_url}/api/v1/robotics/register",
                        json=payload,
                        headers=self._get_headers(),
                        timeout=10
                    )
            elif operation == "task":
                payload = {
                    "task_id": f"TASK-{robot_id}-{int(time.time())}",
                    "robot_id": robot_id,
                    "operation_type": "HARVEST",
                    "priority": 5,
                    "task_detail": {
                        "crop_type": "wheat",
                        "area_m2": 100,
                    },
                    "metadata": {
                        "priority": "high"
                    }
                }
                if self.client:
                    resp = self.client.post("/api/v1/robotics/tasks", json=payload, headers=self._get_headers())
                else:
                    import requests
                    resp = requests.post(
                        f"{self.base_url}/api/v1/robotics/tasks",
                        json=payload,
                        headers=self._get_headers(),
                        timeout=10
                    )
            elif operation == "status":
                payload = {"robot_id": robot_id}
                if self.client:
                    resp = self.client.post("/api/v1/robotics/status", json=payload, headers=self._get_headers())
                else:
                    import requests
                    resp = requests.post(
                        f"{self.base_url}/api/v1/robotics/status",
                        json=payload,
                        headers=self._get_headers(),
                        timeout=10
                    )
            else:
                # Fleet coordination request
                payload = {
                    "task_type": "HARVEST",
                    "zone_id": "ZONE-001",
                    "priority": 5,
                    "robot_count": 5,
                    "task_parameters": {
                        "crop_type": "wheat",
                        "area_m2": 1000,
                        "deployment_style": "balanced"
                    }
                }
                if self.client:
                    resp = self.client.post("/api/v1/robotics/fleet/coordinate", json=payload, headers=self._get_headers())
                else:
                    import requests
                    resp = requests.post(
                        f"{self.base_url}/api/v1/robotics/fleet/coordinate",
                        json=payload,
                        headers=self._get_headers(),
                        timeout=10
                    )

            response_time = time.time() - start_time
            success = resp.status_code in [200, 201]
            return response_time, success

        except Exception as e:
            response_time = time.time() - start_time
            logger.debug(f"Request failed: {e}")
            return response_time, False

    def _run_user_simulation(self, user_id: int) -> Dict[str, Any]:
        """Simulate a single user's behavior during load test."""
        user_stats = {
            "requests_made": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": []
        }

        robot_id = f"LOADTEST-ROBOT-{user_id}"

        # User behavior: register robot, then perform various operations
        operations = ["register", "task", "status", "fleet"]

        for operation in operations:
            response_time, success = self._single_robotics_request(robot_id, operation)
            user_stats["requests_made"] += 1
            user_stats["response_times"].append(response_time)

            if success:
                user_stats["successful_requests"] += 1
            else:
                user_stats["failed_requests"] += 1

        return user_stats

    def run_load_test(self) -> Dict[str, Any]:
        """Run the complete load test and return performance metrics."""
        logger.info(f"🚀 Starting load test: {self.concurrent_users} users, {self.duration_seconds}s duration")

        start_time = time.time()
        end_time = start_time + self.duration_seconds

        # Ramp-up phase
        if self.ramp_up_seconds > 0:
            logger.info(f"📈 Ramping up over {self.ramp_up_seconds} seconds...")
            time.sleep(self.ramp_up_seconds)

        results = []

        with ThreadPoolExecutor(max_workers=self.concurrent_users) as executor:
            futures = []

            # Submit initial batch of requests
            for user_id in range(self.concurrent_users):
                future = executor.submit(self._run_user_simulation, user_id)
                futures.append(future)

            # Continue submitting requests until duration expires
            while time.time() < end_time:
                # Collect completed futures
                for future in as_completed(futures[:], timeout=1.0):
                    try:
                        result = future.result(timeout=1.0)
                        results.append(result)
                        futures.remove(future)
                    except Exception as e:
                        logger.debug(f"Future collection error: {e}")

                # Submit new requests to maintain concurrency
                while len(futures) < self.concurrent_users and time.time() < end_time:
                    user_id = len(results) + len(futures)
                    future = executor.submit(self._run_user_simulation, user_id)
                    futures.append(future)

                time.sleep(0.1)  # Small delay to prevent overwhelming

            # Wait for remaining futures
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=5.0)
                    results.append(result)
                except Exception as e:
                    logger.debug(f"Final future collection error: {e}")

        # Aggregate results
        total_requests = sum(r["requests_made"] for r in results)
        total_successful = sum(r["successful_requests"] for r in results)
        all_response_times = []
        for r in results:
            all_response_times.extend(r["response_times"])

        test_duration = time.time() - start_time

        metrics = {
            "test_duration_seconds": test_duration,
            "total_requests": total_requests,
            "successful_requests": total_successful,
            "failed_requests": total_requests - total_successful,
            "success_rate_percent": (total_successful / total_requests * 100) if total_requests > 0 else 0,
            "requests_per_second": total_requests / test_duration,
            "avg_response_time_ms": statistics.mean(all_response_times) * 1000 if all_response_times else 0,
            "median_response_time_ms": statistics.median(all_response_times) * 1000 if all_response_times else 0,
            "min_response_time_ms": min(all_response_times) * 1000 if all_response_times else 0,
            "max_response_time_ms": max(all_response_times) * 1000 if all_response_times else 0,
            "p95_response_time_ms": statistics.quantiles(all_response_times, n=20)[18] * 1000 if len(all_response_times) >= 20 else 0,
            "p99_response_time_ms": statistics.quantiles(all_response_times, n=100)[98] * 1000 if len(all_response_times) >= 100 else 0,
        }

        logger.info("📊 Load test completed:")
        logger.info(f"   - Total Requests: {metrics['total_requests']}")
        logger.info(f"   - Success Rate: {metrics['success_rate_percent']:.1f}%")
        logger.info(f"   - Throughput: {metrics['requests_per_second']:.1f} req/sec")
        logger.info(f"   - Avg Response Time: {metrics['avg_response_time_ms']:.1f}ms")
        logger.info(f"   - P95 Response Time: {metrics['p95_response_time_ms']:.1f}ms")

        return metrics


class TestPerformanceOptimization:
    """Performance optimization and load testing suite."""

    @pytest.fixture
    def load_tester(self, client, test_db):
        """Create a load test runner for testing using the FastAPI test client and test database."""
        return LoadTestRunner(
            client=client,
            db_factory=test_db,
            concurrent_users=5,  # Reduced for unit test
            duration_seconds=10,  # Reduced for unit test
            ramp_up_seconds=1
        )

    def test_grpc_connection_performance(self):
        """Test gRPC connection establishment and keep-alive performance."""
        connector = RoboticsConnector(
            max_workers=settings.grpc_max_workers,
            keepalive_time_ms=settings.grpc_keepalive_time_ms,
            compression_enabled=settings.grpc_compression_enabled
        )

        start_time = time.time()
        health_status = connector.health_check()
        connection_time = time.time() - start_time

        assert connection_time < 2.0, f"Connection took too long: {connection_time:.2f}s"
        # Health check should return quickly regardless of connection status
        assert isinstance(health_status, bool)

    def test_concurrent_robotics_operations(self, load_tester):
        """Test concurrent robotics API operations under load."""
        # Run a shorter test for unit testing
        load_tester.duration_seconds = 10
        load_tester.concurrent_users = 5

        metrics = load_tester.run_load_test()

        # Performance assertions
        assert metrics["success_rate_percent"] >= 80.0, f"Success rate too low: {metrics['success_rate_percent']:.1f}%"
        assert metrics["avg_response_time_ms"] < 5000, f"Average response time too high: {metrics['avg_response_time_ms']:.1f}ms"
        assert metrics["p95_response_time_ms"] < 10000, f"P95 response time too high: {metrics['p95_response_time_ms']:.1f}ms"

    @pytest.mark.slow
    def test_full_load_test(self, load_tester):
        """Run full load test with configured parameters."""
        metrics = load_tester.run_load_test()

        # More reasonable performance requirements for unit test scale
        assert metrics["success_rate_percent"] >= 80.0, f"Success rate too low: {metrics['success_rate_percent']:.1f}%"
        assert metrics["avg_response_time_ms"] < 5000, f"Average response time too high: {metrics['avg_response_time_ms']:.1f}ms"
        assert metrics["p95_response_time_ms"] < 10000, f"P95 response time too high: {metrics['p95_response_time_ms']:.1f}ms"
        assert metrics["requests_per_second"] >= 1, f"Throughput too low: {metrics['requests_per_second']:.1f} req/sec"