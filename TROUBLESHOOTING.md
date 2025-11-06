# 🔧 DataSplice Troubleshooting Guide

## Common Issues & Solutions

---

### ✅ FIXED: OpenAI "proxies" Error

**Error Message:**
```
Client.init() got an unexpected keyword argument 'proxies'
```

**Cause:** Outdated OpenAI library (v1.3.7)

**Solution:** ✅ Already fixed! Updated to OpenAI v2.6.1

**Verification:**
```bash
cd /Users/vineethvictor/DataSplice
source venv/bin/activate
python -c "import openai; print(openai.__version__)"
# Should show: 2.6.1
```

---

### ✅ FIXED: PyMuPDF "tools" Module Error

**Error Message:**
```
ModuleNotFoundError: No module named 'tools'
```

**Cause:** Corrupted PyMuPDF installation

**Solution:** ✅ Already fixed! Reinstalled PyMuPDF + PyMuPDFb

**Verification:**
```bash
cd /Users/vineethvictor/DataSplice
source venv/bin/activate
python -c "import fitz; print(fitz.__version__)"
# Should show: 1.23.8
```

---

### ✅ FIXED: Frontend Import Error

**Error Message:**
```
ModuleNotFoundError: No module named 'frontend'
```

**Cause:** Python path issues

**Solution:** ✅ Already fixed! Updated `frontend/app.py`

**Verification:**
```bash
cd /Users/vineethvictor/DataSplice
source venv/bin/activate
python -c "from frontend.app import *; print('✓ Working')"
```

---

## Backend Won't Start

### Symptoms
- `Address already in use` error
- Port 8000 is blocked

### Solution
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Restart backend
cd /Users/vineethvictor/DataSplice
./start_backend.sh
```

---

## Frontend Won't Start

### Symptoms
- `Address already in use` error
- Port 8501 is blocked

### Solution
```bash
# Kill Streamlit processes
pkill -f streamlit

# Restart frontend
cd /Users/vineethvictor/DataSplice
./start_frontend.sh
```

---

## OpenAI API Errors

### Symptoms
- `AuthenticationError: 401 Unauthorized`
- `Invalid API key provided`

### Solution
1. Check your `.env` file:
```bash
cat .env | grep OPENAI_API_KEY
```

2. Ensure key starts with `sk-`
3. Test the key:
```bash
cd /Users/vineethvictor/DataSplice
source venv/bin/activate
python -c "
from openai import OpenAI
client = OpenAI()
response = client.models.list()
print('✓ API key valid')
"
```

---

## Document Ingestion Fails

### Symptoms
- PDF extraction errors
- Embedding failures
- Upload timeouts

### Solutions

#### For PDF Issues:
```bash
# Verify PyMuPDF
python -c "import fitz; print(fitz.__version__)"
```

#### For Embedding Issues:
1. Check OpenAI API key (see above)
2. Check rate limits (free tier: 3 RPM)
3. Try smaller batch sizes

#### For Timeouts:
1. Upload fewer/smaller files
2. Check network connection
3. Increase timeout in `frontend/utils/api.py`

---

## ChromaDB Issues

### Symptoms
- `Collection not found`
- Vector store errors

### Solution
```bash
# Clear and recreate vector DB
rm -rf data/vectordb/
mkdir -p data/vectordb

# Restart backend (will reinitialize)
./start_backend.sh
```

---

## Dependency Issues

### Symptoms
- Import errors
- Module not found errors

### Solution
```bash
# Reinstall all dependencies
cd /Users/vineethvictor/DataSplice
source venv/bin/activate
pip install --upgrade -r backend/requirements.txt
```

---

## Virtual Environment Issues

### Symptoms
- `command not found: source`
- Permission errors

### Solution
```bash
# Recreate virtual environment
cd /Users/vineethvictor/DataSplice
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

---

## Check System Status

Run this comprehensive check:

```bash
cd /Users/vineethvictor/DataSplice
source venv/bin/activate

echo "=== Python Version ==="
python --version

echo -e "\n=== Key Dependencies ==="
pip show openai | grep Version
pip show pymupdf | grep Version
pip show streamlit | grep Version
pip show chromadb | grep Version

echo -e "\n=== Backend Module Test ==="
python -c "from backend.main import app; print('✓ Backend OK')"

echo -e "\n=== Frontend Module Test ==="
python -c "from frontend.app import *; print('✓ Frontend OK')"

echo -e "\n=== OpenAI Test ==="
python -c "from openai import OpenAI; print('✓ OpenAI OK')"

echo -e "\n=== PyMuPDF Test ==="
python -c "import fitz; print('✓ PyMuPDF OK')"

echo -e "\n=== All checks complete! ==="
```

---

## Still Having Issues?

1. **Check the logs:**
   - Backend logs appear in Terminal 1
   - Frontend logs appear in Terminal 2

2. **Restart everything:**
   ```bash
   # Kill all processes
   pkill -f uvicorn
   pkill -f streamlit
   
   # Start fresh
   ./start_backend.sh  # Terminal 1
   ./start_frontend.sh # Terminal 2
   ```

3. **Nuclear option (full reset):**
   ```bash
   # WARNING: Deletes all ingested documents!
   cd /Users/vineethvictor/DataSplice
   
   # Remove virtual environment
   rm -rf venv
   
   # Remove vector database
   rm -rf data/vectordb
   
   # Recreate environment
   python3 -m venv venv
   source venv/bin/activate
   pip install -r backend/requirements.txt
   
   # Restart
   ./start_backend.sh
   ```

---

## Need More Help?

Check these files for more information:
- `README.md` - Full project overview
- `GETTING_STARTED.md` - Setup instructions
- `READY_TO_RUN.md` - Current status
- `PRD.md` - Product requirements

---

**Last Updated:** After fixing OpenAI v2.6.1 upgrade

