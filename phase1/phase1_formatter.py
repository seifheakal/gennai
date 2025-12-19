"""
Phase 1 Output Formatter

Formats exploration results into final JSON output.
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime

from phase1_models import Phase1ExplorationOutput

__version__ = "1.0.0"


class OutputFormatter:
    """Format Phase 1 exploration output."""
    
    @staticmethod
    def to_dict(output: Phase1ExplorationOutput) -> Dict[str, Any]:
        """
        Convert exploration output to dictionary.
        
        Args:
            output: Phase1ExplorationOutput instance
        
        Returns:
            dict: Dictionary representation
        """
        return output.model_dump(by_alias=True)
    
    @staticmethod
    def to_json_string(
        output: Phase1ExplorationOutput,
        indent: int = 2,
        include_none: bool = False
    ) -> str:
        """
        Convert exploration output to JSON string.
        
        Args:
            output: Phase1ExplorationOutput instance
            indent: JSON indentation spaces
            include_none: Include None values in output
        
        Returns:
            str: JSON string
        """
        return output.model_dump_json(
            indent=indent,
            exclude_none=(not include_none),
            by_alias=True
        )
    
    @staticmethod
    def save_to_file(
        output: Phase1ExplorationOutput,
        file_path: str,
        indent: int = 2
    ) -> bool:
        """
        Save exploration output to JSON file.
        
        Args:
            output: Phase1ExplorationOutput instance
            file_path: Path to save file
            indent: JSON indentation spaces
        
        Returns:
            bool: True if successful
        """
        try:
            json_string = OutputFormatter.to_json_string(output, indent=indent)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_string)
            return True
        except Exception as e:
            print(f"Failed to save output: {str(e)}")
            return False
    
    @staticmethod
    def pretty_print(output: Phase1ExplorationOutput) -> str:
        """
        Create human-readable summary of exploration.
        
        Args:
            output: Phase1ExplorationOutput instance
        
        Returns:
            str: Formatted summary
        """
        summary = f"""
╔═══════════════════════════════════════════════════════════╗
║          PHASE 1 EXPLORATION RESULTS                      ║
╚═══════════════════════════════════════════════════════════╝

📍 Target URL: {output.page_url}
⏰ Timestamp: {output.exploration_timestamp.isoformat()}

📊 ELEMENTS DISCOVERED
├─ Total Elements: {output.total_elements}
├─ Coverage: {output.coverage_percentage:.1%}
└─ States: {output.total_states_discovered}

📋 INTERACTIVE ELEMENTS ({output.total_elements})
"""
        for idx, element in enumerate(output.interactive_elements, 1):
            summary += f"\n  {idx}. {element.label or element.aria_role}"
            summary += f"\n     ├─ Role: {element.aria_role}"
            summary += f"\n     ├─ Type: {element.type}"
            summary += f"\n     ├─ Enabled: {element.enabled}"
            summary += f"\n     └─ Primary Locator: {element.locators.priority_1_role or 'N/A'}"
        
        summary += f"""

⏱️  PERFORMANCE
├─ Total Time: {output.exploration_statistics.total_time_seconds:.2f}s
├─ Elements/sec: {output.total_elements / max(0.1, output.exploration_statistics.total_time_seconds):.1f}
├─ Accessibility Tree Size: {output.exploration_statistics.tokens_used_accessibility_tree:,} chars
├─ Est. Full DOM Size: {output.exploration_statistics.tokens_estimate_full_dom:,} chars
└─ Efficiency Ratio: {output.exploration_statistics.efficiency_ratio:.1f}x

✅ QUALITY METRICS
├─ Coverage: {output.quality_metrics.coverage_percentage:.1%}
├─ Accessibility Compliance: {output.quality_metrics.accessibility_compliance:.1%}
├─ Avg Locator Reliability: {output.quality_metrics.locator_reliability_avg:.1%}
├─ Validation Pass Rate: {output.quality_metrics.validation_pass_rate:.1%}
├─ Hallucinated Elements: {output.exploration_statistics.hallucinated_elements}
└─ Ready for Phase 2: {'✅ YES' if output.quality_metrics.ready_for_phase2 else '❌ NO'}

📝 CHALLENGES: {', '.join(output.challenges) if output.challenges else 'None'}

💡 RECOMMENDATIONS: {len(output.recommendations)}
"""
        for rec in output.recommendations:
            summary += f"\n  • {rec}"
        
        summary += """
╔═══════════════════════════════════════════════════════════╗
║          ✅ PHASE 1 COMPLETE - READY FOR PHASE 2          ║
╚═══════════════════════════════════════════════════════════╝
"""
        return summary


def format_exploration_output(
    output: Phase1ExplorationOutput,
    format_type: str = "json"
) -> str:
    """
    Format exploration output in specified format.
    
    Args:
        output: Phase1ExplorationOutput instance
        format_type: "json" | "dict" | "summary" | "pretty"
    
    Returns:
        str: Formatted output
    """
    if format_type == "json":
        return OutputFormatter.to_json_string(output)
    elif format_type == "summary":
        return OutputFormatter.pretty_print(output)
    elif format_type == "dict":
        return str(OutputFormatter.to_dict(output))
    else:
        return OutputFormatter.to_json_string(output)
