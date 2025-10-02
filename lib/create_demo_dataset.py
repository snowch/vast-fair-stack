"""
Create mystery climate dataset for conference demo
Intentionally minimal metadata to showcase AI enrichment capabilities
"""
from pathlib import Path
import netCDF4
import numpy as np


def create_mystery_climate_dataset() -> Path:
    """
    Creates a realistic climate model output with minimal metadata
    
    This simulates typical HPC output that researchers encounter:
    - Cryptic variable names (t2m, sst, pr) without explanations
    - Missing institutional metadata
    - No title or clear description
    - Scattered documentation in separate files
    
    Perfect for demonstrating how AI agents can:
    1. Decode abbreviations
    2. Infer scientific domain
    3. Discover and link companion documentation
    4. Transform chaos into FAIR-compliant data
    
    Returns:
        Path to the created NetCDF file
    """
    # Create sample_data directory
    output_dir = Path("sample_data")
    output_dir.mkdir(exist_ok=True)
    
    filepath = output_dir / "mystery_climate_data.nc"
    
    print(f"Creating mystery dataset: {filepath.name}")
    print("  (Intentionally minimal metadata for demo)")
    
    # Create NetCDF with MINIMAL metadata - this is intentional!
    with netCDF4.Dataset(filepath, 'w') as ds:
        # Only bare minimum - no title, institution, description, etc.
        # This is what many HPC outputs actually look like
        ds.Conventions = "CF-1.8"
        ds.history = "Created by climate_model_v3.2 on 2023-12-15"
        
        # Create dimensions
        ds.createDimension('time', 365)  # Daily for one year
        ds.createDimension('lat', 90)    # 2-degree resolution
        ds.createDimension('lon', 180)   # 2-degree resolution
        
        # Time variable
        time = ds.createVariable('time', 'f8', ('time',))
        time.units = 'days since 2020-01-01'
        time.calendar = 'standard'
        time[:] = np.arange(365)
        
        # Latitude
        lat = ds.createVariable('lat', 'f4', ('lat',))
        lat.units = 'degrees_north'
        lat.standard_name = 'latitude'
        lat[:] = np.linspace(-89, 89, 90)
        
        # Longitude  
        lon = ds.createVariable('lon', 'f4', ('lon',))
        lon.units = 'degrees_east'
        lon.standard_name = 'longitude'
        lon[:] = np.linspace(-179, 179, 180)
        
        # ============ CRYPTIC VARIABLES - No explanations! ============
        # This is the key: variable names that need AI to decode
        
        # t2m = temperature at 2 meters (but not documented!)
        t2m = ds.createVariable('t2m', 'f4', ('time', 'lat', 'lon'),
                               fill_value=-999.0, zlib=True)
        t2m.units = 'K'  # Kelvin, not user-friendly Celsius
        # Generate realistic temperature data (250-310K range)
        # Build the array all at once to avoid broadcasting issues
        t2m_data = (280 + 
                   15 * np.sin(np.linspace(0, 2*np.pi, 365))[:, None, None] +
                   20 * np.cos(np.linspace(-np.pi/2, np.pi/2, 90))[None, :, None] +
                   np.random.randn(365, 90, 180) * 3)
        t2m[:] = t2m_data
        
        # sst = sea surface temperature (cryptic!)
        sst = ds.createVariable('sst', 'f4', ('time', 'lat', 'lon'),
                               fill_value=-999.0, zlib=True)
        sst.units = 'K'
        # Warmer than air temp, more variability near equator
        sst_data = (290 + 
                   10 * np.sin(np.linspace(0, 2*np.pi, 365))[:, None, None] +
                   15 * np.cos(np.linspace(-np.pi/2, np.pi/2, 90))[None, :, None] +
                   np.random.randn(365, 90, 180) * 2)
        sst[:] = sst_data
        
        # pr = precipitation rate (very cryptic!)
        pr = ds.createVariable('pr', 'f4', ('time', 'lat', 'lon'),
                              fill_value=-999.0, zlib=True)
        pr.units = 'kg m-2 s-1'  # Not user-friendly units
        # Precipitation pattern: more near equator, seasonal
        lat_factor = 1 - np.abs(np.linspace(-1, 1, 90))**2
        seasonal = 1 + 0.5 * np.sin(np.linspace(0, 2*np.pi, 365))
        pr_data = 0.0001 * seasonal[:, None, None] * lat_factor[None, :, None]
        pr_data += np.abs(np.random.randn(365, 90, 180) * 0.00005)
        pr[:] = pr_data
        
        # wspd = wind speed (another cryptic one)
        wspd = ds.createVariable('wspd', 'f4', ('time', 'lat', 'lon'),
                                fill_value=-999.0, zlib=True)
        wspd.units = 'm s-1'
        # Higher winds at mid-latitudes
        lat_wind = 5 + 10 * (1 - np.abs(np.linspace(-1, 1, 90))**0.5)
        wspd_data = lat_wind[None, :, None] + np.random.randn(365, 90, 180) * 2
        wspd_data = np.maximum(wspd_data, 0)  # No negative wind speeds
        wspd[:] = wspd_data
    
    print(f"  ✓ Created NetCDF file: {filepath.stat().st_size / 1024:.1f} KB")
    print(f"  ✓ Variables: t2m, sst, pr, wspd (cryptic names!)")
    print(f"  ✓ Dimensions: time=365, lat=90, lon=180")
    
    # Create companion documentation (scattered!)
    print("\n  Creating companion documentation...")
    _create_companion_docs(output_dir)
    
    return filepath


