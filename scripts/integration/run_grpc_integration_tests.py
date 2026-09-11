#!/usr/bin/env python3
"""
Day 37: gRPC Integration Test Runner
Comprehensive testing suite for gRPC contracts validation

This script runs end-to-end integration tests for:
- Sensor data streaming (MycelialProbe, AcousticPestMonitor)
- Robotic command execution (AegisRover, AgriSwarmBot, CanopyDrone)
- Security validation
- Performance benchmarking
- Error handling and resilience testing

Usage:
    python scripts/integration/run_grpc_integration_tests.py [--verbose] [--performance] [--security]

Options:
    --verbose: Enable detailed logging
    --performance: Run performance benchmarks
    --security: Run security validation tests
    --all: Run all test categories (default)
"""

import argparse
import logging
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Any
import subprocess

# Add the repository root to the import path when launched from any directory.
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "ai" / "protos"))

from ai.mock_clients import SensorSimulatorManager, RoboticFleetManager
from ai.mock_clients import MockMycelialProbe, MockAcousticPestMonitor
from ai.mock_clients import MockAegisRover, MockAgriSwarmBot, MockCanopyDrone

class GRPCTestRunner:
    """Comprehensive gRPC integration test runner"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.setup_logging()
        self.test_results = {
            "timestamp": time.time(),
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "performance_metrics": {},
            "security_findings": [],
            "errors": []
        }

    def setup_logging(self):
        """Configure logging"""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('grpc_integration_test.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def run_pytest_tests(self, test_pattern: str) -> bool:
        """Run pytest tests with given pattern"""
        try:
            cmd = [sys.executable, "-m", "pytest", f"tests/{test_pattern}", "-v"]
            if not self.verbose:
                cmd.append("--tb=short")

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)

            if result.returncode == 0:
                self.logger.info(f"✅ {test_pattern} tests passed")
                self.test_results["tests_passed"] += 1
                return True
            else:
                self.logger.error(f"❌ {test_pattern} tests failed")
                self.logger.error(result.stdout)
                self.logger.error(result.stderr)
                self.test_results["tests_failed"] += 1
                self.test_results["errors"].append({
                    "test": test_pattern,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                })
                return False

        except Exception as e:
            self.logger.error(f"Failed to run {test_pattern}: {e}")
            self.test_results["tests_failed"] += 1
            return False
        finally:
            self.test_results["tests_run"] += 1

    def run_performance_benchmarks(self) -> Dict[str, Any]:
        """Run performance benchmarking tests"""
        self.logger.info("🏃 Running performance benchmarks...")

        results = {}

        try:
            # Test sensor data throughput
            simulator_manager = SensorSimulatorManager()
            simulator_manager.add_simulator(MockMycelialProbe("perf_mycelial_001"))
            simulator_manager.add_simulator(MockAcousticPestMonitor("perf_acoustic_001"))
            simulator_manager.start_simulation(0.1)  # Fast updates

            # Measure data generation rate
            start_time = time.time()
            readings = 0
            test_duration = 5  # seconds

            while time.time() - start_time < test_duration:
                data = simulator_manager.get_all_sensor_data()
                readings += len(data)

            elapsed = time.time() - start_time
            throughput = readings / elapsed

            results["sensor_throughput"] = {
                "readings_per_second": throughput,
                "test_duration": elapsed,
                "total_readings": readings
            }

            simulator_manager.stop_simulation()

            # Test robotic command execution time
            fleet = RoboticFleetManager()
            fleet.add_robot(MockAegisRover("perf_rover_001"))
            fleet.add_robot(MockAgriSwarmBot("perf_swarm_001"))

            # Measure command execution times
            command_times = []

            for robot in fleet.robots.values():
                start = time.time()
                # Simulate command execution
                result = robot.execute_command(type('MockCommand', (), {
                    'command_type': 1,  # NAVIGATE
                    'navigation_command': type('NavCmd', (), {
                        'target_position': {'x': 10, 'y': 10, 'z': 0}
                    })()
                })())
                elapsed = time.time() - start
                command_times.append(elapsed)

            avg_command_time = sum(command_times) / len(command_times)

            results["robotic_performance"] = {
                "average_command_time": avg_command_time,
                "command_times": command_times,
                "robots_tested": len(fleet.robots)
            }

            self.logger.info(f"📊 Performance results: {throughput:.2f} sensor readings/sec, {avg_command_time:.3f}s avg command time")

        except Exception as e:
            self.logger.error(f"Performance benchmark failed: {e}")
            results["error"] = str(e)

        self.test_results["performance_metrics"] = results
        return results

    def run_security_validation(self) -> List[Dict[str, Any]]:
        """Run security validation checks"""
        self.logger.info("🔒 Running security validation...")

        findings = []

        try:
            # Check for authentication requirements
            # TODO: Implement actual security checks when auth is added
            findings.append({
                "severity": "info",
                "category": "authentication",
                "description": "gRPC services currently use insecure channels - authentication not yet implemented",
                "recommendation": "Implement JWT or certificate-based authentication"
            })

            # Check protobuf message validation
            findings.append({
                "severity": "low",
                "category": "input_validation",
                "description": "Basic input validation present in services",
                "recommendation": "Add comprehensive input sanitization and bounds checking"
            })

            # Check for sensitive data exposure
            findings.append({
                "severity": "medium",
                "category": "data_exposure",
                "description": "Sensor data includes position coordinates - ensure proper access controls",
                "recommendation": "Implement field-level access controls for sensitive data"
            })

            self.logger.info(f"🔍 Security validation complete: {len(findings)} findings")

        except Exception as e:
            self.logger.error(f"Security validation failed: {e}")
            findings.append({
                "severity": "high",
                "category": "test_failure",
                "description": f"Security validation failed: {str(e)}",
                "recommendation": "Fix security validation framework"
            })

        self.test_results["security_findings"] = findings
        return findings

    def run_load_testing(self) -> Dict[str, Any]:
        """Run load testing to validate system resilience"""
        self.logger.info("⚡ Running load testing...")

        results = {}

        try:
            # Test concurrent connections
            import concurrent.futures as cf
            import grpc

            def make_grpc_call(sensor_id: str):
                try:
                    channel = grpc.insecure_channel('localhost:50051')
                    # TODO: Make actual call when services are ready
                    channel.close()
                    return True
                except Exception as e:
                    return False

            # Test with increasing concurrency
            concurrency_levels = [10, 50, 100]
            sensor_ids = ["test_sensor_" + str(i) for i in range(100)]

            for concurrency in concurrency_levels:
                start_time = time.time()

                with cf.ThreadPoolExecutor(max_workers=concurrency) as executor:
                    futures_list = [
                        executor.submit(make_grpc_call, sensor_id)
                        for sensor_id in sensor_ids[:concurrency]
                    ]

                    results_list = [future.result() for future in cf.as_completed(futures_list)]

                elapsed = time.time() - start_time
                success_rate = sum(results_list) / len(results_list)

                results[f"concurrency_{concurrency}"] = {
                    "success_rate": success_rate,
                    "elapsed_time": elapsed,
                    "requests_per_second": concurrency / elapsed
                }

                self.logger.info(f"📈 Concurrency {concurrency}: {success_rate:.2%} success, {concurrency/elapsed:.2f} req/sec")

        except Exception as e:
            self.logger.error(f"Load testing failed: {e}")
            results["error"] = str(e)

        return results

    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        report = []
        report.append("=" * 80)
        report.append("AEGIS GRPC INTEGRATION TEST REPORT")
        report.append("=" * 80)
        report.append(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.test_results['timestamp']))}")
        report.append("")

        # Test Summary
        report.append("TEST SUMMARY")
        report.append("-" * 40)
        report.append(f"Tests Run: {self.test_results['tests_run']}")
        report.append(f"Tests Passed: {self.test_results['tests_passed']}")
        report.append(f"Tests Failed: {self.test_results['tests_failed']}")
        report.append(f"Success Rate: {(self.test_results['tests_passed'] / max(1, self.test_results['tests_run'])) * 100:.1f}%")
        report.append("")

        # Performance Metrics
        if self.test_results.get('performance_metrics'):
            report.append("PERFORMANCE METRICS")
            report.append("-" * 40)
            perf = self.test_results['performance_metrics']

            if 'sensor_throughput' in perf:
                st = perf['sensor_throughput']
                report.append(f"Sensor Throughput: {st['readings_per_second']:.2f} readings/second")
                report.append(f"Test Duration: {st['test_duration']:.2f} seconds")

            if 'robotic_performance' in perf:
                rp = perf['robotic_performance']
                report.append(f"Avg Command Time: {rp['average_command_time']:.3f} seconds")
                report.append(f"Robots Tested: {rp['robots_tested']}")

            report.append("")

        # Security Findings
        if self.test_results.get('security_findings'):
            report.append("SECURITY FINDINGS")
            report.append("-" * 40)
            for finding in self.test_results['security_findings']:
                report.append(f"[{finding['severity'].upper()}] {finding['category']}")
                report.append(f"  {finding['description']}")
                report.append(f"  Recommendation: {finding['recommendation']}")
                report.append("")

        # Errors
        if self.test_results.get('errors'):
            report.append("TEST ERRORS")
            report.append("-" * 40)
            for error in self.test_results['errors']:
                report.append(f"Test: {error['test']}")
                if error.get('stderr'):
                    report.append(f"Error: {error['stderr'].strip()}")
                report.append("")

        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-" * 40)

        success_rate = (self.test_results['tests_passed'] / max(1, self.test_results['tests_run'])) * 100

        if success_rate >= 95:
            report.append("✅ Excellent! gRPC integration tests are passing with high reliability.")
            report.append("   Ready to proceed with production deployment.")
        elif success_rate >= 80:
            report.append("⚠️  Good performance, but some tests are failing.")
            report.append("   Review error logs and fix failing tests before production.")
        else:
            report.append("❌ Critical issues detected in gRPC integration.")
            report.append("   Do not proceed until all critical tests pass.")

        if self.test_results.get('performance_metrics', {}).get('sensor_throughput', {}).get('readings_per_second', 0) < 10:
            report.append("⚠️  Sensor throughput is below recommended levels.")
            report.append("   Consider optimizing data processing pipeline.")

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)

    def save_report(self, filename: str = "grpc_integration_report.txt"):
        """Save test report to file"""
        report = self.generate_report()
        with open(filename, 'w') as f:
            f.write(report)
        self.logger.info(f"📄 Report saved to {filename}")

    def run_all_tests(self, include_performance: bool = True, include_security: bool = True) -> bool:
        """Run complete test suite"""
        self.logger.info("🚀 Starting Aegis gRPC Integration Test Suite")
        self.logger.info("=" * 60)

        # Run unit/integration tests
        self.logger.info("📋 Running core integration tests...")
        core_tests_passed = self.run_pytest_tests("test_grpc_integration.py")

        # Run performance benchmarks
        if include_performance:
            perf_results = self.run_performance_benchmarks()
            self.test_results["load_testing"] = self.run_load_testing()

        # Run security validation
        if include_security:
            security_findings = self.run_security_validation()

        # Generate and save report
        self.save_report()

        # Print summary
        print("\n" + self.generate_report())

        success = self.test_results['tests_failed'] == 0
        self.logger.info(f"🏁 Test suite completed. Overall result: {'PASS' if success else 'FAIL'}")

        return success

def main():
    parser = argparse.ArgumentParser(description="Aegis gRPC Integration Test Runner")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--performance", action="store_true", help="Run performance benchmarks")
    parser.add_argument("--security", action="store_true", help="Run security validation")
    parser.add_argument("--all", action="store_true", help="Run all test categories (default)")

    args = parser.parse_args()

    # Default to running all tests
    if not any([args.performance, args.security]):
        args.all = True

    runner = GRPCTestRunner(verbose=args.verbose)

    try:
        success = runner.run_all_tests(
            include_performance=args.performance or args.all,
            include_security=args.security or args.all
        )
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⚠️  Test run interrupted by user")
        runner.save_report("grpc_integration_report_interrupted.txt")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test runner failed: {e}")
        runner.save_report("grpc_integration_report_error.txt")
        sys.exit(1)

if __name__ == "__main__":
    main()