import json
from pathlib import Path

# Load phase1 data
phase1_file = Path('../../phase1/phase1_real_output2.json')
with open(phase1_file, 'r') as f:
    data = json.load(f)

print("All Element Hierarchy Paths:\n")
for elem in data['interactive_elements']:
    elem_id = elem['element_id']
    label = elem.get('label', 'NONE')
    hierarchy = elem.get('element_hierarchy', 'NONE')
    print(f"{elem_id}: {label}")
    print(f"  Hierarchy: {hierarchy}\n")
