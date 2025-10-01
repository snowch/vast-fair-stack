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

try:
    import requests
except ImportError:
    print("Error: requests library not installed")
    print("Install with: pip install requests")
    sys.exit(1)

from file_validator import FileValidator, quick_validate
from search_engine import FAIRSearchEngine


class SmartDownloader:
    """Download and validate scientific data files"""
    
    def __init__(self, output_dir: Path, chunk_size: int = 8192):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.chunk_size = chunk_size
        self.validator = FileValidator()
    
    def download_file(self, url: str, filename: str = None) -> dict:
        """Download a file from URL"""
        result = {
            'url': url,
            'success': False,
            'filepath': None,
            'size': 0,
            'error': None,
            'is_valid': False
        }
        
        # Determine filename
        if filename is None:
            parsed = urlparse(url)
            filename = Path(parsed.path).name
            if not filename:
                filename = f"download_{hashlib.md5(url.encode()).hexdigest()[:8]}"
        
        filepath = self.output_dir / filename
        result['filepath'] = str(filepath)
        
        try:
            print(f"Downloading: {url}")
            print(f"  → {filepath}")
            
            # Download with progress
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get total size if available
            total_size = int(response.headers.get('content-length', 0))
            
            # Download
            downloaded = 0
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Show progress
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"  Progress: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='\r')
            
            if total_size > 0:
                print()  # New line after progress
            
            result['size'] = downloaded
            result['success'] = True
            print(f"  ✓ Downloaded: {downloaded} bytes")
            
        except requests.exceptions.RequestException as e:
            result['error'] = f"Download failed: {e}"
            print(f"  ✗ Error: {e}")
            
            # Clean up partial download
            if filepath.exists():
                filepath.unlink()
            
            return result
        
        except Exception as e:
            result['error'] = f"Unexpected error: {e}"
            print(f"  ✗ Error: {e}")
            
            if filepath.exists():
                filepath.unlink()
            
            return result
        
        # Validate downloaded file
        print(f"  Validating...")
        is_valid, message = quick_validate(filepath)
        result['is_valid'] = is_valid
        result['validation_message'] = message
        
        if is_valid:
            print(f"  ✓ Valid: {message}")
        else:
            print(f"  ✗ Invalid: {message}")
            
            # Remove invalid files
            filepath.unlink()
            result['success'] = False
            result['error'] = f"Validation failed: {message}"
        
        return result
    
    def download_from_file(self, urls_file: Path) -> list:
        """Download multiple files from a text file (one URL per line)"""
        urls_file = Path(urls_file)
        
        if not urls_file.exists():
            print(f"Error: URLs file not found: {urls_file}")
            return []
        
        # Read URLs
        with open(urls_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        print(f"Found {len(urls)} URLs to download")
        print("=" * 60)
        
        results = []
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] {url}")
            result = self.download_file(url)
            results.append(result)
            
            # Small delay to be nice to servers
            if i < len(urls):
                time.sleep(1)
        
        return results


def print_summary(results: list):
    """Print download summary"""
    print("\n" + "=" * 60)
    print("Download Summary")
    print("=" * 60)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    valid = [r for r in results if r['is_valid']]
    invalid = [r for r in results if r['success'] and not r['is_valid']]
    
    print(f"\nTotal URLs: {len(results)}")
    print(f"✓ Successfully downloaded: {len(successful)}")
    print(f"✓ Valid files: {len(valid)}")
    print(f"✗ Failed downloads: {len(failed)}")
    print(f"✗ Invalid files (removed): {len(invalid)}")
    
    if valid:
        total_size = sum(r['size'] for r in valid)
        print(f"\nTotal size: {total_size / (1024*1024):.2f} MB")
        
        print(f"\nValid files:")
        for r in valid:
            fname = Path(r['filepath']).name
            size_mb = r['size'] / (1024*1024)
            print(f"  ✓ {fname} ({size_mb:.2f} MB)")
    
    if failed:
        print(f"\nFailed downloads:")
        for r in failed:
            print(f"  ✗ {r['url']}")
            print(f"     Error: {r['error']}")
    
    if invalid:
        print(f"\nInvalid files (removed):")
        for r in invalid:
            fname = Path(r['filepath']).name
            print(f"  ✗ {fname}: {r['validation_message']}")


def main():
    parser = argparse.ArgumentParser(
        description="Smart downloader for scientific data with validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create URLs file
  cat > urls.txt << EOF
  https://example.com/data1.nc
  https://example.com/data2.nc
  EOF
  
  # Download and validate
  python download_and_validate.py urls.txt
  
  # Download, validate, and auto-index
  python download_and_validate.py urls.txt --auto-index
  
  # Specify output directory
  python download_and_validate.py urls.txt --output-dir downloads/
        """
    )
    
    parser.add_argument('urls_file', help='Text file with URLs (one per line)')
    parser.add_argument('--output-dir', default='downloads',
                       help='Output directory (default: downloads)')
    parser.add_argument('--auto-index', action='store_true',
                       help='Automatically index valid files')
    parser.add_argument('--chunk-size', type=int, default=8192,
                       help='Download chunk size in bytes (default: 8192)')
    
    args = parser.parse_args()
    
    # Download files
    downloader = SmartDownloader(
        output_dir=args.output_dir,
        chunk_size=args.chunk_size
    )
    
    results = downloader.download_from_file(args.urls_file)
    
    # Print summary
    print_summary(results)
    
    # Auto-index if requested
    if args.auto_index:
        valid_files = [r for r in results if r['is_valid']]
        
        if valid_files:
            print("\n" + "=" * 60)
            print("Auto-Indexing Valid Files")
            print("=" * 60)
            
            try:
                engine = FAIRSearchEngine(load_existing=True)
            except FileNotFoundError:
                print("\nCreating new index...")
                engine = FAIRSearchEngine(load_existing=False)
            
            indexed_count = 0
            for result in valid_files:
                filepath = Path(result['filepath'])
                print(f"\nIndexing: {filepath.name}")
                
                index_result = engine.index_file(filepath)
                if index_result.get('success'):
                    indexed_count += 1
                    print(f"  ✓ Indexed")
                else:
                    print(f"  ✗ Error: {index_result.get('error')}")
            
            # Save index
            if indexed_count > 0:
                print(f"\nSaving index...")
                engine.save()
                print(f"✓ Index saved ({indexed_count} files indexed)")
                
                # Show stats
                stats = engine.get_stats()
                print(f"\nIndex now contains:")
                print(f"  Total datasets: {stats['total_vectors']}")
                print(f"  Unique files: {stats['unique_files']}")
        else:
            print("\n⚠ No valid files to index")
    
    # Return exit code
    failed = [r for r in results if not r['success']]
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
