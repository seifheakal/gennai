"""
Phase 2: Main Orchestrator
Orchestrates all 5 layers: Parse → Generate → Calculate → Visualize → HITL
"""

import json
from pathlib import Path
from datetime import datetime
from phase2_phase1_parser import Phase1Parser
from phase2_test_generator import TestGenerator
from phase2_coverage_calculator import CoverageCalculator
from phase2_coverage_visualizer import CoverageVisualizer
from phase2_hitl_manager import HITLManager
from phase2_validators import HallucinationDetector


class Phase2Orchestrator:
    """
    Main orchestrator for Phase 2: Collaborative Test Design & Generation
    Combines all 5 layers into single pipeline.
    """

    def __init__(self, phase1_json_path: str):
        """
        Initialize orchestrator with Phase 1 output.

        Args:
            phase1_json_path: Path to phase1_output.json
        """
        self.phase1_json_path = phase1_json_path
        self.parser = None
        self.generator = None
        self.calculator = None
        self.visualizer = None
        self.hitl_manager = None
        self.test_cases = None
        self.coverage_metrics = None
        self.heatmap_data = None
        self.hitl_result = None

    def run_full_pipeline(
        self,
        target_coverage: float = 85.0,
        hitl_rounds: int = 2,
        output_dir: str = ".",
    ) -> dict:
        """
        Run complete Phase 2 pipeline.

        Steps:
        1. Parse Phase 1 output
        2. Generate test cases
        3. Calculate coverage
        4. Generate visualization
        5. Run HITL feedback loop
        6. Save outputs

        Args:
            target_coverage: Target blended coverage % (default: 85.0)
            hitl_rounds: Number of HITL feedback rounds (default: 2)
            output_dir: Output directory for JSON files (default: current)

        Returns:
            Dictionary with pipeline results
        """
        print("\n" + "=" * 80)
        print("[PHASE 2] COLLABORATIVE TEST DESIGN & GENERATION")
        print("=" * 80)

        try:
            # LAYER 1: Parse Phase 1
            print("\n[LAYER] LAYER 1: Parsing Phase 1 Output...")
            self._layer_1_parse()

            # LAYER 2: Generate Tests
            print("\n[LAYER] LAYER 2: Generating Test Cases...")
            self._layer_2_generate(target_coverage)

            # LAYER 3: Calculate Coverage
            print("\n[LAYER] LAYER 3: Calculating Coverage...")
            self._layer_3_calculate_coverage()

            # LAYER 4: Visualize
            print("\n[LAYER] LAYER 4: Generating Visualization...")
            self._layer_4_visualize()

            # LAYER 5: HITL Loop
            print("\n[LAYER] LAYER 5: Running HITL 2.0 Feedback Loop...")
            self._layer_5_hitl(hitl_rounds)

            # Save Outputs
            print("\n[LAYER] Saving Outputs...")
            self._save_outputs(output_dir)

            # Summary
            print("\n" + "=" * 80)
            print("[OK] PHASE 2 COMPLETE")
            print("=" * 80)

            return self._generate_summary()

        except Exception as e:
            print(f"\n[ERROR] ERROR: {e}")
            raise

    def _layer_1_parse(self):
        """Layer 1: Parse Phase 1 output"""
        self.parser = Phase1Parser(self.phase1_json_path)
        phase1 = self.parser.parse()

        print(f"  [OK] Parsed Phase 1 output")
        print(f"     URL: {phase1.url}")
        print(f"     Elements: {len(phase1.interactive_elements)}")
        print(f"     Workflows: {len(self.parser.get_workflows())}")

        summary = self.parser.summary()
        print(f"     High-confidence: {summary['high_confidence_elements']}")
        print(f"     Low-confidence: {summary['low_confidence_elements']}")

    def _layer_2_generate(self, target_coverage: float):
        """Layer 2: Generate test cases"""
        self.generator = TestGenerator(self.parser)
        self.test_cases = self.generator.generate_tests(
            target_coverage=target_coverage,
            max_tests=100,
            min_tests=50,
        )

        stats = self.generator.get_algorithm_stats(self.test_cases)
        print(f"  [OK] Generated {len(self.test_cases)} test cases")
        print(f"     EP tests: {stats['ep_tests']} ({stats['ep_percentage']:.1f}%)")
        print(f"     BVA tests: {stats['bva_tests']} ({stats['bva_percentage']:.1f}%)")
        print(f"     State tests: {stats['state_tests']} ({stats['state_percentage']:.1f}%)")

        # Validate (zero hallucinations)
        detector = HallucinationDetector(self.parser.phase1_output)
        result = detector.validate_test_batch(self.test_cases)
        print(f"     Valid tests: {result['valid_tests']}/{result['total_tests']}")
        print(f"     Hallucination rate: {result['hallucination_rate']:.1%}")

        if result['hallucination_rate'] > 0:
            print(f"     [WARN]  WARNING: Found hallucinations!")

    def _layer_3_calculate_coverage(self):
        """Layer 3: Calculate coverage metrics"""
        calculator = CoverageCalculator(self.parser, self.test_cases)
        self.coverage_metrics = calculator.calculate_coverage()

        summary = calculator.get_coverage_summary()
        print(f"  [OK] Coverage calculated")
        print(f"     Element coverage: {summary['element_coverage']}")
        print(f"     Path coverage: {summary['path_coverage']}")
        print(f"     Scenario coverage: {summary['scenario_coverage']}")
        print(f"     Blended coverage: {summary['blended_coverage']}")
        print(f"     Target met: {summary['coverage_target_met']}")
        print(f"     Coverage gaps: {summary['coverage_gaps_count']}")

    def _layer_4_visualize(self):
        """Layer 4: Generate visualization"""
        visualizer = CoverageVisualizer(
            self.coverage_metrics,
            self.parser,
            self.test_cases,
        )
        self.heatmap_data = visualizer.generate_heatmap_data()

        quality_score = visualizer.get_quality_score()
        print(f"  [OK] Visualization generated")
        print(f"     Quality score: {quality_score:.1f}/100")
        print(f"     Elements: {len(self.heatmap_data['elements'])}")

        coverage_report = visualizer.generate_coverage_report()
        print(f"     Green (90%+): {sum(1 for e in self.heatmap_data['elements'] if e['coverage'] >= 90)}")
        print(f"     Orange (75-90%): {sum(1 for e in self.heatmap_data['elements'] if 75 <= e['coverage'] < 90)}")
        print(f"     Red (<75%): {sum(1 for e in self.heatmap_data['elements'] if e['coverage'] < 75)}")

    def _layer_5_hitl(self, rounds: int):
        """Layer 5: Run HITL 2.0 feedback loop"""
        self.hitl_manager = HITLManager(self.generator, self.parser)
        self.hitl_result = self.hitl_manager.run_hitl_loop(rounds=rounds)

        print(f"  [OK] HITL 2.0 loop complete")
        print(f"     Rounds: {len(self.hitl_result.feedback_rounds)}")
        print(f"     Overall approval: {self.hitl_result.overall_approval_rate:.1%}")

        for round_result in self.hitl_result.feedback_rounds:
            print(f"     Round {round_result.round_number}: "
                  f"{round_result.approval_rate:.1%} approval")

        if self.hitl_result.improvements_made:
            print(f"     Improvements:")
            for improvement in self.hitl_result.improvements_made:
                print(f"       - {improvement}")

    def _save_outputs(self, output_dir: str):
        """Save all outputs as JSON files"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save test cases
        test_cases_dict = {
            "metadata": {
                "phase": 2,
                "version": "1.0",
                "generated_timestamp": datetime.utcnow().isoformat(),
                "total_tests": len(self.test_cases),
            },
            "tests": [t.model_dump() for t in self.test_cases],
        }

        test_file = output_path / "phase2_test_cases.json"
        with open(test_file, "w") as f:
            json.dump(test_cases_dict, f, indent=2)
        print(f"  [SAVE] Saved: {test_file}")

        # Save coverage metrics
        coverage_file = output_path / "phase2_coverage_metrics.json"
        with open(coverage_file, "w") as f:
            json.dump(self.coverage_metrics.model_dump(), f, indent=2)
        print(f"  [SAVE] Saved: {coverage_file}")

        # Save heatmap
        heatmap_file = output_path / "phase2_coverage_heatmap.json"
        with open(heatmap_file, "w") as f:
            json.dump(self.heatmap_data, f, indent=2, default=str)
        print(f"  [SAVE] Saved: {heatmap_file}")

        # Save HITL feedback
        feedback_file = output_path / "phase2_feedback_logs.json"
        feedback_dict = {
            "total_rounds": len(self.hitl_result.feedback_rounds),
            "rounds": [
                {
                    "round": r.round_number,
                    "tests_presented": r.tests_presented,
                    "approval_rate": r.approval_rate,
                    "patterns_learned": r.patterns_learned,
                }
                for r in self.hitl_result.feedback_rounds
            ],
            "overall_approval": self.hitl_result.overall_approval_rate,
            "improvements": self.hitl_result.improvements_made,
        }

        with open(feedback_file, "w") as f:
            json.dump(feedback_dict, f, indent=2)
        print(f"  [SAVE] Saved: {feedback_file}")

    def _generate_summary(self) -> dict:
        """Generate summary of Phase 2 results"""
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "total_tests": len(self.test_cases),
                "element_coverage": f"{self.coverage_metrics.element_coverage:.1f}%",
                "path_coverage": f"{self.coverage_metrics.path_coverage:.1f}%",
                "scenario_coverage": f"{self.coverage_metrics.scenario_coverage:.1f}%",
                "blended_coverage": f"{self.coverage_metrics.blended_coverage:.1f}%",
                "coverage_target_met": self.coverage_metrics.blended_coverage >= 85.0,
                "hitl_approval_rate": f"{self.hitl_result.overall_approval_rate:.1%}",
                "hitl_rounds": len(self.hitl_result.feedback_rounds),
                "coverage_gaps": len(self.coverage_metrics.coverage_gaps),
            },
            "output_files": [
                "phase2_test_cases.json",
                "phase2_coverage_metrics.json",
                "phase2_coverage_heatmap.json",
                "phase2_feedback_logs.json",
            ],
        }


def main():
    """CLI entry point"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python phase2_main.py <phase1_output.json> [output_dir]")
        sys.exit(1)

    phase1_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "."

    orchestrator = Phase2Orchestrator(phase1_path)
    result = orchestrator.run_full_pipeline(
        target_coverage=85.0,
        hitl_rounds=2,
        output_dir=output_dir,
    )

    print("\n[SUMMARY] Summary:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
