# Web UI - AI Test Automation Platform

## Overview
A modern, responsive web interface for running the complete 4-phase automated testing pipeline.

## Features
- **URL Input**: Simply enter the website URL to test
- **Real-time Progress**: Live updates as each phase executes
- **Visual Metrics**: Interactive charts showing coverage and test results
- **Complete Dashboard**: View all metrics from all 4 phases
- **Professional Design**: Modern gradient UI with responsive layout

## Quick Start

### 1. Install Dependencies
```bash
cd web_ui
pip install -r requirements.txt
```

### 2. Run the Server
```bash
python app.py
```

### 3. Open Browser
Navigate to: `http://localhost:5000`

## Usage

1. Enter the URL of the website you want to test
2. Click "Start Automation"
3. Watch as the pipeline executes:
   - **Phase 1**: Web exploration and element discovery
   - **Phase 2**: Test case generation
   - **Phase 3**: Executable code generation
   - **Phase 4**: Test execution and reporting

4. View comprehensive results:
   - States discovered
   - Elements found
   - Test coverage metrics
   - Pass/fail rates
   - Interactive charts

## API Endpoints

- `GET /` - Main dashboard
- `POST /api/start` - Start pipeline with URL
- `GET /api/status` - Get current execution status
- `GET /api/results/<phase>` - Get results for specific phase
- `GET /outputs/<path>` - Access generated files

## Architecture

```
web_ui/
├── app.py              # Flask backend server
├── templates/
│   └── index.html      # Frontend dashboard
└── requirements.txt    # Python dependencies
```

## Features in Detail

### Phase Indicators
Color-coded status for each phase:
- Gray: Not started
- Purple gradient: Currently running
- Green: Complete

### Metrics Cards
Four cards showing key metrics from each phase:
- Phase 1: States, elements, coverage, time
- Phase 2: Tests, coverage, approval rate
- Phase 3: Files generated, framework details
- Phase 4: Execution results, pass rate

### Interactive Charts
- **Coverage Chart**: Bar graph showing coverage across phases
- **Execution Chart**: Doughnut chart showing pass/fail distribution

## Technical Stack
- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Charts**: Chart.js 4.4.0
- **Styling**: Modern gradient design with glassmorphism effects

## Configuration
The server runs on `localhost:5000` by default. To change:
```python
# In app.py, modify the last line:
app.run(debug=True, host='0.0.0.0', port=8080)
```

## Notes
- The UI polls for status every 1 second during execution
- All phases run sequentially in a background thread
- Results are stored in memory (lost on server restart)
- Generated files are saved in respective phase directories
