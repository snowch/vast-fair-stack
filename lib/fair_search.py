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


def format_result(result, index, show_full=False):
    """Format a search result for display"""
    lines = []
    lines.append(f"\n{index}. {Path(result['filepath']).name}")
    lines.append(f"   {'─' * 60}")
    lines.append(f"   📊 Relevance: {result['similarity_score']:.3f}")
    lines.append(f"   📁 Path: {result['filepath']}")
    
    if result.get('title'):
        lines.append(f"   📝 Title: {result['title']}")
    
    if result.get('institution'):
        lines.append(f"   🏛️  Institution: {result['institution']}")
    
    if result.get('format'):
        lines.append(f"   📋 Format: {result['format']}")
    
    # Variables
    if 'variables' in result:
        if isinstance(result['variables'], dict):
            var_names = list(result['variables'].keys())[:5]
            lines.append(f"   📈 Variables: {', '.join(var_names)}")
            if len(result['variables']) > 5:
                lines.append(f"      ... and {len(result['variables']) - 5} more")
        elif isinstance(result['variables'], list):
            lines.append(f"   📈 Variables: {', '.join(result['variables'][:5])}")
    
    # Dimensions
    if 'dimensions' in result and show_full:
        dims = ', '.join(f"{k}={v}" for k, v in result['dimensions'].items())
        lines.append(f"   📏 Dimensions: {dims}")
    
    # Archive context
    if 'archive_context' in result:
        ctx = result['archive_context']
        lines.append(f"   📦 From archive: {ctx['from_archive']}")
        if 'relative_path' in ctx:
            lines.append(f"      Path in archive: {ctx['relative_path']}")
    
    return '\n'.join(lines)


def cmd_search(args):
    """Perform a search"""
    try:
        engine = FAIRSearchEngine(load_existing=True)
    except FileNotFoundError:
        print("❌ No index found. Run 'fair_index.py' first to create an index.")
        return 1
    
    # Perform search
    results = engine.search(args.query, top_k=args.top_k)
    
    # Display results
    print(f"\nSearch: '{args.query}'")
    print("=" * 70)
    
    if results:
        print(f"Found {len(results)} result(s):\n")
        
        for i, result in enumerate(results, 1):
            print(format_result(result, i, args.full))
        
        if not args.full:
            print(f"\n💡 Tip: Use --full to see complete metadata")
    else:
        print("No results found.")
        print("\nTips:")
        print("  - Try different keywords")
        print("  - Check if data is indexed (fair_index.py stats)")
        print("  - Use broader search terms")
    
    # JSON output
    if args.json:
        json_file = Path(args.json)
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {json_file}")
    
    return 0


def cmd_interactive(args):
    """Interactive search mode"""
    try:
        engine = FAIRSearchEngine(load_existing=True)
    except FileNotFoundError:
        print("❌ No index found. Run 'fair_index.py' first.")
        return 1
    
    stats = engine.get_stats()
    
    print("=" * 70)
    print("FAIR Data Search - Interactive Mode")
    print("=" * 70)
    print(f"Index contains {stats['total_vectors']} datasets")
    print("\nCommands:")
    print("  search <query>  - Search for datasets")
    print("  list [n]        - List first n datasets (default: 10)")
    print("  stats           - Show index statistics")
    print("  help            - Show this help")
    print("  quit            - Exit")
    print("=" * 70)
    
    while True:
        try:
            command = input("\n🔍 > ").strip()
            
            if not command:
                continue
            
            if command in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            elif command == 'help':
                print("\nCommands:")
                print("  search <query>  - Natural language search")
                print("  list [n]        - List datasets")
                print("  stats           - Statistics")
                print("  quit            - Exit")
            
            elif command == 'stats':
                stats = engine.get_stats()
                print(f"\nTotal datasets: {stats['total_vectors']}")
                print(f"Unique files: {stats['unique_files']}")
                print(f"Model: {stats['model']}")
            
            elif command.startswith('list'):
                parts = command.split()
                n = int(parts[1]) if len(parts) > 1 else 10
                
                print(f"\nFirst {n} datasets:")
                metadata = engine.vector_index.metadata_store[:n]
                for i, meta in enumerate(metadata, 1):
                    fname = Path(meta['filepath']).name
                    title = meta.get('title', 'N/A')
                    print(f"{i:3d}. {fname}")
                    if title != 'N/A':
                        print(f"      {title}")
            
            elif command.startswith('search '):
                query = command[7:].strip()
                if not query:
                    print("Please provide a search query")
                    continue
                
                results = engine.search(query, top_k=args.top_k)
                
                if results:
                    print(f"\nFound {len(results)} result(s):")
                    for i, result in enumerate(results, 1):
                        print(format_result(result, i, False))
                else:
                    print("\nNo results found. Try different keywords.")
            
            else:
                # Treat as search query
                if command:
                    results = engine.search(command, top_k=args.top_k)
                    
                    if results:
                        print(f"\nFound {len(results)} result(s):")
                        for i, result in enumerate(results, 1):
                            print(format_result(result, i, False))
                    else:
                        print("\nNo results found.")
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
    
    return 0


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
    
    parser.add_argument('query', nargs='?', help='Search query')
    parser.add_argument('-i', '--interactive', action='store_true',
                       help='Interactive search mode')
    parser.add_argument('-k', '--top-k', type=int, default=10,
                       help='Number of results to return (default: 10)')
    parser.add_argument('--full', action='store_true',
                       help='Show full metadata')
    parser.add_argument('--json', help='Save results to JSON file')
    parser.add_argument('--list', action='store_true',
                       help='List all indexed datasets')
    parser.add_argument('--limit', type=int, default=20,
                       help='Number of datasets to list (default: 20)')
    parser.add_argument('--offset', type=int, default=0,
                       help='Starting position for list (default: 0)')
    
    args = parser.parse_args()
    
    # Route to command
    if args.interactive:
        return cmd_interactive(args)
    elif args.list:
        return cmd_list(args)
    elif args.query:
        return cmd_search(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
