import csv
import json
import logging
import time
from utils.config import load_config

config = load_config('config/validation_rules.yaml')
required_fields = config['required_fields']


run_id = time.strftime("%Y_%m_%d")
start_time = time.time()

with open('data/raw/events_2025_01_00.json', 'r') as f:
    data = f.read()


json_data = json.loads(data)

valid_cols = [
    'event_id',
    'user_id',
    'event_type',
    'timestamp',
    'source',
    'metadata'
]

total_records = 0
unique_events = []

dupe_events = 0

valid_events = []
invalid_events = []

for event in json_data:
    total_records += 1

    error_reason = ''
    if event not in unique_events:
        unique_events.append(event)
        
    else:
        dupe_events += 1
        error_reason += 'duplicate_event;'
        continue


    if all(col in event for col in valid_cols) \
        and event['event_type'] is not None \
        and event['timestamp'] is not None \
        and event['source'] is not None \
        and event['metadata'] is not None \
        and event['user_id'] is not None \
        and event['event_id'] is not None:
        valid_events.append(event)
        continue

    invalid_col = [col for col in event if event[col] == None]
    missing_col = [col for col in valid_cols if col not in event]

    if invalid_col:
        for col in invalid_col:
            error_reason += f'invalid_{col};'
    if missing_col:
        for col in missing_col:
            error_reason += f'missing_{col};'
    event['error_reason'] = error_reason.strip()
    invalid_events.append(event)

with open('staging/events_invalid.csv', 'w', newline='') as csvfile:
    fieldnames = valid_cols + ['error_reason']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for event in invalid_events:
        writer.writerow(event)

with open('staging/events_valid.csv', 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=valid_cols)
    writer.writeheader()
    for event in valid_events:
        writer.writerow(event)

end_time = time.time()

validation_json = {
    'run_metadata': {
        'run_id': run_id,
        'input_file': 'events_2025_01_00.json',
        'pipeline_stage': 'data_validation',
        'runtime': f'{end_time - start_time:.2f} seconds'
    },
    'data_statistics': {
        'total_records': total_records,
        'valid_records': len(valid_events),
        'invalid_records': len(invalid_events),
        'percent_invalid': f'{(len(invalid_events) / total_records) * 100:.2f}%',
    },
    'failure_analysis': {
        'duplicate_events': dupe_events,
        'invalid_event_type': sum(1 for event in invalid_events if 'invalid_event_type' in event.get('error_reason', '')),
        'invalid_timestamp': sum(1 for event in invalid_events if 'invalid_timestamp' in event.get('error_reason', '')),
        'invalid_source': sum(1 for event in invalid_events if 'invalid_source' in event.get('error_reason', '')),
        'invalid_metadata': sum(1 for event in invalid_events if 'invalid_metadata' in event.get('error_reason', '')),
        'missing_event_id': sum(1 for event in invalid_events if 'missing_event_id' in event.get('error_reason', '')),
        'missing_user_id': sum(1 for event in invalid_events if 'missing_user_id' in event.get('error_reason', '')),
    },
    'multi-failure_records': {
        'records_with_multiple_failures': sum(1 for event in invalid_events if event.get('error_reason', '').count(';') > 1),
        'max_failures_in_single_record': max((event.get('error_reason', '').count(';') + 1) for event in invalid_events) if invalid_events else 0
    },
    'null_rates': {
        'event_type_null_rate': f'{(sum(1 for event in invalid_events if "invalid_event_type" in event.get("error_reason", "") or "missing_event_type" in event.get("error_reason", "")) / total_records) * 100:.2f}%',
        'timestamp_null_rate': f'{(sum(1 for event in invalid_events if "invalid_timestamp" in event.get("error_reason", "") or "missing_timestamp" in event.get("error_reason", "")) / total_records) * 100:.2f}%',
        'source_null_rate': f'{(sum(1 for event in invalid_events if "invalid_source" in event.get("error_reason", "") or "missing_source" in event.get("error_reason", "")) / total_records) * 100:.2f}%',
        'metadata_null_rate': f'{(sum(1 for event in invalid_events if "invalid_metadata" in event.get("error_reason", "") or "missing_metadata" in event.get("error_reason", "")) / total_records) * 100:.2f}%'
    },
    'duplicate_analysis': {
        'total_duplicate_events': dupe_events,
        'percent_duplicates': f'{(dupe_events / total_records) * 100:.2f}%'
    },
    'timestamp_analysis': {
        'earliest_timestamp': min(event['timestamp'] for event in valid_events),
        'latest_timestamp': max(event['timestamp'] for event in valid_events),
        'future_timestamps': sum(1 for event in valid_events if event['timestamp'] > time.strftime("%Y-%m-%d %H:%M:%S"))
    }
}
with open('data_validation_summary.json', 'w') as f:
    json.dump(validation_json, f, indent=4)