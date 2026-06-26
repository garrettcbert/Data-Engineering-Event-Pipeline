import os
import subprocess
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')


def run_stage(script_name, stage_name):
    script_path = os.path.join(SRC_DIR, script_name)
    print(f'\n=== {stage_name} ===')
    start = time.time()
    result = subprocess.run(
        [sys.executable, script_path],
        cwd=PROJECT_ROOT,
        env={**os.environ, 'PYTHONPATH': SRC_DIR}
    )
    elapsed = time.time() - start
    if result.returncode != 0:
        print(f'{stage_name} failed (exit {result.returncode})')
        sys.exit(result.returncode)
    print(f'{stage_name} complete in {elapsed:.1f}s')


if __name__ == '__main__':
    run_stage('ingest.py', 'Ingest')
    run_stage('validate.py', 'Validate')
    run_stage('load.py', 'Load')
    print('\nPipeline complete.')
