#!/usr/bin/env python3
"""
FAIR Data Search - Command-line tool for searching scientific datasets

Usage:
    python fair_search.py "ocean temperature"   # Natural language search
    python fair_search.py -i                    # Interactive mode
    python fair_search.py --list                # List all datasets
"""

import argparse
import sys
from pathlib import Path
from search_engine import FAIRSearchEngine
import json








def cmd_list(args):
    """List all indexed datasets"""
    try:
        engine = FAIRSearchEngine(load_existing=True)
    except FileNotFoundError:
        print("❌ No index found.")
        return 1
    
    metadata = engine.vector_index.metadata_store
    
    print(f"\nIndexed Datasets ({len(metadata)} total)")
    print("=" * 70)
    
    start = args.offset
    end = start + args.limit
    
    for i, meta in enumerate(metadata[start:end], start + 1):
        fname = Path(meta['filepath']).name
        title = meta.get('title', '')
        format_type = meta.get('format', '')
        
        print(f"\n{i}. {fname}")
        if title:
            print(f"   Title: {title}")
        if format_type:
            print(f"   Format: {format_type}")
        
        if 'variables' in meta:
            if isinstance(meta['variables'], dict):
                var_count = len(meta['variables'])
                var_names = list(meta['variables'].keys())[:3]
                print(f"   Variables ({var_count}): {', '.join(var_names)}", end='')
                if var_count > 3:
                    print(f", ...")
                else:
                    print()
    
    if end < len(metadata):
        print(f"\n... and {len(metadata) - end} more")
        print(f"\n💡 Use --offset {end} to see more")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="FAIR Scientific Data Search Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search with natural language
  python fair_search.py "ocean temperature measurements"
  
  # Interactive mode
  python fair_search.py -i
  
  # List all datasets
  python fair_search.py --list
  
  # Save results as JSON
  python fair_search.py "wind speed" --json results.json
  
  # Show full metadata
  python fair_search.py "chlorophyll" --full
        """
    )
    
                       help='Interactive search mode')
                       help='Number of results to return (default: 10)')
                       help='Show full metadata')
    parser.add_argument('--list', action='store_true',
                       help='List all indexed datasets')
    parser.add_argument('--limit', type=int, default=20,
                       help='Number of datasets to list (default: 20)')
    parser.add_argument('--offset', type=int, default=0,
                       help='Starting position for list (default: 0)')
    
    args = parser.parse_args()
    
    # Route to command
        return cmd_search(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