def _create_companion_docs(output_dir: Path):
    """
    Create scattered companion documentation
    
    This simulates real-world scenarios where:
    - Documentation exists but is separate from data
    - README describes the dataset
    - Processing scripts show provenance
    - Citation info is in yet another file
    
    The AI discovery agent will find and link these!
    """
    
    # ============ README with dataset description ============
    readme = output_dir / "README_climate_2023.md"
    with open(readme, 'w') as f:
        f.write("""# CMIP6 Climate Model Ensemble Output - 2020

## Overview
High-resolution climate model output from CMIP6 ensemble simulation.
This dataset represents state-of-the-art climate projections under
the RCP 4.5 emissions scenario.

## File
- mystery_climate_data.nc (primary output file)

## Variables
The dataset contains the following variables:

- **t2m**: Temperature at 2 meters above surface (Kelvin)
  - Standard atmospheric temperature measurement
  - Used for surface climate analysis
  
- **sst**: Sea Surface Temperature (Kelvin)
  - Ocean surface temperature
  - Critical for ocean-atmosphere coupling
  
- **pr**: Precipitation Rate (kg m⁻² s⁻¹)
  - Rainfall and snowfall
  - Key hydrological cycle indicator
  
- **wspd**: Wind Speed at 10m (m s⁻¹)
  - Surface wind velocity
  - Important for weather patterns

## Spatial Coverage
- Global coverage: 90°S to 90°N, 180°W to 180°E
- Resolution: 2 degrees (approximately 200km)
- Grid: Regular latitude-longitude

## Temporal Coverage
- Period: January 1, 2020 - December 31, 2020
- Frequency: Daily
- Time steps: 365 days

## Model Details
- **Model Framework**: CMIP6 Multi-Model Ensemble
- **Scenario**: RCP 4.5 (Representative Concentration Pathway)
- **Institution**: Climate Research Center, University Consortium
- **Ensemble Member**: r1i1p1f1

## Processing
Data has been:
- Quality controlled for outliers
- Regridded to common 2-degree grid
- Bias-corrected using observational data
- Gap-filled using temporal interpolation

## Citation
Please cite this dataset as:

Smith, J., Johnson, A., & Williams, R. (2023). 
CMIP6 High-Resolution Climate Projections for Impact Assessment.
Geoscientific Model Development, 16(4), 1234-1256.
DOI: 10.5194/gmd-2023-185

## Contact
Climate Research Center
Email: climate-data@research-center.edu
Website: https://climate.research-center.edu/cmip6

## License
Creative Commons Attribution 4.0 International (CC BY 4.0)

## Related Publications
- Smith et al. (2023) - Model validation
- Johnson et al. (2022) - Bias correction methodology
- Williams et al. (2021) - Ensemble construction

## Acknowledgments
This work was supported by NSF Grant #12345678 and 
used computational resources from XSEDE allocation ABC123.
""")
    print(f"    ✓ {readme.name}")
    
    # ============ Processing script ============
    script = output_dir / "process_cmip6_ensemble.py"
    with open(script, 'w') as f:
        f.write("""#!/usr/bin/env python
\"\"\"
CMIP6 Climate Model Ensemble Processing Pipeline

This script processes raw CMIP6 model output and generates
the standardized mystery_climate_data.nc file.

Input: Raw CMIP6 netCDF files from multiple models
Output: mystery_climate_data.nc (harmonized, regridded)

Author: Jane Smith (jane.smith@research-center.edu)
Date: 2023-12-15
Version: 3.2

Pipeline Steps:
1. Load raw model outputs
2. Quality control (outlier detection)
3. Regrid to common 2-degree grid
4. Bias correction using ERA5 reanalysis
5. Calculate ensemble statistics
6. Write standardized output

Dependencies:
- xarray
- numpy
- scipy
- cdo (Climate Data Operators)

Usage:
    python process_cmip6_ensemble.py --input raw_cmip6/ --output mystery_climate_data.nc
\"\"\"

import xarray as xr
import numpy as np
from pathlib import Path
from datetime import datetime

# Configuration
INPUT_DIR = Path("raw_cmip6/")
OUTPUT_FILE = "mystery_climate_data.nc"
REFERENCE_GRID = "grid_2deg.nc"
BIAS_CORRECTION_DATA = "era5_climatology.nc"

def load_ensemble_members(input_dir):
    \"\"\"Load all ensemble members from input directory\"\"\"
    models = []
    for model_file in input_dir.glob("*.nc"):
        print(f"Loading {model_file.name}...")
        ds = xr.open_dataset(model_file)
        models.append(ds)
    return models

def quality_control(dataset):
    \"\"\"Remove outliers and invalid data\"\"\"
    # Flag values outside physical bounds
    dataset['t2m'] = dataset['t2m'].where(
        (dataset['t2m'] > 200) & (dataset['t2m'] < 350)
    )
    dataset['sst'] = dataset['sst'].where(
        (dataset['sst'] > 270) & (dataset['sst'] < 310)
    )
    dataset['pr'] = dataset['pr'].where(dataset['pr'] >= 0)
    return dataset

def regrid_to_common(dataset, target_grid):
    \"\"\"Regrid to common 2-degree resolution\"\"\"
    # Use conservative remapping
    # Implementation would use CDO or xesmf
    pass

def bias_correction(dataset, reference):
    \"\"\"Apply bias correction using observational data\"\"\"
    # Delta method: preserve model trends while matching climatology
    pass

def calculate_ensemble_statistics(models):
    \"\"\"Calculate multi-model mean and spread\"\"\"
    ensemble_mean = xr.concat(models, dim='model').mean(dim='model')
    ensemble_std = xr.concat(models, dim='model').std(dim='model')
    return ensemble_mean, ensemble_std

def write_output(dataset, output_file):
    \"\"\"Write processed data to standardized NetCDF\"\"\"
    # Set CF-compliant attributes
    dataset.attrs['Conventions'] = 'CF-1.8'
    dataset.attrs['institution'] = 'Climate Research Center'
    dataset.attrs['source'] = 'CMIP6 Multi-Model Ensemble'
    dataset.attrs['history'] = f'Created {datetime.now().isoformat()}'
    
    # Compression
    encoding = {
        var: {'zlib': True, 'complevel': 4}
        for var in dataset.data_vars
    }
    
    dataset.to_netcdf(output_file, encoding=encoding)
    print(f"✓ Wrote output: {output_file}")

def main():
    \"\"\"Main processing pipeline\"\"\"
    print("CMIP6 Ensemble Processing Pipeline")
    print("=" * 60)
    
    # Load data
    print("\\n1. Loading ensemble members...")
    models = load_ensemble_members(INPUT_DIR)
    print(f"   Loaded {len(models)} models")
    
    # Process each model
    print("\\n2. Quality control...")
    models = [quality_control(m) for m in models]
    
    print("\\n3. Regridding to common grid...")
    target_grid = xr.open_dataset(REFERENCE_GRID)
    models = [regrid_to_common(m, target_grid) for m in models]
    
    print("\\n4. Bias correction...")
    reference = xr.open_dataset(BIAS_CORRECTION_DATA)
    models = [bias_correction(m, reference) for m in models]
    
    print("\\n5. Calculating ensemble statistics...")
    ensemble_mean, ensemble_std = calculate_ensemble_statistics(models)
    
    print("\\n6. Writing output...")
    write_output(ensemble_mean, OUTPUT_FILE)
    
    print("\\n✓ Processing complete!")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"Size: {Path(OUTPUT_FILE).stat().st_size / 1024 / 1024:.1f} MB")

if __name__ == "__main__":
    main()
""")
    print(f"    ✓ {script.name}")
    
    # ============ Citation file ============
    citation = output_dir / "CITATION.bib"
    with open(citation, 'w') as f:
        f.write("""@article{smith2023cmip6,
  title={CMIP6 High-Resolution Climate Projections for Impact Assessment},
  author={Smith, Jane and Johnson, Alice and Williams, Robert},
  journal={Geoscientific Model Development},
  volume={16},
  number={4},
  pages={1234--1256},
  year={2023},
  publisher={Copernicus Publications},
  doi={10.5194/gmd-2023-185}
}

@dataset{climate_ensemble_2023,
  title={CMIP6 Climate Model Ensemble Output - RCP 4.5 Scenario},
  author={Smith, Jane and Johnson, Alice and Williams, Robert},
  year={2023},
  publisher={Climate Research Center Data Repository},
  doi={10.5281/zenodo.7654321},
  url={https://data.climate-research.edu/cmip6/rcp45/}
}

% Please cite both the methodology paper and the dataset when using this data
""")
    print(f"    ✓ {citation.name}")
    
    # ============ Additional metadata file ============
    metadata = output_dir / "METADATA.txt"
    with open(metadata, 'w') as f:
        f.write("""Dataset Metadata
================

Dataset ID: CMIP6-RCP45-2020-v1.0
Creation Date: 2023-12-15
Last Modified: 2023-12-20

Contact Information:
-------------------
Name: Dr. Jane Smith
Email: jane.smith@research-center.edu
Institution: Climate Research Center
Phone: +1 (555) 123-4567

Data Processing:
---------------
Input Data: CMIP6 archive (30 models)
Processing Date: 2023-12-10 to 2023-12-15
Processing Software: CDO v2.0.5, Python 3.9
Quality Control: Automated + manual review
Validation: Compared against ERA5 reanalysis

Known Issues:
------------
- Some coastal grid cells have interpolation artifacts
- High-latitude precipitation may be underestimated
- Sea ice coverage simplified in this version

Future Updates:
--------------
- Version 2.0 planned for Q2 2024
- Will include additional variables (snow, cloud cover)
- Improved high-latitude physics

Funding:
-------
This work was supported by:
- National Science Foundation Grant #ATM-2023-12345
- Department of Energy Grant #DOE-2023-67890
- NOAA Climate Program Office

Computing Resources:
-------------------
Computational resources provided by:
- XSEDE Allocation TG-ATM230045
- NCAR CISL Cheyenne Supercomputer
- Total CPU hours: ~50,000

Related Datasets:
----------------
- CMIP6-RCP26-2020 (lower emissions scenario)
- CMIP6-RCP85-2020 (higher emissions scenario)
- CMIP6-Historical-1850-2014 (historical baseline)
""")
    print(f"    ✓ {metadata.name}")
    
    print("\n  ✓ Companion documentation created")
    print("    (README, script, citation, metadata)")


# Test/demo code
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Creating Mystery Climate Dataset for Conference Demo")
    print("=" * 70 + "\n")
    
    filepath = create_mystery_climate_dataset()
    
    print("\n" + "=" * 70)
    print("Dataset Creation Complete!")
    print("=" * 70)
    print(f"\nPrimary file: {filepath}")
    print(f"Size: {filepath.stat().st_size / 1024:.1f} KB")
    print(f"Exists: {filepath.exists()}")
    
    # Show what was created
    print("\nFiles created in sample_data/:")
    output_dir = Path("sample_data")
    for f in sorted(output_dir.glob("*")):
        if f.is_file():
            size_kb = f.stat().st_size / 1024
            print(f"  - {f.name:40s} ({size_kb:8.1f} KB)")
    
    print("\n💡 This dataset is perfect for the demo because:")
    print("   • Minimal metadata (only Conventions attribute)")
    print("   • Cryptic variable names (t2m, sst, pr, wspd)")
    print("   • Scattered documentation (README, script, citation)")
    print("   • Realistic HPC output that needs AI enrichment")
    print("\n✓ Ready for conference demonstration!")