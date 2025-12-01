#!/usr/bin/env python3
"""
Parse sancov coverage statistics and output in comparable format.

Reads coverage data from sancov_coverage_tracker and outputs statistics
in a format suitable for comparison across different fuzzing runs.
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List


def parse_coverage_file(coverage_file: str) -> Dict:
    """Parse coverage JSON file."""
    with open(coverage_file, 'r') as f:
        return json.load(f)


def format_stats(coverage_data: Dict, output_format: str = "text") -> str:
    """Format coverage statistics."""
    stats = coverage_data.get('stats', {})
    covered_pcs = coverage_data.get('covered_pcs', [])
    test_coverage = coverage_data.get('test_coverage', {})
    
    if output_format == "json":
        return json.dumps({
            'total_pcs': len(covered_pcs),
            'tests_tracked': len(test_coverage),
            'processed_files': stats.get('processed_files', 0),
            'coverage_by_test': {k: len(v) for k, v in test_coverage.items()}
        }, indent=2)
    
    elif output_format == "csv":
        lines = ["test_id,unique_pcs"]
        for test_id, pcs in test_coverage.items():
            lines.append(f"{test_id},{len(pcs)}")
        return "\n".join(lines)
    
    else:  # text format
        lines = [
            "Sancov Coverage Statistics",
            "=" * 40,
            f"Total unique PCs: {len(covered_pcs)}",
            f"Tests tracked: {len(test_coverage)}",
            f"Processed .sancov files: {stats.get('processed_files', 0)}",
            "",
            "Coverage by test:",
            "-" * 40
        ]
        
        # Sort by coverage (descending)
        sorted_tests = sorted(test_coverage.items(), key=lambda x: len(x[1]), reverse=True)
        for test_id, pcs in sorted_tests:
            lines.append(f"  {test_id}: {len(pcs)} PCs")
        
        return "\n".join(lines)


def compare_coverage(coverage_files: List[str], output_format: str = "text") -> str:
    """Compare coverage across multiple runs."""
    coverage_data_list = []
    for cf in coverage_files:
        data = parse_coverage_file(cf)
        coverage_data_list.append((Path(cf).stem, data))
    
    if output_format == "json":
        comparison = {}
        for name, data in coverage_data_list:
            comparison[name] = {
                'total_pcs': len(data.get('covered_pcs', [])),
                'tests_tracked': len(data.get('test_coverage', {})),
                'processed_files': data.get('stats', {}).get('processed_files', 0)
            }
        return json.dumps(comparison, indent=2)
    
    else:  # text format
        lines = [
            "Coverage Comparison",
            "=" * 40
        ]
        
        for name, data in coverage_data_list:
            stats = data.get('stats', {})
            covered_pcs = data.get('covered_pcs', [])
            test_coverage = data.get('test_coverage', {})
            
            lines.append(f"\n{name}:")
            lines.append(f"  Total PCs: {len(covered_pcs)}")
            lines.append(f"  Tests tracked: {len(test_coverage)}")
            lines.append(f"  Processed files: {stats.get('processed_files', 0)}")
        
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Parse and format sancov coverage statistics'
    )
    parser.add_argument(
        'coverage_file',
        nargs='?',
        help='Coverage JSON file from sancov_coverage_tracker'
    )
    parser.add_argument(
        '--format',
        choices=['text', 'json', 'csv'],
        default='text',
        help='Output format (default: text)'
    )
    parser.add_argument(
        '--compare',
        nargs='+',
        metavar='FILE',
        help='Compare coverage across multiple files'
    )
    
    args = parser.parse_args()
    
    if args.compare:
        # Compare mode
        output = compare_coverage(args.compare, args.format)
        print(output)
    elif args.coverage_file:
        # Single file mode
        data = parse_coverage_file(args.coverage_file)
        output = format_stats(data, args.format)
        print(output)
    else:
        parser.print_help()
        sys.exit(1)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

