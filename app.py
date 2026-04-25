
import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(override=True)

st.set_page_config(
    page_title="Personal Knowledge Brain",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    from config import Config
    from src.utils import validate_api_key, format_file_size
    from src.document_processor import DocumentProcessor
    from src.embeddings_manager import EmbeddingsManager
    from src.rag_chain import RAGChain
    from src.memory_manager import MemoryManager
except ImportError as e:
    st.error(f"Import error: {e}")
    st.code("pip install -r requirements.txt")
    st.stop()

st.markdown("""<style>
.hdr{background:linear-gradient(135deg,#6C63FF,#3B82F6);
padding:1.5rem;border-radius:12px;text-align:center;
color:white;margin-bottom:1rem;}
.umsg{background:linear-gradient(135deg,#6C63FF,#8B5CF6);
color:white;padding:1rem;border-radius:12px;margin:.5rem 0;}
.amsg{background:#1E1E2E;border:1px solid #6C63FF;
color:#FAFAFA;padding:1rem;border-radius:12px;margin:.5rem 0;}
.src{background:#262640;border-left:3px solid #6C63FF;
padding:.5rem;border-radius:6px;margin:.3rem 0;
font-size:.85rem;}
</style>""", unsafe_allow_html=True)


def init_session():
    defs = {
        "messages": [],
        "rag_chain": None,
        "embeddings_manager": None,
        "memory_manager": None,
        "vectorstore_ready": False,
        "api_key_valid": False,
        "stats": {
            "total_chunks": 0,
            "total_documents": 0,
            "storage_size": "0 KB",
            "indexed_files": [],
        },
    }
    for k, v in defs.items():
        if k not in st.session_state:
            st.session_state[k] = v


def init_managers():
    try:
        if st.session_state.memory_manager is None:
            st.session_state.memory_manager = MemoryManager()
        em = EmbeddingsManager()
        st.session_state.embeddings_manager = em
        st.session_state.rag_chain = RAGChain(
            em, st.session_state.memory_manager
        )
        if em.vectorstore_exists():
            st.session_state.vectorstore_ready = True
            st.session_state.stats = em.get_vectorstore_stats()
        return True
    except Exception as e:
        st.error(f"Init error: {e}")
        return False


init_session()

with st.sidebar:
    st.markdown("## 🧠 Knowledge Brain")
    st.caption("Personal RAG Assistant v3.0")
    st.divider()

    st.markdown("### 🔑 API Key")
    cur = Config.GOOGLE_API_KEY
    disp = (
        cur
        if (cur and cur != "your_google_api_key_here"
            and not cur.startswith(chr(34)))
        else ""
    )
    api_key = st.text_input(
        "Google API Key",
        value=disp,
        type="password",
        placeholder="AIzaSy...",
        key="api_input",
        help="Get FREE key: https://aistudio.google.com/app/apikey",
    )

    if st.button("Validate and Save", key="vbtn"):
        if not api_key:
            st.warning("Enter your API key first!")
        elif not api_key.startswith("AIza"):
            st.error("Key must start with AIza!")
        elif len(api_key) < 35:
            st.error("Key too short! Copy the full key.")
        else:
            with st.spinner("Validating..."):
                result = validate_api_key(api_key)
            if result["valid"]:
                Config.update_api_key(api_key)
                st.session_state.api_key_valid = True
                with st.spinner("Initializing AI..."):
                    init_managers()
                st.success(result["message"])
                st.rerun()
            else:
                st.error(result["message"])

    if st.session_state.api_key_valid:
        st.success("API Key Active")
    else:
        st.info(
            "[Get FREE API Key](https://aistudio.google.com/app/apikey)"
        )

    st.divider()
    st.markdown("### Upload Documents")
    ups = st.file_uploader(
        "Choose files",
        type=["pdf","docx","txt","md","csv"],
        accept_multiple_files=True,
        key="uploader",
    )
    if ups:
        for f in ups:
            st.caption(
                f"📄 {f.name} ({format_file_size(f.size)})"
            )

    if ups and st.button("Process Documents", key="pbtn"):
        if not st.session_state.api_key_valid:
            st.error("Validate API key first!")
        else:
            prog = st.progress(0)
            stat = st.empty()
            try:
                p = DocumentProcessor()
                all_docs = []
                stat.text("Reading files...")
                prog.progress(15)
                for f in ups:
                    docs = p.load_uploaded_file(f)
                    all_docs.extend(docs)
                if not all_docs:
                    st.error("No text extracted!")
                else:
                    stat.text("Chunking...")
                    prog.progress(40)
                    chunks = p.chunk_documents(all_docs)
                    stat.text("Embedding...")
                    prog.progress(70)
                    em = st.session_state.embeddings_manager
                    em.create_vectorstore(chunks)
                    stat.text("Building chain...")
                    prog.progress(90)
                    st.session_state.rag_chain.rebuild_chain()
                    st.session_state.vectorstore_ready = True
                    st.session_state.stats = (
                        em.get_vectorstore_stats()
                    )
                    prog.progress(100)
                    stat.text("Done!")
                    st.success(
                        f"Processed {len(ups)} files! "
                        f"({len(chunks)} chunks)"
                    )
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()
    st.markdown("### Knowledge Base")
    s = st.session_state.stats
    if st.session_state.vectorstore_ready:
        st.success("Ready")
    else:
        st.info("No documents yet")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Docs", s.get("total_documents", 0))
    with c2:
        st.metric("Chunks", s.get("total_chunks", 0))
    st.caption(f"Size: {s.get('storage_size','0 KB')}")
    if s.get("indexed_files"):
        with st.expander("Files"):
            for f in s["indexed_files"]:
                st.caption(f"📄 {f}")
    if st.button("Clear Knowledge Base", key="ckb"):
        em = st.session_state.embeddings_manager
        if em:
            em.delete_all()
        st.session_state.vectorstore_ready = False
        st.session_state.stats = {
            "total_chunks": 0,
            "total_documents": 0,
            "storage_size": "0 KB",
            "indexed_files": [],
        }
        st.rerun()
    st.divider()
    if st.button("Clear Chat", key="cc"):
        if st.session_state.memory_manager:
            st.session_state.memory_manager.clear_memory()
        st.session_state.messages = []
        st.rerun()

st.markdown("""
<div class='hdr'>
<h1>🧠 Personal Knowledge Brain</h1>
<p>Chat with your documents using AI-powered RAG</p>
</div>
""", unsafe_allow_html=True)

s = st.session_state.stats
ak = "API Active" if st.session_state.api_key_valid else "No API Key"
nd = s.get("total_documents", 0)
nc = s.get("total_chunks", 0)
rdy = "Ready" if st.session_state.vectorstore_ready else "Upload Docs"
st.info(f"{ak}  |  Docs: {nd}  |  Chunks: {nc}  |  {rdy}")

if not st.session_state.vectorstore_ready:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info(
            "**Step 1**\n\n"
            "[Get FREE API Key](https://aistudio.google.com/app/apikey)"
        )
    with c2:
        st.info("**Step 2**\n\nUpload PDF DOCX TXT CSV in sidebar")
    with c3:
        st.info("**Step 3**\n\nAsk anything about your documents!")
else:
    msgs = st.session_state.messages
    if not msgs:
        st.info("Knowledge base ready! Ask anything below.")
    for msg in msgs:
        role = msg.get("role","user")
        content = msg.get("content","")
        ts = msg.get("timestamp","")
        srcs = msg.get("sources",[])
        if role == "user":
            st.markdown(
                f"<div class='umsg'>"
                f"<b>You</b> <small>{ts}</small>"
                f"<br>{content}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div class='amsg'>"
                f"<b>AI</b> <small>{ts}</small>"
                f"<br>{content}</div>",
                unsafe_allow_html=True,
            )
            if srcs:
                with st.expander(f"Sources ({len(srcs)})"):
                    for src in srcs:
                        st.markdown(
                            f"<div class='src'>"
                            f"<b>{src.get('filename','?')}"
                            f"</b> Page:{src.get('page','?')}"
                            f"<br><small>"
                            f"{src.get('preview','')[:150]}"
                            f"</small></div>",
                            unsafe_allow_html=True,
                        )
    q = st.chat_input("Ask anything about your documents...")
    if q:
        ts = datetime.now().strftime("%H:%M")
        st.session_state.messages.append({
            "role": "user",
            "content": q,
            "sources": [],
            "timestamp": ts,
        })
        st.session_state.memory_manager.add_message("user", q)
        with st.spinner("Searching knowledge base..."):
            try:
                res = st.session_state.rag_chain.get_response(q)
                ans = res.get("answer","No response")
                srcs = res.get("sources",[])
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": ans,
                    "sources": srcs,
                    "timestamp": ts,
                })
                st.session_state.memory_manager.add_message(
                    "assistant", ans, srcs
                )
            except Exception as e:
                st.error(f"Error: {e}")
        st.rerun()
