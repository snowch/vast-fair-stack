#!/usr/bin/env python3
"""
Smart download and validation script for scientific data

Downloads files from URLs, validates them, and optionally indexes them.

Usage:
    python download_and_validate.py urls.txt
    python download_and_validate.py urls.txt --output-dir data/ --auto-index
"""

import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse
import time
import hashlib

            
            indexed_count = 0
            for result in valid_files:
                filepath = Path(result['filepath'])
                print(f"\nIndexing: {filepath.name}")
                
                index_result = extractor.extract(filepath)
                if index_result.get('success'):
                    indexed_count += 1
                    print(f"  ✓ Indexed")
                else:
                    print(f"  ✗ Error: {index_result.get('error')}")
            
            # Save index
            if indexed_count > 0:
                print(f"\nSaving index...")
                print(f"✓ Index saved ({indexed_count} files indexed)")
                
                # Show stats
        else:
            print("\n⚠ No valid files to index")
    
    # Return exit code
    failed = [r for r in results if not r['success']]
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
