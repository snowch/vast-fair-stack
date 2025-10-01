# FAIR Scientific Data Discovery System - Project Structure

## 📁 Complete File Organization

```
fair-data-discovery/
│
├── 📋 Documentation
│   ├── README.md                          # Main documentation
│   ├── PROJECT_STRUCTURE.md               # This file
│   └── requirements.txt                   # Python dependencies
│
├── ⚙️ Configuration
│   └── config.py                          # System configuration settings
│
├── 🔧 Core Modules (Small & Modular)
│   ├── utils.py                           # Shared utility functions
│   ├── file_validator.py                 # File validation (magic bytes)
│   ├── metadata_extractors.py            # NetCDF/HDF5/GRIB extraction
│   ├── companion_finder.py               # Find companion documents
│   ├── companion_extractor.py            # Extract companion content
│   ├── archive_handler.py                # Handle .zip, .tar.gz files
│   ├── embedding_generator.py            # Generate embeddings (local)
│   ├── vector_index.py                   # FAISS vector search
│   ├── search_engine.py                  # Main search engine
│   └── llm_enricher.py                   # Optional LLM enrichment
│
├── 🖥️ Command-Line Tools
│   ├── fair_index.py                     # Indexing CLI tool
│   ├── fair_search.py                    # Search CLI tool
│   └── download_and_validate.py          # Smart download script
│
├── 📓 Jupyter Notebooks (For Presentations)
│   ├── 00_Setup_and_Installation.ipynb   # Getting started
│   ├── 01_File_Validation.ipynb          # Validate files
│   ├── 02_Metadata_Extraction.ipynb      # Extract metadata
│   ├── 03_Companion_Documents.ipynb      # Discover companions
│   ├── 04_Vector_Search.ipynb            # Semantic search
│   ├── 06_LLM_Enrichment.ipynb           # Optional LLM features
│   └── 99_Complete_Workflow.ipynb        # End-to-end examples
│
├── 🚀 Setup Scripts
│   └── setup.sh                          # Quick setup script
│
├── 💾 Data Directories (Created Automatically)
│   ├── indexes/                          # FAISS index storage
│   │   ├── faiss_index.bin
│   │   ├── metadata_store.pkl
│   │   └── filepath_map.pkl
│   ├── cache/                            # Embedding cache
│   └── temp/                             # Temporary files
│
└── 📊 Sample Data (Optional)
    └── sample_data/                      # Test datasets
```

## 📦 Module Dependencies

### Core Dependencies (Required)
```
config.py
  └── (no dependencies)

utils.py
  └── (no dependencies)

file_validator.py
  ├── config.py
  └── utils.py

metadata_extractors.py
  ├── config.py
  ├── utils.py
  └── External: netCDF4, h5py, pygrib

companion_finder.py
  └── config.py

companion_extractor.py
  └── utils.py

archive_handler.py
  └── config.py

embedding_generator.py
  ├── config.py
  └── External: sentence-transformers

vector_index.py
  ├── config.py
  └── External: faiss-cpu, numpy

search_engine.py
  ├── metadata_extractors.py
  ├── companion_finder.py
  ├── companion_extractor.py
  ├── archive_handler.py
  ├── embedding_generator.py
  ├── vector_index.py
  ├── file_validator.py
  └── config.py

llm_enricher.py (optional)
  ├── config.py
  └── External: requests (for Ollama)
```

## 🎯 Module Sizes (Approximate)

| Module | Lines | Purpose | Update Frequency |
|--------|-------|---------|------------------|
| config.py | 80 | Settings | Rare |
| utils.py | 150 | Helpers | Rare |
| file_validator.py | 180 | Validation | Occasional |
| metadata_extractors.py | 300 | Extraction | Occasional |
| companion_finder.py | 120 | Discovery | Occasional |
| companion_extractor.py | 250 | Content extraction | Occasional |
| archive_handler.py | 200 | Archives | Rare |
| embedding_generator.py | 150 | Embeddings | Rare |
| vector_index.py | 250 | FAISS index | Occasional |
| search_engine.py | 280 | Main engine | Frequent |
| llm_enricher.py | 250 | LLM (optional) | Occasional |
| fair_index.py | 200 | CLI indexing | Frequent |
| fair_search.py | 280 | CLI search | Frequent |

**Total Core System: ~2,700 lines** (highly modular)

## 🔄 Typical Update Workflow

### Scenario: Update Search Results Display

**Files to modify:**
1. `fair_search.py` - Update formatting (20-30 lines)

**No need to touch:**
- Core modules remain unchanged
- Other scripts unaffected

### Scenario: Add New File Format (e.g., Zarr)

**Files to modify:**
1. `config.py` - Add file extensions
2. `metadata_extractors.py` - Add ZarrExtractor class (~50 lines)
3. Update `MetadataExtractor.extract()` to route to new extractor

**No need to touch:**
- Search engine
- CLI tools
- Vector index
- Other extractors

