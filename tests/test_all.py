#!/usr/bin/env python3
"""
Run all C64 BASIC buildpack test scripts and report overall results.
"""

import subprocess
import sys
import os

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))

TEST_SCRIPTS = [
    'test_interpreter.py',
    'test_arrays.py',
    'test_components.py',
    'test_accept.py',
]


def run_test(script: str) -> bool:
    path = os.path.join(TESTS_DIR, script)
    env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
    result = subprocess.run(
        [sys.executable, path],
        env=env,
        capture_output=True,
        text=True,
        encoding='utf-8',
    )
    print(f"\n{'=' * 60}")
    print(f"  {script}")
    print('=' * 60)
    output = (result.stdout or '') + (result.stderr or '')
    if output:
        print(output, end='')
    return result.returncode == 0


def main():
    passed = []
    failed = []

    for script in TEST_SCRIPTS:
        ok = run_test(script)
        (passed if ok else failed).append(script)

    print(f"\n{'=' * 60}")
    print(f"  Results: {len(passed)}/{len(TEST_SCRIPTS)} passed")
    print('=' * 60)
    for s in passed:
        print(f"  PASS  {s}")
    for s in failed:
        print(f"  FAIL  {s}")
    print()

    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
