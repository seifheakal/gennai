"""
Full Pipeline Web UI
A complete web interface to run all 4 phases and visualize results
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import threading

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent / "phase1"))
sys.path.insert(0, str(Path(__file__).parent.parent / "phase2"))
sys.path.insert(0, str(Path(__file__).parent.parent / "phase3"))
sys.path.insert(0, str(Path(__file__).parent.parent / "phase4"))

app = Flask(__name__)
CORS(app)

# Global state for pipeline execution
pipeline_state = {
    "status": "idle",
    "current_phase": None,
    "progress": 0,
    "results": {},
    "error": None
}

@app.route('/')
def index():
    """Serve the main UI"""
    return render_template('index.html')

@app.route('/api/start', methods=['POST'])
def start_pipeline():
    """Start the full pipeline execution"""
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    # Reset state
    global pipeline_state
    pipeline_state = {
        "status": "running",
        "current_phase": 1,
        "progress": 0,
        "results": {},
        "error": None,
        "url": url,
        "start_time": datetime.now().isoformat()
    }
    
    # Run pipeline in background thread
    thread = threading.Thread(target=run_full_pipeline, args=(url,))
    thread.daemon = True
    thread.start()
    
    return jsonify({"status": "started", "message": "Pipeline execution started"})

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current pipeline status"""
    return jsonify(pipeline_state)

@app.route('/api/results/<phase>', methods=['GET'])
def get_phase_results(phase):
    """Get results for a specific phase"""
    return jsonify(pipeline_state.get('results', {}).get(f'phase{phase}', {}))

@app.route('/outputs/<path:filename>')
def serve_output(filename):
    """Serve output files"""
    output_dir = Path(__file__).parent / 'outputs'
    return send_from_directory(output_dir, filename)

def run_full_pipeline(url: str):
    """Execute all 4 phases sequentially"""
    global pipeline_state
    
    try:
        output_dir = Path(__file__).parent / 'outputs'
        output_dir.mkdir(exist_ok=True)
        
        # PHASE 1: Web Exploration
        pipeline_state["current_phase"] = 1
        pipeline_state["progress"] = 10
        phase1_result = run_phase1(url, output_dir)
        pipeline_state["results"]["phase1"] = phase1_result
        pipeline_state["progress"] = 25
        
        # PHASE 2: Test Generation
        pipeline_state["current_phase"] = 2
        pipeline_state["progress"] = 30
        phase2_result = run_phase2(output_dir / "phase1_output.json", output_dir)
        pipeline_state["results"]["phase2"] = phase2_result
        pipeline_state["progress"] = 50
        
        # PHASE 3: Code Generation
        pipeline_state["current_phase"] = 3
        pipeline_state["progress"] = 55
        phase3_result = run_phase3(output_dir, output_dir / "phase3_outputs")
        pipeline_state["results"]["phase3"] = phase3_result
        pipeline_state["progress"] = 75
        
        # PHASE 4: Test Execution
        pipeline_state["current_phase"] = 4
        pipeline_state["progress"] = 80
        phase4_result = run_phase4(output_dir / "phase3_outputs" / "tests", output_dir / "phase4_output")
        pipeline_state["results"]["phase4"] = phase4_result
        pipeline_state["progress"] = 100
        
        pipeline_state["status"] = "complete"
        pipeline_state["end_time"] = datetime.now().isoformat()
        
    except Exception as e:
        pipeline_state["status"] = "error"
        pipeline_state["error"] = str(e)
        pipeline_state["progress"] = 0
        import traceback
        pipeline_state["traceback"] = traceback.format_exc()

def run_phase1(url: str, output_dir: Path):
    """Run Phase 1: Web Exploration"""
    from phase1_main import main as phase1_main
    from phase1_config import ExplorationConfig, DEFAULT_CONFIG
    from phase1_accessibility_parser import parse_accessibility_tree
    
    config = ExplorationConfig(
        headless=True,
        max_depth=2,
        max_states=10,
        enable_crawling=True
    )
    
    # Run exploration
    result = asyncio.run(parse_accessibility_tree(url, config))
    
    # Save output
    output_file = output_dir / "phase1_output.json"
    with open(output_file, 'w') as f:
        json.dump(result.model_dump(), f, indent=2, default=str)
    
    return {
        "status": "complete",
        "url": url,
        "states_discovered": result.total_states_discovered,
        "elements_found": result.total_elements,
        "coverage": f"{result.coverage_percentage * 100:.1f}%",
        "time_seconds": result.exploration_statistics.total_time_seconds,
        "output_file": str(output_file)
    }

def run_phase2(phase1_file: Path, output_dir: Path):
    """Run Phase 2: Test Generation"""
    from phase2_main import Phase2Orchestrator
    
    orchestrator = Phase2Orchestrator(str(phase1_file.parent))
    result = orchestrator.run_full_pipeline(
        target_coverage=85.0,
        hitl_rounds=2,
        output_dir=str(output_dir)
    )
    
    return {
        "status": "complete",
        "total_tests": result["metrics"]["total_tests"],
        "coverage": result["metrics"]["blended_coverage"],
        "element_coverage": result["metrics"]["element_coverage"],
        "hitl_approval": result["metrics"]["hitl_approval_rate"],
        "coverage_target_met": result["metrics"]["coverage_target_met"]
    }

def run_phase3(phase2_dir: Path, output_dir: Path):
    """Run Phase 3: Code Generation"""
    from phase3_main import Phase3Orchestrator
    
    orchestrator = Phase3Orchestrator(str(phase2_dir), str(output_dir))
    result = orchestrator.run_full_pipeline(
        framework="pytest",
        language="python",
        browsers=["chrome"],
        parallel_workers=1
    )
    
    return {
        "status": "complete",
        "tests_generated": result["layers"]["layer_1"]["tests_generated"],
        "page_objects": result["layers"]["layer_2"].get("page_objects_generated", 0),
        "framework": "pytest",
        "output_dir": str(output_dir)
    }

def run_phase4(test_dir: Path, output_dir: Path):
    """Run Phase 4: Test Execution"""
    from phase4_main import Phase4Orchestrator
    
    orchestrator = Phase4Orchestrator(str(test_dir), str(output_dir))
    result = orchestrator.run_full_pipeline(
        execution_type="all",
        parallel_workers=1
    )
    
    return {
        "status": "complete",
        "tests_executed": result.get("total_tests", 0),
        "passed": result.get("passed", 0),
        "failed": result.get("failed", 0),
        "pass_rate": result.get("pass_rate", 0),
        "duration": result.get("duration", 0)
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
