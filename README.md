# DataSplice 🔍

A **local-first, retrieval-augmented research assistant** that transforms your document corpus into citation-backed intelligence. Built with FastAPI + Streamlit + ChromaDB + OpenAI.

Ask questions. Get structured summaries. See the evidence. All running on your machine.

![DataSplice UI](https://raw.githubusercontent.com/vineethvictor17/DataSplice/main/images/app-screenshot-1.png)
*Query interface with confidence scoring and real-time corpus stats*

![Query Results](https://raw.githubusercontent.com/vineethvictor17/DataSplice/main/images/app-screenshot-2.png)
*Structured summaries with subtopics, bullet points, and full citation transparency*

---

## 🎯 What You Get

* **Multi-format ingestion**: PDF, DOCX, TXT → vectorized and searchable
* **Semantic search**: ChromaDB vector store with cosine similarity
* **Smart clustering**: K-means grouping of retrieved chunks into subtopics
* **LLM synthesis**: Structured summaries with GPT-4o-mini in JSON mode
* **Citation transparency**: Every claim linked to source file + page
* **Confidence scoring**: Evidence-based reliability metrics
* **Local persistence**: All data stored in `./data` (uploads + vector DB)
* **Clean UI**: Streamlit interface with real-time corpus stats

---

## 🚀 Quick Start

### 1. Prerequisites

* **Python 3.9+** (tested on 3.12)
* **OpenAI API key** (for embeddings + LLM)
* **macOS/Linux** (Windows WSL works too)

### 2. Clone & Setup

```bash
git clone https://github.com/vineethvictor17/DataSplice.git
cd DataSplice

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

**Edit `.env` and add your OpenAI API key:**

```bash
OPENAI_API_KEY=sk-your_actual_key_here
```

### 4. Run the Application

**Option A: Use the startup scripts (recommended)**

```bash
# Terminal 1: Start backend
chmod +x start_backend.sh
./start_backend.sh

# Terminal 2: Start frontend
chmod +x start_frontend.sh
./start_frontend.sh
```

**Option B: Manual startup**

```bash
# Terminal 1: Backend
source venv/bin/activate
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
source venv/bin/activate
streamlit run frontend/app.py
```

**Access the app:**
* 🎨 **Frontend UI**: http://localhost:8501
* 🔧 **Backend API**: http://localhost:8000
* 📚 **API Docs**: http://localhost:8000/docs

---

## 📖 How to Use

### Ingest Documents

1. Click **"Browse files"** in the sidebar
2. Upload PDF/DOCX/TXT files (multiple files supported)
3. Click **"📤 Ingest Documents"**
4. Watch the corpus stats update

### Query Your Corpus

1. Type your research question in the main panel (e.g., *"What are the key evolutionary mechanisms discussed?"*)
2. Press **Enter** or click **"🔍 Generate Answer"**
3. Review the structured response:
   * **Summary**: 6-8 line synthesis
   * **Subtopics**: Thematic clusters with bullet points
   * **Confidence**: Evidence strength indicator
   * **Citations**: Source file, page, and excerpt for every claim

### Manage Your Corpus

* **View stats**: See document count and total chunks in the sidebar
* **Refresh stats**: Click 🔄 to update
* **Clear corpus**: Click 🗑️ (with confirmation) to delete all documents

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         STREAMLIT UI                            │
│  (Upload, Query Input, Results Display, Corpus Management)     │
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTP
┌───────────────────────────────▼─────────────────────────────────┐
│                         FASTAPI BACKEND                         │
├─────────────────────────────────────────────────────────────────┤
│  /health  │  /ingest  │  /query  │  /stats  │  /corpus (DELETE) │
└───────┬───────────────────┬─────────────────┬───────────────────┘
        │                   │                 │
    ┌───▼────┐       ┌──────▼──────┐   ┌─────▼─────┐
    │Extract │       │   Embed     │   │  Retrieve │
    │ (PDF)  │──────▶│ (OpenAI)    │──▶│ (ChromaDB)│
    └────────┘       └─────────────┘   └─────┬─────┘
                                              │
                                        ┌─────▼─────┐
                                        │  Cluster  │
                                        │ (K-means) │
                                        └─────┬─────┘
                                              │
                                        ┌─────▼─────┐
                                        │Synthesize │
                                        │(GPT-4o)   │
                                        └───────────┘
```

### Data Flow

1. **Ingestion Pipeline**:
   * `extract_text.py` → Parse PDFs (PyMuPDF), DOCX (python-docx)
   * `chunking.py` → Sentence-aware splitting (600 tokens, 90 overlap)
   * `embedding.py` → Generate vectors via OpenAI `text-embedding-3-large`
   * `vector_store.py` → Upsert to ChromaDB with metadata (file, page, chunk_index)

2. **Query Pipeline**:
   * `vector_store.py` → Semantic search (top-k retrieval)
   * `fusion.py` → K-means clustering (3 subtopics) + deduplication
   * `llm_summarizer.py` → GPT-4o-mini JSON mode synthesis
   * `confidence.py` → Heuristic scoring (coverage + diversity)

3. **API Layer**:
   * FastAPI endpoints with Pydantic validation
   * CORS middleware for frontend-backend communication
   * Structured logging for debugging

---

## 🛠️ Project Structure

```
DataSplice/
├── backend/
│   ├── main.py                 # FastAPI app + endpoints
│   ├── ingestion/
│   │   ├── extract_text.py    # PDF/DOCX parsing
│   │   ├── chunking.py        # Text splitting
│   │   └── embedding.py       # OpenAI embedding generation
│   ├── retrieval/
│   │   ├── vector_store.py    # ChromaDB operations
│   │   └── fusion.py          # Clustering + deduplication
│   ├── synthesis/
│   │   ├── llm_summarizer.py  # GPT-4o-mini synthesis
│   │   └── confidence.py      # Scoring logic
│   ├── models/
│   │   └── schemas.py         # Pydantic models
│   └── utils/
│       ├── config.py          # Environment config
│       └── logger.py          # Logging setup
├── frontend/
│   ├── app.py                 # Streamlit main app
│   ├── components/
│   │   ├── panels.py          # Sidebar + query panel
│   │   ├── evidence.py        # Citation table
│   │   └── metrics.py         # Confidence display
│   └── utils/
│       └── api.py             # Backend HTTP client
├── data/
│   ├── uploads/               # Ingested documents (gitignored)
│   ├── vector_db/             # ChromaDB persistence (gitignored)
│   └── samples/               # Example documents
├── .env.example               # Environment template
├── start_backend.sh           # Backend startup script
├── start_frontend.sh          # Frontend startup script
├── SYSTEM_ARCHITECTURE.md     # Deep dive technical docs
├── INTERVIEW_CHEATSHEET.md    # Interview prep guide
└── README.md                  # This file
```

---

## 🧪 Testing

We include several test scripts to validate the pipeline:

```bash
# Test individual components
python test_extraction.py       # PDF parsing
python test_chunking.py         # Text splitting
python test_embeddings.py       # OpenAI embedding generation
python test_vector_store.py     # ChromaDB operations

# Test end-to-end pipelines
python test_full_pipeline.py    # Ingestion pipeline
python test_query_pipeline.py   # Query pipeline
```

---

## ⚙️ Configuration

Key environment variables in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | **Required** | Your OpenAI API key |
| `EMBED_MODEL` | `text-embedding-3-large` | Embedding model (3072-dim) |
| `LLM_MODEL` | `gpt-4o-mini` | Language model for synthesis |
| `TOP_K` | `12` | Number of chunks to retrieve |
| `CLUSTERS` | `3` | Subtopic clusters |
| `CHUNK_SIZE` | `600` | Target tokens per chunk |
| `CHUNK_OVERLAP` | `90` | Overlap tokens between chunks |
| `BACKEND_URL` | `http://localhost:8000` | Backend API address |

---

## 📊 Design Decisions

### Why OpenAI `text-embedding-3-large`?
* **High dimensionality** (3072): Better semantic capture than smaller models
* **Strong performance**: State-of-the-art on MTEB benchmarks
* **Cost-effective**: $0.13 per 1M tokens (vs. Ada v2 at $0.10, but better quality)

### Why 600 token chunks with 90 token overlap?
* **600 tokens**: Balances context (enough for semantic coherence) vs. granularity (precise retrieval)
* **90 token overlap**: Prevents information loss at chunk boundaries (15% overlap is empirically optimal)
* **Sentence-aware splitting**: Avoids mid-sentence cuts for better readability

### Why K-means clustering?
* **Subtopic discovery**: Groups semantically similar chunks into thematic clusters
* **Deduplication**: Prevents redundant information in synthesis
* **Scalable**: O(k*n) complexity, fast enough for 12-50 chunks

### Why GPT-4o-mini?
* **Cost**: ~15x cheaper than GPT-4 ($0.15 vs $2.50 per 1M input tokens)
* **Speed**: ~2x faster response times
* **Quality**: Sufficient for structured summarization tasks
* **JSON mode**: Reliable structured output with schema validation

---

## 🔒 Privacy & Security

* ✅ **Local-first**: All documents stored in `./data` on your machine
* ✅ **No cloud storage**: No external databases or file hosting
* ⚠️ **OpenAI API calls**: Text sent to OpenAI for embeddings + LLM (subject to [OpenAI's privacy policy](https://openai.com/policies/privacy-policy))
* ✅ **No telemetry**: No tracking or analytics
* ✅ **Single-user**: No authentication or multi-tenancy concerns

**Note**: If you need enterprise-grade data privacy, consider using local embedding models (e.g., `sentence-transformers`) and local LLMs (e.g., Ollama with Llama 3).

---

## 🐛 Troubleshooting

### Backend won't start

**Issue**: `ModuleNotFoundError` or `ImportError`

**Fix**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r backend/requirements.txt

# Check Python version
python --version  # Should be 3.9+
```

### PyMuPDF installation issues

**Issue**: `ModuleNotFoundError: No module named 'tools'` from `fitz`

**Fix**:
```bash
pip uninstall PyMuPDF PyMuPDFb -y
pip install PyMuPDF==1.23.8 PyMuPDFb==1.23.7
```

### OpenAI API errors

**Issue**: `Invalid API key` or `proxies argument` error

**Fix**:
1. Verify `.env` has correct `OPENAI_API_KEY`
2. Ensure `openai>=1.12.0` (check with `pip show openai`)
3. Restart backend after env changes

### Frontend connection refused

**Issue**: `Connection refused at http://localhost:8000`

**Fix**:
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check backend logs for errors
3. Ensure `BACKEND_URL` in `.env` matches backend address

### Corpus stats not updating

**Issue**: Sidebar shows 0 documents after ingestion

**Fix**:
1. Click the 🔄 **Refresh Stats** button
2. Check backend logs for ingestion errors
3. Verify ChromaDB folder exists: `ls data/vector_db/`

### Low confidence scores

**Issue**: All queries return "Low" confidence

**Fix**:
* **Ingest more documents**: Scores improve with corpus size
* **Check relevance**: Ensure documents actually cover the query topic
* **Try specific queries**: Broad questions yield lower confidence

For more detailed troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

---

## 📚 Documentation

* **[SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)**: Deep dive into codebase, data flow, and LLM design
* **[INTERVIEW_CHEATSHEET.md](INTERVIEW_CHEATSHEET.md)**: How to present this project in AI engineer interviews
* **[GETTING_STARTED.md](GETTING_STARTED.md)**: Step-by-step setup guide
* **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**: Common issues and solutions

---

## 🎯 Use Cases

* **Academic research**: Summarize literature across multiple papers
* **Legal discovery**: Query case files and depositions
* **Technical documentation**: Search internal wikis and manuals
* **Market research**: Synthesize analyst reports
* **Competitive intelligence**: Aggregate competitor filings

---

## 🚧 Known Limitations

* **No web crawling**: Only processes uploaded files
* **English-optimized**: Best results with English documents
* **Single-user**: No authentication or collaboration features
* **Basic chunking**: Fixed-length splits (no semantic segmentation)
* **No re-ranking**: Simple cosine similarity (no cross-encoder re-ranking)
* **No hybrid search**: Pure vector search (no BM25 keyword matching)

### Future Enhancements

* [ ] Cross-encoder re-ranking for better relevance
* [ ] Hybrid search (BM25 + vector)
* [ ] LLM-based relevance filtering
* [ ] Query expansion/decomposition
* [ ] Document versioning and updates
* [ ] Multi-language support
* [ ] Image/table extraction from PDFs

---

## 🤝 Contributing

Contributions welcome! To contribute:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

Please ensure:
* Code follows PEP 8 style guidelines
* New features include tests
* Documentation is updated

---

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with:
* [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
* [Streamlit](https://streamlit.io/) - Rapid UI development
* [ChromaDB](https://www.trychroma.com/) - Embeddable vector database
* [OpenAI](https://openai.com/) - Embeddings and LLM
* [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF parsing
* [scikit-learn](https://scikit-learn.org/) - K-means clustering

---

## 💬 Support

* **Issues**: [GitHub Issues](https://github.com/vineethvictor17/DataSplice/issues)
* **Discussions**: [GitHub Discussions](https://github.com/vineethvictor17/DataSplice/discussions)
* **Email**: vineethvictor1517@gmail.com

---

## ⭐ Star This Repo

If you find DataSplice useful, please give it a ⭐ on GitHub! It helps others discover the project.

---

**Built with ❤️ for transparent, citation-backed AI research assistants.**
