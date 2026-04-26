# diagnose.py
import sys
import os
import subprocess

print("=" * 60)
print("  PERSONAL KNOWLEDGE BRAIN — FULL DIAGNOSIS REPORT")
print("=" * 60)

# 1. Python version
print(f"\n🐍 Python: {sys.version}")

# 2. Check all package versions
print("\n📦 PACKAGE VERSIONS:")
packages = [
    "langchain",
    "langchain-google-genai",
    "langchain-community",
    "langchain-chroma",
    "langchain-core",
    "google-generativeai",
    "google-ai-generativelanguage",
    "google-genai",
    "chromadb",
    "streamlit",
]
for pkg in packages:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", pkg],
            capture_output=True, text=True
        )
        found = False
        for line in result.stdout.split("\n"):
            if line.startswith("Version:"):
                print(f"  ✅ {pkg}: {line.split(':')[1].strip()}")
                found = True
                break
        if not found:
            print(f"  ❌ {pkg}: NOT INSTALLED")
    except Exception:
        print(f"  ❌ {pkg}: ERROR CHECKING")

# 3. Check .env file
print("\n⚙️  .env FILE CHECK:")
try:
    with open(".env", "r") as f:
        for line in f.readlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "API_KEY" in line:
                key = line.split("=")[1].strip()
                masked = key[:6] + "****" if len(key) > 6 else "****"
                print(f"  GOOGLE_API_KEY = {masked}")
            elif "EMBEDDING" in line:
                print(f"  {line}")
            elif "MODEL" in line:
                print(f"  {line}")
except FileNotFoundError:
    print("  ❌ .env FILE NOT FOUND!")

# 4. Test ALL embedding models
print("\n🔢 EMBEDDING MODEL TEST:")
try:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY", "")

    if not api_key or "your_google" in api_key:
        print("  ❌ No valid API key found in .env!")
    else:
        print(f"  API Key found: {api_key[:6]}****")
        print()

        models_to_test = [
            "models/embedding-001",
            "gemini-embedding-001",
            "models/text-embedding-004",
            "text-embedding-004",
            "models/gemini-embedding-001",
        ]

        working_model = None
        for model_name in models_to_test:
            try:
                from langchain_google_genai import (
                    GoogleGenerativeAIEmbeddings
                )
                emb = GoogleGenerativeAIEmbeddings(
                    model=model_name,
                    google_api_key=api_key,
                )
                result = emb.embed_query("test")
                print(f"  ✅ {model_name} → WORKS! Dims: {len(result)}")
                if not working_model:
                    working_model = model_name
            except Exception as e:
                err = str(e)[:120]
                print(f"  ❌ {model_name} → FAILED")
                print(f"     Error: {err}")
            print()

        if working_model:
            print(f"  🎯 USE THIS MODEL: {working_model}")
        else:
            print("  🔴 NO WORKING MODEL FOUND!")
            print("  Check your API key and package versions!")

except Exception as e:
    print(f"  ❌ Test failed completely: {e}")

# 5. Check vectorstore
print("\n💾 VECTORSTORE CHECK:")
if os.path.exists("./vectorstore"):
    files = list(os.walk("./vectorstore"))
    total = sum(len(f) for _, _, f in files)
    size = sum(
        os.path.getsize(os.path.join(root, f))
        for root, _, files_list in os.walk("./vectorstore")
        for f in files_list
    )
    print(f"  📁 vectorstore/ exists")
    print(f"  📄 Total files: {total}")
    print(f"  💽 Total size: {round(size/1024, 2)} KB")
else:
    print("  ⚪ vectorstore/ does NOT exist")

# 6. Check all src files
print("\n📁 PROJECT FILES CHECK:")
src_files = [
    "src/embeddings_manager.py",
    "src/rag_chain.py",
    "src/document_processor.py",
    "src/memory_manager.py",
    "src/utils.py",
    "src/__init__.py",
    "config.py",
    "app.py",
    "requirements.txt",
    ".env",
    ".streamlit/config.toml",
]
for f in src_files:
    if os.path.exists(f):
        size = os.path.getsize(f)
        print(f"  ✅ {f} ({size} bytes)")
    else:
        print(f"  ❌ {f} — MISSING!")

# 7. Show embeddings_manager.py model linecd 
print("\n🔍 EMBEDDING MODEL IN CODE:")
try:
    with open("src/embeddings_manager.py", "r") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if "embedding" in line.lower() and (
                "model" in line.lower() or "001" in line or "004" in line
            ):
                print(f"  Line {i+1}: {line.rstrip()}")
except FileNotFoundError:
    print("  ❌ src/embeddings_manager.py NOT FOUND!")

# 8. Show config.py model line
print("\n🔍 EMBEDDING MODEL IN CONFIG:")
try:
    with open("config.py", "r") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if "EMBEDDING_MODEL" in line:
                print(f"  Line {i+1}: {line.rstrip()}")
except FileNotFoundError:
    print("  ❌ config.py NOT FOUND!")

print("\n" + "=" * 60)
print("  ✅ DIAGNOSIS COMPLETE — PASTE OUTPUT IN CHAT!")
print("=" * 60)