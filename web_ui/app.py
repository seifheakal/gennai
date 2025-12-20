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
    # Change to phase1 directory
    import os
    project_root = Path(__file__).parent.parent
    phase1_dir = project_root / 'phase1'
    original_dir = os.getcwd()
    os.chdir(phase1_dir)
    
    try:
        sys.path.insert(0, str(phase1_dir))
        from phase1_config import create_custom_config
        from phase1_accessibility_parser import parse_accessibility_tree
        from phase1_formatter import OutputFormatter
        
        # Configure with increased timeout for slow websites
        config = create_custom_config(
            timeout_seconds=60,  # Increase to 60 seconds
            headless=True,
            coverage_threshold=0.85,
            max_states=10,
            validation_level="moderate"
        )
        
        # Run exploration (async)
        result = asyncio.run(parse_accessibility_tree(url, config))
        
        # Save output
        output_file = phase1_dir / 'phase1_output.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result.model_dump(), f, indent=2, default=str)
        
        # Copy output to web_ui outputs dir
        import shutil
        output_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(output_file, output_dir / 'phase1_output.json')
        
        # Parse result
        with open(phase1_dir / 'phase1_output.json', 'r') as f:
            data = json.load(f)
        
        return {
            "status": "complete",
            "url": url,
            "states_discovered": data.get('total_states_discovered', 0),
            "elements_found": data.get('total_elements', 0),
            "coverage": f"{data.get('coverage_percentage', 0) * 100:.1f}%",
            "time_seconds": data.get('exploration_statistics', {}).get('total_time_seconds', 0),
            "output_file": str(output_dir / 'phase1_output.json')
        }
    finally:
        os.chdir(original_dir)

def run_phase2(phase1_file: Path, output_dir: Path):
    """Run Phase 2: Test Generation"""
    # Change to phase2 directory
    import os
    project_root = Path(__file__).parent.parent
    phase2_dir = project_root / 'phase2'
    original_dir = os.getcwd()
    os.chdir(phase2_dir)
    
    try:
        sys.path.insert(0, str(phase2_dir))
        from phase2_main import main as phase2_main
        
        # Copy phase1 output to phase2 directory
        import shutil
        shutil.copy(phase1_file, phase2_dir / 'phase1_output.json')
        
        # Run phase2
        phase2_main()
        
        # Copy results back
        output_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(phase2_dir / 'phase2_test_cases.json', output_dir / 'phase2_test_cases.json')
        shutil.copy(phase2_dir / 'phase2_coverage_metrics.json', output_dir / 'phase2_coverage_metrics.json')
        
        # Parse results
        with open(phase2_dir / 'phase2_coverage_metrics.json', 'r') as f:
            metrics = json.load(f)
        
        return {
            "status": "complete",
            "total_tests": metrics.get('total_tests', 0),
            "coverage": f"{metrics.get('blended_coverage', 0):.1f}%",
            "element_coverage": f"{metrics.get('element_coverage', 0):.1f}%",
            "hitl_approval": f"{metrics.get('hitl_approval_rate', 0):.1f}%",
            "coverage_target_met": metrics.get('coverage_target_met', False)
        }
    finally:
        os.chdir(original_dir)

def run_phase3(phase2_dir: Path, output_dir: Path):
    """Run Phase 3: Code Generation"""
    # Change to phase3 directory
    import os
    project_root = Path(__file__).parent.parent
    phase3_dir = project_root / 'phase3'
    original_dir = os.getcwd()
    os.chdir(phase3_dir)
    
    try:
        sys.path.insert(0, str(phase3_dir))
        from phase3_main import main as phase3_main
        
        # Copy phase2 outputs
        import shutil
        shutil.copy(phase2_dir / 'phase2_test_cases.json', phase3_dir / 'phase2_test_cases.json')
        shutil.copy(phase2_dir / 'phase1_output.json', phase3_dir / 'phase1_output.json')
        
        # Run phase3
        phase3_main()
        
        # Copy results back
        output_dir.mkdir(parents=True, exist_ok=True)
        if (phase3_dir / 'phase3_outputs').exists():
            shutil.copytree(phase3_dir / 'phase3_outputs', output_dir / 'phase3_outputs', dirs_exist_ok=True)
        
        # Count generated files
        test_files = list((phase3_dir / 'phase3_outputs' / 'tests').glob('test_*.py')) if (phase3_dir / 'phase3_outputs' / 'tests').exists() else []
        page_objects = list((phase3_dir / 'phase3_outputs' / 'pages').glob('*_page.py')) if (phase3_dir / 'phase3_outputs' / 'pages').exists() else []
        
        return {
            "status": "complete",
            "tests_generated": len(test_files),
            "page_objects": len(page_objects),
            "framework": "pytest",
            "output_dir": str(output_dir / 'phase3_outputs')
        }
    finally:
        os.chdir(original_dir)

def run_phase4(test_dir: Path, output_dir: Path):
    """Run Phase 4: Test Execution"""
    # Change to phase4 directory
    import os
    project_root = Path(__file__).parent.parent
    phase4_dir = project_root / 'phase4'
    original_dir = os.getcwd()
    os.chdir(phase4_dir)
    
    try:
        sys.path.insert(0, str(phase4_dir))
        from phase4_main import main as phase4_main
        
        # Copy phase3 outputs
        import shutil
        if (test_dir / 'tests').exists():
            shutil.copytree(test_dir / 'tests', phase4_dir / 'tests', dirs_exist_ok=True)
        
        # Run phase4
        phase4_main()
        
        # Copy results back
        output_dir.mkdir(parents=True, exist_ok=True)
        if (phase4_dir / 'phase4_output').exists():
            shutil.copytree(phase4_dir / 'phase4_output', output_dir / 'phase4_output', dirs_exist_ok=True)
        
        # Parse dashboard for metrics
        dashboard_file = phase4_dir / 'phase4_output' / 'dashboard.html'
        if dashboard_file.exists():
            # Simple HTML parsing for metrics
            import re
            with open(dashboard_file, 'r') as f:
                html = f.read()
            
            # Extract basic metrics from dashboard
            passed = int(re.search(r'Passed:\s*(\d+)', html).group(1)) if re.search(r'Passed:\s*(\d+)', html) else 0
            failed = int(re.search(r'Failed:\s*(\d+)', html).group(1)) if re.search(r'Failed:\s*(\d+)', html) else 0
            total = passed + failed
            pass_rate = (passed / total * 100) if total > 0 else 0
        else:
            passed = failed = total = pass_rate = 0
        
        return {
            "status": "complete",
            "tests_executed": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": pass_rate,
            "duration": 0
        }
    finally:
        os.chdir(original_dir)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
