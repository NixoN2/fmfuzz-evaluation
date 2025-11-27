#!/usr/bin/env python3
"""Read changed functions from variant1 fuzzing statistics

This script downloads variant1 fuzzing statistics from S3 and extracts
the list of changed functions for a given commit.
"""

import os
import sys
import json
import boto3
import gzip
from botocore.exceptions import ClientError

def main():
    if len(sys.argv) < 3:
        print("Usage: read_changed_functions_from_statistics.py <solver> <commit_hash>", file=sys.stderr)
        sys.exit(1)
    
    solver = sys.argv[1]
    commit_hash = sys.argv[2]
    
    bucket = os.getenv('AWS_S3_BUCKET')
    if not bucket:
        raise RuntimeError("AWS_S3_BUCKET environment variable not set")
    
    s3_client = boto3.client('s3', region_name=os.getenv('AWS_REGION', 'eu-north-1'))
    
    # Download variant1 statistics
    s3_key = f"evaluation/rq2/{solver}/fuzzing-statistics/variant1/fuzzing_statistics-{commit_hash}.json.gz"
    
    print(f"🔍 Downloading variant1 statistics from s3://{bucket}/{s3_key}", file=sys.stderr)
    
    try:
        # Download to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json.gz') as tmp_file:
            tmp_path = tmp_file.name
        
        s3_client.download_file(bucket, s3_key, tmp_path)
        
        # Read and decompress
        with gzip.open(tmp_path, 'rt') as f:
            stats = json.load(f)
        
        # Extract changed functions
        changed_functions = []
        if 'functions' in stats:
            for func in stats['functions']:
                if 'function_id' in func:
                    changed_functions.append(func['function_id'])
        
        # Output as JSON
        output = {
            'commit_hash': commit_hash,
            'changed_functions': changed_functions,
            'total_functions': len(changed_functions)
        }
        
        print(json.dumps(output, indent=2))
        print(f"✅ Extracted {len(changed_functions)} changed functions", file=sys.stderr)
        
        # Clean up
        os.unlink(tmp_path)
        
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f"❌ Variant1 statistics not found for commit {commit_hash}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"❌ Error downloading from S3: {e}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()

