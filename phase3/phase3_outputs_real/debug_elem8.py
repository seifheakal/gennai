import json
from pathlib import Path

# Load phase1 data
phase1_file = Path('../../phase1/phase1_real_output2.json')
with open(phase1_file, 'r') as f:
    data = json.load(f)

print("Element 007 and 008 - All Locator Info:\n")
for elem in data['interactive_elements'][-2:]:
    elem_id = elem['element_id']
    label = elem.get('label', 'NONE')
    print(f"\n{elem_id}: {label}")
    
    locators = elem.get('locators', {})
    confidence = elem.get('locator_confidence', {})
    
    print("All Locators:")
    for locator_key, locator_value in locators.items():
        conf = confidence.get(locator_key, 0)
        print(f"  {locator_key} (conf={conf}): {locator_value}")
    
    print("\nElement Details:")
    for key in ['visible', 'enabled', 'accessibility_info', 'bounding_box', 'element_size']:
        print(f"  {key}: {elem.get(key, 'NONE')}")
