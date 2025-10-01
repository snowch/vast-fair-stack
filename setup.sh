#!/bin/bash
# FAIR Scientific Data Discovery System - Quick Setup Script

set -e  # Exit on error

echo "=================================================="
echo "FAIR Scientific Data Discovery System - Setup"
echo "=================================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Create virtual environment (optional but recommended)
read -p "Create virtual environment? (recommended) [Y/n] " create_venv
create_venv=${create_venv:-Y}

if [[ $create_venv =~ ^[Yy]$ ]]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    
    echo "Activating virtual environment..."
    source venv/bin/activate
    
    echo "✓ Virtual environment created and activated"
    echo "  To activate later: source venv/bin/activate"
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✓ Dependencies installed"

# Download embedding model
echo ""
echo "Downloading embedding model (one-time, ~80MB)..."
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

echo ""
echo "✓ Embedding model downloaded and cached"

# Create directories
echo ""
echo "Creating directories..."
python3 -c "import config"  # This will create necessary directories

echo "✓ Directories created"

# Create sample data
echo ""
read -p "Create sample dataset for testing? [Y/n] " create_sample
create_sample=${create_sample:-Y}

if [[ $create_sample =~ ^[Yy]$ ]]; then
    echo ""
    echo "Creating sample data..."
    
    mkdir -p sample_data
    
    python3 << 'EOF'
import netCDF4
import numpy as np
from pathlib import Path

filepath = Path("sample_data/test_ocean_temp.nc")

with netCDF4.Dataset(filepath, 'w') as ds:
    ds.title = "Test Ocean Temperature Data"
    ds.institution = "FAIR Discovery Demo"
    ds.source = "Sample data for testing"
    ds.Conventions = "CF-1.8"
    
    ds.createDimension('time', 10)
    ds.createDimension('lat', 20)
    ds.createDimension('lon', 30)
    
    time = ds.createVariable('time', 'f8', ('time',))
    time.units = 'days since 2020-01-01'
    time[:] = np.arange(10)
    
    lat = ds.createVariable('lat', 'f4', ('lat',))
    lat.units = 'degrees_north'
    lat[:] = np.linspace(-90, 90, 20)
    
    lon = ds.createVariable('lon', 'f4', ('lon',))
    lon.units = 'degrees_east'
    lon[:] = np.linspace(-180, 180, 30)
    
    temp = ds.createVariable('sea_surface_temperature', 'f4', ('time', 'lat', 'lon'))
    temp.units = 'celsius'
    temp.long_name = 'Sea Surface Temperature'
    temp.standard_name = 'sea_surface_temperature'
    temp[:] = np.random.randn(10, 20, 30) * 5 + 15

print(f"✓ Created sample file: {filepath}")
EOF

    # Create README
    cat > sample_data/README.md << 'EOF'
# Sample Ocean Temperature Dataset

This is a test dataset for the FAIR Discovery System.

## Description
Sea surface temperature measurements for testing and demonstration.

## Variables
- **sea_surface_temperature**: SST in Celsius
- **time**: Days since 2020-01-01
- **lat**: Latitude in degrees north
- **lon**: Longitude in degrees east

## Institution
FAIR Discovery Demo

## License
Public Domain
EOF

    echo "✓ Sample data created in sample_data/"
fi

# Test indexing
echo ""
read -p "Index sample data now? [Y/n] " test_index
test_index=${test_index:-Y}

if [[ $test_index =~ ^[Yy]$ ]]; then
    echo ""
    echo "Indexing sample data..."
    python3 fair_index.py index sample_data/
    
    echo ""
    echo "Index statistics:"
    python3 fair_index.py stats
fi

# Test search
if [[ $test_index =~ ^[Yy]$ ]]; then
    echo ""
    echo "Testing search..."
    python3 fair_search.py "ocean temperature"
fi

# Optional: Install Ollama
echo ""
echo "=================================================="
echo "Optional: LLM Enrichment with Ollama"
echo "=================================================="
echo ""
echo "For enhanced metadata enrichment, you can install Ollama."
echo "This is completely optional - the system works without it."
echo ""
read -p "Install Ollama? [y/N] " install_ollama
install_ollama=${install_ollama:-N}

if [[ $install_ollama =~ ^[Yy]$ ]]; then
    echo ""
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    
    echo ""
    echo "Pulling llama3.2:3b model..."
    ollama pull llama3.2:3b
    
    echo "✓ Ollama installed and model ready"
fi

# Summary
echo ""
echo "=================================================="
echo "Setup Complete! 🎉"
echo "=================================================="
echo ""
echo "Quick start commands:"
echo ""
echo "  # Index your data"
echo "  python3 fair_index.py index /path/to/data"
echo ""
echo "  # Search"
echo "  python3 fair_search.py \"your query here\""
echo ""
echo "  # Interactive mode"
echo "  python3 fair_search.py -i"
echo ""
echo "  # Jupyter notebooks (for presentations)"
echo "  jupyter notebook"
echo ""
echo "Documentation:"
echo "  - README.md - Full documentation"
echo "  - Notebooks 00-99 - Step-by-step tutorials"
echo ""

if [[ $create_venv =~ ^[Yy]$ ]]; then
    echo "Remember to activate the virtual environment:"
    echo "  source venv/bin/activate"
    echo ""
fi

echo "=================================================="
echo "Happy data discovering! 🔍📊"
echo "=================================================="
