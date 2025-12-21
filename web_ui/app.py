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
    "error": None,
    "logs": [],
    "current_status": "Idle",
    "chat_messages": [],
    "waiting_for_input": False,
    "user_input": None,
    "pending_question": None,
    "metrics": {
        "response_times": [],  # Track LLM response times
        "tokens_used": [],     # Track token usage per operation
        "phase_durations": {}  # Track duration of each phase
    },
    "evidence": {
        "screenshots": [],
        "videos": [],
        "logs_files": []
    },
    "config": {
        "phase1": {
            "browser": "chromium",
            "headless": True,
            "screenshots": True,
            "max_depth": 2,
            "max_states": 10,
            "timeout": 60,
            "crawling": True,
            "show_browser": False  # NEW: Control browser visibility
        },
        "phase2": {
            "hitl_rounds": 2,
            "target_coverage": 85.0,
            "auto_approve": False
        },
        "phase3": {
            "framework": "pytest",
            "browsers": ["chrome"],
            "parallel": 1
        },
        "phase4": {
            "headless": True,
            "parallel": 1,
            "generate_dashboard": True,
            "record_video": True  # NEW: Enable video recording
        }
    }
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

@app.route('/api/chat', methods=['POST'])
def send_chat_message():
    """Send a chat message or respond to pipeline question"""
    global pipeline_state
    data = request.json
    message = data.get('message', '')
    
    # Ensure chat_messages exists
    if 'chat_messages' not in pipeline_state:
        pipeline_state['chat_messages'] = []
    
    # Add user message to chat
    chat_entry = {
        "sender": "user",
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    pipeline_state["chat_messages"].append(chat_entry)
    
    # If pipeline is waiting for input, provide it
    if pipeline_state.get('waiting_for_input'):
        pipeline_state['user_input'] = message
        pipeline_state['waiting_for_input'] = False
        log_status(f"📥 User responded: {message}")
    
    return jsonify({"status": "success", "message": "Message received"})

@app.route('/api/config', methods=['GET', 'POST'])
def manage_config():
    """Get or update pipeline configuration"""
    global pipeline_state
    
    # Ensure config exists
    if 'config' not in pipeline_state:
        pipeline_state['config'] = {
            "phase1": {
                "browser": "chromium",
                "headless": True,
                "screenshots": True,
                "max_depth": 2,
                "max_states": 10,
                "timeout": 60,
                "crawling": True,
                "show_browser": False
            },
            "phase2": {
                "hitl_rounds": 2,
                "target_coverage": 85.0,
                "auto_approve": False
            },
            "phase3": {
                "framework": "pytest",
                "browsers": ["chrome"],
                "parallel": 1
            },
            "phase4": {
                "headless": True,
                "parallel": 1,
                "generate_dashboard": True,
                "record_video": True
            }
        }
    
    if request.method == 'GET':
        return jsonify(pipeline_state.get('config', {}))
    
    elif request.method == 'POST':
        data = request.json
        phase = data.get('phase')
        config_updates = data.get('config', {})
        
        if phase and phase in pipeline_state['config']:
            pipeline_state['config'][phase].update(config_updates)
            log_status(f"⚙️ Updated {phase} configuration")
            return jsonify({"status": "success", "config": pipeline_state['config']})
        
        return jsonify({"status": "error", "message": "Invalid phase"}), 400

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get performance metrics (response time, tokens)"""
    if 'metrics' not in pipeline_state:
        pipeline_state['metrics'] = {
            "response_times": [],
            "tokens_used": [],
            "phase_durations": {}
        }
    return jsonify(pipeline_state.get('metrics', {}))

@app.route('/api/evidence', methods=['GET'])
def get_evidence():
    """Get evidence files (screenshots, videos, logs)"""
    if 'evidence' not in pipeline_state:
        pipeline_state['evidence'] = {
            "screenshots": [],
            "videos": [],
            "logs_files": []
        }
    return jsonify(pipeline_state.get('evidence', {}))

@app.route('/outputs/<path:filename>')
def serve_output(filename):
    """Serve output files"""
    output_dir = Path(__file__).parent / 'outputs'
    return send_from_directory(output_dir, filename)

def log_status(message: str):
    """Add a log message to pipeline state"""
    global pipeline_state
    
    # Ensure logs list exists
    if 'logs' not in pipeline_state:
        pipeline_state['logs'] = []
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    pipeline_state["logs"].append(log_entry)
    pipeline_state["current_status"] = message
    print(log_entry)  # Also print to console

def ask_user(question: str, options: list = None, timeout: int = 10) -> str:
    """Ask user a question and wait for response with timeout"""
    global pipeline_state
    
    # Ensure required keys exist
    if 'chat_messages' not in pipeline_state:
        pipeline_state['chat_messages'] = []
    
    # Add question to chat as system message
    chat_entry = {
        "sender": "system",
        "message": question,
        "options": options,
        "timestamp": datetime.now().isoformat()
    }
    pipeline_state["chat_messages"].append(chat_entry)
    pipeline_state["waiting_for_input"] = True
    pipeline_state["pending_question"] = question
    pipeline_state["user_input"] = None
    
    log_status(f"⏸️ Question: {question}")
    
    # Wait for user response (with timeout)
    import time
    elapsed = 0
    while pipeline_state.get('waiting_for_input') and elapsed < timeout:
        time.sleep(0.5)
        elapsed += 0.5
    
    # Get response or use default
    response = pipeline_state.get('user_input', '')
    pipeline_state["pending_question"] = None
    pipeline_state["waiting_for_input"] = False
    
    # If no response, use first option as default
    if not response and options:
        response = options[0]
        log_status(f"⏭️ No response, continuing with: {response}")
    
    return response if response else "continue"

def run_full_pipeline(url: str):
    """Execute all 4 phases sequentially"""
    global pipeline_state
    
    try:
        output_dir = Path(__file__).parent / 'outputs'
        output_dir.mkdir(exist_ok=True)
        
        # PHASE 1: Web Exploration
        pipeline_state["current_phase"] = 1
        pipeline_state["progress"] = 10
        log_status("🚀 Phase 1: Starting web exploration...")
        phase1_result = run_phase1(url, output_dir)
        pipeline_state["results"]["phase1"] = phase1_result
        pipeline_state["progress"] = 25
        log_status(f"✅ Phase 1 Complete: Found {phase1_result['elements_found']} elements")
        
        # PHASE 2: Test Generation
        pipeline_state["current_phase"] = 2
        pipeline_state["progress"] = 30
        log_status("🧪 Phase 2: Starting test generation...")
        phase2_result = run_phase2(output_dir / "phase1_output.json", output_dir)
        pipeline_state["results"]["phase2"] = phase2_result
        pipeline_state["progress"] = 50
        log_status(f"✅ Phase 2 Complete: Generated {phase2_result['total_tests']} tests")
        
        # PHASE 3: Code Generation
        pipeline_state["current_phase"] = 3
        pipeline_state["progress"] = 55
        log_status("💻 Phase 3: Generating executable test code...")
        phase3_result = run_phase3(output_dir, output_dir / "phase3_outputs")
        pipeline_state["results"]["phase3"] = phase3_result
        pipeline_state["progress"] = 75
        log_status(f"✅ Phase 3 Complete: Created {phase3_result['tests_generated']} test files")
        
        # PHASE 4: Test Execution
        pipeline_state["current_phase"] = 4
        pipeline_state["progress"] = 80
        log_status("🎯 Phase 4: Executing tests...")
        phase4_result = run_phase4(output_dir / "phase3_outputs" / "tests", output_dir / "phase4_output")
        pipeline_state["results"]["phase4"] = phase4_result
        pipeline_state["progress"] = 100
        log_status(f"✅ Phase 4 Complete: {phase4_result['passed']}/{phase4_result['tests_executed']} tests passed")
        
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
        log_status("⚙️ Configuring browser...")
        sys.path.insert(0, str(phase1_dir))
        from phase1_config import create_custom_config
        from phase1_accessibility_parser import parse_accessibility_tree
        from phase1_formatter import OutputFormatter
        
        # Get config from pipeline_state
        p1_config = pipeline_state.get('config', {}).get('phase1', {})
        
        # Configure with user settings or defaults
        config = create_custom_config(
            timeout_seconds=p1_config.get('timeout', 60),
            headless=p1_config.get('headless', True),
            coverage_threshold=0.85,
            max_states=p1_config.get('max_states', 10),
            validation_level="moderate",
            browser_type=p1_config.get('browser', 'chromium'),
            take_screenshots=p1_config.get('screenshots', True),
            enable_crawling=p1_config.get('crawling', True),
            max_depth=p1_config.get('max_depth', 2)
        )
        
        log_status(f"🌐 Navigating to {url}...")
        pipeline_state["progress"] = 15
        
        # Track start time for metrics
        import time
        start_time = time.time()
        
        # Run exploration (async) with explicit event loop cleanup
        try:
            # Create new event loop to avoid conflicts
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(parse_accessibility_tree(url, config))
            finally:
                # Give pending tasks time to complete
                pending = asyncio.all_tasks(loop)
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                loop.close()
        except Exception as e:
            log_status(f"⚠️ Browser cleanup warning: {str(e)}")
            # Continue even if there's a cleanup issue
            raise
        
        # Track duration
        duration = time.time() - start_time
        if 'metrics' not in pipeline_state:
            pipeline_state['metrics'] = {
                "response_times": [],
                "tokens_used": [],
                "phase_durations": {}
            }
        pipeline_state["metrics"]["phase_durations"]["phase1"] = duration
        
        log_status("📊 Analyzing elements...")
        pipeline_state["progress"] = 22
        
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
        
        # Give Playwright time to fully clean up processes
        import time
        time.sleep(2)
        
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
        log_status("📋 Parsing Phase 1 results...")
        pipeline_state["progress"] = 32
        sys.path.insert(0, str(phase2_dir))
        from phase2_main import Phase2Orchestrator  # Import the class, not main()
        
        # Copy phase1 output to phase2 directory
        import shutil
        shutil.copy(phase1_file, phase2_dir / 'phase1_output.json')
        
        log_status("🔍 Analyzing element patterns...")
        pipeline_state["progress"] = 35
        
        log_status("🧪 Generating test cases...")
        pipeline_state["progress"] = 40
        
        # Ask user if they want to review tests interactively (10 sec timeout)
        review_mode = ask_user(
            "🤔 Would you like to review and approve test cases as they're generated?",
            options=["auto-approve", "yes", "no"],
            timeout=10
        )
        
        if review_mode.lower() in ['yes', 'y']:
            log_status("👁️ Interactive review mode enabled")
        else:
            log_status("⚡ Auto-approve mode - continuing automatically")
        
        pipeline_state["progress"] = 42
        
        # Run phase2 using the orchestrator class directly
        log_status("🔄 Executing Phase 2 orchestrator...")
        orchestrator = Phase2Orchestrator(str(phase2_dir / 'phase1_output.json'))
        result = orchestrator.run_full_pipeline(
            target_coverage=85.0,
            hitl_rounds=2,
            output_dir=str(phase2_dir)
        )
        log_status("✅ Phase 2 orchestration completed")
        
        log_status("📈 Calculating coverage metrics...")
        pipeline_state["progress"] = 48
        
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
        log_status("📝 Loading test cases...")
        pipeline_state["progress"] = 58
        sys.path.insert(0, str(phase3_dir))
        from phase3_main import Phase3Orchestrator  # Import the class, not main()
        
        # Copy phase2 outputs
        import shutil
        shutil.copy(phase2_dir / 'phase2_test_cases.json', phase3_dir / 'phase2_test_cases.json')
        shutil.copy(phase2_dir / 'phase2_coverage_metrics.json', phase3_dir / 'phase2_coverage_metrics.json')
        
        log_status("🏗️ Building page objects...")
        pipeline_state["progress"] = 62
        
        # Ask about code generation preferences (10 sec timeout)
        framework_choice = ask_user(
            "💻 Which test framework would you prefer?",
            options=["pytest (default)", "unittest", "robot framework"],
            timeout=10
        )
        
        if "unittest" in framework_choice.lower():
            log_status("📝 Note: Using pytest (unittest support coming soon)")
        elif "robot" in framework_choice.lower():
            log_status("📝 Note: Using pytest (Robot Framework support coming soon)")
        else:
            log_status("✅ Using pytest framework")
        
        log_status("⚡ Generating test code...")
        pipeline_state["progress"] = 68
        shutil.copy(phase2_dir / 'phase1_output.json', phase3_dir / 'phase1_output.json')
        
        # Run phase3 using the orchestrator class directly
        log_status("🔄 Executing Phase 3 orchestrator...")
        orchestrator = Phase3Orchestrator(str(phase3_dir), str(phase3_dir / 'phase3_outputs'))
        result = orchestrator.run_full_pipeline(
            framework="pytest",
            language="python",
            browsers=["chrome"],
            parallel_workers=1
        )
        log_status("✅ Phase 3 orchestration completed")
        
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
        log_status("📦 Preparing test environment...")
        pipeline_state["progress"] = 82
        sys.path.insert(0, str(phase4_dir))
        from phase4_main import Phase4Orchestrator  # Import the class, not main()
        
        # Copy phase3 outputs
        import shutil
        if (test_dir / 'tests').exists():
            shutil.copytree(test_dir / 'tests', phase4_dir / 'tests', dirs_exist_ok=True)
        
        log_status("🚀 Running test suite...")
        pipeline_state["progress"] = 85
        
        # Ask about execution preferences (10 sec timeout)
        exec_mode = ask_user(
            "🎯 How would you like to run the tests?",
            options=["run all tests", "run in headless mode", "show browser"],
            timeout=10
        )
        
        if "show browser" in exec_mode.lower():
            log_status("👁️ Browser visibility enabled (using config settings)")
        else:
            log_status("🚀 Running in headless mode")
        
        # Run phase4 using the orchestrator class directly
        log_status("🔄 Executing Phase 4 orchestrator...")
        orchestrator = Phase4Orchestrator(str(phase4_dir / 'tests'), str(phase4_dir / 'phase4_output'))
        result = orchestrator.run_full_pipeline(
            execution_type="all",
            parallel_workers=1
        )
        log_status("✅ Phase 4 orchestration completed")
        
        log_status("📊 Generating dashboard...")
        pipeline_state["progress"] = 95
        
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
