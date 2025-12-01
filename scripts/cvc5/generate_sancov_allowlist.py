#!/usr/bin/env python3
"""
Generate sancov coverage allowlist from prepare_commit_fuzzer output.

This script reads the JSON output from prepare_commit_fuzzer.py (which includes
function_info_map with mangled names) and generates a coverage allowlist file
in the format required by Clang's sanitizer coverage allowlist feature.

Format:
  src:path/to/file.cpp
  fun:_Z9fibonaccii
  fun:_Z19handleLargeDigitSumi
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Set


def generate_allowlist(function_info_map: Dict, output_file: str):
    """Generate sancov allowlist file from function info map."""
    
    # Group functions by source file
    file_to_functions: Dict[str, List[str]] = {}
    
    for func_key, func_info in function_info_map.items():
        mangled_name = func_info.get('mangled_name')
        file_path = func_info.get('file', '')
        
        if not mangled_name:
            print(f"Warning: No mangled name for {func_key}, skipping", file=sys.stderr)
            continue
        
        # Normalize file path - use relative path from repo root
        # Remove absolute path prefix if present
        if file_path.startswith('/'):
            # Try to extract relative path (e.g., src/...)
            if '/src/' in file_path:
                file_path = 'src/' + file_path.split('/src/')[-1]
            elif '/cvc5/src/' in file_path:
                file_path = 'src/' + file_path.split('/cvc5/src/')[-1]
            else:
                # Fallback: use just the filename
                file_path = Path(file_path).name
        
        # Ensure file path starts with src/ for cvc5
        if not file_path.startswith('src/'):
            # Try to find src/ in the path
            if 'src/' in file_path:
                file_path = 'src/' + file_path.split('src/')[-1]
            else:
                print(f"Warning: File path {file_path} doesn't start with src/, using as-is", file=sys.stderr)
        
        if file_path not in file_to_functions:
            file_to_functions[file_path] = []
        
        # Add mangled name (remove any leading/trailing whitespace)
        mangled_name = mangled_name.strip()
        if mangled_name and mangled_name not in file_to_functions[file_path]:
            file_to_functions[file_path].append(mangled_name)
    
    # Write allowlist file
    with open(output_file, 'w') as f:
        for file_path in sorted(file_to_functions.keys()):
            # Write src: line
            f.write(f"src:{file_path}\n")
            
            # Write fun: lines for each mangled name
            for mangled_name in sorted(file_to_functions[file_path]):
                f.write(f"fun:{mangled_name}\n")
            
            # Add blank line between files for readability
            f.write("\n")
    
    total_functions = sum(len(funcs) for funcs in file_to_functions.values())
    print(f"Generated allowlist with {total_functions} functions across {len(file_to_functions)} files")
    print(f"Output written to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate sancov coverage allowlist from prepare_commit_fuzzer output'
    )
    parser.add_argument(
        'input_json',
        help='JSON file from prepare_commit_fuzzer.py (must contain function_info_map)'
    )
    parser.add_argument(
        '-o', '--output',
        default='coverage_allowlist.txt',
        help='Output allowlist file (default: coverage_allowlist.txt)'
    )
    
    args = parser.parse_args()
    
    # Read input JSON
    try:
        with open(args.input_json, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found: {args.input_json}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {args.input_json}: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Extract function_info_map
    function_info_map = data.get('function_info_map', {})
    
    if not function_info_map:
        print("Warning: No function_info_map found in input JSON", file=sys.stderr)
        print("This might be because prepare_commit_fuzzer.py was run with an older version", file=sys.stderr)
        sys.exit(1)
    
    # Generate allowlist
    generate_allowlist(function_info_map, args.output)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

