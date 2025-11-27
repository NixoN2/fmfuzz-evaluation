#!/usr/bin/env python3
"""Shuffle all tests for baseline fuzzing

This script discovers all available tests using ctest, shuffles them
in random order, and splits them into jobs for baseline fuzzing.
"""

import os
import sys
import json
import subprocess
import random
import argparse
import re
from pathlib import Path

def get_all_tests_from_ctest(build_dir: Path) -> list:
    """Get all test names from ctest using --show-only (human-readable format)
    
    This approach doesn't require test executables to exist, unlike json-v1 format
    which tries to validate tests.
    """
    try:
        # Use ctest --show-only which lists tests without validating executables
        # Format: "Test #1: test_name"
        result = subprocess.run(
            ["ctest", "--show-only"],
            cwd=build_dir,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            print(f"Error: ctest failed with return code {result.returncode}", file=sys.stderr)
            print(f"stderr: {result.stderr}", file=sys.stderr)
            if result.stdout:
                print(f"stdout (first 500 chars): {result.stdout[:500]}", file=sys.stderr)
            return []
        
        if not result.stdout or not result.stdout.strip():
            print(f"Error: ctest returned empty output", file=sys.stderr)
            return []
        
        # Parse human-readable output: "Test #N: test_name"
        # Regex matches lines like: "Test #1: unit/test/example"
        test_regex = re.compile(r'Test\s+#\d+:\s*(.+)')
        tests = []
        
        for line in result.stdout.split('\n'):
            line = line.strip()
            if not line:
                continue
            match = test_regex.match(line)
            if match:
                test_name = match.group(1).strip()
                if test_name:
                    tests.append(test_name)
        
        return tests
    except Exception as e:
        print(f"Error getting tests from ctest: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return []

def main():
    parser = argparse.ArgumentParser(description='Shuffle all tests for baseline fuzzing')
    parser.add_argument('--build-dir', required=True, help='Build directory with ctest')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility (default: 42)')
    parser.add_argument('--output', required=True, help='Output JSON file with test list')
    
    args = parser.parse_args()
    
    build_dir = Path(args.build_dir)
    if not build_dir.exists():
        print(f"Error: Build directory not found: {build_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Get all tests
    print(f"🔍 Discovering tests from ctest...", file=sys.stderr)
    all_tests = get_all_tests_from_ctest(build_dir)
    
    if not all_tests:
        print("❌ No tests found", file=sys.stderr)
        sys.exit(1)
    
    print(f"✅ Found {len(all_tests)} total tests", file=sys.stderr)
    
    # Set random seed for reproducibility
    random.seed(args.seed)
    
    # Shuffle all tests in random order
    shuffled_tests = all_tests.copy()
    random.shuffle(shuffled_tests)
    
    print(f"✅ Shuffled {len(shuffled_tests)} tests in random order (seed: {args.seed})", file=sys.stderr)
    
    # Create matrix structure (similar to prepare_commit_fuzzer output)
    # Split into 4 jobs (same as variant1)
    tests_per_job = (len(shuffled_tests) + 3) // 4  # Ceil division
    jobs = []
    
    for i in range(0, len(shuffled_tests), tests_per_job):
        job_tests = shuffled_tests[i:i + tests_per_job]
        job_id = i // tests_per_job
        jobs.append({
            'job_id': job_id,
            'tests': job_tests
        })
    
    output = {
        'matrix': {'include': jobs},
        'total_tests': len(shuffled_tests),
        'total_jobs': len(jobs),
        'tests_per_job': tests_per_job
    }
    
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Wrote matrix to {args.output} with {len(shuffled_tests)} tests in {len(jobs)} jobs", file=sys.stderr)

if __name__ == '__main__':
    main()

