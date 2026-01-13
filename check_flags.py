import json
from pathlib import Path

# Load and display feature flags
flags_path = Path('config/feature_flags.json')
with open(flags_path, 'r') as f:
    flags = json.load(f)

print("=" * 60)
print("FEATURE FLAG STATUS")
print("=" * 60)
print(f"ENABLE_AI = {flags['ENABLE_AI']}")
print(f"Mode: {'ENABLED (Full AI)' if flags['ENABLE_AI'] else 'DISABLED (extraction-only)'}")
print("=" * 60)
