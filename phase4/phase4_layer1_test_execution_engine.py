"""
Phase 4: Layer 1 - Test Execution Engine
Executes Phase 3 tests with real-time monitoring and artifact collection
"""

import subprocess
import json
import time
from typing import Dict, List, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Single test execution result"""
    test_id: str
    status: str  # passed, failed, skipped, error
    duration: float
    artifacts: Dict[str, str]  # screenshot_path, log_path, etc.
    error_message: Optional[str] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ExecutionMetrics:
    """Execution metrics"""
    total: int
    passed: int
    failed: int
    skipped: int
    duration: float
    pass_rate: float
    avg_duration: float


@dataclass
class ExecutionStatus:
    """Current execution status"""
    total: int
    passed: int
    failed: int
    skipped: int
    running: int
    eta_seconds: Optional[float]
    progress_percent: float


class TestExecutionEngine:
    """
    LAYER 1: Test Execution Engine
    Executes tests with real-time monitoring and artifact collection
    """

    def __init__(self, test_dir: str = "./tests", report_dir: str = "./reports"):
        """
        Initialize execution engine.

        Args:
            test_dir: Directory containing test files
            report_dir: Directory for reports and artifacts
        """
        self.test_dir = Path(test_dir)
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)

        self.current_execution = None
        self.execution_id = None
        self.results: List[ExecutionResult] = []

    def execute_single_test(self, test_path: str) -> ExecutionResult:
        """
        Execute single test.

        Args:
            test_path: Path to test file/method

        Returns:
            ExecutionResult with status, duration, artifacts
        """
        logger.info(f"Executing single test: {test_path}")

        start_time = time.time()
        execution_id = f"test_{int(start_time)}"

        try:
            # Run pytest for specific test
            cmd = [
                "pytest",
                test_path,
                "-v",
                "--tb=short",
                f"--junit-xml={self.report_dir}/junit_{execution_id}.xml",
                f"--html={self.report_dir}/report_{execution_id}.html",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            duration = time.time() - start_time

            # Determine status
            status = "passed" if result.returncode == 0 else "failed"

            # Collect artifacts
            artifacts = self._collect_artifacts(execution_id)

            exec_result = ExecutionResult(
                test_id=test_path,
                status=status,
                duration=duration,
                artifacts=artifacts,
                error_message=result.stderr if result.returncode != 0 else None,
            )

            self.results.append(exec_result)
            logger.info(f"Test completed: {status} ({duration:.2f}s)")

            return exec_result

        except subprocess.TimeoutExpired:
            logger.error(f"Test timeout: {test_path}")
            return ExecutionResult(
                test_id=test_path,
                status="error",
                duration=300.0,
                artifacts={},
                error_message="Test execution timeout",
            )

    def execute_all_tests(
        self,
        test_filter: Optional[str] = None,
        progress_callback: Optional[Callable] = None,
    ) -> List[ExecutionResult]:
        """
        Execute all tests.

        Args:
            test_filter: Filter pattern (pytest -k syntax)
            progress_callback: Callback for progress updates

        Returns:
            List of ExecutionResult objects
        """
        logger.info("Executing all tests")

        self.execution_id = f"exec_{int(time.time())}"
        start_time = time.time()

        try:
            cmd = [
                "python", "-m", "pytest",
                str(self.test_dir),
                "-v",
                "--tb=short",
                f"--junit-xml={self.report_dir}/junit_{self.execution_id}.xml",
                f"--html={self.report_dir}/report_{self.execution_id}.html",
                "--json-report",
                f"--json-report-file={self.report_dir}/report_{self.execution_id}.json",
            ]

            if test_filter:
                cmd.extend(["-k", test_filter])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            duration = time.time() - start_time

            # Parse results
            results = self._parse_pytest_results(self.execution_id)

            # Call progress callback if provided
            if progress_callback:
                metrics = self._calculate_metrics(results, duration)
                progress_callback(
                    {
                        "status": "complete",
                        "metrics": asdict(metrics),
                        "execution_id": self.execution_id,
                    }
                )

            logger.info(
                f"All tests completed: {len(results)} tests in {duration:.2f}s"
            )

            return results

        except subprocess.TimeoutExpired:
            logger.error("Test execution timeout")
            return []

    def execute_parallel(
        self,
        num_workers: int = 4,
        progress_callback: Optional[Callable] = None,
    ) -> List[ExecutionResult]:
        """
        Execute tests in parallel.

        Args:
            num_workers: Number of parallel workers
            progress_callback: Callback for progress updates

        Returns:
            List of ExecutionResult objects
        """
        logger.info(f"Executing tests in parallel ({num_workers} workers)")

        self.execution_id = f"parallel_{int(time.time())}"
        start_time = time.time()

        try:
            cmd = [
                "pytest",
                str(self.test_dir),
                "-v",
                "-n",
                str(num_workers),
                "--dist",
                "loadscope",
                f"--junit-xml={self.report_dir}/junit_{self.execution_id}.xml",
                f"--html={self.report_dir}/report_{self.execution_id}.html",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            duration = time.time() - start_time

            results = self._parse_pytest_results(self.execution_id)

            if progress_callback:
                metrics = self._calculate_metrics(results, duration)
                progress_callback(
                    {
                        "status": "complete",
                        "metrics": asdict(metrics),
                        "workers": num_workers,
                        "execution_id": self.execution_id,
                    }
                )

            logger.info(f"Parallel execution completed: {duration:.2f}s")

            return results

        except subprocess.TimeoutExpired:
            logger.error("Parallel test execution timeout")
            return []

    def _collect_artifacts(self, execution_id: str) -> Dict[str, str]:
        """Collect test artifacts (screenshots, logs)"""
        artifacts = {}

        # Look for screenshots
        screenshot_dir = self.report_dir / "screenshots"
        if screenshot_dir.exists():
            for screenshot in screenshot_dir.glob(f"*{execution_id}*"):
                artifacts["screenshot"] = str(screenshot)

        # Report files
        for report_file in self.report_dir.glob(f"*{execution_id}*"):
            if report_file.suffix == ".html":
                artifacts["report"] = str(report_file)
            elif report_file.suffix == ".json":
                artifacts["json_report"] = str(report_file)
            elif report_file.suffix == ".xml":
                artifacts["junit_report"] = str(report_file)

        return artifacts

    def _parse_pytest_results(self, execution_id: str) -> List[ExecutionResult]:
        """Parse pytest JSON output"""
        results = []

        json_report_path = self.report_dir / f"report_{execution_id}.json"

        if json_report_path.exists():
            try:
                with open(json_report_path) as f:
                    report_data = json.load(f)

                for test in report_data.get("tests", []):
                    result = ExecutionResult(
                        test_id=test.get("nodeid"),
                        status=test.get("outcome"),
                        duration=test.get("duration", 0),
                        artifacts=self._collect_artifacts(execution_id),
                        error_message=test.get("call", {}).get("longrepr"),
                    )
                    results.append(result)

            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error parsing pytest results: {e}")

        return results

    def _calculate_metrics(
        self, results: List[ExecutionResult], total_duration: float
    ) -> ExecutionMetrics:
        """Calculate execution metrics"""
        passed = sum(1 for r in results if r.status == "passed")
        failed = sum(1 for r in results if r.status == "failed")
        skipped = sum(1 for r in results if r.status == "skipped")
        total = len(results)

        avg_duration = (
            sum(r.duration for r in results) / total if total > 0 else 0
        )

        pass_rate = (passed / total * 100) if total > 0 else 0

        return ExecutionMetrics(
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=total_duration,
            pass_rate=pass_rate,
            avg_duration=avg_duration,
        )

    def get_execution_status(self) -> ExecutionStatus:
        """Get current execution status"""
        if not self.results:
            return ExecutionStatus(
                total=0,
                passed=0,
                failed=0,
                skipped=0,
                running=0,
                eta_seconds=None,
                progress_percent=0,
            )

        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "passed")
        failed = sum(1 for r in self.results if r.status == "failed")
        skipped = sum(1 for r in self.results if r.status == "skipped")

        progress_percent = (passed + failed + skipped) / total * 100 if total > 0 else 0

        return ExecutionStatus(
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            running=0,
            eta_seconds=None,
            progress_percent=progress_percent,
        )

    def monitor_execution(
        self, callback: Callable, interval: float = 1.0
    ) -> None:
        """
        Monitor execution with real-time callbacks.

        Args:
            callback: Callback function for status updates
            interval: Update interval in seconds
        """
        while self.get_execution_status().progress_percent < 100:
            status = self.get_execution_status()
            callback(asdict(status))
            time.sleep(interval)
