import json

# Load the index
with open('output/index.json', 'r') as f:
    data = json.load(f)

records = data['records']

# Analysis
print("=" * 80)
print("DETAILED RESULTS ANALYSIS")
print("=" * 80)
print()

# Actionable breakdown
actionable = [r for r in records if r['actionable']]
non_actionable = [r for r in records if not r['actionable']]

print(f"ACTIONABLE BREAKDOWN:")
print(f"  Actionable records: {len(actionable)} ({len(actionable)/len(records)*100:.1f}%)")
print(f"  Non-actionable: {len(non_actionable)} ({len(non_actionable)/len(records)*100:.1f}%)")
print()

# Extraction methods
methods = {}
for r in records:
    m = r['metadata']['extraction_method']
    methods[m] = methods.get(m, 0) + 1

print(f"EXTRACTION METHODS:")
for method, count in sorted(methods.items(), key=lambda x: x[1], reverse=True):
    print(f"  {method:15s}: {count:4d} ({count/len(records)*100:.1f}%)")
print()

# File types
file_types = {}
for r in records:
    ft = r['file_type']
    file_types[ft] = file_types.get(ft, 0) + 1

print(f"FILE TYPES IN RECORDS:")
for ft, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
    print(f"  {ft:10s}: {count:4d} ({count/len(records)*100:.1f}%)")
print()

# Field confidence analysis
fields = ['pickup_number', 'scheduled_date', 'material', 'weight', 'weight_unit', 'reference_number']
field_stats = {f: {'found': 0, 'avg_conf': []} for f in fields}

for r in records:
    for field in fields:
        if r['extracted_fields'][field]['value'] is not None:
            field_stats[field]['found'] += 1
            field_stats[field]['avg_conf'].append(r['extracted_fields'][field]['confidence'])

print(f"FIELD EXTRACTION RATES:")
for field in fields:
    found = field_stats[field]['found']
    avg = sum(field_stats[field]['avg_conf']) / len(field_stats[field]['avg_conf']) if field_stats[field]['avg_conf'] else 0
    print(f"  {field:20s}: {found:4d}/{len(records)} ({found/len(records)*100:.1f}%) | Avg Confidence: {avg:.2f}")
print()

# Actionable records sample
print(f"SAMPLE ACTIONABLE RECORDS:")
for i, r in enumerate(actionable[:5]):
    source = r['source_file'].split('\\')[-1]  # Get filename only
    avg_conf = r['metadata']['average_confidence']
    print(f"  {i+1}. {r['record_id']} | {source[:50]} | Confidence: {avg_conf:.2f}")
print()

# Most common issues
print(f"COMMON EXTRACTION ISSUES:")
missing_pickup = sum(1 for r in records if r['extracted_fields']['pickup_number']['value'] is None)
missing_date = sum(1 for r in records if r['extracted_fields']['scheduled_date']['value'] is None)
missing_weight = sum(1 for r in records if r['extracted_fields']['weight']['value'] is None)

print(f"  Missing pickup_number: {missing_pickup} ({missing_pickup/len(records)*100:.1f}%)")
print(f"  Missing scheduled_date: {missing_date} ({missing_date/len(records)*100:.1f}%)")
print(f"  Missing weight: {missing_weight} ({missing_weight/len(records)*100:.1f}%)")
print()

print("=" * 80)
