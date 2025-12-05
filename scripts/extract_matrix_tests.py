#!/usr/bin/env python3
"""
Extract test list from fuzzing matrix for a specific commit and job_id.

Usage:
    python3 extract_matrix_tests.py <matrix_file> <commit> <job_id>

Outputs the tests array as JSON to stdout.
"""

import json
import sys
from pathlib import Path


def find_matching_entry(matrix_data, commit, job_id):
    """
    Find the matrix entry that matches the given commit and job_id.
    
    Handles:
    - Short vs full commit hashes (prefix matching)
    - String vs numeric job_id
    """
    if 'include' not in matrix_data:
        raise ValueError("Matrix file missing 'include' field")
    
    # Try to convert job_id to int if possible, keep as string otherwise
    try:
        job_id_int = int(job_id)
    except ValueError:
        job_id_int = None
    
    for entry in matrix_data['include']:
        # Skip non-object entries
        if not isinstance(entry, dict):
            continue
        
        # Check commit match (exact or prefix)
        entry_commit = entry.get('commit', '')
        commit_matches = (
            entry_commit == commit or
            entry_commit.startswith(commit) or
            commit.startswith(entry_commit)
        )
        
        if not commit_matches:
            continue
        
        # Check job_id match
        fuzzer_job = entry.get('fuzzer_job', {})
        entry_job_id = fuzzer_job.get('job_id')
        
        # Try both string and numeric comparison
        job_id_matches = (
            str(entry_job_id) == str(job_id) or
            (job_id_int is not None and entry_job_id == job_id_int)
        )
        
        if job_id_matches:
            return fuzzer_job.get('tests', [])
    
    return None


def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <matrix_file> <commit> <job_id>", file=sys.stderr)
        sys.exit(1)
    
    matrix_file = Path(sys.argv[1])
    commit = sys.argv[2]
    job_id = sys.argv[3]
    
    if not matrix_file.exists():
        print(f"Error: Matrix file not found: {matrix_file}", file=sys.stderr)
        sys.exit(1)
    
    try:
        with open(matrix_file, 'r') as f:
            matrix_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in matrix file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to read matrix file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Find matching entry
    tests = find_matching_entry(matrix_data, commit, job_id)
    
    if tests is None:
        print(f"Error: Could not find test data for commit {commit}, job_id {job_id}", file=sys.stderr)
        
        # Show available options for debugging
        if 'include' in matrix_data:
            commits = set()
            job_ids_for_commit = []
            for entry in matrix_data['include']:
                if isinstance(entry, dict):
                    entry_commit = entry.get('commit', '')
                    commits.add(entry_commit)
                    if (entry_commit == commit or 
                        entry_commit.startswith(commit) or 
                        commit.startswith(entry_commit)):
                        job_id_val = entry.get('fuzzer_job', {}).get('job_id')
                        if job_id_val is not None:
                            job_ids_for_commit.append(job_id_val)
            
            print(f"Available commits in matrix: {sorted(list(commits))[:5]}", file=sys.stderr)
            if job_ids_for_commit:
                print(f"Available job_ids for this commit: {sorted(set(job_ids_for_commit))[:5]}", file=sys.stderr)
        
        sys.exit(1)
    
    # Output tests as JSON
    print(json.dumps(tests, separators=(',', ':')))


if __name__ == '__main__':
    main()

