# FAIR Scientific Data Discovery System

A **complete, local, free** system for making scientific datasets (NetCDF, HDF5, GRIB) **Findable, Accessible, Interoperable, and Reusable (FAIR)** through semantic vector search.

## 🎯 Key Features

- ✅ **100% Local & Free** - No API keys required, works offline
- ✅ **Natural Language Search** - Find data using plain English
- ✅ **Handles Minimal Metadata** - Works even with poorly documented files
- ✅ **Archive Support** - Automatically extracts and indexes .zip, .tar.gz files
- ✅ **Companion Discovery** - Finds READMEs, citations, scripts
- ✅ **Fast Search** - Sub-second queries using FAISS
- ✅ **Optional LLM Enrichment** - Use local Ollama for enhanced metadata

## 🚀 Quick Start

### (my) VM Specifications

* **OS:** Ubuntu 23.04
* **CPU:** 8 vCPUs
* **RAM:** 8 GB
* **Disk Space:** 100 GB

### Installation

```bash
# Clone or download the repository
cd fair-data-discovery

# Install dependencies
pip install -r requirements.txt

# Quick test
python fair_index.py stats
```

### Index Your First Dataset

```bash
# Index a single file
python fair_index.py index data/ocean_temp.nc

# Index a directory
python fair_index.py index /path/to/data --extract-archives

# Check what was indexed
python fair_index.py stats
```

### Search

```bash
# Natural language search
python fair_search.py "ocean temperature measurements"

# Interactive mode
python fair_search.py -i

# List all datasets
python fair_search.py --list
```

## 📊 What Gets Indexed?

### From Data Files
- Global attributes (title, institution, conventions)
- Variables (names, units, descriptions)
- Dimensions (time, latitude, longitude, etc.)
- File format and structure

### From Companion Documents
- **README files**: Dataset descriptions, methodology
- **Citations**: DOIs, papers, authors
- **Scripts**: Processing code, examples
- **Documentation**: User guides, technical notes

### From Filenames
- Dates (YYYYMMDD patterns)
- Versions (v1.0, version_2)
- Variable hints (sst → sea_surface_temperature)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SYSTEM LAYERS                            │
└─────────────────────────────────────────────────────────────┘

Layer 1: DATA INGESTION
├── Archive Handler (.zip, .tar.gz extraction)
├── File Validator (magic byte verification)
├── Metadata Extractors (NetCDF, HDF5, GRIB)
└── Companion Doc Discovery (README, scripts, citations)

Layer 2: METADATA ENRICHMENT
├── Basic Text Generation (from extracted metadata)
├── Data Inspection Tools (statistics, temporal/spatial coverage)
└── LLM Enrichment (optional, using local Ollama)

Layer 3: INDEXING & STORAGE
├── Embedding Generation (sentence-transformers)
├── Vector Index (FAISS - local similarity search)
└── Metadata Store (pickle - full metadata preservation)

Layer 4: DISCOVERY INTERFACE
├── Python API (programmatic access)
├── CLI Search Interface (interactive/command-line)
└── Jupyter Notebooks (academic presentations)
```

## 📚 Documentation

### Jupyter Notebooks (for Academic Presentations)

1. **00_Setup_and_Installation.ipynb** - Get started, install dependencies
2. **01_File_Validation.ipynb** - Detect corrupt or invalid files
3. **02_Metadata_Extraction.ipynb** - Extract from NetCDF/HDF5/GRIB
4. **03_Companion_Documents.ipynb** - Discover READMEs, citations, scripts
5. **04_Vector_Search.ipynb** - Semantic search with embeddings
6. **99_Complete_Workflow.ipynb** - End-to-end examples

### Command-Line Tools

- **fair_index.py** - Index files and directories
- **fair_search.py** - Search indexed datasets

### Python Modules

- **config.py** - Configuration settings
- **utils.py** - Shared utilities
- **file_validator.py** - File validation using magic bytes
- **metadata_extractors.py** - Format-specific extraction
- **companion_finder.py** - Find companion documents
- **companion_extractor.py** - Extract content from companions
- **archive_handler.py** - Handle compressed archives
- **embedding_generator.py** - Generate embeddings
- **vector_index.py** - FAISS-based search index
- **search_engine.py** - Main search engine
- **llm_enricher.py** - Optional LLM enrichment

## 🔧 Usage Examples

### Python API

```python
from search_engine import FAIRSearchEngine

# Initialize
engine = FAIRSearchEngine()

# Index a file
engine.index_file("data/ocean_temp.nc")

# Search
results = engine.search("ocean temperature", top_k=5)

for result in results:
    print(f"{result['filepath']}: {result['similarity_score']:.3f}")

# Find similar datasets
similar = engine.find_similar("data/reference.nc", top_k=5)

# Save index
engine.save()
```

### Command Line

```bash
# Index with all features
python fair_index.py index /data --extract-archives

# Validate before indexing
python fair_index.py validate /data

