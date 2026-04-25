# 🧠 Personal Knowledge Brain

## Overview

**Personal Knowledge Brain** is a powerful, AI-powered RAG (Retrieval-Augmented Generation) application that turns your documents into an interactive knowledge base. Upload PDFs, Word docs, text files, CSVs, or even web pages, then ask questions in natural language — the AI answers using only your uploaded content, with full source citations.

## ✨ Features

- 📄 **Multi-format Support**: PDF, DOCX, TXT, MD, CSV, and URLs
- 🔍 **Smart Search**: Semantic similarity search with ChromaDB vector store
- 💬 **Conversational AI**: Chat with memory and follow-up question support
- 🧠 **Google Gemini Integration**: Free AI model with generous limits
- 🌐 **Web Scraping**: Ingest content from any website
- 💾 **Session Management**: Save and restore chat sessions
- 🎨 **Beautiful UI**: Dark-themed Streamlit interface
- 📚 **Source Citations**: Every answer shows exactly which document it came from
- ⚡ **Fast Embeddings**: Google embedding-001 for quick document indexing
- 🔒 **Privacy First**: Your documents stay local, API key stays in .env

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | Streamlit |
| LLM | Google Gemini 1.5 Flash |
| Embeddings | Google embedding-001 |
| Vector DB | ChromaDB |
| Document Parsing | PyPDF2, PyMuPDF, python-docx |
| Web Scraping | BeautifulSoup4, requests |
| Database | SQLite (sessions) |
| Testing | pytest |

## 🚀 Quick Start (3 Steps)

### Step 1: Clone & Install

```bash
git clone <your-repo-url>
cd personal-knowledge-brain
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### Step 2: Configure

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your Google API key
# Or enter it directly in the app sidebar
```

### Step 3: Run

```bash
streamlit run app.py
```

Open your browser at: **http://localhost:8501**

## 🔑 Get Free Google API Key

1. Go to: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Select **"Create API key in new project"**
5. Copy the key (starts with `AIza...`)
6. Paste it in the app sidebar or .env file

✅ **100% FREE** — No credit card needed!  
✅ **Works instantly** — No approval required!  
✅ **Generous free tier**: 15 req/min, 1M tokens/min, 1,500 req/day

## 📁 Project Structure

```
personal-knowledge-brain/
├── app.py                      # Main Streamlit application
├── config.py                   # Configuration loader
├── ingest.py                   # CLI document ingestion script
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not in git)
├── .env.example                # Env template
├── .gitignore                  # Git ignore rules
├── .streamlit/
│   ├── config.toml             # Streamlit theme config
│   └── secrets.toml.example    # Cloud secrets template
├── src/
│   ├── __init__.py             # Package exports
│   ├── utils.py                # Utility functions
│   ├── document_processor.py   # Document loading & chunking
│   ├── embeddings_manager.py   # Vector store management
│   ├── rag_chain.py            # RAG conversation chain
│   └── memory_manager.py       # Chat history & sessions
├── tests/                      # pytest test suite
├── documents/                  # Uploaded documents
├── vectorstore/                # ChromaDB persistent storage
├── sessions/                   # SQLite database
└── logs/                       # Application logs
```

## 🖥️ CLI Usage

```bash
# Process all documents in ./documents
python ingest.py

# Process a specific folder
python ingest.py --folder ./my_docs

# Clear vectorstore and re-ingest
python ingest.py --folder ./my_docs --reset

# Filter by file type
python ingest.py --format pdf

# Show verbose output
python ingest.py --verbose
```

## 🌐 Deploy to Streamlit Cloud (FREE)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Add `GOOGLE_API_KEY` in App Settings → Secrets
5. Click **Deploy!**

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `GOOGLE_API_KEY invalid` | Get a new key at aistudio.google.com |
| `ChromaDB errors` | Delete `vectorstore/` folder and restart |
| `PDF not loading` | Install PyMuPDF: `pip install pymupdf` |
| `Out of memory` | Reduce `CHUNK_SIZE` in .env to 500 |
| `Rate limit exceeded` | Wait a minute — free tier has limits |

## 📝 License

MIT License — feel free to use, modify, and distribute!

---

Built with ❤️ using Python, LangChain, and Streamlit.
