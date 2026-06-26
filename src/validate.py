import csv
import glob
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import config

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

cfg = config.load_config(os.path.join(PROJECT_ROOT, 'config/pipeline.yaml'))
rules = config.load_config(os.path.join(PROJECT_ROOT, 'config/validation_rules.yaml'))

RAW_DIR = os.path.join(PROJECT_ROOT, cfg['file_paths']['raw_data'])
STAGING_DIR = os.path.join(PROJECT_ROOT, cfg['file_paths']['staging_data'])
SUMMARY_PATH = os.path.join(PROJECT_ROOT, 'data_validation_summary.json')

logging.basicConfig(
    filename=os.path.join(PROJECT_ROOT, cfg['logging']['log_file']),
    filemode='w',
    level=getattr(logging, cfg['logging']['level']),
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)

required_cols = rules['required_fields']
optional_cols = rules['optional_fields']
all_cols = required_cols + optional_cols
allowed_event_types = set(rules['event_type']['allowed_values'])
allow_future_timestamps = rules['timestamp']['allow_future']

NOW_UTC = datetime.now(timezone.utc).replace(tzinfo=None)


def normalize_event_type(value):
    if value is None:
        return None
    return str(value).strip().lower()


def is_valid_timestamp(value):
    try:
        ts = datetime.fromisoformat(str(value))
        if not allow_future_timestamps and ts > NOW_UTC:
            return False
        return True
    except (ValueError, TypeError):
        return False


def main():
    run_start = time.time()
    raw_files = sorted(glob.glob(os.path.join(RAW_DIR, '*.json')))

    if not raw_files:
        logger.error('No raw JSON files found in %s', RAW_DIR)
        return

    total_records = 0
    dupe_events = 0
    valid_events = []
    invalid_events = []
    seen_hashes = set()

    for raw_file in raw_files:
        with open(raw_file, 'r') as f:
            file_data = json.load(f)

        for event in file_data:
            total_records += 1
            error_reasons = []

            # O(1) dedup via hash of the raw event before normalization
            event_hash = json.dumps(event, sort_keys=True)
            if event_hash in seen_hashes:
                dupe_events += 1
                event['error_reason'] = 'duplicate_event'
                invalid_events.append(event)
                continue
            seen_hashes.add(event_hash)

            # Normalize event_type in-place before validation
            if 'event_type' in event and event['event_type'] is not None:
                event['event_type'] = normalize_event_type(event['event_type'])

            # Check required fields are present and non-null
            for col in required_cols:
                if col not in event:
                    error_reasons.append(f'missing_{col}')
                elif event[col] is None:
                    error_reasons.append(f'invalid_{col}')

            # Validate event_type against allowed values (only if not already flagged)
            if ('invalid_event_type' not in error_reasons
                    and 'missing_event_type' not in error_reasons
                    and event.get('event_type') is not None):
                if event['event_type'] not in allowed_event_types:
                    error_reasons.append('invalid_event_type')

            # Validate timestamp format and future check (only if not already flagged)
            if ('invalid_timestamp' not in error_reasons
                    and 'missing_timestamp' not in error_reasons
                    and event.get('timestamp') is not None):
                if not is_valid_timestamp(event['timestamp']):
                    error_reasons.append('invalid_timestamp')

            if error_reasons:
                event['error_reason'] = ';'.join(error_reasons)
                invalid_events.append(event)
            else:
                valid_events.append(event)

    os.makedirs(STAGING_DIR, exist_ok=True)

    with open(os.path.join(STAGING_DIR, 'events_invalid.csv'), 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=all_cols + ['error_reason'], extrasaction='ignore')
        writer.writeheader()
        writer.writerows(invalid_events)

    with open(os.path.join(STAGING_DIR, 'events_valid.csv'), 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=all_cols, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(valid_events)

    run_end = time.time()

    # Null rates across all unique (non-duplicate) events
    unique_events = valid_events + [
        e for e in invalid_events if 'duplicate_event' not in e.get('error_reason', '')
    ]
    total_unique = len(unique_events) or 1

    def null_rate(col):
        count = sum(1 for e in unique_events if e.get(col) is None or col not in e)
        return f'{count / total_unique * 100:.2f}%'

    validation_json = {
        'run_metadata': {
            'run_id': time.strftime('%Y_%m_%d'),
            'input_files': [os.path.basename(f) for f in raw_files],
            'pipeline_stage': 'data_validation',
            'runtime': f'{run_end - run_start:.2f} seconds'
        },
        'data_statistics': {
            'total_records': total_records,
            'valid_records': len(valid_events),
            'invalid_records': len(invalid_events),
            'percent_invalid': f'{len(invalid_events) / total_records * 100:.2f}%' if total_records else '0.00%'
        },
        'failure_analysis': {
            'duplicate_events': dupe_events,
            'invalid_event_type': sum(1 for e in invalid_events if 'invalid_event_type' in e.get('error_reason', '')),
            'invalid_timestamp': sum(1 for e in invalid_events if 'invalid_timestamp' in e.get('error_reason', '')),
            'missing_event_id': sum(1 for e in invalid_events if 'missing_event_id' in e.get('error_reason', '')),
            'missing_user_id': sum(1 for e in invalid_events if 'missing_user_id' in e.get('error_reason', '')),
            'missing_event_type': sum(1 for e in invalid_events if 'missing_event_type' in e.get('error_reason', '')),
            'missing_timestamp': sum(1 for e in invalid_events if 'missing_timestamp' in e.get('error_reason', '')),
        },
        'multi_failure_records': {
            'records_with_multiple_failures': sum(
                1 for e in invalid_events if e.get('error_reason', '').count(';') >= 1
            ),
            'max_failures_in_single_record': max(
                (e.get('error_reason', '').count(';') + 1) for e in invalid_events
            ) if invalid_events else 0
        },
        'null_rates': {col: null_rate(col) for col in ['event_type', 'timestamp', 'source', 'metadata']},
        'duplicate_analysis': {
            'total_duplicate_events': dupe_events,
            'percent_duplicates': f'{dupe_events / total_records * 100:.2f}%' if total_records else '0.00%'
        },
        'timestamp_analysis': {
            'earliest_timestamp': min(e['timestamp'] for e in valid_events) if valid_events else None,
            'latest_timestamp': max(e['timestamp'] for e in valid_events) if valid_events else None,
            'future_timestamps': sum(
                1 for e in valid_events if e['timestamp'] > NOW_UTC.isoformat()
            )
        }
    }

    with open(SUMMARY_PATH, 'w') as f:
        json.dump(validation_json, f, indent=4)

    logger.info(
        'Files processed: %s', ', '.join(os.path.basename(f) for f in raw_files)
    )
    logger.info(
        'Total: %d | Valid: %d | Invalid: %d | Duplicates: %d',
        total_records, len(valid_events), len(invalid_events), dupe_events
    )


if __name__ == '__main__':
    main()
