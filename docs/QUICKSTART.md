# Quick Start Guide - 5 Minutes to FAIR Data Discovery

## 🚀 Installation (2 minutes)

```bash
# 1. Clone or download the repository
cd fair-data-discovery

# 2. Run setup script (creates venv, installs deps, downloads model)
chmod +x setup.sh
./setup.sh

# Answer 'Y' to all prompts for quickest setup
```

**That's it!** The setup script will:
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Download embedding model (~80MB)
- ✅ Create sample data
- ✅ Index sample data
- ✅ Test search

## 📊 First Search (30 seconds)

```bash
# Search for something
python fair_search.py "ocean temperature"

# Should show results with similarity scores
```

## 📁 Index Your Data (2 minutes)

```bash
# Index a single file
python fair_index.py index /path/to/your/data.nc

# Index entire directory
python fair_index.py index /path/to/data/

# Index with archive extraction
python fair_index.py index /path/to/data/ --extract-archives

# Check what was indexed
python fair_index.py stats
```

## 🔍 Search Your Data (30 seconds)

```bash
# Natural language search
python fair_search.py "sea surface temperature measurements"

# Interactive mode (recommended)
python fair_search.py -i
# Then type queries like:
# > ocean temperature
# > wind speed data
# > list 10
# > quit

# Show full metadata
python fair_search.py "your query" --full

# Save results as JSON
python fair_search.py "your query" --json results.json
```

## 📓 For Academic Presentations

```bash
# Start Jupyter
jupyter notebook

# Open notebooks in order:
# 1. 00_Setup_and_Installation.ipynb
# 2. 01_File_Validation.ipynb
# 3. 02_Metadata_Extraction.ipynb
# 4. 03_Companion_Documents.ipynb
# 5. 04_Vector_Search.ipynb
# 6. 99_Complete_Workflow.ipynb
```

## 🎯 Common Tasks

### Download and Index Data from URLs

```bash
# 1. Create URLs file
cat > data_urls.txt << EOF
https://example.com/data1.nc
https://example.com/data2.nc
EOF

# 2. Download, validate, and auto-index
python download_and_validate.py data_urls.txt --auto-index
```

### Validate Files Before Indexing

```bash
# Validate single file
python fair_index.py validate data.nc

# Validate directory
python fair_index.py validate /path/to/data/

# Shows which files are valid/invalid and why
```

### Work with Archives

```bash
# Index a .zip file (auto-extracts)
python fair_index.py index research_data.zip --extract-archives

# All files in archive are automatically discovered and indexed
```

### Find Similar Datasets

```python
# In Python
from search_engine import FAIRSearchEngine

engine = FAIRSearchEngine(load_existing=True)
similar = engine.find_similar("reference_data.nc", top_k=5)

for result in similar:
    print(f"{result['filepath']}: {result['similarity_score']:.3f}")
```

## 🔧 Configuration

Edit `config.py` to customize:

```python
# Search settings
DEFAULT_TOP_K = 10              # Results per search
SIMILARITY_THRESHOLD = 0.3      # Minimum relevance

# Embedding model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# File paths
INDEX_DIR = Path("indexes")      # Where indexes are stored
```

## 🐛 Troubleshooting

### "No index found"
```bash
# Create an index first
python fair_index.py index /path/to/data/
```

### "Model not found"
```bash
# Re-run setup to download model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

### Slow indexing
- Normal speed: ~10 files/minute
- Progress bar shows status
- For 1000+ files, run overnight

### No search results
```bash
# Check if data is indexed
python fair_index.py stats

# Try broader search terms
python fair_search.py "ocean"  # Instead of "ocean surface temperature salinity"
```

## 📖 Python API Quick Reference

```python
from search_engine import FAIRSearchEngine

# Initialize
engine = FAIRSearchEngine()

# Index files
engine.index_file("data.nc")
engine.index_directory("/path/to/data", extract_archives=True)

# Search
results = engine.search("ocean temperature", top_k=10)
similar = engine.find_similar("reference.nc", top_k=5)

# Results format
for r in results:
    print(r['filepath'])           # File path
    print(r['similarity_score'])   # 0-1 relevance
    print(r['title'])              # Dataset title
    print(r['institution'])        # Institution
    print(r['variables'])          # Variables dict

# Save index
engine.save()

# Statistics
stats = engine.get_stats()
print(f"Indexed {stats['total_vectors']} datasets")
```

## 🎓 Next Steps

### For Regular Use
1. Index your research data: `python fair_index.py index /my/data`
2. Search as needed: `python fair_search.py -i`
3. Re-index periodically: `python fair_index.py index /my/data`

### For Presentations
1. Work through Jupyter notebooks 00-99
2. Customize with your own examples
3. Present to your research group

### For Development
1. Read `PROJECT_STRUCTURE.md` for architecture
2. Each module is small and focused
3. Easy to extend or modify

### Optional: LLM Enrichment

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b

# Then see notebook 06_LLM_Enrichment.ipynb
```

## 💡 Pro Tips

1. **Index incrementally**: Add new data without rebuilding entire index
2. **Use interactive mode**: `fair_search.py -i` is fastest for exploring
3. **Validate first**: Catch bad files before indexing
4. **Archive everything**: System handles .zip automatically
5. **Add READMEs**: Companion docs improve search quality

## 📊 Performance Expectations

| Task | Speed | Notes |
|------|-------|-------|
| Validation | 1000 files/sec | Very fast |
| Indexing | 10 files/min | Includes embedding generation |
| Search | <200ms | Very fast, even with 10k files |
| Archive extraction | Varies | Depends on archive size |

## 🆘 Getting Help

1. Check `README.md` for full documentation
2. Review relevant Jupyter notebook
3. Read `PROJECT_STRUCTURE.md` for architecture
4. Check error messages - they're designed to be helpful!

## ✅ You're Ready!

You now have a working FAIR data discovery system:
- ✅ Index any NetCDF/HDF5/GRIB files
- ✅ Search with natural language
- ✅ Find similar datasets
- ✅ Handle archives automatically
- ✅ Validate data quality
- ✅ Discover companion documentation

**Start indexing your scientific data and making it FAIR!** 🎉🔬📊

---

**Questions?** See README.md for detailed documentation.
