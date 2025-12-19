"""
Phase 4: Main Orchestrator & Web Service
Coordinates all layers with REST API + WebSocket
"""

import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from phase4_layer1_test_execution_engine import (
    TestExecutionEngine,
    ExecutionResult,
    ExecutionMetrics,
)
from phase4_layers_2_6_complete import (
    ResultsCollector,
    ResultsAnalyzer,
    DashboardGenerator,
    NotificationEngine,
    HistoricalTracker,
    CollectedResults,
)


class Phase4Orchestrator:
    """
    PHASE 4 ORCHESTRATOR
    Coordinates all 6 layers for complete test execution and automation
    """

    def __init__(self, test_dir: str = "./tests", output_dir: str = "./phase4_output"):
        """Initialize orchestrator with all layers"""
        self.test_dir = test_dir
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize all layers
        self.execution_engine = TestExecutionEngine(test_dir, str(self.output_dir))
        self.results_collector = ResultsCollector(str(self.output_dir / "results"))
        self.results_analyzer = ResultsAnalyzer()
        self.dashboard_gen = DashboardGenerator()
        self.notification_engine = NotificationEngine()
        self.history_tracker = HistoricalTracker(
            str(self.output_dir / "test_history.db")
        )

        self.current_analysis = None
        self.current_results = None

    def run_full_pipeline(
        self,
        execution_type: str = "all",
        parallel_workers: int = 1,
        progress_callback=None,
    ) -> Dict:
        """
        Run complete Phase 4 pipeline.

        Args:
            execution_type: "single", "all", "parallel"
            parallel_workers: Number of workers for parallel execution
            progress_callback: Callback for progress updates

        Returns:
            Complete execution result with all layers
        """
        print("\n" + "=" * 80)
        print("🚀 PHASE 4: INTELLIGENT TEST EXECUTION PLATFORM")
        print("=" * 80)

        execution_id = f"exec_{int(datetime.now().timestamp())}"

        # ===== LAYER 1: EXECUTE TESTS =====
        print("\n📝 LAYER 1: Test Execution Engine")
        print("-" * 80)

        if execution_type == "parallel":
            results = self.execution_engine.execute_parallel(
                num_workers=parallel_workers, progress_callback=progress_callback
            )
        else:
            results = self.execution_engine.execute_all_tests(
                progress_callback=progress_callback
            )

        print(f"✅ Layer 1 Complete: {len(results)} tests executed")

        # ===== LAYER 2: COLLECT RESULTS =====
        print("\n📊 LAYER 2: Results Collector")
        print("-" * 80)

        collected = self.results_collector.collect_test_results(str(self.output_dir))
        self.results_collector.store_results(collected, str(self.output_dir))

        print(f"✅ Layer 2 Complete: Results collected and stored")

        # ===== LAYER 3: ANALYZE RESULTS =====
        print("\n🔍 LAYER 3: Results Analyzer")
        print("-" * 80)

        # Get historical data
        historical = self.history_tracker.get_latest_results(10)
        historical_results = [collected] if not historical else []

        analysis = self.results_analyzer.analyze_results(
            collected, historical_results
        )

        self.current_analysis = analysis

        print(f"✅ Layer 3 Complete: Analysis generated")
        print(f"   - Flaky tests: {len(analysis.flaky_tests)}")
        print(f"   - Regressions: {len(analysis.regressions)}")
        for insight in analysis.insights:
            print(f"   - {insight}")

        # ===== LAYER 4: GENERATE DASHBOARD =====
        print("\n📈 LAYER 4: Dashboard Generator")
        print("-" * 80)

        dashboard_html = self.dashboard_gen.generate_dashboard(
            analysis, collected.metrics
        )

        dashboard_path = self.output_dir / "dashboard.html"
        dashboard_path.write_text(dashboard_html)

        print(f"✅ Layer 4 Complete: Dashboard generated")
        print(f"   - Path: {dashboard_path}")

        # ===== LAYER 5: SEND NOTIFICATIONS =====
        print("\n🔔 LAYER 5: Notification Engine")
        print("-" * 80)

        self.notification_engine.notify_completion(collected.metrics, analysis)

        if analysis.flaky_tests:
            self.notification_engine.notify_failures(analysis.flaky_tests)

        print(f"✅ Layer 5 Complete: Notifications sent")

        # ===== LAYER 6: STORE HISTORY =====
        print("\n📚 LAYER 6: Historical Tracker")
        print("-" * 80)

        self.history_tracker.store_result(collected)
        self.current_results = collected

        print(f"✅ Layer 6 Complete: History stored in database")

        # ===== SUMMARY =====
        summary = {
            "execution_id": execution_id,
            "timestamp": datetime.now().isoformat(),
            "status": "complete",
            "layers": {
                "layer_1_execution": {
                    "tests_executed": len(results),
                    "metrics": collected.metrics,
                },
                "layer_2_collection": {
                    "status": "complete",
                    "results_stored": collected.result_id,
                },
                "layer_3_analysis": {
                    "flaky_tests": len(analysis.flaky_tests),
                    "regressions": len(analysis.regressions),
                    "insights": len(analysis.insights),
                },
                "layer_4_dashboard": {
                    "status": "complete",
                    "path": str(dashboard_path),
                },
                "layer_5_notifications": {"status": "complete", "alerts": 3},
                "layer_6_history": {"status": "complete", "stored": True},
            },
        }

        print("\n" + "=" * 80)
        print("🏆 PHASE 4 EXECUTION COMPLETE")
        print("=" * 80)
        print(f"Execution ID: {execution_id}")
        print(f"Total Tests: {collected.metrics.get('total')}")
        print(f"Passed: {collected.metrics.get('passed')}")
        print(f"Failed: {collected.metrics.get('failed')}")
        print(f"Pass Rate: {collected.metrics.get('pass_rate'):.1f}%")
        print(f"Duration: {collected.metrics.get('total_duration'):.2f}s")

        return summary


