#!/usr/bin/env python3
"""
FAIR Data Index - Command-line tool for indexing scientific datasets

Usage:
    python fair_index.py index <path>           # Index file or directory
    python fair_index.py stats                  # Show index statistics
    python fair_index.py validate <path>        # Validate files
    python fair_index.py rebuild                # Rebuild entire index
"""

import argparse
import sys
from pathlib import Path
from search_engine import FAIRSearchEngine
from file_validator import FileValidator
import config


def cmd_index(args):
    """Index a file or directory"""
    path = Path(args.path)
    
    if not path.exists():
        print(f"Error: Path does not exist: {path}")
        return 1
    
    # Initialize engine
    print("Initializing search engine...")
    engine = FAIRSearchEngine(load_existing=not args.new)
    
    # Index
    if path.is_file():
        print(f"\nIndexing file: {path}")
        result = engine.index_file(
            path,
            validate=not args.no_validate,
            include_companions=not args.no_companions
        )
        
        if result.get('success'):
            print(f"✓ Successfully indexed: {path.name}")
        else:
            print(f"✗ Error: {result.get('error', 'Unknown error')}")
            return 1
    
    elif path.is_dir():
        print(f"\nIndexing directory: {path}")
        result = engine.index_directory(
            path,
            validate=not args.no_validate,
            include_companions=not args.no_companions,
            extract_archives=args.extract_archives,
            show_progress=not args.quiet
        )
        
        print(f"\nResults:")
        print(f"  ✓ Indexed: {result['indexed']}")
        print(f"  ✗ Errors: {result['errors']}")
        print(f"  📦 Archives: {result['archives_processed']}")
        
        if result['errors'] > 0 and not args.quiet:
            print(f"\nFirst few errors:")
            for error in result['details']['errors'][:5]:
                print(f"  - {error.get('filepath', 'unknown')}: {error.get('error', '')}")
    
    # Save
    print("\nSaving index...")
    engine.save()
    print("✓ Index saved")
    
    # Show stats
    stats = engine.get_stats()
    print(f"\nIndex now contains:")
    print(f"  Total datasets: {stats['total_vectors']}")
    print(f"  Unique files: {stats['unique_files']}")
    
    return 0


def cmd_stats(args):
    """Show index statistics"""
    try:
        engine = FAIRSearchEngine(load_existing=True)
        stats = engine.get_stats()
        
        print("FAIR Data Index Statistics")
        print("=" * 60)
        print(f"Total datasets indexed: {stats['total_vectors']}")
        print(f"Unique files: {stats['unique_files']}")
        print(f"Embedding dimension: {stats['embedding_dim']}")
        print(f"Model: {stats['model']}")
        print(f"Cache size: {stats['cache_size']}")
        print(f"Index type: {stats['index_type']}")
        
        print(f"\nIndex files:")
        print(f"  FAISS: {config.FAISS_INDEX_FILE}")
        print(f"  Metadata: {config.METADATA_STORE_FILE}")
        print(f"  File map: {config.FILEPATH_MAP_FILE}")
        
        return 0
    
    except FileNotFoundError:
        print("No index found. Run 'index' command first.")
        return 1


def cmd_validate(args):
    """Validate files"""
    path = Path(args.path)
    
    if not path.exists():
        print(f"Error: Path does not exist: {path}")
        return 1
    
    validator = FileValidator()
    
    if path.is_file():
        result = validator.check_file_signature(path)
        
        print(f"Validation: {path.name}")
        print("=" * 60)
        print(f"Size: {result['size_formatted']}")
        print(f"Expected type: {result['expected_type']}")
        print(f"Detected type: {result['detected_type']}")
        print(f"Valid: {'✓' if result['is_valid'] else '✗'}")
        
        if result['issues']:
            print(f"\nIssues:")
            for issue in result['issues']:
                print(f"  - {issue}")
            
            suggestions = validator.suggest_fixes(result)
            if suggestions:
                print(f"\nSuggestions:")
                for suggestion in suggestions:
                    print(f"  - {suggestion}")
        
        return 0 if result['is_valid'] else 1
    
    elif path.is_dir():
        results = validator.validate_directory(path)
        
        print(f"Validation: {path}")
        print("=" * 60)
        print(f"Total files: {results['total_files']}")
        print(f"✓ Valid: {len(results['valid'])}")
        print(f"✗ Invalid: {len(results['invalid'])}")
        
        if results['invalid']:
            print(f"\nInvalid files:")
            for inv in results['invalid'][:20]:
                fname = Path(inv['filepath']).name
                issues = ', '.join(inv['issues'])
                print(f"  - {fname}: {issues}")
            
            if len(results['invalid']) > 20:
                print(f"  ... and {len(results['invalid']) - 20} more")
        
        if results['issues_summary']:
            print(f"\nIssue summary:")
            for issue, count in results['issues_summary'].items():
                print(f"  - {issue}: {count}")
        
        return 0 if len(results['invalid']) == 0 else 1


def cmd_rebuild(args):
    """Rebuild entire index"""
    if not args.yes:
        response = input("This will delete the existing index. Continue? [y/N] ")
        if response.lower() != 'y':
            print("Cancelled.")
            return 0
    
    # Delete existing index files
    for filepath in [config.FAISS_INDEX_FILE, config.METADATA_STORE_FILE, 
                     config.FILEPATH_MAP_FILE]:
        if filepath.exists():
            filepath.unlink()
            print(f"Deleted: {filepath}")
    
    print("\n✓ Index files deleted. Use 'index' command to rebuild.")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="FAIR Scientific Data Indexing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Index a single file
  python fair_index.py index data/ocean_temp.nc
  
  # Index a directory
  python fair_index.py index /path/to/data --extract-archives
  
  # Validate files
  python fair_index.py validate data/
  
  # Show statistics
  python fair_index.py stats
  
  # Rebuild index
  python fair_index.py rebuild --yes
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Index command
    index_parser = subparsers.add_parser('index', help='Index files or directories')
    index_parser.add_argument('path', help='Path to file or directory')
    index_parser.add_argument('--new', action='store_true', 
                            help='Create new index (discard existing)')
    index_parser.add_argument('--no-validate', action='store_true',
                            help='Skip file validation')
    index_parser.add_argument('--no-companions', action='store_true',
                            help='Skip companion document discovery')
    index_parser.add_argument('--extract-archives', action='store_true',
                            help='Extract and index archive contents')
    index_parser.add_argument('--quiet', action='store_true',
                            help='Minimal output')
    
    # Stats command
    subparsers.add_parser('stats', help='Show index statistics')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate files')
    validate_parser.add_argument('path', help='Path to file or directory')
    
    # Rebuild command
    rebuild_parser = subparsers.add_parser('rebuild', help='Rebuild index from scratch')
    rebuild_parser.add_argument('--yes', action='store_true',
                              help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to command handler
    if args.command == 'index':
        return cmd_index(args)
    elif args.command == 'stats':
        return cmd_stats(args)
    elif args.command == 'validate':
        return cmd_validate(args)
    elif args.command == 'rebuild':
        return cmd_rebuild(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
