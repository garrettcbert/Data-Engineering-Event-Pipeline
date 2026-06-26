import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import config

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

cfg = config.load_config(os.path.join(PROJECT_ROOT, 'config/pipeline.yaml'))

STAGING_DIR = os.path.join(PROJECT_ROOT, cfg['file_paths']['staging_data'])
CLEANED_DIR = os.path.join(PROJECT_ROOT, cfg['file_paths']['cleaned_data'])


def main():
    valid_df = pd.read_csv(os.path.join(STAGING_DIR, 'events_valid.csv'))

    cleaned_df = valid_df.copy()
    cleaned_df['user_id'] = pd.to_numeric(cleaned_df['user_id'], errors='coerce').astype('Int64')
    cleaned_df['timestamp'] = pd.to_datetime(cleaned_df['timestamp'], errors='coerce')
    cleaned_df = cleaned_df.sort_values('timestamp').reset_index(drop=True)

    os.makedirs(CLEANED_DIR, exist_ok=True)
    out_path = os.path.join(CLEANED_DIR, 'events_cleaned.csv')
    cleaned_df.to_csv(out_path, index=False)
    print(f'Loaded {len(cleaned_df)} records -> {out_path}')


if __name__ == '__main__':
    main()