# ============================================================================
# WEB SERVICE (Flask-based)
# ============================================================================

try:
    from flask import Flask, jsonify, request
    from flask_cors import CORS

    app = Flask(__name__)
    CORS(app)

    # Global orchestrator instance
    orchestrator = None

    @app.route("/api/tests/execute", methods=["POST"])
    def execute_tests():
        """Execute tests"""
        data = request.json or {}
        execution_type = data.get("execution_type", "all")
        workers = data.get("workers", 1)

        result = orchestrator.run_full_pipeline(execution_type, workers)

        return jsonify(result), 200

    @app.route("/api/tests/status/<execution_id>", methods=["GET"])
    def get_execution_status(execution_id):
        """Get execution status"""
        status = orchestrator.execution_engine.get_execution_status()

        return jsonify(
            {
                "execution_id": execution_id,
                "status": status.__dict__,
            }
        ), 200

    @app.route("/api/tests/results/<result_id>", methods=["GET"])
    def get_results(result_id):
        """Get test results"""
        result = orchestrator.history_tracker.get_result_by_id(result_id)

        if result:
            return jsonify(result), 200
        return jsonify({"error": "Result not found"}), 404

    @app.route("/api/tests/dashboard", methods=["GET"])
    def get_dashboard():
        """Get dashboard HTML"""
        if orchestrator.current_analysis and orchestrator.current_results:
            html = orchestrator.dashboard_gen.generate_dashboard(
                orchestrator.current_analysis,
                orchestrator.current_results.metrics,
            )
            return html, 200, {"Content-Type": "text/html"}

        return jsonify({"error": "No analysis available"}), 404

    @app.route("/api/tests/history", methods=["GET"])
    def get_history():
        """Get test history"""
        limit = request.args.get("limit", 10, type=int)
        history = orchestrator.history_tracker.get_latest_results(limit)

        return jsonify({"results": history}), 200

    @app.route("/api/tests/flaky", methods=["GET"])
    def get_flaky_tests():
        """Get flaky tests"""
        if orchestrator.current_analysis:
            return jsonify({"flaky_tests": orchestrator.current_analysis.flaky_tests}), 200

        return jsonify({"error": "No analysis available"}), 404

    @app.route("/api/tests/regressions", methods=["GET"])
    def get_regressions():
        """Get regressions"""
        if orchestrator.current_analysis:
            return (
                jsonify({"regressions": orchestrator.current_analysis.regressions}),
                200,
            )

        return jsonify({"error": "No analysis available"}), 404

    @app.route("/api/health", methods=["GET"])
    def health():
        """Health check"""
        return jsonify({"status": "healthy", "service": "phase4"}), 200

    def create_app(test_dir: str = "./tests"):
        """Create Flask app"""
        global orchestrator
        orchestrator = Phase4Orchestrator(test_dir)
        return app

except ImportError:
    print("⚠️  Flask not installed - web service unavailable")
    app = None


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Phase 4: Test Execution Platform")

    parser.add_argument(
        "--test-dir", default="./tests", help="Test directory"
    )

    parser.add_argument(
        "--execution-type",
        choices=["all", "parallel"],
        default="all",
        help="Execution type",
    )

    parser.add_argument(
        "--workers", type=int, default=1, help="Number of parallel workers"
    )

    parser.add_argument(
        "--web-server",
        action="store_true",
        help="Start web server",
    )

    parser.add_argument(
        "--port", type=int, default=5000, help="Web server port"
    )

    args = parser.parse_args()

    if args.web_server:
        if app is None:
            print("❌ Flask not installed. Install with: pip install flask flask-cors")
            return 1

        orchestrator_instance = Phase4Orchestrator(args.test_dir)
        app.run(host="0.0.0.0", port=args.port, debug=False)
    else:
        orchestrator = Phase4Orchestrator(args.test_dir)
        result = orchestrator.run_full_pipeline(
            execution_type=args.execution_type,
            parallel_workers=args.workers,
        )

        return 0 if result.get("status") == "complete" else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
