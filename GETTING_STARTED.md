# 🚀 Getting Started with DataSplice

Complete guide to running your citation-backed research assistant.

## ✅ Prerequisites

- Python 3.9+
- OpenAI API key

## 📦 Installation

### 1. Set up environment

```bash
cd /Users/vineethvictor/DataSplice

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 2. Configure environment variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env  # or use any editor
```

Your `.env` should look like:
```
OPENAI_API_KEY=sk-your-actual-key-here
EMBED_MODEL=text-embedding-3-large
LLM_MODEL=gpt-4o-mini
VECTOR_DB_PATH=./data/vector_db
UPLOAD_DIR=./data/uploads
TOP_K=12
CLUSTERS=3
```

## 🏃 Running the Application

You need **TWO terminal windows** - one for backend, one for frontend.

### Option A: Use Startup Scripts (Easiest!)

**Terminal 1: Backend**
```bash
cd /Users/vineethvictor/DataSplice
./start_backend.sh
```

**Terminal 2: Frontend**
```bash
cd /Users/vineethvictor/DataSplice
./start_frontend.sh
```

### Option B: Manual Start

**Terminal 1: Start Backend**
```bash
cd /Users/vineethvictor/DataSplice
source venv/bin/activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2: Start Frontend**
```bash
cd /Users/vineethvictor/DataSplice
source venv/bin/activate
streamlit run frontend/app.py
```

### What You Should See

**Backend:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Frontend:**
Streamlit will automatically open at `http://localhost:8501`

**Keep both terminals running!**

## 🎯 Using the Application

### Step 1: Upload Documents

1. In the sidebar, click **"Browse files"**
2. Select one or more PDF files (DOCX and TXT also supported)
3. Click **"📤 Ingest Documents"**
4. Wait for processing (progress shown in UI)
5. You'll see: **"✓ Successfully ingested X chunks!"**

### Step 2: Ask Questions

1. In the main panel, enter your research question
2. Click **"🔍 Generate"**
3. Wait 10-20 seconds for:
   - Semantic search
   - Clustering
   - LLM synthesis
4. View your results:
   - **Summary** (6-8 line answer)
   - **Confidence Score** (Low/Medium/High)
   - **Key Findings** (organized subtopics)
   - **Evidence** (citations with source files & pages)

### Step 3: Explore Results

- **Read the summary** - concise answer to your question
- **Check confidence** - how reliable is the answer?
- **Review subtopics** - organized findings with bullets
- **Verify citations** - see exact source files and pages
- **Download JSON** - export complete response

## 🔍 Example Queries

Try these with your documents:

```
"What is the main topic of these documents?"
"What are the key findings or conclusions?"
"What methodology was used in the research?"
"What are the limitations mentioned?"
"What data sources were analyzed?"
```

## 🛠️ API Access (Optional)

### Check Backend Health

```bash
curl http://localhost:8000/health
```

### Ingest via API

```bash
curl -X POST "http://localhost:8000/ingest" \
  -F "files=@/path/to/your/document.pdf"
```

### Query via API

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the main findings?", "top_k": 12}'
```

## 📊 API Documentation

Once backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## ⚠️ Troubleshooting

### Backend won't start

**Problem**: `ModuleNotFoundError`
**Solution**:
```bash
pip install -r backend/requirements.txt
```

**Problem**: `OPENAI_API_KEY not set`
**Solution**: Edit `.env` file and add your API key

### Frontend won't connect

**Problem**: "Connection refused"
**Solution**: Make sure backend is running first (Terminal 1)

### No results for query

**Problem**: Empty vector store
**Solution**: Upload documents first via the sidebar

### Slow query responses

**Problem**: Takes 30+ seconds
**Solution**: 
- Normal for first query (cold start)
- Reduce `TOP_K` in `.env` (try 8 instead of 12)
- Use shorter documents

## 💰 API Costs

**Embeddings** (text-embedding-3-large):
- ~$0.13 per 1M tokens
- Typical document (10 pages) ≈ $0.001

**LLM** (gpt-4o-mini):
- ~$0.150 per 1M input tokens
- ~$0.600 per 1M output tokens
- Typical query ≈ $0.002-0.005

**Example**: Processing 100 documents + 50 queries ≈ $0.50

## 🔒 Privacy

- All data stored locally in `./data/`
- Vector database: `./data/vector_db`
- Uploaded files: `./data/uploads`
- Only API calls to OpenAI (embeddings + LLM)
- No data shared with third parties

## 🎓 Next Steps

1. **Test with sample PDFs** - Try with 2-3 research papers
2. **Experiment with queries** - See what works best
3. **Check confidence scores** - Learn when answers are reliable
4. **Review citations** - Verify sources are accurate
5. **Export results** - Download JSON for records

## 📚 Additional Resources

- **README.md** - Full documentation
- **test_*.py** - Test scripts for each component
- **backend/main.py** - API endpoint code
- **frontend/app.py** - UI code

## 🐛 Issues?

Check logs in your terminal windows for detailed error messages.

---

**🎉 You're ready to go! Start by uploading a PDF in the sidebar.**