### Scenario: Improve Metadata Enrichment

**Files to modify:**
1. `llm_enricher.py` - Update prompts or add methods

**No need to touch:**
- Everything else (optional module)

## 📊 Data Flow

```
Input Data → Validation → Extraction → Enrichment → Embedding → Indexing → Search
                ↓            ↓           ↓           ↓           ↓         ↓
         file_validator  metadata_   companion_  embedding_  vector_   search_
                          extractors  extractor   generator    index    engine
```

## 🎓 Notebook Presentation Order

For academic presentations, follow this order:

1. **00_Setup** - 15 min - Get everyone running
2. **01_Validation** - 10 min - Show real-world problems
3. **02_Metadata** - 15 min - Extraction techniques
4. **03_Companions** - 10 min - External documentation
5. **04_Search** - 20 min - How semantic search works
6. **06_LLM** (optional) - 15 min - Advanced enrichment
7. **99_Workflow** - 20 min - Complete examples

**Total: ~90 minutes** (adjust as needed)

## 🔧 Customization Points

### Easy Customizations (No Core Changes)
- Add new search CLI options in `fair_search.py`
- Change embedding model in `config.py`
- Adjust similarity threshold in `config.py`
- Add custom companion patterns in `config.py`

### Medium Customizations (Single Module)
- Add new file format support in `metadata_extractors.py`
- Improve LLM prompts in `llm_enricher.py`
- Add new validation checks in `file_validator.py`
- Customize search result display in `fair_search.py`

### Advanced Customizations (Multiple Modules)
- Add web interface (new module + search_engine.py integration)
- Add MCP server support (new module)
- Implement distributed indexing (vector_index.py + new coordinator)
- Add real-time file watching (new module + search_engine.py)

## 🧪 Testing Strategy

### Unit Tests (Per Module)
```python
# test_file_validator.py
def test_netcdf_validation()
def test_html_detection()
def test_directory_validation()

# test_metadata_extractors.py
def test_netcdf_extraction()
def test_minimal_metadata()
def test_companion_integration()

# test_vector_index.py
def test_add_and_search()
def test_duplicate_removal()
def test_save_and_load()
```

### Integration Tests
```python
# test_end_to_end.py
def test_index_and_search_workflow()
def test_archive_processing()
def test_batch_indexing()
```

### Performance Tests
```python
# test_performance.py
def test_search_speed()
def test_indexing_throughput()
def test_memory_usage()
```

## 📈 Scaling Guidelines

### Small Scale (< 1,000 files)
- Use default settings
- Single machine
- No special configuration needed

### Medium Scale (1,000 - 10,000 files)
- Consider batch processing
- May need >8GB RAM during indexing
- Search remains fast

### Large Scale (> 10,000 files)
- Process in batches
- Consider index sharding (future enhancement)
- May need dedicated indexing machine

## 🔐 Security Considerations

### File Validation
- Magic byte checking prevents malicious files
- Path traversal protection in archive handler
- Size limits on file processing

### Privacy
- All processing local (no external API calls)
- Optional LLM uses local Ollama
- No data leaves your machine

### Best Practices
- Validate files before indexing
- Use virtual environments
- Keep dependencies updated
- Review companion documents before trusting content

## 🚀 Deployment Scenarios

### Personal Research Use
- Run on laptop/desktop
- Use setup.sh for installation
- Index personal datasets

### Lab/Group Use
- Shared file server with index
- Multiple users access same index
- Periodic re-indexing of new data

### Institutional Repository
- Dedicated indexing server
- Automated ingestion pipeline
- Web interface for users (future enhancement)

### Cloud Deployment
- Docker container (create Dockerfile)
- API service (future enhancement)
- Scalable storage

## 📚 Future Enhancements

### Priority 1 (High Value, Low Complexity)
- [ ] Web UI for browsing
- [ ] Export to BibTeX/JSON
- [ ] Advanced filtering by date/format
- [ ] Batch metadata editing

### Priority 2 (High Value, Medium Complexity)
- [ ] MCP server for LLM integration
- [ ] Real-time file watching
- [ ] Plugin system for custom extractors
- [ ] Distributed indexing

### Priority 3 (Nice to Have)
- [ ] Visualization of search results
- [ ] Data lineage tracking
- [ ] Version control for datasets
- [ ] API server for remote access

## 🤝 Contributing Guide

### Adding Features
1. Create new module if needed (keep it small!)
2. Add tests
3. Update relevant notebook
4. Update documentation
5. Submit with examples

### Reporting Issues
1. Include minimal reproducing example
2. Specify Python version and OS
3. Attach sample file (if relevant)
4. Check existing issues first

### Code Style
- Follow PEP 8
- Type hints encouraged
- Docstrings for public functions
- Keep functions < 50 lines when possible

---

**This modular design makes the system easy to understand, maintain, and extend!** 🎯
