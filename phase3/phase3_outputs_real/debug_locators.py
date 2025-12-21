import json
from pathlib import Path

# Load phase1 data
phase1_file = Path('../../phase1/phase1_real_output2.json')
with open(phase1_file, 'r') as f:
    data = json.load(f)

for elem in data['interactive_elements'][-3:]:
    print(f"\nElement: {elem['element_id']}")
    print(f"  Label: {elem.get('label', 'NONE')}")
    print(f"  Type: {elem.get('type', 'NONE')}")
    locators = elem.get('locators', {})
    confidence = elem.get('locator_confidence', {})
    for k, v in locators.items():
        conf = confidence.get(k, 0)
        print(f"    {k} (conf={conf}): {v}")
