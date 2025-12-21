"""
Phase 2: Layer 5 - HITL 2.0 Feedback Loop Manager
Implements human-in-the-loop feedback with intelligent learning.
"""

from typing import List, Dict, Tuple
from datetime import datetime
from phase2_models import (
    TestCase,
    TestCaseFeedback,
    FeedbackRound,
    HITLResult,
)
from phase2_test_generator import TestGenerator
from phase2_phase1_parser import Phase1Parser


class HITLManager:
    """
    LAYER 5: Human-in-the-Loop 2.0
    Implements feedback loop with learning.
    """

    def __init__(self, generator: TestGenerator, parser: Phase1Parser):
        """
        Initialize HITL manager.

        Args:
            generator: TestGenerator instance
            parser: Phase1Parser instance
        """
        self.generator = generator
        self.parser = parser
        self.feedback_rounds: List[FeedbackRound] = []
        self.algorithm_frequencies = {
            "ep": 1.0,
            "bva": 1.0,
            "state_combination": 1.0,
        }

    def run_hitl_loop(self, rounds: int = 2) -> HITLResult:
        """
        Run complete HITL feedback loop.

        Flow:
        Round N:
          1. Generate tests
          2. Present to human (CLI)
          3. Collect feedback
          4. Extract patterns
          5. Adjust frequencies for next round

        Args:
            rounds: Number of HITL rounds (default: 2)

        Returns:
            HITLResult with all feedback history
        """
        print(f"\n[RETRY] Starting HITL 2.0 Loop ({rounds} rounds)")
        print("=" * 70)

        for round_num in range(1, rounds + 1):
            print(f"\n[LAYER] ROUND {round_num}/{rounds}")
            print("-" * 70)

            # Step 1: Generate tests for this round
            tests = self.generator.generate_tests()
            print(f"[OK] Generated {len(tests)} tests")

            # Step 2: Present and collect feedback
            feedback_items = self._present_and_collect_feedback(tests, round_num)

            # Step 3: Calculate metrics
            approval_rate = self._calculate_approval_rate(feedback_items)
            print(f"[OK] Approval rate: {approval_rate:.1%}")

            # Step 4: Extract patterns
            patterns = self._extract_patterns(feedback_items)
            print(f"[OK] Patterns learned: {len(patterns)}")
            for pattern in patterns[:3]:  # Show first 3
                print(f"   - {pattern}")

            # Step 5: Create feedback round
            round_result = FeedbackRound(
                round_number=round_num,
                tests_presented=len(tests),
                feedback_items=feedback_items,
                approval_rate=approval_rate,
                patterns_learned=patterns,
            )
            self.feedback_rounds.append(round_result)

            # Step 6: Apply learning for next round
            if round_num < rounds:
                print(f"[LEARNING] Applying learning for next round...")
                self._apply_learning(patterns)

        # Calculate overall metrics
        overall_approval = self._calculate_overall_approval()

        print(f"\n[COMPLETE] HITL Loop Complete")
        print(f"   Overall approval rate: {overall_approval:.1%}")
        print("=" * 70)

        return HITLResult(
            feedback_rounds=self.feedback_rounds,
            overall_approval_rate=overall_approval,
            improvements_made=self._get_improvements(),
        )

    def _present_and_collect_feedback(
        self,
        tests: List[TestCase],
        round_num: int
    ) -> List[TestCaseFeedback]:
        """
        Present tests to human and collect feedback.

        For demo purposes, simulates feedback based on test quality.
        In production, this would be interactive CLI.

        Args:
            tests: List of tests to present
            round_num: Current round number

        Returns:
            List of TestCaseFeedback items
        """
        feedback_items = []

        for test in tests:
            # Simulate human feedback (in production: interactive CLI)
            verdict, confidence = self._simulate_human_feedback(test, round_num)

            feedback = TestCaseFeedback(
                test_id=test.test_id,
                verdict=verdict,
                comment=f"Round {round_num} feedback",
                element_id=test.elements_used[0] if test.elements_used else "unknown",
                algorithm=test.algorithm_used,
                approval_confidence=confidence if verdict == "approve" else None,
            )

            feedback_items.append(feedback)

        return feedback_items

    def _simulate_human_feedback(
        self,
        test: TestCase,
        round_num: int
    ) -> Tuple[str, float]:
        """
        Simulate human feedback (for demo).

        In Round 1: State tests ~95%, others ~85%
        In Round 2: All tests improved

        Args:
            test: TestCase to evaluate
            round_num: Current round number

        Returns:
            (verdict, confidence)
        """
        # Base approval rates by algorithm
        algo_rates = {
            "state_combination": 0.95 if round_num == 1 else 0.98,
            "ep": 0.82 if round_num == 1 else 0.90,
            "bva": 0.80 if round_num == 1 else 0.88,
        }

        base_rate = algo_rates.get(test.algorithm_used, 0.80)

        # Adjust by importance
        if test.importance_score > 0.85:
            base_rate += 0.05

        # Make decision
        import random
        decision = random.random()

        if decision < base_rate:
            return ("approve", base_rate)
        else:
            return ("reject", 0.0)

    def _calculate_approval_rate(self, feedback: List[TestCaseFeedback]) -> float:
        """Calculate approval rate from feedback"""
        if not feedback:
            return 0.0
        approved = sum(1 for f in feedback if f.verdict == "approve")
        return approved / len(feedback)

    def _extract_patterns(self, feedback: List[TestCaseFeedback]) -> List[str]:
        """
        Extract patterns from feedback.

        Pattern types:
        1. Algorithm approval rates
        2. Element type approval rates
        3. Confidence-based patterns
        4. Complexity patterns

        Args:
            feedback: List of feedback items

        Returns:
            List of pattern strings
        """
        patterns = []

        # Pattern 1: Algorithm approval rates
        algo_stats: Dict = {}
        for f in feedback:
            if f.algorithm not in algo_stats:
                algo_stats[f.algorithm] = {"approve": 0, "reject": 0}
            algo_stats[f.algorithm][f.verdict] += 1

        for algo, counts in algo_stats.items():
            total = counts["approve"] + counts["reject"]
            approval_rate = counts["approve"] / total if total > 0 else 0.0

            if approval_rate >= 0.90:
                patterns.append(f"{algo}_high_approval_{approval_rate:.0%}")
            elif approval_rate <= 0.70:
                patterns.append(f"{algo}_low_approval_{approval_rate:.0%}")

        # Pattern 2: General success patterns
        overall_approval = self._calculate_approval_rate(feedback)
        if overall_approval >= 0.92:
            patterns.append("strong_feedback_positive")
        elif overall_approval <= 0.80:
            patterns.append("weak_feedback_needs_improvement")

        # Pattern 3: Algorithm opportunity
        if "state_combination_high_approval_95%" in patterns:
            patterns.append("increase_workflow_tests")
        if "bva_low_approval_70%" in patterns:
            patterns.append("simplify_boundary_testing")

        return patterns

    def _apply_learning(self, patterns: List[str]):
        """
        Apply learning to adjust future test generation.

        Args:
            patterns: List of patterns to learn from
        """
        for pattern in patterns:
            if "high_approval" in pattern:
                algo = pattern.split("_")[0]
                self.algorithm_frequencies[algo] *= 1.2  # Increase
                print(f"   [UARROW] Increased {algo} frequency")

            if "low_approval" in pattern:
                algo = pattern.split("_")[0]
                self.algorithm_frequencies[algo] *= 0.8  # Decrease
                print(f"   [DARROW] Decreased {algo} frequency")

            if "increase_workflow_tests" in pattern:
                print(f"   [INFO] Will increase workflow tests in next round")

    def _calculate_overall_approval(self) -> float:
        """Calculate overall approval across all rounds"""
        total_approved = 0
        total_feedback = 0

        for round_result in self.feedback_rounds:
            total_approved += sum(
                1 for f in round_result.feedback_items
                if f.verdict == "approve"
            )
            total_feedback += len(round_result.feedback_items)

        return total_approved / total_feedback if total_feedback > 0 else 0.0

    def _get_improvements(self) -> List[str]:
        """Extract improvements made across rounds"""
        improvements = []

        if len(self.feedback_rounds) >= 2:
            round1_approval = self.feedback_rounds[0].approval_rate
            round2_approval = self.feedback_rounds[1].approval_rate

            if round2_approval > round1_approval:
                improvement = round2_approval - round1_approval
                improvements.append(
                    f"Round 2 improved by {improvement:.1%} "
                    f"({round1_approval:.1%} [ARROW] {round2_approval:.1%})"
                )

            # Check for pattern-based improvements
            patterns1 = set(self.feedback_rounds[0].patterns_learned)
            patterns2 = set(self.feedback_rounds[1].patterns_learned)

            new_patterns = patterns2 - patterns1
            if new_patterns:
                improvements.append(f"Learned new patterns: {list(new_patterns)[:2]}")

        return improvements

    def get_feedback_summary(self) -> Dict:
        """Get summary of all feedback rounds"""
        return {
            "total_rounds": len(self.feedback_rounds),
            "rounds": [
                {
                    "round": r.round_number,
                    "tests": r.tests_presented,
                    "approval_rate": f"{r.approval_rate:.1%}",
                    "patterns": r.patterns_learned,
                }
                for r in self.feedback_rounds
            ],
            "overall_approval": f"{self._calculate_overall_approval():.1%}",
            "improvements": self._get_improvements(),
        }