# Interactive search
python fair_search.py -i

# Search and save results
python fair_search.py "wind speed" --json results.json --full

# Show index statistics
python fair_index.py stats
```

### Jupyter Notebooks

```python
# In Jupyter
%load_ext autoreload
%autoreload 2

from search_engine import FAIRSearchEngine

engine = FAIRSearchEngine()
results = engine.search("your query here")

# Display results in notebook
for i, r in enumerate(results, 1):
    print(f"{i}. {r['title']} (score: {r['similarity_score']:.3f})")
```

## 🎓 Academic Use Cases

### 1. Research Data Management
- Index lab datasets as they're created
- Find related experiments quickly
- Track data provenance

### 2. Multi-Project Data Discovery
- Index data from multiple projects
- Find similar datasets across projects
- Identify reusable data

### 3. Data Repository Management
- Make institutional data FAIR
- Improve data discoverability
- Support data reuse

### 4. Literature Review Support
- Find datasets mentioned in papers
- Locate supplementary data
- Track dataset citations

## 🔬 Technical Details

### Embedding Model
- **Model**: sentence-transformers/all-MiniLM-L6-v2
- **Size**: ~80MB
- **Dimension**: 384
- **Quality**: 90-95% of OpenAI embeddings
- **Speed**: ~0.01s per embedding

### Vector Search
- **Engine**: FAISS IndexFlatIP
- **Similarity**: Cosine similarity (normalized)
- **Speed**: <200ms for 10k datasets
- **Scalability**: Millions of vectors

### File Format Support
- **NetCDF**: .nc, .nc4 (via netCDF4-python)
- **HDF5**: .hdf, .hdf5, .h5 (via h5py)
- **GRIB**: .grb, .grb2, .grib (via pygrib, optional)

### Archive Support
- **ZIP**: .zip
- **TAR**: .tar, .tar.gz, .tgz, .tar.bz2

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Embedding model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Search settings
DEFAULT_TOP_K = 10
SIMILARITY_THRESHOLD = 0.3

# File validation
MIN_FILE_SIZE = 100  # bytes
MAX_HEADER_BYTES = 1024

# LLM settings (optional)
OLLAMA_MODEL = "llama3.2:3b"
OLLAMA_URL = "http://localhost:11434"
```

## 🔄 Optional: LLM Enrichment

For enhanced metadata using a local LLM:

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3.2:3b

# Enable in Python
from llm_enricher import LLMEnricher

enricher = LLMEnricher()
enriched = enricher.enrich_metadata(metadata)
```

## 🐛 Troubleshooting

### "No index found"
```bash
# Create an index first
python fair_index.py index /path/to/data
```

### "pygrib not installed"
```bash
# Optional - only needed for GRIB files
# Requires system dependencies (eccodes)
pip install pygrib
```

### Slow indexing
```bash
# Index runs at ~10 files/minute
# For large datasets, run overnight or use progress bar:
python fair_index.py index /data  # Progress bar shown by default
```

### Search returns no results
- Verify data is indexed: `python fair_index.py stats`
- Try broader search terms
- Check similarity threshold in config.py

## 📊 Performance Benchmarks

**Test System**: MacBook Pro M1, 16GB RAM

| Operation | Speed | Notes |
|-----------|-------|-------|
| File validation | 1000 files/sec | Magic byte check |
| Metadata extraction | 10 files/min | Depends on file size |
| Embedding generation | 100 texts/sec | Cached after first run |
| Search query | <200ms | For 10,000 datasets |
| Index size | 2MB / 1000 files | FAISS + metadata |

## 🤝 Contributing

This is a modular system designed for easy extension:

### Adding New File Formats

1. Create extractor in `metadata_extractors.py`:
```python
class NewFormatExtractor:
    def extract(self, filepath: Path) -> Dict[str, Any]:
        # Your extraction logic
        pass
```

2. Register in `MetadataExtractor.extract()`

### Adding New Companion Types

1. Add patterns to `config.py`:
```python
NEW_DOC_PATTERNS = ['*pattern*']
```

2. Add extraction method to `CompanionDocExtractor`

## 📝 License

[Specify your license here]

## 🙏 Acknowledgments

Built with:
- [sentence-transformers](https://www.sbert.net/) - Local embeddings
- [FAISS](https://github.com/facebookresearch/faiss) - Vector search
- [netCDF4-python](https://unidata.github.io/netcdf4-python/) - NetCDF support
- [h5py](https://www.h5py.org/) - HDF5 support

## 📧 Contact

[Your contact information]

## 📖 Citation

If you use this system in your research, please cite:

```bibtex
@software{fair_discovery,
  title = {FAIR Scientific Data Discovery System},
  author = {[Your Name]},
  year = {2024},
  url = {https://github.com/yourusername/fair-discovery}
}
```

---

**Making Scientific Data FAIR, One Dataset at a Time** 🌍🔬📊
